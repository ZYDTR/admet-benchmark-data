"""Read synthetic /proc fixtures through the actual copied resource monitor."""
import datetime
import json
import sys
import uuid
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
from adapter_common import load_runtime


def main():
    suite = ADAPTER/'checks'/('proc-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    suite.mkdir()
    resource = load_runtime('resource_checks')
    results = []
    scenarios = [('Z', None, True, 10), ('X', None, True, 10),
                 ('S', None, False, None), ('unknown', None, False, None),
                 ('R', '20 kB', True, 30), ('S', '-1 kB', False, None),
                 ('S', 'garbage', False, None)]
    for index, (state, rss, expected, total) in enumerate(scenarios):
        proc = suite/str(index)
        (proc/'self').mkdir(parents=True)
        (proc/'self/stat').write_text('present')
        for pid, value, resident, children in ((100, 'S', '10 kB', '101'), (101, state, rss, '')):
            base = proc/str(pid)
            (base/'task'/str(pid)).mkdir(parents=True)
            (base/'stat').write_text(f'{pid} (fixture) {value} '+'0 '*20)
            (base/'status').write_text('State:\t'+value+'\nThreads:\t1\n'+('VmRSS:\t'+resident+'\n' if resident is not None else ''))
            (base/'task'/str(pid)/'children').write_text(children)
        try:
            value = resource.own_process_observation(100, proc)
        except (ValueError, RuntimeError) as error:
            assert not expected, (state, rss, error)
            result = {'state': state, 'rss': rss, 'passed': True, 'rejected': str(error)}
        else:
            assert expected and value['tree_rss_bytes'] == total*1024
            child = value['processes'][1]
            assert child['terminal'] is (state in ('Z', 'X'))
            assert child['rss_field_present'] is (rss is not None)
            result = {'state': state, 'rss': rss, 'passed': True, 'observation': value}
        results.append(result)
    # Separate stat/status reads can straddle an exit: the bounded reread must
    # confirm the terminal state, rather than treating all missing RSS as zero.
    for terminal in ('Z', 'X'):
        proc = suite/('transition-'+terminal)
        (proc/'self').mkdir(parents=True)
        (proc/'self/stat').write_text('present')
        base = proc/'101'
        (base/'task/101').mkdir(parents=True)
        (base/'stat').write_text('101 (fixture) '+terminal+' '+'0 '*20)
        (base/'status').write_text('State:\tS\nThreads:\t1\n')
        (base/'task/101/children').write_text('')
        value = resource.own_process_observation(101, proc)
        assert value['tree_rss_bytes'] == 0 and value['processes'][0]['process_state'] == terminal
        results.append({'state_transition': 'S->'+terminal, 'passed': True, 'observation': value})
    # Vanished own child is skipped; missing Linux /proc itself is unknown/failure.
    proc = suite/'vanished'
    (proc/'self').mkdir(parents=True)
    (proc/'self/stat').write_text('present')
    assert resource.own_process_observation(999, proc)['processes'] == []
    try:
        resource.own_process_observation(999, suite/'missing')
    except RuntimeError:
        pass
    else:
        raise AssertionError('missing /proc accepted')
    report = {'passed': True, 'checks': len(results)+2, 'results': results,
              'source': 'source/runtime-v1/resource_checks.py', 'actual_linux_proc_sampled': False,
              'terminal_without_RSS_only_Z_X': True, 'live_unknown_missing_RSS_fails': True,
              'parameter_updates': 0, 'remote_operations': False}
    (suite/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': True, 'evidence': str(suite/'result.json'), 'checks': report['checks']}))


if __name__ == '__main__':
    main()
