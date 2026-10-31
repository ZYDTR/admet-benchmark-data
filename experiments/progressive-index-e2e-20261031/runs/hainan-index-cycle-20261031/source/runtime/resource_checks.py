"""Deferred resource observations plus pure fail-closed validation.

No observations happen at import. Offline fixtures cannot establish target
health/availability. Stage two must capture fresh raw XML/apps before EACH
phase, repeat idle observations, and recheck immediately before actual launch.
"""
import csv
import io
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from common_guarded import safe


def validate_idle_gpu(xml, apps_csv, gpu_uuid, gpu_index):
    gpu = ET.fromstring(xml).find('gpu')
    if gpu is None:
        raise ValueError('missing GPU record')
    expected = {
        'uuid': gpu_uuid, 'minor_number': str(gpu_index),
        'gpu_recovery_action': 'None', 'compute_mode': 'Default',
        'mig_mode/current_mig': 'Disabled',
        'remapped_rows/remapped_row_pending': 'No',
        'remapped_rows/remapped_row_failure': 'No',
        'fb_memory_usage/used': '0 MiB', 'utilization/gpu_util': '0 %',
    }
    for field, value in expected.items():
        if gpu.findtext(field) != value:
            raise ValueError('GPU field failed or unknown: ' + field)
    uncorrectable = [item for item in gpu.findall('ecc_errors/volatile/*')
                     if 'uncorrectable' in item.tag]
    if not uncorrectable or any(item.text != '0' for item in uncorrectable):
        raise ValueError('uncorrectable ECC failed or unknown')
    apps = parse_apps(apps_csv)
    if any(app['gpu_uuid'] == gpu_uuid for app in apps):
        raise ValueError('candidate GPU occupied')
    return {'gpu_uuid': gpu_uuid, 'gpu_index': gpu_index, 'idle': True,
            'healthy': True, 'shared_use_verified': False}


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


def own_process_observation(leader_pid):
    """Linux only; record /proc identities for this leader and descendants."""
    if not Path('/proc/self/stat').exists():
        raise RuntimeError('Linux /proc required; resource state unknown')
    found, processes, rss = [leader_pid], [], 0
    for pid in found:
        base = Path('/proc')/str(pid)
        try:
            start_stat = (base/'stat').read_text()
            fields = dict(line.split(':', 1) for line in (base/'status').read_text().splitlines())
            rss_kib = int(fields['VmRSS'].split()[0])
            rss += rss_kib * 1024
            processes.append({'pid': pid, 'start_stat': start_stat,
                              'rss_kib': rss_kib, 'threads': fields.get('Threads')})
            for child in (base/'task'/str(pid)/'children').read_text().split():
                if int(child) not in found:
                    found.append(int(child))
        except FileNotFoundError:
            continue  # child exited; terminal evidence must still be verified
    return {'processes': processes, 'pids': [p['pid'] for p in processes],
            'tree_rss_bytes': rss, 'loadavg': os.getloadavg()}


def result_bytes(root):
    total = 0
    for directory in ('raw', 'artifacts'):
        for path in (root/directory).rglob('*'):
            safe(root, path, True)
            if path.is_file():
                total += path.stat().st_size
    return total


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
