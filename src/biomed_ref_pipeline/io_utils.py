from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def read_pmids(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    seen: set[str] = set()
    pmids: list[str] = []
    for token in text.replace(",", " ").replace(";", " ").split():
        digits = "".join(ch for ch in token if ch.isdigit())
        if len(digits) >= 6 and digits not in seen:
            seen.add(digits)
            pmids.append(digits)
    return pmids


def write_lines(path: str | Path, lines: Iterable[str]) -> None:
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tsv(path: str | Path, rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str] | None = None) -> None:
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key, "")) for key in fieldnames})


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(item) for item in value)
    return str(value).replace("\r\n", " ").replace("\n", " ").strip()
