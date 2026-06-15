from __future__ import annotations

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Iterable


EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_pubmed_metadata(
    pmids: Iterable[str],
    *,
    email: str | None = None,
    api_key: str | None = None,
    tool: str = "biomed-ref-pipeline",
    batch_size: int = 100,
    retries: int = 3,
    timeout: int = 30,
) -> list[dict[str, str]]:
    pmid_list = [str(pmid).strip() for pmid in pmids if str(pmid).strip()]
    rows: list[dict[str, str]] = []
    for index in range(0, len(pmid_list), batch_size):
        batch = pmid_list[index : index + batch_size]
        xml_text = _fetch_batch(batch, email=email, api_key=api_key, tool=tool, retries=retries, timeout=timeout)
        rows.extend(parse_pubmed_xml(xml_text))
        if index + batch_size < len(pmid_list):
            time.sleep(0.34 if not api_key else 0.11)
    return rows


def parse_pubmed_xml(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, str]] = []
    for article in root.findall(".//PubmedArticle"):
        rows.append(_parse_article(article))
    return rows


def _fetch_batch(
    pmids: list[str],
    *,
    email: str | None,
    api_key: str | None,
    tool: str,
    retries: int,
    timeout: int,
) -> str:
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": tool,
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    url = f"{EFETCH_URL}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - depends on network state
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"PubMed fetch failed after {retries} attempts for {len(pmids)} PMIDs: {last_error}")


def _parse_article(article: ET.Element) -> dict[str, str]:
    medline = article.find("MedlineCitation")
    article_node = medline.find("Article") if medline is not None else None
    journal = article_node.find("Journal") if article_node is not None else None

    pmid = _text(medline.find("PMID") if medline is not None else None)
    title = _all_text(article_node.find("ArticleTitle") if article_node is not None else None)
    abstract = " ".join(
        _all_text(node) for node in (article_node.findall(".//AbstractText") if article_node is not None else [])
    ).strip()
    authors = "; ".join(_author_name(node) for node in (article_node.findall(".//Author") if article_node is not None else []))
    journal_title = _all_text(journal.find("Title") if journal is not None else None)
    iso_abbrev = _all_text(journal.find("ISOAbbreviation") if journal is not None else None)
    year = _year(article_node, journal)
    doi = _article_id(article, "doi")
    pub_types = "; ".join(_all_text(node) for node in article.findall(".//PublicationType"))
    mesh_terms = "; ".join(_all_text(node.find("DescriptorName")) for node in article.findall(".//MeshHeading"))

    return {
        "pmid": pmid,
        "title": title,
        "authors": authors,
        "journal": journal_title,
        "iso_abbreviation": iso_abbrev,
        "year": year,
        "doi": doi,
        "publication_types": pub_types,
        "mesh_terms": mesh_terms,
        "abstract": abstract,
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def _year(article_node: ET.Element | None, journal: ET.Element | None) -> str:
    candidates = [
        article_node.find(".//ArticleDate/Year") if article_node is not None else None,
        journal.find(".//PubDate/Year") if journal is not None else None,
        journal.find(".//PubDate/MedlineDate") if journal is not None else None,
    ]
    for candidate in candidates:
        value = _text(candidate)
        if value:
            return value[:4]
    return ""


def _article_id(article: ET.Element, id_type: str) -> str:
    for node in article.findall(".//ArticleId"):
        if node.attrib.get("IdType", "").lower() == id_type.lower():
            return _text(node)
    return ""


def _author_name(node: ET.Element) -> str:
    collective = _text(node.find("CollectiveName"))
    if collective:
        return collective
    last = _text(node.find("LastName"))
    initials = _text(node.find("Initials"))
    fore = _text(node.find("ForeName"))
    given = initials or fore
    return " ".join(part for part in [last, given] if part)


def _text(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text.strip()


def _all_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join(part.strip() for part in node.itertext() if part and part.strip())
