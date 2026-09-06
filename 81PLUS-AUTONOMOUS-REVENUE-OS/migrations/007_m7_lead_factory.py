"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 007
M7 LEAD FACTORY H24 & SOURCE REGISTRY
Aggiunge source_registry, source_acquisition_runs, source_policies e source_economics.
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

    # 1. Source Registry & Legal Policies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_registry (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_type TEXT NOT NULL, -- OPEN_DATA_GOV, PUBLIC_DATASET, REGISTRO_PUBLIC, DIRECTORY
            license_terms TEXT NOT NULL,
            policy_status TEXT NOT NULL DEFAULT 'QUARANTINE', -- APPROVED, QUARANTINE, FORBIDDEN
            rate_limit_per_min INTEGER DEFAULT 60,
            daily_quota INTEGER DEFAULT 5000,
            last_run_at TEXT,
            records_collected_total INTEGER DEFAULT 0,
            source_roi_score REAL DEFAULT 1.0,
            created_at TEXT NOT NULL
        );
    """)

    # 2. Source Acquisition Runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_acquisition_runs (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            records_fetched INTEGER DEFAULT 0,
            records_valid INTEGER DEFAULT 0,
            records_deduped INTEGER DEFAULT 0,
            records_quarantined INTEGER DEFAULT 0,
            status TEXT NOT NULL, -- STARTED, COMPLETED, QUARANTINED, FAILED
            error_message TEXT,
            duration_sec REAL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES source_registry(id)
        );
    """)

    # 3. Source Economics & ROI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_economics (
            source_id TEXT PRIMARY KEY,
            total_cost_eur REAL DEFAULT 0.0,
            total_leads_acquired INTEGER DEFAULT 0,
            total_buyers_generated INTEGER DEFAULT 0,
            total_revenue_generated REAL DEFAULT 0.0,
            cac_eur REAL DEFAULT 0.0,
            roi_ratio REAL DEFAULT 0.0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES source_registry(id)
        );
    """)

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 007 (M7 Lead Factory H24) completata con successo.")

if __name__ == "__main__":
    run_migration()
