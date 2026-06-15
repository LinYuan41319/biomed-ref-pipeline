from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Iterable


def check_pmids_in_zotero_sqlite(pmids: Iterable[str], sqlite_path: str | Path) -> list[dict[str, str]]:
    path = Path(sqlite_path)
    if not path.exists():
        raise FileNotFoundError(path)

    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return [_check_one(conn, str(pmid).strip()) for pmid in pmids if str(pmid).strip()]
    finally:
        conn.close()


def _check_one(conn: sqlite3.Connection, pmid: str) -> dict[str, str]:
    pattern = re.compile(rf"(?<!\d){re.escape(pmid)}(?!\d)")
    values = []
    for (value,) in conn.execute("SELECT value FROM itemDataValues WHERE value LIKE ? LIMIT 20", (f"%{pmid}%",)):
        if value and pattern.search(str(value)):
            values.append(str(value))
    return {
        "pmid": pmid,
        "in_zotero": "yes" if values else "no",
        "matched_values": " | ".join(values[:3]),
    }
