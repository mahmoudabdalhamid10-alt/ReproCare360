"""Anonymous local journal storage.

Everything lives in a single SQLite file on the user's machine (default
``data/repro360.db``, override with the ``REPRO360_DB`` environment
variable). No accounts, no network calls, nothing leaves the device.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def default_db_path() -> Path:
    env = os.environ.get("REPRO360_DB")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data" / "repro360.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    category TEXT NOT NULL,
    note TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lab_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    parameter TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    habit_key TEXT NOT NULL,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS triage_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    level TEXT NOT NULL,
    flags TEXT NOT NULL DEFAULT '[]'
);
"""


class Store:
    """Tiny SQLite helper. One method per kind of record."""

    def __init__(self, path: Optional[os.PathLike | str] = None):
        self.path = str(path) if path else str(default_db_path())
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- journal ---------------------------------------------------------
    def add_entry(self, category: str, note: str) -> Dict[str, Any]:
        ts = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO journal_entries (created_at, category, note) VALUES (?,?,?)",
                (ts, category, note),
            )
            return {"id": cur.lastrowid, "created_at": ts, "category": category, "note": note}

    def entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM journal_entries ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # -- lab results -----------------------------------------------------
    def add_lab(self, parameter: str, value: float, unit: str = "") -> Dict[str, Any]:
        ts = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO lab_results (created_at, parameter, value, unit) VALUES (?,?,?,?)",
                (ts, parameter, float(value), unit),
            )
            return {"id": cur.lastrowid, "created_at": ts, "parameter": parameter,
                    "value": float(value), "unit": unit}

    def labs(self, parameter: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if parameter:
                rows = conn.execute(
                    "SELECT * FROM lab_results WHERE parameter=? ORDER BY created_at LIMIT ?",
                    (parameter, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM lab_results ORDER BY created_at LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]

    # -- habits ----------------------------------------------------------
    def add_habit(self, habit_key: str, value: str) -> Dict[str, Any]:
        ts = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO habit_logs (created_at, habit_key, value) VALUES (?,?,?)",
                (ts, habit_key, value),
            )
            return {"id": cur.lastrowid, "created_at": ts, "habit_key": habit_key, "value": value}

    def habits(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM habit_logs ORDER BY created_at LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # -- triage history --------------------------------------------------
    def add_triage(self, level: str, flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        ts = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO triage_checks (created_at, level, flags) VALUES (?,?,?)",
                (ts, level, json.dumps(flags)),
            )
            return {"id": cur.lastrowid, "created_at": ts, "level": level, "flags": flags}

    def triage_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM triage_checks ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["flags"] = json.loads(d["flags"])
            out.append(d)
        return out
