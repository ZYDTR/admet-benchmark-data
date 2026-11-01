"""Finite per-job wrapper records actual pipeline OS exit. No transport/service."""
import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapter_common import ADAPTER, RUN, generic, process_identity, strict_json, write
from admission import GateClosed, require_production
from pipeline import CASES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('offline', 'production'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--case', choices=CASES, default='success')
    parser.add_argument('--profile', type=Path, default=ADAPTER/'adapter-profile.json')
    args = parser.parse_args()
    if args.mode == 'offline':
        root = args.root
        if root is None or ADAPTER/'checks' not in root.parents:
            raise GateClosed('offline test root outside new adapter checks')
        command = [sys.executable, '-I', '-B', '-u', str(ADAPTER/'pipeline.py'),
                   'offline', '--root', str(root), '--case', args.case]
        python, gpu = sys.executable, None
    else:
        root = RUN
        profile = strict_json(generic.safe(root, args.profile, True))
        require_production(profile, root)
        if sys.platform != 'linux' or os.uname().nodename != '<COMPUTE_HOST>' or os.getuid() != 1012:
            raise GateClosed('target identity mismatch')
        command = [profile['python'], '-I', '-B', '-u', str(ADAPTER/'pipeline.py'),
                   'production', '--profile', str(args.profile)]
        python, gpu = profile['python'], profile['gpu_uuid']
    env = generic.environment(root, python, gpu_uuid=gpu)
    generic.prepare_environment_dirs(root, env)
    raw = generic.safe(root, root/'raw')
    raw.mkdir(exist_ok=True)
    # This lock is distinct from the phase and learning locks; never reclaim it.
    state = generic.safe(root, root/'state')
    state.mkdir(exist_ok=True)
    try:
        with (state/'job-waiter-start.lock').open('x') as stream:
            json.dump({'at': generic.now(), 'run_id': RUN.name, 'mode': args.mode}, stream)
    except FileExistsError:
        return 73
    if args.mode == 'production':
        import resource
        selected = sorted(os.sched_getaffinity(0))[:2]
        if len(selected) != 2:
            raise RuntimeError('insufficient CPU affinity')
        os.sched_setaffinity(0, selected)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_FSIZE, (450*1024**2, 450*1024**2))
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, cwd=root, env=env,
                             start_new_session=True)
    identity = process_identity(child.pid)
    write(root, raw/'job-pipeline-start.json', {'at': generic.now(), 'command': command,
                                               'identity': identity, 'offline_fixture': args.mode == 'offline'})
    def cancel(signum, frame):
        if child.poll() is None:
            child.send_signal(signum)  # pipeline cooperatively stops its own exact child
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, cancel)
    code = child.wait()
    write(root, raw/'job-wait-exit.json', {'at': generic.now(), 'run_id': RUN.name,
                                          'actual_os_exit_code': code, 'pipeline_identity': identity,
                                          'waiter_pid': os.getpid(), 'offline_fixture': args.mode == 'offline'})
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except GateClosed as error:
        print(json.dumps({'state': 'production_gate_closed', 'success': False, 'reason': str(error)}))
        raise SystemExit(78)
