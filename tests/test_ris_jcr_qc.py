import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from biomed_ref_pipeline.jcr import load_jcr_records, screen_metadata_rows
from biomed_ref_pipeline.qc import manuscript_qc_report
from biomed_ref_pipeline.ris import read_ris_records, record_to_ris, split_ris_file


class RisJcrQcTests(unittest.TestCase):
    def test_ris_record(self):
        record = record_to_ris({"pmid": "12345678", "title": "T", "journal": "J", "year": "2025"})
        self.assertIn("TY  - JOUR", record)
        self.assertIn("N1  - PMID: 12345678", record)
        self.assertIn("ER  -", record)

    def test_split_ris_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "all.ris"
            source.write_text(
                record_to_ris({"pmid": "1", "title": "A"}) + "\n" + record_to_ris({"pmid": "2", "title": "B"}),
                encoding="utf-8",
            )
            records = read_ris_records(source)
            self.assertEqual(len(records), 2)
            outputs = split_ris_file(source, Path(tmp) / "batches", batch_size=1)
            self.assertEqual(len(outputs), 2)

    def test_jcr_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jcr.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["Journal Name", "JIF Quartile", "5-Year JIF", "JIF 2024"])
            ws.append(["Example Journal", "Q1", 6.7, 6.1])
            wb.save(path)
            records = load_jcr_records(path)
            rows = screen_metadata_rows([{"pmid": "1", "journal": "Example Journal"}], records)
            self.assertEqual(rows[0]["priority_q1q2_if5"], "yes")

    def test_qc_flags_overclaim(self):
        report = manuscript_qc_report("Single-cell association proves causal disease remodeling. PMID: 12345678 23456789 34567890 45678901")
        self.assertIn("Strong causal wording", report)
        self.assertIn("citation density", report)


if __name__ == "__main__":
    unittest.main()
