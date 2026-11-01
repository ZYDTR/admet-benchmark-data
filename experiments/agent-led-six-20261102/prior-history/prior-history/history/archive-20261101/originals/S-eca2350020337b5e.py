"""Regression checks for scientifically consequential cleaning boundaries."""
import csv
import pathlib
import tempfile
import unittest

from clean_data import inspect_smiles, normalize_label, read_source, validate_output_location, annotate_group, FIELDS


class CleaningPolicyTests(unittest.TestCase):
    def test_ids_and_bom_are_lossless(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "train.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Drug_ID", "Drug", "Y"])
                for identifier in ["00123", "NA", "", "123.0"]:
                    writer.writerow([identifier, "CCO", "1.0"])
            rows = read_source(path, "train")
            self.assertEqual([r["Drug_ID"] for r in rows], ["00123", "NA", "", "123.0"])

    def test_numeric_labels_are_not_transformed(self):
        self.assertEqual(normalize_label("1.0", "classification", "train"), ("1", "valid"))
        self.assertEqual(normalize_label("-7.7600002", "regression", "train"), ("-7.7600002", "valid"))
        self.assertEqual(normalize_label("1e-3", "regression", "train"), ("0.001", "valid"))
        self.assertEqual(normalize_label("2", "classification", "train")[1], "invalid_binary_label")
        self.assertEqual(normalize_label("nan", "regression", "train")[1], "invalid_numeric")
        self.assertEqual(normalize_label("", "regression", "test"), ("", "not_provided"))

    def test_stereochemistry_and_salts_are_preserved(self):
        self.assertEqual(inspect_smiles("CCO")["molecule_id"], inspect_smiles("OCC")["molecule_id"])
        self.assertNotEqual(inspect_smiles("C[C@H](O)F")["molecule_id"], inspect_smiles("C[C@@H](O)F")["molecule_id"])
        salt = inspect_smiles("CC(=O)[O-].[Na+]")
        self.assertEqual(salt["fragment_count"], 2)
        self.assertIn(".", salt["canonical_smiles"])
        self.assertNotEqual(salt["molecule_id"], inspect_smiles("CC(=O)O")["molecule_id"])

    def test_invalid_and_acyclic_are_not_conflated(self):
        invalid = inspect_smiles("CC1=CC=C[NH+2]([O-])[CH-]1")
        self.assertEqual(invalid["parse_status"], "invalid")
        self.assertEqual(invalid["canonical_smiles"], "")
        self.assertTrue(invalid["parse_error"])
        acyclic = inspect_smiles("CCO")
        self.assertEqual(acyclic["parse_status"], "valid")
        self.assertEqual(acyclic["scaffold_type"], "acyclic")
        self.assertEqual(acyclic["scaffold_id"], "")

    def test_dedup_preserves_conflicting_measurements_and_multiplicity(self):
        rows = []
        for index, label in enumerate(["1", "1", "0"]):
            row = dict.fromkeys(FIELDS, "")
            row.update(task="example", split="train", sample_idx=index,
                       row_id=f"example/train/{index:06d}", molecule_id="same_molecule",
                       drug_id=str(index), y=label, y_original=label, label_status="valid",
                       sample_weight=1, _issues=[])
            rows.append(row)
        conflicts, duplicates, dedup = annotate_group(rows)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(len(dedup), 2)
        self.assertEqual([r["sample_weight"] for r in dedup], [2, 1])
        self.assertEqual({r["y"] for r in dedup}, {"0", "1"})
        self.assertEqual(sum(r["sample_weight"] for r in dedup), 3)

    def test_output_cannot_target_originals(self):
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder)
            for target in [source, source / "ames", source / "ames/processed"]:
                with self.assertRaises(ValueError):
                    validate_output_location(source, target, ["ames"])
            validate_output_location(source, source / "new_directory", ["ames"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
