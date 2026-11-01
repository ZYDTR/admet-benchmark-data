"""Only standard-library toy work. Never import the scientific runner or GPU libs."""
import json
import os
import signal
import sys
import time
from pathlib import Path


def main():
    case, directory, token, run_id = sys.argv[1:]
    directory = Path(directory)
    (directory/'child-started.json').write_text(json.dumps({'pid': os.getpid(), 'case': case}))
    if case == 'exit7':
        return 7
    if case == 'exception':
        raise RuntimeError('intentional toy-child failure')
    if case in ('timeout', 'monitor_failure'):
        time.sleep(30)
        return 0
    if case == 'slow_success':
        time.sleep(0.3)
    if case == 'missing_receipt':
        return 0
    if case == 'signal_child':
        os.kill(os.getpid(), signal.SIGTERM)
        return 99
    if case == 'malformed_receipt':
        (directory/'completion.json').write_text('{')
        return 0
    receipt = {'status': 'success', 'pid': os.getpid(), 'run_id': run_id,
               'token': token if case != 'wrong_token' else 'stale-token',
               'offline_fake_task': True}
    (directory/'completion.json').write_text(json.dumps(receipt))
    print('toy child finished', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
