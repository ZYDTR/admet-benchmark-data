"""Feature-cache checks with SYNTHETIC arrays.

No model, no torch, no backward pass: we call ``save_cache``/``load_cache``
directly with fixed numeric arrays, then corrupt or re-source the cache and assert
it is refused.  This is the "fixed small-data counter-example" required for cache
rejection of wrong source and corruption.  Runs on the stdlib array backend when
NumPy is unavailable (the format name is recorded, so it is never confused with a
NumPy cache).
"""

import json
import os
import shutil
import tempfile
import unittest

import helpers

import feature_array as fa
from dataio import read_split
from errors import CacheError
from feature_cache import build_manifest, load_cache, save_cache

DEPS = {"torch": "2.6.0", "chemprop": "2.2.1", "rdkit": "2024.9.6",
        "numpy": "1.26.4", "pandas": "2.2.3"}


def _meta(feature_dim=4, sha="a" * 64):
    return {"id": "chemeleon_mp", "code_commit": "b5e5bd88a7070c3f278e7e65e85b792617bf125c",
            "feature_dim": feature_dim, "hyper_parameters": {"depth": 3},
            "weights": {"size": 34859448, "md5": "6a80b54fdb7de37ef0374d302f01e8ce",
                        "sha256": sha}}


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ocprep_", dir=helpers.WORK_TMP)
        self.root = os.path.join(self.tmp, "pack")
        self.tasks, self.sizes = helpers.make_synthetic_root(self.root)
        self.cache = os.path.join(self.tmp, "cache")
        self.table = read_split(self.root, "ames", "train")
        self.manifest = build_manifest(self.table, _meta(), DEPS, 8)
        n = self.table["n_rows"]
        self.feats = fa.synthetic(n, 4, seed=0)
        self.kept = list(range(n))
        self.failures = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _save(self, **over):
        save_cache(self.cache, over.get("manifest", self.manifest),
                   over.get("feats", self.feats), over.get("kept", self.kept),
                   over.get("failures", self.failures))

    def _entry(self, key=None):
        return os.path.join(self.cache, "train", "ames", key or self.manifest["key"])

    def test_hit_returns_same_array(self):
        self._save()
        feats, man = load_cache(self.cache, self.manifest)
        # On-disk format is float32, so a hit must equal the stdlib reference
        # values packed/unpacked through float32 (bit-exact, not "approximately").
        from mini_linalg import pack_f32, unpack_f32

        blob = pack_f32(self.feats.obj)
        rt = fa.Array(unpack_f32(blob, self.feats.shape[0], self.feats.shape[1]))
        self.assertTrue(fa.same(feats, rt))
        self.assertEqual(man["key"], self.manifest["key"])

    def test_input_content_change_forces_miss(self):
        self._save()
        path = os.path.join(self.root, "official", "data_benchmark", "ames", "train.csv")
        helpers.write_csv(path, ["Drug_ID", "Drug", "Y"],
                          [["Drug 0", "CCX", 0]] + [
                              [f"Drug {i}", f"C{'C' * i}O", i % 2]
                              for i in range(1, self.sizes["train"])])
        changed = read_split(self.root, "ames", "train")
        new_manifest = build_manifest(changed, _meta(), DEPS, 8)
        self.assertNotEqual(new_manifest["key"], self.manifest["key"])
        with self.assertRaises(CacheError):
            load_cache(self.cache, new_manifest)

    def test_weight_hash_change_forces_miss(self):
        self._save()
        other = build_manifest(self.table, _meta(sha="b" * 64), DEPS, 8)
        self.assertNotEqual(other["key"], self.manifest["key"])
        with self.assertRaises(CacheError):
            load_cache(self.cache, other)

    def test_dep_version_change_forces_miss(self):
        self._save()
        other = build_manifest(self.table, _meta(), dict(DEPS, chemprop="2.2.0"), 8)
        with self.assertRaises(CacheError):
            load_cache(self.cache, other)

    def test_row_order_change_forces_miss(self):
        self._save()
        rev = dict(self.table)
        rev["rows"] = list(reversed(self.table["rows"]))
        other = build_manifest(rev, _meta(), DEPS, 8)
        self.assertNotEqual(other["key"], self.manifest["key"])

    def test_index_shift_same_molecule_forces_miss(self):
        # Same set of rows, but row_index renumbered 1..n: identity must differ.
        self._save()
        shifted = dict(self.table)
        shifted["rows"] = [dict(r, row_index=r["row_index"] + 1) for r in self.table["rows"]]
        other = build_manifest(shifted, _meta(), DEPS, 8)
        self.assertNotEqual(other["key"], self.manifest["key"])

    def test_corrupted_array_is_rejected(self):
        self._save()
        entry = self._entry()
        fpath = os.path.join(entry, f"features.{fa.format_name()}")
        with open(fpath, "r+b") as fh:
            fh.seek(0)
            first = fh.read(4)
            fh.seek(0)
            fh.write(bytes((b ^ 0xFF) for b in first))
        with self.assertRaises(CacheError):
            load_cache(self.cache, self.manifest)

    def test_nonfinite_array_rejected(self):
        bad = fa.synthetic(self.table["n_rows"], 4, seed=1)
        bad[1, 2] = float("nan")
        with self.assertRaises(CacheError):
            self._save(feats=bad)

    def test_manifest_identity_tamper_rejected(self):
        self._save()
        mp = os.path.join(self._entry(), "manifest.json")
        with open(mp, "r", encoding="utf-8") as fh:
            man = json.load(fh)
        man["rows_sha256"] = "0" * 64
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump(man, fh)
        with self.assertRaises(CacheError):
            load_cache(self.cache, self.manifest)

    def test_failure_partition_enforced(self):
        kept = list(range(1, self.table["n_rows"]))
        feats = fa.synthetic(len(kept), 4, seed=2)
        failures = [{"row_index": 0, "smiles": "x", "error": "unparseable"}]
        self._save(feats=feats, kept=kept, failures=failures)
        f2, man = load_cache(self.cache, self.manifest)
        self.assertEqual(man["kept_row_indices"], kept)
        self.assertEqual(man["failures"], failures)
        self.assertEqual(f2.shape[0], len(kept))
        mp = os.path.join(self._entry(), "manifest.json")
        with open(mp, "r", encoding="utf-8") as fh:
            man = json.load(fh)
        man["failures"] = []
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump(man, fh)
        with self.assertRaises(CacheError):
            load_cache(self.cache, self.manifest)

    def test_overlapping_failure_and_feature_rejected(self):
        failures = [{"row_index": 0, "smiles": "x", "error": "e"}]
        with self.assertRaises(CacheError):
            self._save(failures=failures)  # row 0 also in kept -> overlap

    def test_missing_manifest_is_miss_not_hit(self):
        with self.assertRaises(CacheError):
            load_cache(self.cache, self.manifest)

    def test_wrong_array_backend_format_rejected(self):
        # A manifest claims the other backend's format -> cannot silently reuse.
        self._save()
        other = dict(self.manifest)
        other["array_format"] = "npy" if fa.format_name() == "npyf" else "npyf"
        other["key"] = self.manifest["key"]  # force same dir but different format
        with self.assertRaises(CacheError):
            load_cache(self.cache, other)


if __name__ == "__main__":
    unittest.main()