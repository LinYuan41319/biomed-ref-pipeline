# Roadmap

This roadmap follows the current productivity priority order.

## 0.1.0 - Working CLI MVP

Status: done.

- Extract PMID groups from `.docx`.
- Fetch PubMed metadata.
- Generate Zotero RIS.
- Check PMIDs against Zotero SQLite snapshots.
- Screen PubMed metadata against JCR workbooks.
- Run heuristic manuscript QC.
- Include tests and GitHub Actions CI.

## 0.2.0 - Safer Zotero/Word Workflow

Goal: reduce manual work before Zotero citation insertion.

Status: partly done.

- Done: generate a per-location citation plan for one PMID or multiple PMIDs.
- Done: generate a review copy with a citation plan appendix.
- Done: validate final Word documents for remaining PMID placeholders and Zotero field markers.
- Done: clearer missing-item triage: already in Zotero, import needed, PubMed metadata missing.
- Done: add import batches for large RIS files.
- Done: add Word `ADDIN ZOTERO_ITEM` and `ZOTERO_BIBL` field insertion with embedded CSL item data.
- Remaining: harden Zotero connector import when Zotero Desktop times out.

## 0.3.0 - JCR and Evidence Ranking

Goal: turn PubMed metadata into writing-ready reference tables.

Status: partly done.

- Done: priority scoring by year, publication type, JCR quartile, impact factor, and evidence type.
- Done: export `reference_scores.tsv`.
- Remaining: improve journal-name matching with abbreviation aliases.
- Remaining: add configurable JCR column mapping.
- Remaining: export section-level `writing_input.md` and `reference_table.tsv`.

## 0.4.0 - Manuscript QC Expansion

Goal: catch common biomedical review weaknesses before submission.

- Detect unsupported causal language in more contexts.
- Detect review citations being used as primary mechanism evidence.
- Detect candidate pathways written as validated mechanisms.
- Detect inconsistent spelling and abbreviation expansion.
- Generate clean Markdown and Word QC reports.

## 0.5.0 - Local Web UI

Goal: make the workflow usable without remembering CLI commands.

- Add a local FastAPI or Streamlit interface.
- Upload manuscript, JCR workbook, and optional Zotero snapshot.
- Show run progress and failure recovery.
- Download a complete manuscript-support package.

## 1.0.0 - Biomedical Review Workbench

Goal: integrate literature mining, reference management, writing inputs, and final QC into one stable local application.

- Project-based workspace structure.
- PubMed search strategy builder.
- JCR screening dashboard.
- Zotero import and Word validation workflow.
- Manuscript package export.
- GitHub-backed version history and releases.
