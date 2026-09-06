"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 004
M3 DELIVERY & TRAINING ROUTING DATA MODEL
Tabelle per Product Graph, Edizioni d'Aula (CLASS81), Domanda Territoriale (DEMAND81/GEO81)
e Stati di Erogazione (FULFILLMENT81).
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

    # 1. Product Graph (PRODUCT81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_catalog (
            product_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL, -- COURSE, DOCUMENT, SERVICE
            delivery_mode TEXT NOT NULL, -- ONLINE, AULA, BLENDED, NONE
            duration_hours INTEGER DEFAULT 0,
            provider TEXT NOT NULL, -- PARTNER_2377_FAD, CENTRO_ANFOS_RO3, DIRECT_81PLUS
            price_gross REAL NOT NULL,
            unit_cost REAL NOT NULL,
            commission_rate REAL NOT NULL,
            active INTEGER DEFAULT 1,
            validity_years INTEGER DEFAULT 5,
            legal_basis TEXT,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_mode ON product_catalog(delivery_mode, type);")

    # 2. Class Editions & Classroom Logistics (CLASS81 & SCHEDULE81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_editions (
            edition_id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            province TEXT NOT NULL,
            starts_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 15,
            min_participants INTEGER NOT NULL DEFAULT 6,
            enrolled_count INTEGER NOT NULL DEFAULT 0,
            waitlist_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'IDEA', -- IDEA, DEMAND_DETECTED, PROPOSED, OPEN, CONFIRMED, FULL, DELIVERED, CLOSED
            instructor TEXT DEFAULT 'DOCENTE FORMATORE QUALIFICATO 81+',
            created_at TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES product_catalog(product_id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_geo ON class_editions(province, status);")

    # 3. Aggregated Demand Signals (DEMAND81 & GEO81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS territory_demand_signals (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            province TEXT NOT NULL,
            company_count INTEGER NOT NULL DEFAULT 0,
            potential_attendees INTEGER NOT NULL DEFAULT 0,
            potential_revenue REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'ACCUMULATING', -- ACCUMULATING, THRESHOLD_REACHED, PROPOSED_EDITION
            last_signal_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_demand_geo ON territory_demand_signals(province, course_id);")

    # 4. Fulfillment State Machine (FULFILLMENT81)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fulfillment_records (
            fulfillment_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            status TEXT NOT NULL, -- PENDING, ENROLLED, IN_PROGRESS, ATTENDED, COMPLETED, CERTIFIED, DELIVERED
            evidence_url TEXT,
            certificate_qr TEXT,
            started_at TEXT,
            completed_at TEXT,
            delivered_at TEXT,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fulf_status ON fulfillment_records(status);")

    # Popola catalogo base (ONLINE + AULA + DOCUMENTI)
    base_products = [
        ("CRS_FAD_GEN", "Formazione Generale Lavoratori (4 ore)", "COURSE", "ONLINE", 4, "PARTNER_2377_FAD", 50.0, 15.0, 0.40, 5, "D.Lgs. 81/08 art. 37"),
        ("CRS_FAD_SPEC_B", "Formazione Specifica Rischio Basso (4 ore)", "COURSE", "ONLINE", 4, "PARTNER_2377_FAD", 60.0, 18.0, 0.40, 5, "Accordo Stato-Regioni 2025"),
        ("CRS_AULA_CARRELLI", "Abilitazione Carrelli Elevatori Semoventi (12 ore)", "COURSE", "AULA", 12, "CENTRO_ANFOS_RO3", 180.0, 30.0, 0.50, 5, "Art. 73 c. 5 D.Lgs. 81/08"),
        ("CRS_AULA_PLE", "Abilitazione Piattaforme Elevabili PLE (10 ore)", "COURSE", "AULA", 10, "CENTRO_ANFOS_RO3", 160.0, 30.0, 0.50, 5, "Art. 73 c. 5 D.Lgs. 81/08"),
        ("CRS_AULA_ALTO", "Formazione Lavoratori Rischio Alto (16 ore)", "COURSE", "BLENDED", 16, "CENTRO_ANFOS_RO3", 220.0, 35.0, 0.45, 5, "Accordo Stato-Regioni 2025"),
        ("CRS_AULA_ANTINC_2", "Addetto Antincendio Livello 2 (8 ore)", "COURSE", "AULA", 8, "CENTRO_ANFOS_RO3", 150.0, 25.0, 0.50, 5, "D.M. 02/09/2021"),
        ("CRS_AULA_PRISOC_B", "Addetto Primo Soccorso Gruppo B-C (12 ore)", "COURSE", "AULA", 12, "CENTRO_ANFOS_RO3", 160.0, 25.0, 0.50, 3, "D.M. 388/2003"),
        ("DOC_DVR_STD", "Documento di Valutazione dei Rischi (DVR)", "DOCUMENT", "NONE", 0, "DIRECT_81PLUS", 350.0, 50.0, 0.60, 1, "Art. 28-29 D.Lgs. 81/08"),
        ("DOC_POS_EDIL", "Piano Operativo di Sicurezza Cantieri (POS)", "DOCUMENT", "NONE", 0, "DIRECT_81PLUS", 250.0, 40.0, 0.60, 1, "Art. 96 D.Lgs. 81/08"),
        ("DOC_HACCP_MAN", "Manuale Autocontrollo HACCP", "DOCUMENT", "NONE", 0, "DIRECT_81PLUS", 200.0, 30.0, 0.60, 2, "Regolamento CE 852/2004")
    ]

    for pid, title, ptype, mode, hrs, prov, pr, cst, comm, vy, leg in base_products:
        cursor.execute("""
            INSERT OR IGNORE INTO product_catalog
            (product_id, title, type, delivery_mode, duration_hours, provider, price_gross, unit_cost, commission_rate, active, validity_years, legal_basis, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, datetime('now'))
        """, (pid, title, ptype, mode, hrs, prov, pr, cst, comm, vy, leg))

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 004 (M3 Delivery & Routing) eseguita con successo.")

if __name__ == "__main__":
    run_migration()
