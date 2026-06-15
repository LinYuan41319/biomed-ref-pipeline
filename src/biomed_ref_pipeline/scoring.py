from __future__ import annotations

import re
from datetime import date
from typing import Mapping


REVIEW_RE = re.compile(r"\breview\b|meta-analysis|systematic review", re.I)
TRIAL_RE = re.compile(r"clinical trial|randomized|randomised", re.I)
CLINICAL_RE = re.compile(r"\bhumans?\b|cohort|case-control|patients?", re.I)
OMICS_RE = re.compile(r"single-cell|spatial|transcriptom|proteom|metabolom|bioinformatic|omics", re.I)
MECHANISM_RE = re.compile(r"mechanism|pathway|knockout|silencing|overexpression|mouse|mice|rat|cell line|in vitro|in vivo", re.I)
METHOD_RE = re.compile(r"method|protocol|software|database|algorithm", re.I)


def score_references(
    metadata_rows: list[Mapping[str, str]],
    jcr_rows: list[Mapping[str, str]] | None = None,
    *,
    current_year: int | None = None,
) -> list[dict[str, str]]:
    jcr_by_pmid = {str(row.get("pmid", "")): row for row in jcr_rows or []}
    return [_score_one(row, jcr_by_pmid.get(str(row.get("pmid", "")), {}), current_year=current_year) for row in metadata_rows]


def classify_evidence(row: Mapping[str, str]) -> tuple[str, str]:
    haystack = " ".join(
        [
            str(row.get("title", "")),
            str(row.get("abstract", "")),
            str(row.get("publication_types", "")),
            str(row.get("mesh_terms", "")),
        ]
    )
    publication_types = str(row.get("publication_types", ""))

    if TRIAL_RE.search(haystack):
        return "clinical_trial", "Clinical intervention evidence; verify design, sample size, and endpoints."
    if REVIEW_RE.search(publication_types):
        return "review_or_meta_analysis", "Useful for framing, but do not cite as primary mechanism evidence."
    if OMICS_RE.search(haystack):
        return "omics_or_bioinformatics", "Association or candidate-pathway evidence unless independently validated."
    if MECHANISM_RE.search(haystack):
        return "experimental_mechanism", "Mechanistic evidence; verify model and whether the pathway is closed."
    if CLINICAL_RE.search(haystack):
        return "clinical_observation", "Clinical association evidence; avoid causal wording."
    if METHOD_RE.search(haystack):
        return "methodology", "Method or resource evidence; cite only when method support is needed."
    return "general_biomedical", "Evidence type requires manual review."


def _score_one(row: Mapping[str, str], jcr: Mapping[str, str], *, current_year: int | None) -> dict[str, str]:
    evidence_type, note = classify_evidence(row)
    year = _int(row.get("year", ""))
    current_year = current_year or date.today().year
    quartile = str(jcr.get("jcr_quartile", row.get("jcr_quartile", ""))).upper()
    impact = _float(jcr.get("jcr_5yr_if", "") or jcr.get("jcr_2024_if", "") or row.get("jcr_5yr_if", ""))

    score = 0
    if year:
        age = max(0, current_year - year)
        score += max(0, 30 - age * 3)
    if evidence_type == "clinical_trial":
        score += 24
    elif evidence_type == "experimental_mechanism":
        score += 22
    elif evidence_type == "clinical_observation":
        score += 18
    elif evidence_type == "omics_or_bioinformatics":
        score += 14
    elif evidence_type == "review_or_meta_analysis":
        score += 8
    elif evidence_type == "methodology":
        score += 6

    if quartile == "Q1":
        score += 20
    elif quartile == "Q2":
        score += 12
    elif quartile == "Q3":
        score += 4

    if impact is not None:
        score += min(20, int(impact * 2))

    tier = "high" if score >= 62 else "medium" if score >= 40 else "low"
    retain_reason = _retain_reason(row, evidence_type, quartile, impact)

    return {
        **{str(key): str(value) for key, value in row.items()},
        "evidence_type": evidence_type,
        "evidence_strength_note": note,
        "priority_score": str(score),
        "priority_tier": tier,
        "retain_reason": retain_reason,
    }


def _retain_reason(row: Mapping[str, str], evidence_type: str, quartile: str, impact: float | None) -> str:
    title = str(row.get("title", ""))
    if evidence_type == "experimental_mechanism":
        base = "mechanistic relevance"
    elif evidence_type == "clinical_trial":
        base = "clinical intervention relevance"
    elif evidence_type == "omics_or_bioinformatics":
        base = "frontier discovery or candidate pathway relevance"
    elif evidence_type == "review_or_meta_analysis":
        base = "background synthesis"
    else:
        base = "topic relevance"
    journal = f"{quartile}" if quartile else "JCR unmatched"
    if impact is not None:
        journal += f", IF {impact:g}"
    return f"{base}; {journal}; {title[:90]}"


def _int(value: object) -> int | None:
    try:
        return int(str(value)[:4])
    except ValueError:
        return None


def _float(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except ValueError:
        return None
