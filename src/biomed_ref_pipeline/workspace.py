from __future__ import annotations

from pathlib import Path


WORKSPACE_DIRS = [
    "00_inputs",
    "01_pmid_extraction",
    "02_pubmed_metadata",
    "03_zotero_import",
    "04_jcr_screening",
    "05_reference_scoring",
    "06_citation_plan",
    "07_manuscript_qc",
    "08_final_validation",
    "logs",
]


def init_workspace(path: str | Path, *, project_name: str = "biomed-reference-project") -> list[Path]:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for dirname in WORKSPACE_DIRS:
        target = root / dirname
        target.mkdir(parents=True, exist_ok=True)
        created.append(target)

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(_workspace_readme(project_name), encoding="utf-8")

    config = root / "biomed_ref_pipeline.toml"
    if not config.exists():
        config.write_text(_config_template(project_name), encoding="utf-8")

    return created


def _workspace_readme(project_name: str) -> str:
    return f"""# {project_name}

Biomedical reference project workspace.

## Directory Map

- `00_inputs`: source manuscript, outline, JCR workbook, and user-provided files.
- `01_pmid_extraction`: PMID groups and unique PMID lists.
- `02_pubmed_metadata`: PubMed metadata TSV/XML exports.
- `03_zotero_import`: RIS files and Zotero import batches.
- `04_jcr_screening`: JCR matching and IF/Q screening.
- `05_reference_scoring`: reference priority scores and evidence classes.
- `06_citation_plan`: Zotero insertion plan files and review copies.
- `07_manuscript_qc`: manuscript QC reports.
- `08_final_validation`: final DOCX validation reports.
- `logs`: run logs and decisions.

"""


def _config_template(project_name: str) -> str:
    return f"""project_name = "{project_name}"
email = ""
ncbi_api_key = ""

[paths]
manuscript = "00_inputs/source_manuscript.docx"
jcr_xlsx = "00_inputs/jcr_2024_full.xlsx"
zotero_sqlite = ""

[screening]
min_if = 5.0
ris_batch_size = 100
"""
