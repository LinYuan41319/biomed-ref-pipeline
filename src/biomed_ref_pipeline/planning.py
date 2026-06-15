from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Mapping


def build_citation_plan(
    group_rows: list[Mapping[str, str]],
    *,
    metadata_rows: list[Mapping[str, str]] | None = None,
    zotero_rows: list[Mapping[str, str]] | None = None,
    scored_rows: list[Mapping[str, str]] | None = None,
) -> list[dict[str, str]]:
    metadata_by_pmid = {str(row.get("pmid", "")): row for row in metadata_rows or []}
    zotero_by_pmid = {str(row.get("pmid", "")): row for row in zotero_rows or []}
    score_by_pmid = {str(row.get("pmid", "")): row for row in scored_rows or []}

    plan: list[dict[str, str]] = []
    for index, group in enumerate(group_rows, start=1):
        pmids = parse_pmids_cell(str(group.get("pmids", "")))
        missing_pubmed = [pmid for pmid in pmids if pmid not in metadata_by_pmid]
        missing_zotero = [
            pmid for pmid in pmids if zotero_by_pmid and zotero_by_pmid.get(pmid, {}).get("in_zotero", "") != "yes"
        ]
        titles = [_compact(metadata_by_pmid.get(pmid, {}).get("title", "")) for pmid in pmids]
        evidence_types = [score_by_pmid.get(pmid, {}).get("evidence_type", "") for pmid in pmids]
        priority_scores = [score_by_pmid.get(pmid, {}).get("priority_score", "") for pmid in pmids]

        action = "ready_for_zotero_insert"
        if missing_pubmed:
            action = "verify_pubmed_missing"
        elif missing_zotero:
            action = "import_missing_to_zotero"

        plan.append(
            {
                "citation_id": f"CITE-{index:04d}",
                "source": str(group.get("source", "")),
                "location": str(group.get("location", "")),
                "raw_text": str(group.get("raw_text", "")),
                "pmids": " ".join(pmids),
                "pmid_count": str(len(pmids)),
                "pubmed_status": "missing:" + " ".join(missing_pubmed) if missing_pubmed else "verified",
                "zotero_status": _zotero_status(pmids, zotero_by_pmid, missing_zotero),
                "recommended_action": action,
                "titles": " | ".join(title for title in titles if title),
                "evidence_types": " | ".join(value for value in evidence_types if value),
                "priority_scores": " | ".join(value for value in priority_scores if value),
                "notes": _notes(pmids, missing_pubmed, missing_zotero),
            }
        )
    return plan


def write_citation_plan_markdown(plan_rows: list[Mapping[str, str]], path: str | Path) -> None:
    lines = [
        "# Citation Plan",
        "",
        "Use this file before Zotero insertion. Each row maps one manuscript location to the PMID(s) that should be inserted together.",
        "",
    ]
    counts = Counter(row.get("recommended_action", "") for row in plan_rows)
    lines.append("## Summary")
    lines.append("")
    for action, count in sorted(counts.items()):
        lines.append(f"- {action}: {count}")
    lines.append("")
    lines.append("## Items")
    lines.append("")
    for row in plan_rows:
        lines.extend(
            [
                f"### {row.get('citation_id', '')}",
                "",
                f"- Location: `{row.get('location', '')}`",
                f"- PMIDs: `{row.get('pmids', '')}`",
                f"- PubMed: {row.get('pubmed_status', '')}",
                f"- Zotero: {row.get('zotero_status', '')}",
                f"- Action: `{row.get('recommended_action', '')}`",
            ]
        )
        if row.get("titles"):
            lines.append(f"- Titles: {row.get('titles')}")
        if row.get("notes"):
            lines.append(f"- Notes: {row.get('notes')}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def parse_pmids_cell(value: str) -> list[str]:
    seen: set[str] = set()
    pmids: list[str] = []
    for token in value.replace(",", " ").replace(";", " ").split():
        digits = "".join(ch for ch in token if ch.isdigit())
        if len(digits) >= 6 and digits not in seen:
            seen.add(digits)
            pmids.append(digits)
    return pmids


def _zotero_status(pmids: list[str], zotero_by_pmid: Mapping[str, Mapping[str, str]], missing_zotero: list[str]) -> str:
    if not zotero_by_pmid:
        return "not_checked"
    if missing_zotero:
        return "missing:" + " ".join(missing_zotero)
    return "available"


def _notes(pmids: list[str], missing_pubmed: list[str], missing_zotero: list[str]) -> str:
    notes: list[str] = []
    if len(pmids) > 1:
        notes.append("insert as one multi-source citation")
    if missing_pubmed:
        notes.append("PubMed metadata missing; verify PMID before insertion")
    if missing_zotero:
        notes.append("import missing items into Zotero before insertion")
    return "; ".join(notes)


def _compact(value: object, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."
