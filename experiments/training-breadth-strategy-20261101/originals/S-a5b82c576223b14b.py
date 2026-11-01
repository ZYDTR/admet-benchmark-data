"""Targeted read-only reaggregation of scaffold coverage; no label access or fitting.

This uses the same RDKit version and Murcko definition as the original chemistry
audit, with a separately written aggregation. It is not an independent chemical
identity method and cannot recover the historical split-generation algorithm.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem.Scaffolds import MurckoScaffold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    RDLogger.DisableLog('rdApp.*')
    if rdBase.rdkitVersion != '2025.09.6':
        raise RuntimeError('This review requires RDKit 2025.09.6')
    cache, tasks, hashes = {}, {}, {}

    def scaffold_info(smiles):
        if smiles not in cache:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                cache[smiles] = None
            else:
                scaffold = MurckoScaffold.MurckoScaffoldSmiles(
                    mol=mol, includeChirality=False
                )
                cache[smiles] = (scaffold, mol.GetRingInfo().NumRings())
        return cache[smiles]

    for task_dir in sorted((args.snapshot / 'data_benchmark').iterdir()):
        if not task_dir.is_dir():
            continue
        tasks[task_dir.name] = {}
        for split in ('train', 'valid', 'test'):
            path = task_dir / (split + '.csv')
            hashes[str(path.relative_to(args.snapshot))] = hashlib.sha256(path.read_bytes()).hexdigest()
            counts = Counter()
            failed, rings_zero, disagreements = [], 0, []
            rows = 0
            with path.open(encoding='utf-8-sig', newline='') as handle:
                for row_index, row in enumerate(csv.DictReader(handle)):
                    rows += 1
                    info = scaffold_info(row['Drug'])  # Deliberately never read Y.
                    if info is None:
                        failed.append(row_index)
                        continue
                    scaffold, ring_count = info
                    counts[scaffold] += 1
                    rings_zero += int(ring_count == 0)
                    if (scaffold == '') != (ring_count == 0):
                        disagreements.append(row_index)
            empty_rows = counts.pop('', 0)
            nonempty_rows = sum(counts.values())
            assert rows == empty_rows + nonempty_rows + len(failed)
            tasks[task_dir.name][split] = {
                'rows': rows,
                'parse_failed_rows': failed,
                'empty_scaffold_rows': empty_rows,
                'nonempty_scaffold_rows': nonempty_rows,
                'nonempty_scaffold_distinct': len(counts),
                'empty_scaffold_fraction_of_all_rows': empty_rows / rows,
                'largest_nonempty_scaffold_rows': max(counts.values(), default=0),
                'largest_nonempty_scaffold_fraction_of_all_rows': max(counts.values(), default=0) / rows,
                'top_nonempty_scaffolds': [{'scaffold_smiles': s, 'rows': n} for s, n in counts.most_common(5)],
                'zero_ring_rows': rings_zero,
                'empty_scaffold_vs_zero_rings_disagreement_rows': disagreements,
            }
    result = {
        'snapshot_commit': '0275588ac7a5d3df032ec7dc0794cab21dfcfeeb',
        'rdkit_version': rdBase.rdkitVersion,
        'scope': 'Read-only recomputation of all 66 train/valid/test CSV scaffold distributions. No labels, model weights, external samples or training used.',
        'method': 'Default sanitized MolFromSmiles; MurckoScaffoldSmiles(mol=mol, includeChirality=False). Same chemical definition as original audit; independently written aggregation. Ring counts are a diagnostic cross-check, not an independent split validation.',
        'limits': 'Empty Murcko scaffold means this ring-centered representation is empty; it is not one common chemical family. Counts do not identify the original split algorithm or prove performance bias.',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_sha256': hashes,
        'unique_raw_smiles_processed': len(cache),
        'tasks': tasks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'tasks': len(tasks), 'unique_raw_smiles_processed': len(cache), 'rdkit_version': rdBase.rdkitVersion}))


if __name__ == '__main__':
    main()
