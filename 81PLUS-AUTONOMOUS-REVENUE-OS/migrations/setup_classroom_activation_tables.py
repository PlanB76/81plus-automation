"""
81PLUS-AUTONOMOUS-REVENUE-OS
migrations/setup_classroom_activation_tables.py — Setup Tabelle AULA, DEMAND & ACTIVATION
"""
import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

def setup_classroom_activation_tables():
    conn = get_connection()
    cur = conn.cursor()
    
    print("📦 Creazione tabelle per Gestione Aule, Domanda Aggregata e Funnel di Attivazione...")
    
    # 1. Classroom Editions (SCHEDULE81 + SUPPLY81)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS classroom_editions (
        edition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        codice_corso TEXT NOT NULL,
        titolo_corso TEXT NOT NULL,
        citta TEXT NOT NULL,
        provincia TEXT NOT NULL,
        indirizzo_sede TEXT NOT NULL,
        data_inizio TEXT NOT NULL, -- YYYY-MM-DD
        orario TEXT NOT NULL, -- es. 09:00 - 18:00
        durata_ore INTEGER NOT NULL,
        posti_totali INTEGER NOT NULL DEFAULT 12,
        posti_occupati INTEGER NOT NULL DEFAULT 0,
        quorum_minimo INTEGER NOT NULL DEFAULT 5,
        prezzo_corsista REAL NOT NULL, -- es. 240.0 - 280.0
        costo_attestato_anfos REAL NOT NULL DEFAULT 30.0,
        provider_piattaforma TEXT DEFAULT 'ANFOS_CENTRI',
        stato TEXT DEFAULT 'IN_ATTESA_QUORUM', -- IN_ATTESA_QUORUM, CONFERMATO, COMPLETO, ARCHIVIATO, ANNULLATO
        note_logistica TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Class Demand Aggregations (DEMAND81 + CLASS81)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS class_demand_aggregations (
        aggregation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provincia TEXT NOT NULL,
        codice_corso TEXT NOT NULL,
        aziende_interessate_count INTEGER DEFAULT 0,
        corsisti_potenziali_count INTEGER DEFAULT 0,
        valore_stimato_totale REAL DEFAULT 0.0,
        stato_proposta TEXT DEFAULT 'ACCUMULO', -- ACCUMULO, QUORUM_RAGGIUNTO, CLASSE_GENERATA
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 3. Funnel Activation Events (ONBOARD81 + ACTIVATION81 + FRICTION81)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS funnel_activation_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        contact_id INTEGER,
        step TEXT NOT NULL, -- PLATFORM_CLICK, LANDING_VIEW, GUIDE_VIEW, REGISTER_SUCCESS, FIRST_CHECK_DONE, CART_CREATED, PURCHASE_SUCCESS
        durata_secondi INTEGER DEFAULT 0,
        friction_detected TEXT, -- SLOW_PAGE, VALIDATION_ERROR, ABANDONED_CART, NO_ACTION
        source_campaign TEXT,
        device_type TEXT DEFAULT 'DESKTOP',
        FOREIGN KEY (contact_id) REFERENCES compliance_digital_twin(contact_id)
    );
    """)
    
    # 4. Lost Revenue Reasons (LOST81)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lost_revenue_reasons (
        loss_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        contact_id INTEGER,
        codice_corso TEXT,
        motivo_chiave TEXT NOT NULL, -- PREZZO, DISTANZA_SEDE, DATA_INCOMPATIBILE, GIA_FATTO, MODALITA_ERRATA, NON_DECISORE, FRIZIONE_PIATTAFORMA, DUBBIO_LEGALE
        dettagli TEXT,
        canale_rilevamento TEXT, -- EMAIL_REPLY, CHAT_BOT, CART_EXIT, SURVEY
        recovery_status TEXT DEFAULT 'PENDING', -- PENDING, RECOVERED, UNRECOVERABLE
        FOREIGN KEY (contact_id) REFERENCES compliance_digital_twin(contact_id)
    );
    """)
    
    # 5. Post Course Lifecycle & Attestati (POSTCOURSE81)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS postcourse_lifecycle (
        lifecycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        codice_corso TEXT NOT NULL,
        nome_corsista TEXT NOT NULL,
        codice_fiscale_corsista TEXT,
        data_completamento TEXT NOT NULL,
        data_scadenza_aggiornamento TEXT NOT NULL,
        codice_attestato_univoco TEXT UNIQUE NOT NULL,
        ente_rilascio TEXT DEFAULT 'ORGANISMO_PARITETICO_NAZIONALE',
        rating_gradimento INTEGER DEFAULT 5,
        notifica_t90_inviata INTEGER DEFAULT 0,
        notifica_t60_inviata INTEGER DEFAULT 0,
        notifica_t30_inviata INTEGER DEFAULT 0,
        next_complementary_nba TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_id) REFERENCES compliance_digital_twin(contact_id)
    );
    """)
    
    # Seed Edizioni d'Aula iniziali
    seed_editions = [
        ("AULA_MULETTO_CARRELLI_12H", "Abilitazione Carrelli Elevatori Semoventi (12h)", "Bologna", "BO", "Via dell'Industria 14, Bologna", "2026-10-15", "09:00 - 18:00", 12, 12, 4, 5, 260.0, 30.0, "ANFOS_CENTRI", "IN_ATTESA_QUORUM", "Campo prove pratico certificato"),
        ("AULA_ANTINCENDIO_L2", "Addetto Antincendio Livello 2 (8h)", "Modena", "MO", "Via Emilia Est 88, Modena", "2026-10-22", "09:00 - 18:00", 8, 15, 8, 6, 220.0, 25.0, "ANFOS_CENTRI", "CONFERMATO", "Vasca prove di spegnimento a norma"),
        ("AULA_PRIMOSOCCORSO_GRUPPO_B", "Primo Soccorso Aziendale Gruppo B-C (12h)", "Ferrara", "FE", "Via Bologna 210, Ferrara", "2026-11-05", "09:00 - 16:00", 12, 12, 2, 5, 240.0, 28.0, "ANFOS_CENTRI", "IN_ATTESA_QUORUM", "Manichino didattico e defibrillatore DAE")
    ]
    
    for ed in seed_editions:
        cur.execute("""
            INSERT OR REPLACE INTO classroom_editions
            (codice_corso, titolo_corso, citta, provincia, indirizzo_sede, data_inizio, orario, durata_ore, posti_totali, posti_occupati, quorum_minimo, prezzo_corsista, costo_attestato_anfos, provider_piattaforma, stato, note_logistica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ed)
        
    conn.commit()
    conn.close()
    print("✅ Tabelle AULA, DEMAND, ACTIVATION e POSTCOURSE configurate e popolate con successo!")

if __name__ == '__main__':
    setup_classroom_activation_tables()
