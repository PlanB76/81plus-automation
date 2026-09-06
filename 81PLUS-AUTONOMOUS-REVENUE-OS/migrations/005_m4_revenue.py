"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 005
M4 REVENUE, COMMISSIONS, RECONCILIATION & RENEWAL CADENCE
Aggiunge cash_ledger, payment_transactions, revenue_reconciliations e renewal_cadences.
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

    # 1. Cash Ledger (Doppia partita / Separazione Net Cash)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cash_ledger (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            entry_type TEXT NOT NULL, -- ORDER_PAYMENT, COMMISSION_EARNED, COMMISSION_RECEIVED, PLATFORM_EXPENSE, REFUND
            gross_amount REAL NOT NULL,
            net_amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            is_reconciled INTEGER DEFAULT 0,
            reconciled_at TEXT,
            reconciliation_ref TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES revenue_ledger(order_id),
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cl_order ON cash_ledger(order_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cl_type ON cash_ledger(entry_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cl_reconciled ON cash_ledger(is_reconciled);")

    # 2. Payment Transactions & Idempotency Store
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            idempotency_key TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            payment_provider TEXT NOT NULL, -- STRIPE, PAYPAL, BONIFICO, ANFOS_DIRECT
            amount REAL NOT NULL,
            status TEXT NOT NULL, -- AUTHORIZED, CAPTURED, SETTLED, FAILED, REFUNDED
            provider_transaction_id TEXT,
            raw_event_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES revenue_ledger(order_id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pt_order ON payment_transactions(order_id);")

    # 3. Reconciliations Audit Log (RECON81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revenue_reconciliations (
            id TEXT PRIMARY KEY,
            cycle_date TEXT NOT NULL,
            orders_checked INTEGER DEFAULT 0,
            commissions_checked INTEGER DEFAULT 0,
            mismatches_count INTEGER DEFAULT 0,
            quarantined_count INTEGER DEFAULT 0,
            status TEXT NOT NULL, -- BALANCED, DISCREPANCY_DETECTED, RESOLVED
            details_json TEXT,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rr_date ON revenue_reconciliations(cycle_date);")

    # 4. Renewal Cadences Tracking (RENEW81 Timeline)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS renewal_cadences (
            id TEXT PRIMARY KEY,
            deadline_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            window_step TEXT NOT NULL, -- T-90, T-60, T-30, T-7, DUE, GRACE, WINBACK
            target_date TEXT NOT NULL,
            alert_sent_at TEXT,
            channel TEXT DEFAULT 'EMAIL',
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, SENT, CONVERTED, SUPPRESSED
            created_at TEXT NOT NULL,
            FOREIGN KEY (deadline_id) REFERENCES compliance_deadlines(id),
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rc_deadline ON renewal_cadences(deadline_id, window_step);")

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 005 (M4 Revenue, Commissions & Renewals) completata con successo.")

if __name__ == "__main__":
    run_migration()
