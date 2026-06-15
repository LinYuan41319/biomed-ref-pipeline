# Contributing

Thanks for considering a contribution to Biomed Ref Pipeline.

## Scope

This project focuses on local biomedical reference workflows:

- PMID extraction from Word manuscripts.
- PubMed metadata verification.
- Zotero RIS import preparation and Zotero Word field insertion.
- JCR-style journal screening.
- Citation-plan and manuscript-QC reports.

Please keep contributions scoped to reproducible local workflows and avoid uploading manuscripts, Zotero databases, JCR workbooks, or other private research files.

## Development Setup

```powershell
python -m pip install -e .
python -m unittest discover -s tests -t .
```

## Pull Request Expectations

- Add or update tests when behavior changes.
- Keep generated manuscript files, SQLite files, and local output folders out of the repository.
- Prefer small, focused changes.
- Document user-facing workflow changes in `README.md` or `docs/USER_WORKFLOW.md`.

## Privacy

Do not include protected health information, unpublished manuscripts, reviewer comments, private Zotero databases, or licensed JCR data in issues, tests, examples, or pull requests.
