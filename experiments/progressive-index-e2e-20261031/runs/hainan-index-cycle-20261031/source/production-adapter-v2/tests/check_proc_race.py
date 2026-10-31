"""Reproduce old VmRSS KeyError and prove terminal-vs-unknown accounting locally."""
import datetime
import importlib.util
import json
import sys
import uuid
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
from adapter_common import RUN, generic, load_runtime


def main():
    root = ADAPTER/'checks'/('proc-fixtures-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    root.mkdir()
    proc = root/'proc'
    (proc/'self').mkdir(parents=True)
    (proc/'self/stat').write_text('inert fixture')
    def process(pid, state, rss, children=''):
        base = proc/str(pid)
        (base/'task'/str(pid)).mkdir(parents=True, exist_ok=True)
        (base/'stat').write_text(str(pid)+' (fixture) '+state+' inert fixture fields\n')
        (base/'status').write_text('State:\t'+state+'\nThreads:\t1\n'+
                                 ('VmRSS:\t'+rss+' kB\n' if rss is not None else ''))
        (base/'task'/str(pid)/'children').write_text(children)
    process(100, 'S', '10', '101')
    process(101, 'Z', None)
    previous = sys.modules.get('common_guarded')
    sys.modules['common_guarded'] = generic
    try:
        spec = importlib.util.spec_from_file_location('_old_resource_ref', RUN/'source/runtime/resource_checks.py')
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
    finally:
        if previous is None:
            sys.modules.pop('common_guarded', None)
        else:
            sys.modules['common_guarded'] = previous
    path_class = Path
    old.Path = lambda value: proc/path_class(value).relative_to('/proc')
    reproduced = False
    try:
        old.own_process_observation(100)
    except KeyError as error:
        assert error.args == ('VmRSS',)
        reproduced = True
    assert reproduced
    fixed = load_runtime('resource_checks')
    value = fixed.own_process_observation(100, proc_root=proc)
    assert value['tree_rss_bytes'] == 10*1024
    assert value['processes'][1]['terminal'] is True
    assert value['processes'][1]['rss_field_present'] is False
    cases = [{'case': 'old_zombie_missing_rss_reproduced', 'passed': True},
             {'case': 'fixed_zombie_accounted_terminal', 'passed': True}]
    for state, rss, should_pass in (('X', None, True), ('S', None, False),
                                    ('unknown', None, False), ('R', '20', True),
                                    ('S', '-1', False), ('S', 'unavailable', False)):
        process(101, state, rss)
        try:
            value = fixed.own_process_observation(100, proc_root=proc)
        except (RuntimeError, ValueError):
            assert not should_pass, (state, rss)
        else:
            assert should_pass, (state, rss)
            assert value['tree_rss_bytes'] == (10+(int(rss) if rss is not None else 0))*1024
        cases.append({'state': state, 'rss': rss, 'passed': True})
    result = {'passed': True, 'cases': cases, 'checks': len(cases),
              'old_exact_exception_reproduced': True, 'actual_linux_proc_tested': False,
              'unknown_live_memory_remains_failure': True, 'training_or_cuda': False}
    (root/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'root': str(root), **result}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
