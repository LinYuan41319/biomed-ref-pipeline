# Maintainer Automation Plan

This project is designed to use Codex and GitHub automation for open-source maintenance.

## Current Automation

- GitHub Actions runs unit tests on push and pull request.
- The CLI emits deterministic TSV, Markdown, RIS, JSON, and DOCX artifacts.
- Tests cover PMID extraction, PubMed XML parsing, RIS splitting, JCR matching, citation planning, scoring, DOCX validation, and Zotero Word field insertion.

## Planned Codex Uses

- Triage issues that include synthetic reproduction files.
- Draft focused fixes for failing CI runs.
- Review pull requests for privacy-sensitive file additions.
- Maintain release notes and changelog entries.
- Generate small synthetic DOCX fixtures for regression tests.
- Expand journal alias matching and JCR column mapping safely.

## API Credit Use Case

API credits would be used for maintainer automation, not manuscript processing by default:

- classify incoming issues by affected workflow
- summarize pull request risk
- propose tests for citation and DOCX edge cases
- draft release notes from merged changes
- run security-oriented review prompts on code changes

No private manuscripts or local Zotero databases should be sent to hosted models unless a user explicitly chooses that workflow and strips sensitive data.
