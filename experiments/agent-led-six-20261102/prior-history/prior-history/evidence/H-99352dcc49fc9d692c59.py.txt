"""Explicit fixed offline fixtures, feeding the real production classifier."""
from pathlib import Path
from adapter_common import generic
from process_state import sample_pid


def inject_process_observation(root, context, child, case):
    attempt = context['attempt_root']/'train'
    trigger = attempt/('adapter-complete.json' if case in ('terminal_missing_rss', 'terminal_malformed_artifact') else 'worker-start.json')
    if not trigger.exists():
        return
    proc = root/'raw/proc-fixture'
    base = proc/str(child.pid)
    base.mkdir(parents=True, exist_ok=True)
    (base/'stat').write_text(f'{child.pid} (fixed offline fixture) R 1 {child.pid} '+'0 '*16+'12345 0 0\n')
    (base/'status').write_text('State:\tR (running)\nThreads:\t1\n')
    expected = {'start_ticks': '99999' if case == 'identity_mismatch' else '12345'}
    reader = None
    if case == 'unreadable_rss':
        def reader(path):
            if path.name == 'status':
                raise PermissionError('explicit offline unreadable-status fixture')
            return path.read_text()
    sample_pid(child.pid, expected, proc, context['process_audit'], reader=reader)
