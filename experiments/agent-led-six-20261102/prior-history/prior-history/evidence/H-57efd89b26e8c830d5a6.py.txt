"""Raw, identity-bound process observations. Unknown memory never becomes zero."""
import os
import signal
import subprocess
import time
from pathlib import Path


class ObservationUnknown(RuntimeError):
    def __init__(self, reason, evidence, terminal_reconciliation_allowed=False):
        super().__init__(reason)
        self.evidence = evidence
        self.terminal_reconciliation_allowed = terminal_reconciliation_allowed


class IdentityMismatch(ObservationUnknown):
    pass


def parse_stat(raw):
    pid_text, tail = raw.split(' (', 1)
    fields = tail.rsplit(')', 1)[1].split()
    if len(fields) < 20 or not fields[19].isdigit():
        raise ValueError('malformed stat/starttime')
    return {'pid': int(pid_text), 'state': fields[0], 'ppid': int(fields[1]),
            'pgid': int(fields[2]), 'start_ticks': fields[19], 'start_stat': raw}


def native_identity(pid):
    proc = Path('/proc')/str(pid)/'stat'
    if Path('/proc/self/stat').exists():
        return parse_stat(proc.read_text())
    # Offline macOS only. Production requires Linux /proc. Direct unreaped
    # Popen children additionally retain their kernel wait identity.
    process = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'lstart='], capture_output=True, text=True)
    if process.returncode:
        raise ProcessLookupError(pid)
    value = process.stdout.strip()
    if not value:
        raise ProcessLookupError(pid)
    return {'pid': pid, 'pgid': os.getpgid(pid), 'start_ticks': 'offline-ps:'+value,
            'start_stat': value, 'identity_source': 'offline_ps_not_linux_proc'}


def sample_pid(pid, expected, proc_root=Path('/proc'), audit=None, attempts=3, delay=.01, reader=None):
    """Bounded resampling, preserving both stat reads, status and every error."""
    read = reader or (lambda path: path.read_text())
    samples = []
    hard_seen = False
    for index in range(attempts):
        item = {'pid': pid, 'attempt': index+1, 'monotonic': time.monotonic(),
                'expected_start_ticks': expected['start_ticks'], 'raw': {}, 'errors': {}}
        parsed = {}
        for name, relative in (('stat_before', 'stat'), ('status', 'status'), ('stat_after', 'stat')):
            try:
                item['raw'][name] = read(proc_root/str(pid)/relative)
                if name != 'status':
                    parsed[name] = parse_stat(item['raw'][name])
            except (OSError, ValueError, IndexError) as error:
                item['errors'][name] = {'type': type(error).__name__, 'message': str(error)}
        samples.append(item)
        if audit:
            audit(item)
        for stat_value in parsed.values():
            if stat_value['pid'] != pid or stat_value['start_ticks'] != expected['start_ticks']:
                raise IdentityMismatch('PID/starttime mismatch; not owned', samples)
        if any(error['type'] != 'FileNotFoundError' for error in item['errors'].values()):
            hard_seen = True
        if 'status' in item['raw']:
            checked_fields = dict(line.split(':', 1) for line in item['raw']['status'].splitlines() if ':' in line)
            state_text = checked_fields.get('State', '').split()
            if not state_text or state_text[0] not in ('R', 'S', 'D', 'T', 't', 'K', 'W', 'P', 'I', 'Z', 'X'):
                hard_seen = True
            if 'VmRSS' in checked_fields:
                checked_rss = checked_fields['VmRSS'].split()
                if len(checked_rss) != 2 or checked_rss[1] != 'kB' or not checked_rss[0].isdigit():
                    hard_seen = True
        if len(parsed) == 2 and not hard_seen:
            latest = parsed['stat_after']
            if latest['state'] in ('Z', 'X'):
                return {**latest, 'classification': 'confirmed_terminal', 'rss_bytes': None,
                        'rss_available': False, 'raw_samples': samples}
            if not item['errors']:
                fields = dict(line.split(':', 1) for line in item['raw']['status'].splitlines() if ':' in line)
                status_state = fields.get('State', '').split()
                rss = fields.get('VmRSS', '').split()
                if status_state and status_state[0] == latest['state'] and len(rss) == 2 and rss[1] == 'kB':
                    try:
                        kib = int(rss[0])
                    except ValueError:
                        kib = -1
                    if kib >= 0:
                        return {**latest, 'classification': 'live_measured', 'rss_bytes': kib*1024,
                                'rss_available': True, 'raw_samples': samples}
        if index+1 < attempts:
            time.sleep(delay)
    eligible = not hard_seen
    for item in samples:
        if any(error['type'] != 'FileNotFoundError' for error in item['errors'].values()):
            eligible = False
        if not item['errors']:
            fields = dict(line.split(':', 1) for line in item['raw']['status'].splitlines() if ':' in line)
            status_state = fields.get('State', '').split()
            if ('VmRSS' in fields or not status_state
                    or status_state[0] not in ('R', 'S', 'D', 'T', 't', 'K', 'W', 'P', 'I')):
                eligible = False
    raise ObservationUnknown('owned process memory/state unavailable after bounded resample', samples,
                             terminal_reconciliation_allowed=eligible)


def observe_tree(leader, expected, proc_root=Path('/proc'), audit=None):
    if not (proc_root/'self/stat').exists():
        raise ObservationUnknown('Linux /proc unavailable', [])
    found, records, total = [leader], [], 0
    for pid in found:
        if pid not in expected:
            raise IdentityMismatch('unregistered process', [{'pid': pid}])
        record = sample_pid(pid, expected[pid], proc_root, audit)
        records.append(record)
        if record['classification'] == 'live_measured':
            total += record['rss_bytes']
        if record['classification'] == 'confirmed_terminal':
            continue
        child_path = proc_root/str(pid)/'task'/str(pid)/'children'
        try:
            raw_children = child_path.read_text()
        except OSError as error:
            raise ObservationUnknown('owned children view unavailable', [{'path': str(child_path), 'error': repr(error)}]) from error
        for text in raw_children.split():
            child = int(text)
            try:
                raw = (proc_root/text/'stat').read_text()
                identity = parse_stat(raw)
            except OSError as error:
                raise ObservationUnknown('discovered child identity unavailable', [{'pid': child, 'error': repr(error)}]) from error
            if identity['ppid'] != pid or identity['pgid'] != expected[leader]['pgid']:
                raise IdentityMismatch('descendant parent/group mismatch', [identity])
            if child in expected and expected[child]['start_ticks'] != identity['start_ticks']:
                raise IdentityMismatch('discovered PID reused', [identity])
            expected.setdefault(child, identity)
            if child not in found:
                found.append(child)
    return {'processes': records, 'pids': [p['pid'] for p in records],
            'tree_rss_bytes': total, 'terminal_RSS_is_not_fabricated': True, 'loadavg': os.getloadavg()}


def require_exited_identity(identity, proc_root=Path('/proc'), audit=None):
    """After actual wait and a valid receipt: disappearance/terminal proof only."""
    if not Path('/proc/self/stat').exists() and proc_root == Path('/proc'):
        return {'state': 'offline_direct_Popen_wait_only', 'pid': identity['pid']}
    path = proc_root/str(identity['pid'])/'stat'
    try:
        raw = path.read_text()
    except FileNotFoundError:
        proof = {'pid': identity['pid'], 'state': 'absent_after_actual_child_wait', 'path': str(path)}
    except OSError as error:
        raise ObservationUnknown('exit state unreadable', [{'path': str(path), 'error': repr(error)}]) from error
    else:
        current = parse_stat(raw)
        if current['start_ticks'] != identity['start_ticks']:
            raise IdentityMismatch('PID reused at completion', [current, identity])
        if current['state'] not in ('Z', 'X'):
            raise ObservationUnknown('matching process still live after child exit', [current])
        proof = {'pid': identity['pid'], 'state': 'matching_terminal', 'raw_stat': raw}
    if audit:
        audit(proof)
    return proof


def signal_exact(identity, signum, identity_reader=native_identity, sender=None, direct_child=None):
    descriptor = None
    try:
        if sender is None and Path('/proc/self/stat').exists():
            if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
                raise RuntimeError('exact Linux signalling requires pidfd support')
            descriptor = os.pidfd_open(identity['pid'], 0)
        elif sender is None and (direct_child is None or direct_child.pid != identity['pid'] or direct_child.poll() is not None):
            raise RuntimeError('offline signal requires held, unreaped direct Popen child')
        current = identity_reader(identity['pid'])
    except (ProcessLookupError, FileNotFoundError):
        if descriptor is not None:
            os.close(descriptor)
        return {'pid': identity['pid'], 'signalled': False, 'state': 'absent'}
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    try:
        if current['start_ticks'] != identity['start_ticks'] or current['pgid'] != identity['pgid']:
            raise IdentityMismatch('signal refused for changed identity', [identity, current])
        if current.get('state') in ('Z', 'X'):
            return {'pid': identity['pid'], 'signalled': False, 'state': 'terminal'}
        if descriptor is not None:
            try:
                signal.pidfd_send_signal(descriptor, signum, None, 0)
            except ProcessLookupError:
                return {'pid': identity['pid'], 'signalled': False,
                        'state': 'pinned_process_exited_before_signal', 'kernel_handle': 'pidfd'}
        else:
            (sender or os.kill)(identity['pid'], signum)
        return {'pid': identity['pid'], 'signalled': True, 'signal': signum,
                'kernel_handle': 'pidfd' if descriptor is not None else 'offline_held_direct_child_or_test_spy'}
    finally:
        if descriptor is not None:
            os.close(descriptor)
