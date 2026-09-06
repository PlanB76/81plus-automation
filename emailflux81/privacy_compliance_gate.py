#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
privacy_compliance_gate.py — Legal & Privacy Gate per 81+ Autonomous Revenue OS
Ecosistema 81+ · SICURISSIMO81+ (Partner ID 2377)

Principio Tecnico: ZERO MANI != ZERO CONTROLLO

Funzionalità:
1. Valutazione di ogni record prima dell'invio: CAN_CONTACT, DO_NOT_CONTACT, REVIEW_NEEDED
2. Verifica conformità GDPR (Reg. UE 2016/679) & D.Lgs. 196/03 novellato
3. Gestione della Global Suppression List (Unsubscribe, Bounce duri, Reclami)
4. Audit Log della provenienza, base giuridica e data di consenso/acquisizione
5. Blocco preventivo di email personali, caselle spam trap note e domini problematici
"""

import os
import sys
import sqlite3
import datetime
import re

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "81plus.db")

# Domini personali o non conformi al contatto B2B diretto
DOMINI_NON_CONFORMI = {
    "gmail.com", "yahoo.com", "yahoo.it", "hotmail.com", "hotmail.it",
    "outlook.com", "outlook.it", "live.it", "live.com", "icloud.com",
    "me.com", "libero.it", "virgilio.it", "alice.it", "tin.it", "tiscali.it"
}

# Prefissi sospetti o spam trap
PREFIX_SPAM_TRAP = {
    "abuse", "postmaster", "spam", "trap", "noc", "hostmaster", "root", "security"
}

def init_privacy_tables(conn):
    """Crea le tabelle del Privacy Gate e della Suppression List."""
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS privacy_compliance_gate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER,
        email TEXT UNIQUE,
        company_name TEXT,
        status_permesso TEXT DEFAULT 'REVIEW_NEEDED', -- CAN_CONTACT, DO_NOT_CONTACT, REVIEW_NEEDED
        base_giuridica TEXT,                         -- LEGITTIMO_INTERESSE_B2B, CONSENSO_ESPLICITO, CONTRATTUALE_CLIENTE
        fonte_acquisizione TEXT,
        data_acquisizione TEXT DEFAULT CURRENT_TIMESTAMP,
        is_pec INTEGER DEFAULT 0,
        is_corporate INTEGER DEFAULT 1,
        note_audit TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS global_suppression_list (
        email TEXT PRIMARY KEY,
        motivo TEXT, -- UNSUBSCRIBE, HARD_BOUNCE, COMPLAINT, POLICY_EXCLUSION
        data_inserimento TEXT DEFAULT CURRENT_TIMESTAMP,
        ip_richiesta TEXT
    );
    """)
    conn.commit()

def valuta_contatto(email, azienda=""):
    """Determina se un indirizzo può essere contattato o richiede revisione."""
    em = (email or "").strip().lower()
    if not em or "@" not in em:
        return "DO_NOT_CONTACT", "Email mancante o formato non valido", "NESSUNA", 0, 0

    local_part, domain = em.split("@", 1)

    # 1. Verifica se in lista di soppressione
    # (controllo rapido a livello logico)
    if local_part in PREFIX_SPAM_TRAP:
        return "DO_NOT_CONTACT", "Indirizzo identificato come spam-trap o ruolo generico", "NESSUNA", 0, 0

    is_pec = 1 if "pec" in domain or "pec" in local_part else 0
    is_corporate = 0 if domain in DOMINI_NON_CONFORMI else 1

    # Indirizzi PEC istituzionali: non inviare marketing massivo
    if is_pec:
        return "DO_NOT_CONTACT", "Indirizzo PEC riservato ad atti legali formali", "ESCLUSO_PEC", 1, is_corporate

    # Indirizzi B2B aziendali (dominio proprietario): Legittimo interesse B2B con opt-out
    if is_corporate:
        return "CAN_CONTACT", "Contatto B2B con dominio aziendale identificabile", "LEGITTIMO_INTERESSE_B2B", 0, 1

    # Indirizzi gratuiti (Gmail, Libero, ecc.): richiedono verifica se appartengono a ditte individuali o clienti
    return "REVIEW_NEEDED", "Casella consumer/freemail: richiede verifica storico o consenso esplicito", "VERIFICA_CONSENSO", 0, 0

def audit_and_populate_gate():
    """Analizza tutti i contatti in 81plus.db e assegna il permesso di contatto."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_privacy_tables(conn)
    cur = conn.cursor()

    # Pre-carica soppressioni
    cur.execute("SELECT email FROM global_suppression_list")
    suppressed = set(r['email'].lower() for r in cur.fetchall())

    # Pre-carica clienti che hanno acquistato (hanno rapporto contrattuale -> CAN_CONTACT garantito)
    cur.execute("SELECT DISTINCT email FROM network_corsisti WHERE stato = 'COMPLETATO' AND email IS NOT NULL")
    clienti_contrattuali = set(r['email'].lower() for r in cur.fetchall())

    cur.execute("SELECT contact_id, email, azienda FROM ghl_user360")
    contacts = cur.fetchall()
    tot = len(contacts)

    can_count = 0
    do_not_count = 0
    review_count = 0

    print(f"[*] Audit Privacy Gate per {tot} contatti in corso...")

    for c in contacts:
        cid = c['contact_id']
        em = (c['email'] or "").strip().lower()
        az = c['azienda'] or ""

        if not em:
            continue

        if em in suppressed:
            status = "DO_NOT_CONTACT"
            motivo = "Presente nella Global Suppression List"
            base = "REVOCA_CONSENSO"
            is_pec = 0
            is_corp = 0
        elif em in clienti_contrattuali:
            status = "CAN_CONTACT"
            motivo = "Cliente attivo o con attestato FAD (rapporto contrattuale in essere)"
            base = "RAPPORTO_CONTRATTUALE"
            is_pec = 0
            is_corp = 1
        else:
            status, motivo, base, is_pec, is_corp = valuta_contatto(em, az)

        if status == "CAN_CONTACT":
            can_count += 1
        elif status == "DO_NOT_CONTACT":
            do_not_count += 1
        else:
            review_count += 1

        cur.execute("""
            INSERT INTO privacy_compliance_gate (
                contact_id, email, company_name, status_permesso, base_giuridica,
                fonte_acquisizione, is_pec, is_corporate, note_audit, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'DATABASE_81PLUS_UNIFICATO', ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
                status_permesso = excluded.status_permesso,
                base_giuridica = excluded.base_giuridica,
                note_audit = excluded.note_audit,
                updated_at = CURRENT_TIMESTAMP
        """, (cid, em, az, status, base, is_pec, is_corp, motivo))

    conn.commit()
    conn.close()

    print(f"[+] Privacy Gate completato:")
    print(f"    - CAN_CONTACT: {can_count}")
    print(f"    - REVIEW_NEEDED: {review_count}")
    print(f"    - DO_NOT_CONTACT: {do_not_count}")
    return can_count, review_count, do_not_count

if __name__ == "__main__":
    audit_and_populate_gate()
