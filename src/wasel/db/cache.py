"""SqliteExtractionCache (implements contracts.ExtractionCache). Survives reset and purge (no FK)."""
from __future__ import annotations

import json
import sqlite3

from wasel.contracts import CachedExtraction


class SqliteExtractionCache:
    """The extraction cache table. `get` matches on the input hash and `prompt_version`, so bumping the prompt
    version makes every old entry a miss.
    """

    def __init__(self, conn: sqlite3.Connection, prompt_version: str = "extract-v1"):
        self.conn, self.prompt_version = conn, prompt_version

    def get(self, input_hash: str) -> CachedExtraction | None:
        """The cached extraction for `input_hash` under this cache's prompt version, or None."""
        r = self.conn.execute("SELECT * FROM extraction_cache WHERE input_hash=? AND prompt_version=?",
                              (input_hash, self.prompt_version)).fetchone()
        if r is None:
            return None
        return CachedExtraction(r["input_hash"], r["provider"], r["model"], r["origin_path"],
                                json.loads(r["extraction_json"]))
