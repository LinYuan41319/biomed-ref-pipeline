# Security Policy

## Supported Versions

Security fixes target the latest version on the `main` branch until tagged releases are established.

## Reporting A Vulnerability

Please open a private security advisory on GitHub if the repository is public and the issue could expose private manuscripts, local Zotero data, filesystem paths, or remote-code execution risks.

For lower-risk issues, open a GitHub issue with:

- affected command
- expected behavior
- observed behavior
- minimal reproduction using synthetic data only

Do not attach real manuscripts, Zotero databases, JCR workbooks, or personal medical information.

## Current Security Boundaries

- The tool runs locally and does not upload manuscript content.
- PubMed metadata fetching uses NCBI E-utilities.
- Zotero checks read a local SQLite snapshot in read-only mode.
- Generated Word files are written to explicit output paths and should be reviewed before sharing.
