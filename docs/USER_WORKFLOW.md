# User Workflow

## 1. Create A Project Workspace

```powershell
biomed-ref init-project --out "my_review_project" --name "Mitochondrial Translation Review"
```

Place source files in `00_inputs`:

- source manuscript `.docx`
- JCR workbook `.xlsx`
- optional Zotero SQLite snapshot

## 2. Run The Main Pipeline

```powershell
biomed-ref run `
  --docx "my_review_project\00_inputs\source_manuscript.docx" `
  --out "my_review_project\pipeline_out" `
  --jcr-xlsx "my_review_project\00_inputs\jcr_2024_full.xlsx" `
  --zotero-sqlite "my_review_project\00_inputs\zotero.sqlite" `
  --ris-batch-size 100 `
  --review-docx "my_review_project\06_citation_plan\review_copy.docx" `
  --zotero-field-docx "my_review_project\06_citation_plan\manuscript_zotero_fields.docx"
```

## 3. Import Missing References Into Zotero

Use `zotero_import.ris` or the files in `ris_batches/`.

## 4. Insert Citations In Word

Use `citation_plan.md` as the insertion checklist. One row equals one manuscript location; multiple PMIDs in one row should be inserted as one multi-source citation.

For an automated Word-field copy:

```powershell
biomed-ref insert-zotero-fields `
  --docx "my_review_project\00_inputs\source_manuscript.docx" `
  --groups "my_review_project\pipeline_out\pmid_groups.tsv" `
  --metadata "my_review_project\pipeline_out\pubmed_metadata.tsv" `
  --out "my_review_project\06_citation_plan\manuscript_zotero_fields.docx" `
  --report "my_review_project\06_citation_plan\zotero_field_insert_report.json"
```

This writes embedded Zotero `ADDIN ZOTERO_ITEM CSL_CITATION` fields and a `ZOTERO_BIBL` field into a new `.docx` copy.

## 5. Validate Final Word File

```powershell
biomed-ref validate-docx `
  --docx "final_manuscript.docx" `
  --expected-pmids "pipeline_out\unique_pmids.txt" `
  --out "08_final_validation\final_docx_validation.md"
```

Review any remaining visible PMID placeholders before submission.
