"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 002
M1 COMPANY TWIN, CONTACTABILITY & REVENUE DATA MODEL
Aggiunge le tabelle per Company Twin, Digital Twin, ATECO mapping,
Communication Twin, NBA, Orders, Commissions e Renewals.
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

    # 1. Company Twins (Golden Record)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_twins (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            clean_name TEXT NOT NULL,
            domain TEXT,
            vat_code TEXT,
            ateco_code TEXT,
            ateco_description TEXT,
            risk_level TEXT DEFAULT 'MEDIO', -- BASSO, MEDIO, ALTO
            employee_count INTEGER DEFAULT 1,
            city TEXT,
            province TEXT,
            region TEXT,
            data_confidence REAL DEFAULT 0.8,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ct_clean_name ON company_twins(clean_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ct_domain ON company_twins(domain);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ct_ateco ON company_twins(ateco_code);")

    # 2. Contacts & Contactability Gate
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_contacts (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            full_name TEXT,
            email TEXT NOT NULL,
            phone TEXT,
            role TEXT DEFAULT 'DECISORE', -- TITOLARE, RSPP, HR, HSE, AMMINISTRAZIONE
            contactability_status TEXT NOT NULL DEFAULT 'PENDING', -- CONTACTABLE, SUPPRESSED, QUARANTINE, DO_NOT_CONTACT
            provenance TEXT NOT NULL,
            verified_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cc_email ON company_contacts(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cc_status ON company_contacts(contactability_status);")

    # 3. Communication Twins (COPY81 State Machine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communication_twins (
            company_id TEXT PRIMARY KEY,
            w_score INTEGER DEFAULT 0, -- W00, W20, W40, W60, W80, W100
            dominant_need TEXT,
            dominant_objection TEXT,
            epppa_before_json TEXT,
            epppa_after_json TEXT,
            winning_angle TEXT,
            messages_sent_count INTEGER DEFAULT 0,
            last_message_at TEXT,
            last_action TEXT,
            next_best_action TEXT,
            cta_primary TEXT DEFAULT 'VAI SULLA PIATTAFORMA',
            updated_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)

    # 4. Simulated/Real Orders & Revenue Ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revenue_ledger (
            order_id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            delivery_mode TEXT NOT NULL, -- ONLINE, AULA, DOCUMENT, SERVICE
            amount_gross REAL NOT NULL,
            commission_rate REAL NOT NULL,
            commission_earned REAL NOT NULL,
            commission_received REAL DEFAULT 0.0,
            status TEXT NOT NULL, -- ORDERED, PAID, PROVISIONED, COMPLETED, REFUNDED
            ordered_at TEXT NOT NULL,
            paid_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_company ON revenue_ledger(company_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_status ON revenue_ledger(status);")

    # 5. Deadlines & Lifecycle Renewals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_deadlines (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            course_or_doc TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            validity_years INTEGER NOT NULL,
            renewal_due_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, UPCOMING, EXPIRED, RENEWED
            last_alert_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deadlines_due ON compliance_deadlines(renewal_due_at, status);")

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 002 (M1 Company Twin & Revenue) eseguita con successo.")

if __name__ == "__main__":
    run_migration()
