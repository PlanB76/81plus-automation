"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 003
M2 PLATFORM ACTIVATION & FUNNEL TRACKING SCHEMA
Tabelle per funnel tracking, attivazione utente, rilevamento frizioni (FRICTION81)
e versionamento della Guida Piattaforma (GUIDE81).
"""

import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.database.db import get_connection

def run_migration(conn: sqlite3.Connection = None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()

    # 1. Funnel Events (ONBOARD81 & ACTIVATION81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_funnel_events (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            session_id TEXT NOT NULL,
            step TEXT NOT NULL, -- EMAIL_CLICK, PLATFORM_VISIT, GUIDE_VIEW, REGISTRATION, ACTIVATION, PRODUCT_VIEW, CHECKOUT_START, COMPLETED
            url TEXT,
            referrer TEXT,
            device_type TEXT,
            metadata_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_step ON platform_funnel_events(step, created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_company ON platform_funnel_events(company_id);")

    # 2. Platform Friction Drops (FRICTION81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_friction_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_date TEXT NOT NULL,
            from_step TEXT NOT NULL,
            to_step TEXT NOT NULL,
            total_entered INTEGER NOT NULL,
            total_progressed INTEGER NOT NULL,
            drop_off_count INTEGER NOT NULL,
            drop_off_rate REAL NOT NULL, -- 0.0 .. 1.0
            anomaly_flag INTEGER DEFAULT 0, -- 1 se drop-off > soglia attesa
            diagnosis TEXT,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fric_steps ON platform_friction_metrics(from_step, to_step, period_date);")

    # 3. Platform Guide Versions (GUIDE81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_guide_versions (
            version_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            subtitle TEXT,
            content_html TEXT NOT NULL,
            content_markdown TEXT NOT NULL,
            sections_json TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );
    """)

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 003 (M2 Platform Activation) eseguita con successo.")

if __name__ == "__main__":
    run_migration()
