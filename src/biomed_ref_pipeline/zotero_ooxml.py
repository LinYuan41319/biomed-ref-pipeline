from __future__ import annotations

import json
import random
import re
import string
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Mapping
from xml.sax.saxutils import escape

from lxml import etree

from .planning import parse_pmids_cell


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CUSTOM_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
NS = {"w": W_NS}
STYLE_ID = "http://www.zotero.org/styles/ageing-research-reviews"
STYLE_NAME = "Ageing Research Reviews"


def insert_zotero_fields(
    source_docx: str | Path,
    group_rows: list[Mapping[str, str]],
    metadata_rows: list[Mapping[str, str]],
    out_docx: str | Path,
    *,
    bibliography_title: str = "Reference",
    on_missing: str = "fail",
) -> dict[str, object]:
    metadata_by_pmid = {str(row.get("pmid", "")): row for row in metadata_rows}
    replacements = []
    ordered_pmids: list[str] = []
    seen_pmids: set[str] = set()
    skipped_groups: list[dict[str, object]] = []

    for index, group in enumerate(group_rows, start=1):
        pmids = parse_pmids_cell(str(group.get("pmids", "")))
        missing = sorted(set(pmids) - set(metadata_by_pmid))
        if missing:
            if on_missing == "skip":
                skipped_groups.append(
                    {
                        "index": index,
                        "placeholder": str(group.get("raw_text", "")),
                        "pmids": " ".join(pmids),
                        "missing_pmids": " ".join(missing),
                    }
                )
                continue
            raise ValueError(f"Missing metadata for PMIDs: {' '.join(missing)}")
        items = [metadata_by_pmid[pmid] for pmid in pmids]
        citation_text = render_citation(items)
        payload = citation_payload(items, citation_text)
        instr = f" ADDIN ZOTERO_ITEM CSL_CITATION {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))} "
        replacements.append(
            {
                "index": index,
                "placeholder": str(group.get("raw_text", "")),
                "pmids": pmids,
                "citation_text": citation_text,
                "instr": instr,
            }
        )
        for pmid in pmids:
            if pmid not in seen_pmids:
                seen_pmids.add(pmid)
                ordered_pmids.append(pmid)

    bibliography_text = render_bibliography([metadata_by_pmid[pmid] for pmid in ordered_pmids])

    with zipfile.ZipFile(source_docx, "r") as zin:
        parts = {info.filename: zin.read(info.filename) for info in zin.infolist()}
        infos = zin.infolist()

    parser = etree.XMLParser(remove_blank_text=False, recover=False)
    root = etree.fromstring(parts["word/document.xml"], parser)

    replaced: list[int] = []
    missing_placeholders: list[dict[str, object]] = []
    for repl in replacements:
        ok = replace_placeholder(root, repl["placeholder"], repl["instr"], repl["citation_text"])
        if ok:
            replaced.append(int(repl["index"]))
        else:
            missing_placeholders.append(repl)
    if missing_placeholders:
        missing_ids = [str(item["index"]) for item in missing_placeholders]
        raise RuntimeError(f"Failed to replace placeholders: {', '.join(missing_ids)}")

    add_reference_and_bibliography(root, bibliography_text, title=bibliography_title)
    parts["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    ensure_custom_props(parts)

    out_path = Path(out_docx)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        written = set()
        for info in infos:
            zout.writestr(info, parts[info.filename])
            written.add(info.filename)
        for name, data in parts.items():
            if name not in written:
                zout.writestr(name, data)

    with zipfile.ZipFile(out_path, "r") as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f"Bad zip part: {bad}")
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")

    return {
        "source_docx": str(source_docx),
        "out_docx": str(out_path),
        "style_name": STYLE_NAME,
        "style_id": STYLE_ID,
        "citation_field_count": xml.count("ZOTERO_ITEM"),
        "bibliography_field_count": xml.count("ZOTERO_BIBL"),
        "citation_group_count": len(group_rows),
        "inserted_group_count": len(replacements),
        "skipped_group_count": len(skipped_groups),
        "skipped_groups": skipped_groups,
        "unique_pmid_count": len(ordered_pmids),
        "replaced_indices": replaced,
        "remaining_placeholder_count": sum(1 for repl in replacements if str(repl["placeholder"]) in xml),
    }


def render_citation(items: list[Mapping[str, str]]) -> str:
    return "(" + "; ".join(_citation_inner(item) for item in items) + ")"


def render_bibliography(items: list[Mapping[str, str]]) -> str:
    return "\n".join(_bibliography_entry(item) for item in items)


def citation_payload(items: list[Mapping[str, str]], text: str) -> dict[str, object]:
    return {
        "citationID": _rid(),
        "properties": {
            "noteIndex": 0,
            "formattedCitation": text,
            "plainCitation": text,
        },
        "citationItems": [{"id": _item_id(item), "uris": [_item_id(item)], "itemData": csl_item(item)} for item in items],
        "schema": "https://github.com/citation-style-language/schema/raw/master/csl-citation.json",
    }


def csl_item(item: Mapping[str, str]) -> dict[str, object]:
    year = str(item.get("year", "")).strip()
    data: dict[str, object] = {
        "id": _item_id(item),
        "type": "article-journal",
        "title": str(item.get("title", "")).strip(),
        "container-title": str(item.get("journal", "")).strip(),
        "URL": str(item.get("pubmed_url", "")).strip(),
        "PMID": str(item.get("pmid", "")).strip(),
    }
    if year:
        data["issued"] = {"date-parts": [[int(year)]] if year.isdigit() else [[year]]}
    doi = str(item.get("doi", "")).strip()
    if doi:
        data["DOI"] = doi
    authors = _csl_authors(str(item.get("authors", "")))
    if authors:
        data["author"] = authors
    return data


def replace_placeholder(root: etree._Element, placeholder: str, instr: str, result_text: str) -> bool:
    if not placeholder:
        return False
    for t in root.xpath(".//w:t", namespaces=NS):
        if t.text and placeholder in t.text:
            run = t.getparent()
            parent = run.getparent()
            idx = parent.index(run)
            rpr = run.find(_qn("w:rPr"))
            before, after = t.text.split(placeholder, 1)
            new_runs = []
            if before:
                new_runs.append(_make_run_text(before, rpr))
            new_runs.extend(_make_field_runs(instr, result_text, rpr))
            if after:
                new_runs.append(_make_run_text(after, rpr))
            parent.remove(run)
            for offset, new_run in enumerate(new_runs):
                parent.insert(idx + offset, new_run)
            return True
    return False


def add_reference_and_bibliography(root: etree._Element, bibliography_text: str, *, title: str) -> None:
    body = root.find(_qn("w:body"))
    sect = body.find(_qn("w:sectPr"))
    insert_at = len(body) - 1 if sect is not None else len(body)

    ref_p = etree.Element(_qn("w:p"))
    ppr = etree.SubElement(ref_p, _qn("w:pPr"))
    pstyle = etree.SubElement(ppr, _qn("w:pStyle"))
    pstyle.set(_qn("w:val"), "Heading1")
    r = etree.SubElement(ref_p, _qn("w:r"))
    t = etree.SubElement(r, _qn("w:t"))
    t.text = title

    bib_p = etree.Element(_qn("w:p"))
    bib_payload = json.dumps({"uncited": [], "omitted": [], "custom": []}, ensure_ascii=False, separators=(",", ":"))
    instr = f" ADDIN ZOTERO_BIBL {bib_payload} CSL_BIBLIOGRAPHY "
    for run in _make_field_runs(instr, bibliography_text):
        bib_p.append(run)

    body.insert(insert_at, ref_p)
    body.insert(insert_at + 1, bib_p)


def ensure_custom_props(parts: dict[str, bytes]) -> None:
    prefs = (
        '<data data-version="3" zotero-version="9.0.5">'
        f'<session id="{_rid(8)}"/>'
        f'<style id="{STYLE_ID}" hasBibliography="1" bibliographyStyleHasBeenSet="0"/>'
        '<prefs><pref name="fieldType" value="Field"/></prefs>'
        "</data>"
    )
    custom_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Properties xmlns="{CUSTOM_NS}" xmlns:vt="{VT_NS}">'
        '<property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="ZOTERO_PREF_1">'
        f"<vt:lpwstr>{escape(prefs)}</vt:lpwstr>"
        "</property></Properties>"
    )
    parts["docProps/custom.xml"] = custom_xml.encode("utf-8")

    ct_name = "[Content_Types].xml"
    ct_root = etree.fromstring(parts[ct_name])
    custom_part = "/docProps/custom.xml"
    exists = any(el.get("PartName") == custom_part for el in ct_root)
    if not exists:
        override = etree.Element(f"{{{CT_NS}}}Override")
        override.set("PartName", custom_part)
        override.set("ContentType", "application/vnd.openxmlformats-officedocument.custom-properties+xml")
        ct_root.append(override)
    parts[ct_name] = etree.tostring(ct_root, xml_declaration=True, encoding="UTF-8", standalone=True)

    rel_name = "_rels/.rels"
    rel_root = etree.fromstring(parts[rel_name])
    rel_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
    exists = any(el.get("Type") == rel_type for el in rel_root)
    if not exists:
        used = {el.get("Id") for el in rel_root}
        i = 1
        while f"rIdZotero{i}" in used:
            i += 1
        rel = etree.Element(f"{{{PKG_REL_NS}}}Relationship")
        rel.set("Id", f"rIdZotero{i}")
        rel.set("Type", rel_type)
        rel.set("Target", "docProps/custom.xml")
        rel_root.append(rel)
    parts[rel_name] = etree.tostring(rel_root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _citation_inner(item: Mapping[str, str]) -> str:
    author = _first_author(str(item.get("authors", "")))
    year = str(item.get("year", "")).strip() or "n.d."
    if author:
        return f"{author} et al., {year}"
    journal = str(item.get("journal", "")).strip()
    return f"{journal}, {year}" if journal else year


def _bibliography_entry(item: Mapping[str, str]) -> str:
    authors = str(item.get("authors", "")).strip()
    year = str(item.get("year", "")).strip()
    title = str(item.get("title", "")).strip()
    journal = str(item.get("journal", "")).strip()
    doi = str(item.get("doi", "")).strip()
    pieces = []
    if authors:
        pieces.append(authors + ".")
    if year:
        pieces.append(f"({year}).")
    if title:
        pieces.append(title)
    if journal:
        pieces.append(journal + ".")
    if doi:
        pieces.append(f"https://doi.org/{doi}")
    return " ".join(pieces)


def _make_run_text(text: str, rpr: etree._Element | None = None) -> etree._Element:
    run = etree.Element(_qn("w:r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    t = etree.SubElement(run, _qn("w:t"))
    if text[:1].isspace() or text[-1:].isspace():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return run


def _make_field_runs(instr: str, result_text: str, rpr: etree._Element | None = None) -> list[etree._Element]:
    runs = []
    run = etree.Element(_qn("w:r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    fld = etree.SubElement(run, _qn("w:fldChar"))
    fld.set(_qn("w:fldCharType"), "begin")
    runs.append(run)

    run = etree.Element(_qn("w:r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    instr_el = etree.SubElement(run, _qn("w:instrText"))
    instr_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr_el.text = instr
    runs.append(run)

    run = etree.Element(_qn("w:r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    fld = etree.SubElement(run, _qn("w:fldChar"))
    fld.set(_qn("w:fldCharType"), "separate")
    runs.append(run)

    result_run = etree.Element(_qn("w:r"))
    if rpr is not None:
        result_run.append(deepcopy(rpr))
    for idx, part in enumerate(result_text.split("\n")):
        if idx:
            etree.SubElement(result_run, _qn("w:br"))
        t = etree.SubElement(result_run, _qn("w:t"))
        if part[:1].isspace() or part[-1:].isspace():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = part
    runs.append(result_run)

    run = etree.Element(_qn("w:r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    fld = etree.SubElement(run, _qn("w:fldChar"))
    fld.set(_qn("w:fldCharType"), "end")
    runs.append(run)
    return runs


def _csl_authors(value: str) -> list[dict[str, str]]:
    authors = []
    for author in [part.strip() for part in value.split(";") if part.strip()]:
        pieces = author.split(" ", 1)
        if len(pieces) == 1:
            authors.append({"family": pieces[0]})
        else:
            authors.append({"family": pieces[0], "given": pieces[1]})
    return authors


def _first_author(value: str) -> str:
    first = value.split(";", 1)[0].strip()
    return first.split(" ", 1)[0] if first else ""


def _item_id(item: Mapping[str, str]) -> str:
    pmid = str(item.get("pmid", "")).strip()
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else f"urn:biomed-ref:{_rid(10)}"


def _rid(n: int = 8) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def _qn(tag: str) -> str:
    _, local = tag.split(":")
    return f"{{{W_NS}}}{local}"
