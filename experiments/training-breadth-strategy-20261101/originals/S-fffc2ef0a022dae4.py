"""Read-only structure audit; no data cleaning, fitting, or test-label access."""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
from decimal import Decimal

from rdkit import Chem, rdBase, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    RDLogger.DisableLog('rdApp.*')
    records, hashes = {}, {}
    for folder in sorted((args.snapshot / 'data_benchmark').iterdir()):
        if not folder.is_dir():
            continue
        records[folder.name] = {}
        for role in ('train', 'valid', 'test'):
            path = folder / (role + '.csv')
            hashes[str(path.relative_to(args.snapshot))] = hashlib.sha256(path.read_bytes()).hexdigest()
            with path.open(encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                # Projection intentionally excludes any test label field.
                records[folder.name][role] = [
                    {'row': i, 'smiles': r['Drug'], **({'y': r['Y']} if role != 'test' else {})}
                    for i, r in enumerate(reader)
                ]
    strings = sorted({r['smiles'] for splits in records.values() for rows in splits.values() for r in rows})
    structures = {}
    for s in strings:
        mol = Chem.MolFromSmiles(s)
        if mol is None:
            structures[s] = {'parse_ok': False}
            continue
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        structures[s] = {
            'parse_ok': True,
            'canonical_isomeric': Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True),
            'canonical_without_stereo': Chem.MolToSmiles(mol, canonical=True, isomericSmiles=False),
            'murcko_without_stereo': Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=False),
            'atoms_after_default_parse': mol.GetNumAtoms(),
            'heavy_atoms': mol.GetNumHeavyAtoms(),
            'fragments': len(Chem.GetMolFrags(mol)),
            'elements': sorted({a.GetSymbol() for a in mol.GetAtoms()}),
            'specified_atom_stereo': sum(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in mol.GetAtoms()),
        }
    def identities(rows, key):
        return {structures[r['smiles']][key] for r in rows if structures[r['smiles']]['parse_ok']}
    output = {
        'rdkit_version': rdBase.rdkitVersion,
        'commit': '0275588ac7a5d3df032ec7dc0794cab21dfcfeeb',
        'scope': 'Diagnostic only. No standardization, salt removal, neutralization, tautomer normalization, split changes, label edits, feature fitting or model training.',
        'identity_definitions': {
            'canonical_isomeric': 'Default sanitized MolFromSmiles, canonical MolToSmiles(isomericSmiles=True); preserves supported specified stereochemistry.',
            'canonical_without_stereo': 'Sensitivity analysis only; cannot be interpreted as biological identity or automatic deduplication key.',
            'murcko_without_stereo': 'RDKit Bemis-Murcko scaffold without stereochemistry; empty acyclic scaffolds counted separately and excluded from nonempty overlap.',
        },
        'source_hashes': hashes,
        'unique_raw_smiles': len(strings),
        'parse_failures_unique': sum(not x['parse_ok'] for x in structures.values()),
        'input_coverage_exceptions': [],
        'tasks': {},
    }
    ok = [x for x in structures.values() if x['parse_ok']]
    output['structure_summary_unique_raw_inputs'] = {
        'unique_canonical_isomeric': len({x['canonical_isomeric'] for x in ok}),
        'heavy_atom_min': min(x['heavy_atoms'] for x in ok),
        'heavy_atom_max': max(x['heavy_atoms'] for x in ok),
        'heavy_atoms_over_200': sum(x['heavy_atoms'] > 200 for x in ok),
        'multi_fragment_inputs': sum(x['fragments'] > 1 for x in ok),
        'inputs_with_specified_atom_stereo': sum(x['specified_atom_stereo'] > 0 for x in ok),
        'elements': sorted({e for x in ok for e in x['elements']}),
    }
    for task, splits in records.items():
        entry = {'roles': {}, 'overlap': {}}
        for role, rows in splits.items():
            valid_rows = [r for r in rows if structures[r['smiles']]['parse_ok']]
            sc = identities(rows, 'murcko_without_stereo')
            stats = {
                'rows': len(rows),
                'parse_failed_rows': [r['row'] for r in rows if not structures[r['smiles']]['parse_ok']],
                'canonical_isomeric_unique': len(identities(rows, 'canonical_isomeric')),
                'nonempty_murcko_scaffolds': len(sc - {''}),
                'empty_murcko_rows': sum(structures[r['smiles']]['murcko_without_stereo'] == '' for r in valid_rows),
                'heavy_atom_max': max((structures[r['smiles']]['heavy_atoms'] for r in valid_rows), default=0),
            }
            for r in rows:
                s = structures[r['smiles']]
                if not s['parse_ok']:
                    output['input_coverage_exceptions'].append({'task': task, 'role': role, 'row_index': r['row'], 'reason': 'RDKit2025.09.6 default sanitized parse returned None', 'source_path': f'data_benchmark/{task}/{role}.csv'})
                elif s['heavy_atoms'] > 200:
                    output['input_coverage_exceptions'].append({'task': task, 'role': role, 'row_index': r['row'], 'heavy_atoms': s['heavy_atoms'], 'source_path': f'data_benchmark/{task}/{role}.csv'})
            if role != 'test':
                raw_labels, canonical_labels = collections.defaultdict(set), collections.defaultdict(set)
                for r in valid_rows:
                    raw_labels[r['smiles']].add(Decimal(r['y']))
                    canonical_labels[structures[r['smiles']]['canonical_isomeric']].add(Decimal(r['y']))
                stats['raw_smiles_distinct_numeric_labels'] = sum(len(v) > 1 for v in raw_labels.values())
                stats['canonical_isomeric_distinct_numeric_labels'] = sum(len(v) > 1 for v in canonical_labels.values())
            entry['roles'][role] = stats
        for a, b in [('train', 'valid'), ('train', 'test'), ('valid', 'test')]:
            detail = {}
            for key in ('canonical_isomeric', 'canonical_without_stereo', 'murcko_without_stereo'):
                left, right = identities(splits[a], key), identities(splits[b], key)
                if key == 'murcko_without_stereo':
                    left.discard(''); right.discard('')
                common = left & right
                detail[key + '_unique_intersection'] = len(common)
                detail[key + '_right_rows_seen_in_left'] = sum(
                    structures[r['smiles']]['parse_ok'] and structures[r['smiles']].get(key) in left
                    for r in splits[b]
                )
            entry['overlap'][a + '_' + b] = detail
        output['tasks'][task] = entry
    output['aggregate'] = {
        'same_task_train_valid_canonical_intersections_sum': sum(t['overlap']['train_valid']['canonical_isomeric_unique_intersection'] for t in output['tasks'].values()),
        'same_task_train_test_canonical_intersections_sum': sum(t['overlap']['train_test']['canonical_isomeric_unique_intersection'] for t in output['tasks'].values()),
        'tasks_with_train_valid_nonempty_scaffold_overlap': [task for task, t in output['tasks'].items() if t['overlap']['train_valid']['murcko_without_stereo_unique_intersection']],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: output[k] for k in ['rdkit_version', 'unique_raw_smiles', 'parse_failures_unique', 'structure_summary_unique_raw_inputs', 'aggregate']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
