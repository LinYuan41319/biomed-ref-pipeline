# Demo Workflow

This demo uses synthetic text only. Do not commit real manuscripts.

## 1. Create A Small Word Manuscript

Create a `.docx` containing:

```text
Ferroptosis was linked to cardiovascular injury (PMID: 35805165, 28776083).
Single-cell association requires validation. PMID: 29449364
```

## 2. Run The Pipeline

```powershell
python -m pip install -e .
biomed-ref run --docx sample.docx --out out --ris-batch-size 100 --review-docx out\review_copy.docx
```

## 3. Insert Zotero-Compatible Fields

```powershell
biomed-ref insert-zotero-fields `
  --docx sample.docx `
  --groups out\pmid_groups.tsv `
  --metadata out\pubmed_metadata.tsv `
  --out out\sample_zotero_fields.docx `
  --report out\zotero_field_insert_report.json `
  --on-missing skip
```

## 4. Validate The Output

```powershell
biomed-ref validate-docx `
  --docx out\sample_zotero_fields.docx `
  --expected-pmids out\unique_pmids.txt `
  --out out\validation.md
```

Expected outputs include `pmid_groups.tsv`, `pubmed_metadata.tsv`, `zotero_import.ris`, `citation_plan.md`, `manuscript_qc.md`, and validation reports.
