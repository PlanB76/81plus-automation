"""
81PLUS-AUTONOMOUS-REVENUE-OS
shared/database/db.py — Gestore di Connessione al Database Centrale 81plus.db
"""

import sqlite3
import os
import sys

def find_db_path():
    """Localizza il file 81plus.db risalendo l'albero delle directory."""
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "emailflux81", "81plus.db")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "GITHUB_81PLUS_AUTOMATION", "emailflux81", "81plus.db")),
        r"c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\emailflux81\81plus.db",
        r"c:\81PLUS_GLOBAL_MASTER\81plus.net\81plus.db"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def get_connection():
    db_path = find_db_path()
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

if __name__ == "__main__":
    p = find_db_path()
    print(f"[OK] Database path: {p} (Esiste: {os.path.exists(p)})")
