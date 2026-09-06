"""
81+ AUTONOMOUS REVENUE OS — MIGRATION 006
M5 COPY81 COMMUNICATION & CONVERSION OS DATA MODEL
Aggiunge copy_message_genes, copy_narrative_episodes, objection_taxonomy,
copy_experiments, winning_language e negative_language.
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

    # 1. Geni di Comunicazione (Evolutionary Copy Engine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS copy_message_genes (
            id TEXT PRIMARY KEY,
            gene_type TEXT NOT NULL, -- SUBJECT, HOOK, HUMOR, PAIN, DESIRE, PROOF, OBJECTION, BENEFIT, CTA
            content TEXT NOT NULL,
            sarcasm_score INTEGER DEFAULT 2, -- 0 (serio/tecnico) a 5 (sarcastico graffiante)
            status TEXT DEFAULT 'TEST', -- TEST, PROMOTED, RETIRED
            impressions_count INTEGER DEFAULT 0,
            clicks_count INTEGER DEFAULT 0,
            conversions_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cmg_type ON copy_message_genes(gene_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cmg_status ON copy_message_genes(status);")

    # 2. Episodi Narrativi Seriali (12 Episodi Base)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS copy_narrative_episodes (
            episode_num INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            cognitive_goal TEXT NOT NULL,
            dominant_angle TEXT NOT NULL,
            w_score_target TEXT NOT NULL,
            cta_text TEXT DEFAULT 'VAI SULLA PIATTAFORMA'
        );
    """)

    # 3. Tassonomia Obiezioni & Anti-No Graph
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objection_taxonomy (
            id TEXT PRIMARY KEY,
            objection_code TEXT UNIQUE NOT NULL, -- NON_HO_TEMPO, NON_SO_COSA_SERVE, etc.
            trigger_keywords_json TEXT NOT NULL,
            resolution_angle TEXT NOT NULL,
            max_attempts INTEGER DEFAULT 2,
            exit_condition TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)

    # 4. Esperimenti e Attribution Copy
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS copy_experiments (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            episode_num INTEGER NOT NULL,
            variant_code TEXT NOT NULL,
            genes_used_json TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            cta_url TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            opened_at TEXT,
            clicked_at TEXT,
            registered_at TEXT,
            ordered_at TEXT,
            outcome TEXT DEFAULT 'SENT', -- SENT, OPENED, CLICKED, REGISTERED, BOUGHT, SUPPRESSED, FAILED
            FOREIGN KEY (company_id) REFERENCES company_twins(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ce_comp ON copy_experiments(company_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ce_outcome ON copy_experiments(outcome);")

    # 5. Winning Language Memory (Proprietary Intelligence)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS winning_language (
            id TEXT PRIMARY KEY,
            ateco_macro TEXT NOT NULL, -- COSTRUZIONI, COMMERCIO, RISTORAZIONE, MANIFATTURA, etc.
            w_score_range TEXT NOT NULL, -- W00-W40, W40-W80, W80-W100
            gene_type TEXT NOT NULL,
            gene_content TEXT NOT NULL,
            conversion_rate REAL NOT NULL,
            confidence REAL NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)

    # 6. Negative Language Guardrails (Cose che NON funzionano o vietate)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS negative_language (
            id TEXT PRIMARY KEY,
            pattern_regex TEXT NOT NULL,
            violation_category TEXT NOT NULL, -- SARCASM_ON_TRAGEDY, FAKE_URGENCY, BUREAUCRATIC_JARGON
            reason TEXT NOT NULL,
            blocked_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)

    conn.commit()
    if close_conn:
        conn.close()
    print("[OK] Migrazione 006 (M5 COPY81 Communication OS) completata con successo.")

if __name__ == "__main__":
    run_migration()
