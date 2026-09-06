"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 008
M8 AUTOPILOT, ICP LEARNING & EXECUTIVE BRIEFINGS
Aggiunge autopilot_states, icp_profiles ed executive_briefings.
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

    # 1. Autopilot States & Kill Switches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS autopilot_states (
            id TEXT PRIMARY KEY,
            mode TEXT NOT NULL DEFAULT 'GUARDED', -- SHADOW, ASSISTED, GUARDED, AUTONOMOUS, EMERGENCY
            kill_switch_active INTEGER DEFAULT 0,
            active_incident_reason TEXT,
            allowed_autonomous_actions TEXT,
            updated_at TEXT NOT NULL
        );
    """)

    # 2. ICP Profiles & Behavioral Intelligence (ICP81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS icp_profiles (
            ateco_prefix TEXT PRIMARY KEY,
            sector_label TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            buyer_count INTEGER DEFAULT 0,
            total_revenue REAL DEFAULT 0.0,
            score_multiplier REAL DEFAULT 1.0,
            updated_at TEXT NOT NULL
        );
    """)

    # 3. Executive Daily Briefings (EXECUTIVE81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS executive_briefings (
            id TEXT PRIMARY KEY,
            date_str TEXT NOT NULL,
            health_score INTEGER NOT NULL,
            system_status TEXT NOT NULL, -- RUN, DEGRADED, STOP
            daily_revenue_actual REAL NOT NULL,
            target_gap REAL NOT NULL,
            bottleneck_stage TEXT NOT NULL,
            briefing_markdown TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 008 (M8 Autopilot & Executive Briefings) completata con successo.")

if __name__ == "__main__":
    run_migration()
