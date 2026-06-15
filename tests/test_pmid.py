import unittest

from biomed_ref_pipeline.pmid import extract_pmid_groups_from_text, extract_pmids_from_text, unique_pmids


class PmidExtractionTests(unittest.TestCase):
    def test_extracts_context_pmids(self):
        text = "Mechanism sentence (pmid: 12345678, 23456789); next PMID:34567890."
        self.assertEqual(extract_pmids_from_text(text), ["12345678", "23456789", "34567890"])

    def test_groups_keep_multi_pmid_locations(self):
        groups = extract_pmid_groups_from_text("Claim (PMIDs: 12345678; 23456789).", source="x", location="p1")
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].pmids, ["12345678", "23456789"])
        self.assertEqual(unique_pmids(groups), ["12345678", "23456789"])


if __name__ == "__main__":
    unittest.main()
