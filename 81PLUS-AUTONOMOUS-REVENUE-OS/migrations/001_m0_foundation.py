"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 001
M0 FOUNDATION SCHEMA
Definisce le tabelle primarie operative per CRON81, QUEUE81, WORKER81, EVENT81,
AUDIT81, HEALTH81, FEATURE_FLAGS e SUPPRESSION GATE.
"""

import sqlite3
import os
import sys

# Aggiungi shared path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.database.db import get_connection, find_db_path

def run_migration(conn: sqlite3.Connection = None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()

    # 1. Scheduled Jobs (Queue & Scheduler unificato)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            priority INTEGER DEFAULT 10,
            status TEXT NOT NULL DEFAULT 'PENDING',
            due_at TEXT NOT NULL,
            locked_at TEXT,
            locked_by TEXT,
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 5,
            last_error TEXT,
            last_run_at TEXT,
            next_run_at TEXT,
            idempotency_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_due_status ON scheduled_jobs(status, due_at, priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_idemp ON scheduled_jobs(idempotency_key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_type ON scheduled_jobs(job_type);")

    # 2. Dead Letter Queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dead_letter_jobs (
            id TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            failed_at TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            fatal_error TEXT NOT NULL,
            idempotency_key TEXT
        );
    """)

    # 3. Events Bus (EVENT81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events81 (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            aggregate_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            processed_at TEXT
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events81_type ON events81(event_type, timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events81_aggregate ON events81(aggregate_type, aggregate_id);")

    # 4. Audit Logs (Audit Append-Only)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            details_json TEXT,
            ip_address TEXT
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_type, target_id);")

    # 5. System Health (HEALTH81 & CONTROL81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            component TEXT NOT NULL,
            status TEXT NOT NULL, -- RUN, DEGRADED, STOP
            health_score INTEGER NOT NULL, -- 0..100
            metrics_json TEXT,
            last_tick TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_comp ON system_health(component, timestamp);")

    # 6. Feature Flags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_flags (
            key TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            updated_at TEXT NOT NULL
        );
    """)

    # 7. Global Suppressions (DO_NOT_CONTACT & Opt-out Gate)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT UNIQUE NOT NULL, -- email, domain, vat, phone
            type TEXT NOT NULL, -- EMAIL, DOMAIN, VAT, PHONE
            reason TEXT NOT NULL, -- UNSUBSCRIBE, COMPLAINT, HARD_BOUNCE, MANUAL, DO_NOT_CONTACT
            created_at TEXT NOT NULL,
            source TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_suppr_ident ON suppressions(identifier);")

    # Seed Default Feature Flags
    default_flags = [
        ("AUTOPILOT_ENABLED", 0, "Consente l'esecuzione autonoma a basso rischio"),
        ("DISCOVERY_H24", 1, "Consente il ciclo continuo di acquisizione lead approvati"),
        ("MAILGATE_ACTIVE", 1, "Applica controlli ferrei prima di ogni invio email"),
        ("KILL_SWITCH_ACTIVE", 0, "Se 1 blocca tutti i worker e gli invii outbound"),
        ("ANFOS_NIGHTLY_VALIDATOR", 1, "Consente la validazione notturna automatica dei corsi ANFOS")
    ]
    for key, enabled, desc in default_flags:
        cursor.execute("""
            INSERT OR IGNORE INTO feature_flags (key, enabled, description, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (key, enabled, desc))

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 001 (M0 Foundation) eseguita con successo.")

if __name__ == "__main__":
    run_migration()
