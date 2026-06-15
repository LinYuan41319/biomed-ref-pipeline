# Biomed Ref Pipeline

[![CI](https://github.com/LinYuan41319/biomed-ref-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/LinYuan41319/biomed-ref-pipeline/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Local biomedical reference automation for manuscript work:

- Extract PMID groups from Word manuscripts.
- Fetch verified PubMed metadata through NCBI E-utilities.
- Generate RIS files for Zotero import.
- Check whether PMIDs already exist in a Zotero SQLite database or snapshot.
- Match PubMed journal metadata against a JCR workbook.
- Build a per-location Zotero citation insertion plan.
- Generate a Word review copy with a citation plan appendix.
- Replace visible PMID placeholders with embedded Zotero Word fields.
- Validate final Word documents after Zotero insertion.
- Score references by recency, evidence type, JCR quartile, and impact factor.
- Run lightweight manuscript QC for citation density and evidence-strength wording.

The first version is intentionally CLI-first so it can be scripted, tested, and pushed to GitHub. A desktop/web UI can be added on top of the same package later.

## Why This Exists

Biomedical manuscripts often accumulate raw PMID placeholders during drafting. Turning those placeholders into verified Zotero citations is repetitive and error-prone: each PMID must be checked against PubMed, imported into Zotero, inserted at the right Word location, and validated before submission.

Biomed Ref Pipeline makes that workflow reproducible. It keeps the original manuscript untouched, writes review copies separately, and produces machine-readable audit files for every citation group.

## Project Status

This is an early open-source CLI project. The current priority is a reliable local workflow for researchers and maintainers who need PubMed, Zotero, Word, and JCR-style screening in one scriptable tool.

- Tested with `python -m unittest discover -s tests -t .`.
- Packaged with `pyproject.toml`.
- CI runs on push and pull request.
- Planned next steps are tracked in [ROADMAP.md](ROADMAP.md).

## Quick Start

```powershell
python -m pip install -e .
biomed-ref init-project --out "my_review_project" --name "Mitochondrial Translation Review"
biomed-ref run --docx "manuscript.docx" --out "out"
```

With Zotero and JCR checks:

```powershell
biomed-ref run `
  --docx "manuscript.docx" `
  --out "out" `
  --zotero-sqlite "zotero.sqlite" `
  --jcr-xlsx "jcr_2024_full.xlsx" `
  --email "your.email@example.com" `
  --ris-batch-size 100 `
  --review-docx "out\manuscript_review_copy.docx" `
  --zotero-field-docx "out\manuscript_zotero_fields.docx"
```

Outputs:

- `pmid_groups.tsv`: each detected PMID group and source location.
- `unique_pmids.txt`: deduplicated PMIDs, one per line.
- `pubmed_metadata.tsv`: verified PubMed metadata.
- `zotero_import.ris`: RIS import file for Zotero.
- optional `ris_batches/`: Zotero import batches when `--ris-batch-size` is used.
- `zotero_check.tsv`: whether each PMID appears in a Zotero SQLite database.
- `jcr_screen.tsv`: JCR quartile and impact factor screening result.
- `reference_scores.tsv`: evidence type, priority score, tier, and retain reason.
- `citation_plan.tsv`: per-location Zotero insertion plan.
- `citation_plan.md`: readable citation plan for manual review.
- optional review `.docx`: original manuscript plus citation plan appendix.
- optional Zotero field `.docx`: visible PMID placeholders replaced by `ADDIN ZOTERO_ITEM CSL_CITATION` fields, plus one `ZOTERO_BIBL` field.
- `manuscript_qc.md`: manuscript quality-control report.
- `run_summary.md`: short end-of-run summary.

## Commands

```powershell
biomed-ref init-project --out my_review_project --name "My Review"
biomed-ref extract --docx manuscript.docx --out out
biomed-ref fetch --pmids out/unique_pmids.txt --out out --email you@example.com
biomed-ref ris --metadata out/pubmed_metadata.tsv --out out/zotero_import.ris
biomed-ref split-ris --ris out/zotero_import.ris --out out/ris_batches --batch-size 100
biomed-ref zotero-check --pmids out/unique_pmids.txt --sqlite zotero.sqlite --out out/zotero_check.tsv
biomed-ref jcr-screen --metadata out/pubmed_metadata.tsv --jcr-xlsx jcr_2024_full.xlsx --out out/jcr_screen.tsv
biomed-ref score --metadata out/pubmed_metadata.tsv --jcr-screen out/jcr_screen.tsv --out out/reference_scores.tsv
biomed-ref plan --groups out/pmid_groups.tsv --metadata out/pubmed_metadata.tsv --zotero-check out/zotero_check.tsv --scores out/reference_scores.tsv --out out/citation_plan.tsv --markdown out/citation_plan.md
biomed-ref review-docx --docx manuscript.docx --plan out/citation_plan.tsv --out out/manuscript_review_copy.docx
biomed-ref insert-zotero-fields --docx manuscript.docx --groups out/pmid_groups.tsv --metadata out/pubmed_metadata.tsv --out out/manuscript_zotero_fields.docx --report out/zotero_field_insert_report.json
biomed-ref validate-docx --docx final_manuscript.docx --expected-pmids out/unique_pmids.txt --out out/final_docx_validation.md
biomed-ref qc --docx manuscript.docx --out out/manuscript_qc.md
```

See [docs/USER_WORKFLOW.md](docs/USER_WORKFLOW.md) for the recommended manuscript workflow.

## Open Source Readiness

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Demo workflow: [docs/DEMO.md](docs/DEMO.md)
- Maintainer automation plan: [docs/MAINTAINER_AUTOMATION.md](docs/MAINTAINER_AUTOMATION.md)

For grant or open-source support applications, make sure the GitHub profile and repository are public before submitting.

## GitHub Publishing

If Git and GitHub CLI are installed and authenticated:

```powershell
.\scripts\publish_to_github.ps1 -Repo "yourname/biomed-ref-pipeline" -CreateRepo
```

If you use the Codex GitHub plugin, create an empty repository first, then ask Codex to push this folder to that repository or open a PR.

## Notes

- The tool never edits the original manuscript. Review copies are written to a separate output path.
- Zotero field insertion writes Word `ADDIN ZOTERO_ITEM CSL_CITATION` and `ZOTERO_BIBL` fields with embedded CSL item data. It does not require overwriting the source manuscript.
- Zotero library import is still handled through RIS files and Zotero connector/API checks; connector timeouts should be resolved before running real manuscripts unattended.
- PubMed requests use standard library networking and retry logic; no `requests` dependency is required.
- The final `.docx` validator detects remaining visible PMID placeholders and embedded Zotero field markers, but it does not replace expert review.
