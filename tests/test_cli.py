import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import FIELDS
from audit_catalog import audit_catalog


class LocalCatalogAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "client.csv"
        self.output = self.root / "reports"
        valid = {field: "" for field in FIELDS}
        valid.update({"id": "A-1", "title": "=2+2", "type": "movie", "release_year": "2022", "genres": "['Drama']"})
        blank = {field: "" for field in FIELDS}
        blank.update({"id": "A-1", "type": "SHOW"})
        with self.source.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows([valid, blank])

    def tearDown(self):
        self.temp.cleanup()

    def test_downloadable_template_matches_supported_schema(self):
        template = Path(__file__).resolve().parents[1] / "examples" / "catalog-template.csv"
        with template.open(encoding="utf-8", newline="") as file:
            self.assertEqual(next(csv.reader(file)), list(FIELDS))

    def test_reads_bom_utf8_and_preserves_non_ascii_catalog_text(self):
        row = {field: "" for field in FIELDS}
        row.update({"id": "A-2", "title": "Café 東京", "type": "MOVIE", "release_year": "2024"})
        with self.source.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(row)

        audit_catalog(self.source, self.output)
        with (self.output / "clean.csv").open(encoding="utf-8-sig", newline="") as file:
            self.assertEqual(next(csv.DictReader(file))["title"], "Café 東京")

    def test_falls_back_to_legacy_latin1_catalog_text(self):
        row = {field: "" for field in FIELDS}
        row.update({"id": "A-3", "title": "Café", "type": "MOVIE", "release_year": "2024"})
        with self.source.open("w", encoding="latin1", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(row)

        audit_catalog(self.source, self.output)
        with (self.output / "clean.csv").open(encoding="utf-8-sig", newline="") as file:
            self.assertEqual(next(csv.DictReader(file))["title"], "Café")

    def test_creates_private_local_report_clean_and_review_exports(self):
        report = audit_catalog(self.source, self.output)
        self.assertEqual(report["records"], 2)
        self.assertEqual(report["flagged_records"], 2)
        self.assertEqual(report["duplicate_source_ids"], 1)
        self.assertEqual(report["source_file"], "client.csv")
        self.assertNotIn(str(self.root), json.dumps(report))
        with (self.output / "audit.json").open(encoding="utf-8") as file:
            self.assertEqual(json.load(file), report)
        summary = (self.output / "summary.md").read_text(encoding="utf-8")
        self.assertIn("Records needing review: 2", summary)
        self.assertIn("Source SHA-256", summary)
        self.assertNotIn("=2+2", summary)
        with (self.output / "clean.csv").open(encoding="utf-8-sig", newline="") as file:
            clean = list(csv.DictReader(file))
        with (self.output / "review.csv").open(encoding="utf-8-sig", newline="") as file:
            review = list(csv.DictReader(file))
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["title"], "'=2+2")
        self.assertEqual(len(review), 2)
        self.assertEqual(review[0]["title"], "'=2+2")
        self.assertIn("Repeated source ID", review[0]["review_flags"])

    def test_refuses_overwrite_without_explicit_force(self):
        audit_catalog(self.source, self.output)
        with self.assertRaises(FileExistsError):
            audit_catalog(self.source, self.output)
        self.assertEqual(audit_catalog(self.source, self.output, force=True)["records"], 2)

    def test_rejects_missing_schema_without_creating_reports(self):
        self.source.write_text("id,title\n1,Movie\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            audit_catalog(self.source, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_rejects_duplicate_columns_without_creating_reports(self):
        columns = [*FIELDS, FIELDS[0]]
        with self.source.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerow(["value"] * len(columns))

        with self.assertRaisesRegex(ValueError, "duplicate columns"):
            audit_catalog(self.source, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_enforces_file_and_row_limits(self):
        with patch("audit_catalog.MAX_INPUT_BYTES", 1), self.assertRaisesRegex(ValueError, "exceeds"):
            audit_catalog(self.source, self.output)
        with patch("audit_catalog.MAX_ROWS", 1), self.assertRaisesRegex(ValueError, "row limit"):
            audit_catalog(self.source, self.output)
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
