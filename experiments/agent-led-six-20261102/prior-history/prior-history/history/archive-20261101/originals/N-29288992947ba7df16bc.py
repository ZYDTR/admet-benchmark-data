"""Deferred resource observations plus pure fail-closed validation.

No observations happen at import. Offline fixtures cannot establish target
health/availability. Stage two must capture fresh raw XML/apps before EACH
phase, repeat idle observations, and recheck immediately before actual launch.
"""
import csv
import io
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from common_guarded import safe


def validate_idle_gpu(xml, apps_csv, gpu_uuid, gpu_index):
    records = ET.fromstring(xml).findall('gpu')
    if len(records) != 1:
        raise ValueError('exactly one selected GPU record required')
    gpu = records[0]
    expected = {
        'uuid': gpu_uuid, 'minor_number': str(gpu_index),
        'gpu_recovery_action': 'None', 'compute_mode': 'Default',
        'mig_mode/current_mig': 'Disabled',
        'remapped_rows/remapped_row_pending': 'No',
        'remapped_rows/remapped_row_failure': 'No',
        'utilization/gpu_util': '0 %', 'utilization/memory_util': '0 %',
    }
    for field, value in expected.items():
        if gpu.findtext(field) != value:
            raise ValueError('GPU field failed or unknown: ' + field)
    # This run budgets 4096 MiB peak plus 4096 MiB headroom, informed by the
    # prior same-backbone Caco2 measurement (~1156 MiB). Existing allocated
    # memory need not equal zero or lie below a magic residual-size cutoff.
    # This branch requires no observed active workload; occupied-card sharing
    # needs a separately reviewed workload/impact policy, not an idle label.
    memory = {}
    for field in ('used', 'free', 'total'):
        text = gpu.findtext('fb_memory_usage/' + field) or ''
        if not re.fullmatch(r'[0-9]+ MiB', text):
            raise ValueError('GPU memory failed or unknown: ' + field)
        memory[field] = int(text.split()[0])
    if memory['free'] < 8192 or memory['total'] < memory['free'] + memory['used']:
        raise ValueError('GPU available memory outside reviewed budget or inconsistent')
    processes = gpu.find('processes')
    if processes is None or list(processes) or (processes.text or '').strip():
        raise ValueError('GPU XML compute/graphics process view occupied or unknown')
    uncorrectable = [item for item in gpu.findall('ecc_errors/volatile/*')
                     if 'uncorrectable' in item.tag]
    for field in ('sram_uncorrectable_parity', 'sram_uncorrectable_secded', 'dram_uncorrectable'):
        if gpu.findtext('ecc_errors/volatile/' + field) != '0':
            raise ValueError('required uncorrectable ECC failed or unknown: ' + field)
    if not uncorrectable or any(item.text != '0' for item in uncorrectable):
        raise ValueError('uncorrectable ECC failed or unknown')
    apps = parse_apps(apps_csv)
    if any(app['gpu_uuid'] == gpu_uuid for app in apps):
        raise ValueError('candidate GPU occupied')
    return {'gpu_uuid': gpu_uuid, 'gpu_index': gpu_index, 'idle': True,
            'healthy': True, 'shared_use_verified': False,
            'memory_used_mib': memory['used'], 'free_memory_mib': memory['free'],
            'planned_peak_mib': 4096, 'additional_headroom_mib': 4096,
            'residual_cause': 'not_determined',
            'qualification': 'no_observed_work_and_sufficient_headroom_not_reservation'}


def parse_apps(value):
    result = []
    for row in csv.reader(io.StringIO(value)):
        if not row:
            continue
        if len(row) != 3 or not row[0].strip().startswith('GPU-'):
            raise ValueError('unknown compute-apps format')
        pid, memory = int(row[1].strip()), int(row[2].strip())
        if pid <= 0 or memory < 0:
            raise ValueError('invalid GPU process observation')
        result.append({'gpu_uuid': row[0].strip(), 'pid': pid, 'memory_mib': memory})
    return result


def own_process_observation(leader_pid, proc_root=Path('/proc'), expected=None, audit=None):
    from process_state import observe_tree
    if expected is None:
        raise RuntimeError('explicit registered process identities required')
    return observe_tree(leader_pid, expected, proc_root, audit)


def result_bytes(root, audit=None):
    """Bounded complete rescans for concurrent file rename/unlink.

    A directory listing is not a filesystem snapshot. Never convert an absent
    enumerated file to zero or ignore permission/path errors. Recheck the root
    and retry only scoped ENOENT; persistent churn remains an explicit failure.
    """
    import stat
    import time
    root = Path(root)
    for scan in range(3):
        total = 0
        safe(root, root, True)
        try:
            for directory in ('raw', 'artifacts'):
                base = safe(root, root/directory, True)
                for path in base.rglob('*'):
                    safe(root, path, True)
                    info = path.lstat()
                    if stat.S_ISLNK(info.st_mode):
                        raise ValueError('symbolic link in result scan')
                    if stat.S_ISREG(info.st_mode):
                        if info.st_nlink != 1:
                            raise ValueError('multiply linked result file')
                        total += info.st_size
            if audit is not None:
                audit({'kind': 'result_scan_complete', 'scan': scan + 1,
                       'result_bytes': total})
            return total
        except FileNotFoundError as error:
            missing = Path(error.filename) if error.filename else None
            if (missing is None or not missing.is_absolute()
                    or not any(root/name in missing.parents
                               for name in ('raw', 'artifacts'))):
                raise
            # Missing root/output roots, links, mounts, permission errors and
            # escaped paths are hard failures rather than rename retries.
            safe(root, root, True)
            for name in ('raw', 'artifacts'):
                safe(root, root/name, True)
            safe(root, missing, False)
            if audit is not None:
                audit({'kind': 'result_scan_retry', 'scan': scan + 1,
                       'missing_path': str(missing), 'error': repr(error)})
            if scan == 2:
                raise
            time.sleep(.005)


def enforce_observation(observation, budget, gpu_uuid, own_pids):
    """Missing fields raise; own PID membership never inferred from shared UID."""
    if observation['tree_rss_bytes'] > budget['ram_target_gib']*1024**3:
        raise RuntimeError('RAM target exceeded')
    if observation['result_bytes'] > budget['result_budget_gib']*1024**3:
        raise RuntimeError('result target exceeded')
    apps = parse_apps(observation['apps_csv'])
    if any(app['gpu_uuid'] == gpu_uuid and app['pid'] not in own_pids for app in apps):
        raise RuntimeError('other process appeared; yield own task')
    own_memory = sum(app['memory_mib'] for app in apps if app['gpu_uuid'] == gpu_uuid)
    if own_memory > budget['gpu_peak_target_mib']:
        raise RuntimeError('GPU memory target exceeded')
    return {'observation_passed': True, 'quotas_enforced': False}
