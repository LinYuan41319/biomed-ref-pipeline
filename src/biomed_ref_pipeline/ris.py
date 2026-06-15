from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping


def write_ris(rows: Iterable[Mapping[str, object]], path: str | Path) -> None:
    records = [record_to_ris(row) for row in rows if str(row.get("pmid", "")).strip()]
    Path(path).write_text("\n".join(records), encoding="utf-8")


def split_ris_file(path: str | Path, out_dir: str | Path, *, batch_size: int = 100, prefix: str = "zotero_import_batch") -> list[Path]:
    records = read_ris_records(path)
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for index in range(0, len(records), batch_size):
        batch = records[index : index + batch_size]
        out_path = target / f"{prefix}_{len(outputs) + 1:03d}.ris"
        out_path.write_text("\n".join(batch) + "\n", encoding="utf-8")
        outputs.append(out_path)
    return outputs


def read_ris_records(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    records: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if not line.strip() and not current:
            continue
        current.append(line)
        if line.strip() == "ER  -":
            records.append("\n".join(current).strip() + "\n")
            current = []
    if current:
        records.append("\n".join(current).strip() + "\n")
    return records


def record_to_ris(row: Mapping[str, object]) -> str:
    pmid = _value(row, "pmid")
    lines = ["TY  - JOUR"]
    _add(lines, "TI", _value(row, "title"))
    _add(lines, "JO", _value(row, "journal"))
    _add(lines, "PY", _value(row, "year"))
    _add(lines, "DO", _value(row, "doi"))
    _add(lines, "UR", _value(row, "pubmed_url") or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
    _add(lines, "AB", _value(row, "abstract"))
    _add(lines, "N1", f"PMID: {pmid}")
    _add(lines, "ID", pmid)
    lines.append("ER  -")
    return "\n".join(lines) + "\n"


def _add(lines: list[str], tag: str, value: str) -> None:
    value = " ".join(value.replace("\r", " ").replace("\n", " ").split())
    if value:
        lines.append(f"{tag}  - {value}")


def _value(row: Mapping[str, object], key: str) -> str:
    value = row.get(key, "")
    return "" if value is None else str(value).strip()
