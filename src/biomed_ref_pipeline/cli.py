from __future__ import annotations

import argparse
import json
from pathlib import Path

from .docx_tools import validate_final_docx, write_review_docx
from .io_utils import ensure_dir, read_pmids, read_tsv, write_lines, write_tsv
from .jcr import load_jcr_records, screen_metadata_rows
from .pmid import extract_pmid_groups_from_docx, unique_pmids
from .planning import build_citation_plan, write_citation_plan_markdown
from .pubmed import fetch_pubmed_metadata
from .qc import manuscript_qc_report, read_docx_text
from .ris import split_ris_file, write_ris
from .scoring import score_references
from .workspace import init_workspace
from .zotero import check_pmids_in_zotero_sqlite
from .zotero_ooxml import insert_zotero_fields


METADATA_FIELDS = [
    "pmid",
    "title",
    "authors",
    "journal",
    "iso_abbreviation",
    "year",
    "doi",
    "publication_types",
    "mesh_terms",
    "abstract",
    "pubmed_url",
]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="biomed-ref", description="Biomedical reference automation CLI")
    sub = parser.add_subparsers(required=True)

    init = sub.add_parser("init-project", help="Create a standard project workspace")
    init.add_argument("--out", required=True)
    init.add_argument("--name", default="biomed-reference-project")
    init.set_defaults(func=cmd_init_project)

    extract = sub.add_parser("extract", help="Extract PMID groups from a Word document")
    extract.add_argument("--docx", required=True)
    extract.add_argument("--out", required=True)
    extract.set_defaults(func=cmd_extract)

    fetch = sub.add_parser("fetch", help="Fetch PubMed metadata for PMIDs")
    fetch.add_argument("--pmids", required=True)
    fetch.add_argument("--out", required=True)
    fetch.add_argument("--email")
    fetch.add_argument("--api-key")
    fetch.set_defaults(func=cmd_fetch)

    ris = sub.add_parser("ris", help="Generate Zotero RIS from PubMed metadata TSV")
    ris.add_argument("--metadata", required=True)
    ris.add_argument("--out", required=True)
    ris.set_defaults(func=cmd_ris)

    split_ris = sub.add_parser("split-ris", help="Split a RIS file into Zotero-friendly batches")
    split_ris.add_argument("--ris", required=True)
    split_ris.add_argument("--out", required=True)
    split_ris.add_argument("--batch-size", type=int, default=100)
    split_ris.set_defaults(func=cmd_split_ris)

    zotero = sub.add_parser("zotero-check", help="Check PMIDs against a Zotero SQLite database")
    zotero.add_argument("--pmids", required=True)
    zotero.add_argument("--sqlite", required=True)
    zotero.add_argument("--out", required=True)
    zotero.set_defaults(func=cmd_zotero_check)

    jcr = sub.add_parser("jcr-screen", help="Screen PubMed metadata against a JCR workbook")
    jcr.add_argument("--metadata", required=True)
    jcr.add_argument("--jcr-xlsx", required=True)
    jcr.add_argument("--out", required=True)
    jcr.add_argument("--min-if", type=float, default=5.0)
    jcr.set_defaults(func=cmd_jcr_screen)

    score = sub.add_parser("score", help="Score and classify references for writing priority")
    score.add_argument("--metadata", required=True)
    score.add_argument("--jcr-screen")
    score.add_argument("--out", required=True)
    score.set_defaults(func=cmd_score)

    plan = sub.add_parser("plan", help="Build a per-location Zotero insertion plan")
    plan.add_argument("--groups", required=True)
    plan.add_argument("--metadata")
    plan.add_argument("--zotero-check")
    plan.add_argument("--scores")
    plan.add_argument("--out", required=True)
    plan.add_argument("--markdown")
    plan.set_defaults(func=cmd_plan)

    review = sub.add_parser("review-docx", help="Create a Word review copy with a citation plan appendix")
    review.add_argument("--docx", required=True)
    review.add_argument("--plan", required=True)
    review.add_argument("--out", required=True)
    review.set_defaults(func=cmd_review_docx)

    insert_fields = sub.add_parser("insert-zotero-fields", help="Replace PMID placeholders with Zotero Word fields")
    insert_fields.add_argument("--docx", required=True)
    insert_fields.add_argument("--groups", required=True)
    insert_fields.add_argument("--metadata", required=True)
    insert_fields.add_argument("--out", required=True)
    insert_fields.add_argument("--report")
    insert_fields.add_argument("--on-missing", choices=["fail", "skip"], default="fail")
    insert_fields.set_defaults(func=cmd_insert_zotero_fields)

    validate = sub.add_parser("validate-docx", help="Validate a final Word document after Zotero insertion")
    validate.add_argument("--docx", required=True)
    validate.add_argument("--expected-pmids")
    validate.add_argument("--out", required=True)
    validate.set_defaults(func=cmd_validate_docx)

    qc = sub.add_parser("qc", help="Run heuristic manuscript QC")
    qc.add_argument("--docx", required=True)
    qc.add_argument("--out", required=True)
    qc.set_defaults(func=cmd_qc)

    run = sub.add_parser("run", help="Run the end-to-end MVP pipeline")
    run.add_argument("--docx", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--zotero-sqlite")
    run.add_argument("--jcr-xlsx")
    run.add_argument("--email")
    run.add_argument("--api-key")
    run.add_argument("--review-docx", help="Optional path for a Word review copy with citation plan appendix")
    run.add_argument("--zotero-field-docx", help="Optional path for a Word copy with embedded Zotero ADDIN fields")
    run.add_argument("--ris-batch-size", type=int, default=0, help="When >0, split zotero_import.ris into batches of this size")
    run.set_defaults(func=cmd_run)
    return parser


def cmd_init_project(args: argparse.Namespace) -> int:
    created = init_workspace(args.out, project_name=args.name)
    print(f"Initialized project workspace at {args.out} with {len(created)} directories.")
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(args.out)
    groups = extract_pmid_groups_from_docx(args.docx)
    pmids = unique_pmids(groups)
    write_tsv(out_dir / "pmid_groups.tsv", [group.to_row() for group in groups], ["source", "location", "raw_text", "pmids"])
    write_lines(out_dir / "unique_pmids.txt", pmids)
    print(f"Extracted {len(pmids)} unique PMIDs from {len(groups)} groups.")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(args.out)
    rows = fetch_pubmed_metadata(read_pmids(args.pmids), email=args.email, api_key=args.api_key)
    write_tsv(out_dir / "pubmed_metadata.tsv", rows, METADATA_FIELDS)
    print(f"Fetched metadata for {len(rows)} PubMed records.")
    return 0


def cmd_ris(args: argparse.Namespace) -> int:
    rows = read_tsv(args.metadata)
    write_ris(rows, args.out)
    print(f"Wrote RIS records to {args.out}.")
    return 0


def cmd_split_ris(args: argparse.Namespace) -> int:
    outputs = split_ris_file(args.ris, args.out, batch_size=args.batch_size)
    print(f"Wrote {len(outputs)} RIS batch file(s) to {args.out}.")
    return 0


def cmd_zotero_check(args: argparse.Namespace) -> int:
    rows = check_pmids_in_zotero_sqlite(read_pmids(args.pmids), args.sqlite)
    write_tsv(args.out, rows, ["pmid", "in_zotero", "matched_values"])
    print(f"Wrote Zotero check for {len(rows)} PMIDs.")
    return 0


def cmd_jcr_screen(args: argparse.Namespace) -> int:
    metadata = read_tsv(args.metadata)
    records = load_jcr_records(args.jcr_xlsx)
    rows = screen_metadata_rows(metadata, records, min_if=args.min_if)
    write_tsv(args.out, rows)
    print(f"Wrote JCR screen for {len(rows)} metadata rows.")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    metadata = read_tsv(args.metadata)
    jcr_rows = read_tsv(args.jcr_screen) if args.jcr_screen else None
    rows = score_references(metadata, jcr_rows)
    write_tsv(args.out, rows)
    print(f"Wrote reference scores for {len(rows)} metadata rows.")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    group_rows = read_tsv(args.groups)
    metadata_rows = read_tsv(args.metadata) if args.metadata else None
    zotero_rows = read_tsv(args.zotero_check) if args.zotero_check else None
    scored_rows = read_tsv(args.scores) if args.scores else None
    rows = build_citation_plan(
        group_rows,
        metadata_rows=metadata_rows,
        zotero_rows=zotero_rows,
        scored_rows=scored_rows,
    )
    write_tsv(args.out, rows)
    if args.markdown:
        write_citation_plan_markdown(rows, args.markdown)
    print(f"Wrote citation plan for {len(rows)} citation groups.")
    return 0


def cmd_review_docx(args: argparse.Namespace) -> int:
    plan_rows = read_tsv(args.plan)
    write_review_docx(args.docx, plan_rows, args.out)
    print(f"Wrote Word review copy to {args.out}.")
    return 0


def cmd_insert_zotero_fields(args: argparse.Namespace) -> int:
    report = insert_zotero_fields(
        args.docx,
        read_tsv(args.groups),
        read_tsv(args.metadata),
        args.out,
        on_missing=args.on_missing,
    )
    report_text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).write_text(report_text + "\n", encoding="utf-8")
    print(report_text)
    return 0


def cmd_validate_docx(args: argparse.Namespace) -> int:
    expected = read_pmids(args.expected_pmids) if args.expected_pmids else None
    report = validate_final_docx(args.docx, expected)
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Wrote final DOCX validation report to {args.out}.")
    return 0


def cmd_qc(args: argparse.Namespace) -> int:
    report = manuscript_qc_report(read_docx_text(args.docx))
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Wrote manuscript QC report to {args.out}.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(args.out)

    groups = extract_pmid_groups_from_docx(args.docx)
    pmids = unique_pmids(groups)
    write_tsv(out_dir / "pmid_groups.tsv", [group.to_row() for group in groups], ["source", "location", "raw_text", "pmids"])
    write_lines(out_dir / "unique_pmids.txt", pmids)

    metadata_rows = []
    if pmids:
        metadata_rows = fetch_pubmed_metadata(pmids, email=args.email, api_key=args.api_key)
        write_tsv(out_dir / "pubmed_metadata.tsv", metadata_rows, METADATA_FIELDS)
        ris_path = out_dir / "zotero_import.ris"
        write_ris(metadata_rows, ris_path)
        if args.ris_batch_size and args.ris_batch_size > 0:
            split_ris_file(ris_path, out_dir / "ris_batches", batch_size=args.ris_batch_size)

    zotero_rows = []
    if args.zotero_sqlite:
        zotero_rows = check_pmids_in_zotero_sqlite(pmids, args.zotero_sqlite)
        write_tsv(out_dir / "zotero_check.tsv", zotero_rows, ["pmid", "in_zotero", "matched_values"])

    jcr_rows = []
    if args.jcr_xlsx and metadata_rows:
        jcr_records = load_jcr_records(args.jcr_xlsx)
        jcr_rows = screen_metadata_rows(metadata_rows, jcr_records)
        write_tsv(out_dir / "jcr_screen.tsv", jcr_rows)

    scored_rows = []
    if metadata_rows:
        scored_rows = score_references(metadata_rows, jcr_rows)
        write_tsv(out_dir / "reference_scores.tsv", scored_rows)

    plan_rows = build_citation_plan(
        [group.to_row() for group in groups],
        metadata_rows=metadata_rows,
        zotero_rows=zotero_rows,
        scored_rows=scored_rows,
    )
    write_tsv(out_dir / "citation_plan.tsv", plan_rows)
    write_citation_plan_markdown(plan_rows, out_dir / "citation_plan.md")
    if args.review_docx:
        write_review_docx(args.docx, plan_rows, args.review_docx)
    if args.zotero_field_docx:
        report = insert_zotero_fields(args.docx, [group.to_row() for group in groups], metadata_rows, args.zotero_field_docx)
        (out_dir / "zotero_field_insert_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    qc_report = manuscript_qc_report(read_docx_text(args.docx))
    (out_dir / "manuscript_qc.md").write_text(qc_report, encoding="utf-8")
    _write_summary(out_dir, pmids, groups, metadata_rows)
    print(f"Pipeline complete. Output directory: {out_dir}")
    return 0


def _write_summary(out_dir: Path, pmids: list[str], groups: list[object], metadata_rows: list[dict[str, str]]) -> None:
    missing = sorted(set(pmids) - {row.get("pmid", "") for row in metadata_rows})
    lines = [
        "# Run Summary",
        "",
        f"- PMID groups found: {len(groups)}",
        f"- Unique PMIDs found: {len(pmids)}",
        f"- PubMed records fetched: {len(metadata_rows)}",
        f"- Missing PubMed records: {len(missing)}",
    ]
    if missing:
        lines.append(f"- Missing PMIDs: {' '.join(missing)}")
    (out_dir / "run_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
