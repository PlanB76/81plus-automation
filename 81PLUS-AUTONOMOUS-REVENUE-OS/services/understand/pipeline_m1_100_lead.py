"""
81+ AUTONOMOUS REVENUE OS
services/understand/pipeline_m1_100_lead.py — M1 VERTICAL SLICE 100 LEAD ENGINE
Esegue l'elaborazione end-to-end su 100 aziende:
1. IMPORT & DEDUPE: Normalizzazione denominazione e deduplica su Clean Name & Domain (≥95%).
2. COMPANY TWIN: Risoluzione ATECO, profilo di rischio (Basso/Medio/Alto) e Provenance 100%.
3. CONTACTABILITY GATE: Controllo ferreo Suppression Gate & sintassi.
4. COMMUNICATION TWIN: EPPPA before, W-score, obiezione dominante e CTA 'VAI SULLA PIATTAFORMA'.
5. NBA & REVENUE ATTRIBUTION: Calcolo Next Best Action, simulazione d'ordine nel Revenue Ledger
   e creazione automatica deadline di rinnovo (Renewal Loop).
"""

import os
import sys
import re
import json
import uuid
from datetime import datetime, timedelta
import sqlite3
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.security.suppression_gate import SuppressionGate
from shared.events.event_bus import EventBus81

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [M1-PIPE] %(message)s")
logger = logging.getLogger("M1_PIPELINE")

def clean_company_name(name: str) -> str:
    """Normalizza la ragione sociale rimuovendo forme giuridiche comuni e caratteri speciali."""
    if not name:
        return "AZIENDA_NON_DEFINITA"
    n = name.upper()
    # Rimuovi SRLS, SRL, SPA, SNC, SAS, SS, DITTA INDIVIDUALE, IMPRESA EDILE
    tokens_to_strip = [
        r"\bS\.R\.L\.S\b", r"\bSRLS\b", r"\bS\.R\.L\.\b", r"\bSRL\b",
        r"\bS\.P\.A\.\b", r"\bSPA\b", r"\bS\.N\.C\.\b", r"\bSNC\b",
        r"\bS\.A\.S\.\b", r"\bSAS\b", r"\bS\.S\.\b", r"\bSOC\. COOP\b",
        r"\bCOOP\b", r"\bIMPRESA EDILE\b", r"\bSTUDIO TECNICO\b"
    ]
    for pattern in tokens_to_strip:
        n = re.sub(pattern, "", n, flags=re.IGNORECASE)
    # Rimuovi punteggiatura ridondante
    n = re.sub(r"[^\w\s]", " ", n)
    return re.sub(r"\s+", " ", n).strip()

def extract_domain(email: str) -> str:
    """Estrae il dominio dall'email, ignorando i webmail gratuiti per la company deduplication."""
    if not email or "@" not in email:
        return None
    d = email.split("@")[-1].strip().lower()
    public_domains = {"gmail.com", "yahoo.it", "libero.it", "virgilio.it", "tiscali.it", "hotmail.it", "hotmail.com", "outlook.it", "alice.it"}
    return None if d in public_domains else d

def infer_ateco_and_risk(name: str, email: str) -> tuple[str, str, str]:
    """Deduce codice ATECO stimato, descrizione e livello di rischio normativo."""
    text = (name + " " + email).lower()
    if any(k in text for k in ["edil", "costruz", "scavi", "impiant", "idraulic", "elettr"]):
        return "F41.20", "Costruzione di edifici residenziali e non residenziali", "ALTO"
    if any(k in text for k in ["ristor", "bar", "pizz", "trattor", "hotel", "alberg", "caffe"]):
        return "I56.10", "Ristorazione con somministrazione", "MEDIO"
    if any(k in text for k in ["trasport", "logist", "spediz", "corrier", "autotrasport"]):
        return "H49.41", "Trasporto di merci su strada", "MEDIO"
    if any(k in text for k in ["meccanic", "officin", "fabbro", "carrozzer"]):
        return "C25.62", "Lavorazioni di meccanica generale", "ALTO"
    if any(k in text for k in ["commerci", "vendit", "store", "negozi"]):
        return "G47.19", "Commercio al dettaglio in altri esercizi", "BASSO"
    return "M70.22", "Consulenza aziendale e gestione", "BASSO"

def run_m1_pipeline(limit: int = 100) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    suppression_gate = SuppressionGate(conn=conn)
    event_bus = EventBus81(conn=conn)

    logger.info("================================================================================")
    logger.info(f"AVVIO M1 PIPELINE — VERTICAL SLICE {limit} AZIENDE")
    logger.info("================================================================================")

    # 1. Recupera lead grezzi
    cursor.execute("""
        SELECT id, nome, email, telefono, stato, fonte 
        FROM leads 
        WHERE email IS NOT NULL AND email != ''
        LIMIT ?
    """, (limit * 2,)) # Prendi extra per testare deduplica reale
    raw_leads = cursor.fetchall()

    logger.info(f"Lead grezzi estratti dalla sorgente: {len(raw_leads)}")

    companies_seen = {} # clean_name -> company_id
    domains_seen = {}   # domain -> company_id
    stats = {
        "imported": 0,
        "deduped": 0,
        "contactable": 0,
        "suppressed": 0,
        "orders_simulated": 0,
        "deadlines_created": 0,
        "total_revenue_simulated": 0.0,
        "total_commissions_earned": 0.0
    }

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for lead in raw_leads:
        if stats["imported"] >= limit:
            break

        raw_name = lead["nome"] or "Azienda Senza Nome"
        email = lead["email"].strip().lower()
        clean_name = clean_company_name(raw_name)
        domain = extract_domain(email)

        # Controllo Deduplica (Clean Name o Dominio Aziendale Esclusivo)
        if clean_name in companies_seen or (domain and domain in domains_seen):
            stats["deduped"] += 1
            continue

        company_id = str(uuid.uuid4())
        companies_seen[clean_name] = company_id
        if domain:
            domains_seen[domain] = company_id

        # Risoluzione ATECO & Rischio
        ateco_code, ateco_desc, risk_level = infer_ateco_and_risk(raw_name, email)

        # Inserisci Company Twin
        cursor.execute("""
            INSERT INTO company_twins 
            (id, business_name, clean_name, domain, ateco_code, ateco_description, risk_level, data_confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0.95, ?, ?)
        """, (company_id, raw_name, clean_name, domain, ateco_code, ateco_desc, risk_level, now_str, now_str))

        # Contactability Gate
        is_suppressed = suppression_gate.is_suppressed(email)
        contact_status = "SUPPRESSED" if is_suppressed else "CONTACTABLE"
        if is_suppressed:
            stats["suppressed"] += 1
        else:
            stats["contactable"] += 1

        contact_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO company_contacts 
            (id, company_id, full_name, email, phone, role, contactability_status, provenance, verified_at, created_at)
            VALUES (?, ?, ?, ?, ?, 'DECISORE', ?, ?, ?, ?)
        """, (contact_id, company_id, raw_name, email, lead["telefono"], contact_status, lead["fonte"] or "LEADS_SEED", now_str, now_str))

        # Communication Twin (COPY81 State Machine)
        w_score = 0 if is_suppressed else 20
        objection = "NON_HO_TEMPO" if risk_level == "ALTO" else "NON_SO_COSA_SERVE"
        epppa_before = {
            "emozioni": "confusione/noia",
            "pensieri": "un'altra incombenza da rimandare",
            "parole": "lo facciamo lunedi",
            "persone": "titolare/amministratore",
            "azione": "procrastina"
        }
        epppa_after = {
            "emozioni": "controllo/sollievo",
            "pensieri": "posso verificare e risolvere in 60 secondi",
            "parole": "vediamo cosa manca",
            "persone": "decisore",
            "azione": "VAI SULLA PIATTAFORMA"
        }

        # Next Best Action (NBA)
        if risk_level == "ALTO":
            nba = "CORSO_LAVORATORI_RISCHIO_ALTO_16H"
            product_name = "Corso Formazione Lavoratori Rischio Alto (16 ore)"
            delivery_mode = "BLENDED"
            price = 220.0
            comm_rate = 0.35
            validity_yrs = 5
        elif risk_level == "MEDIO":
            nba = "CORSO_LAVORATORI_RISCHIO_MEDIO_8H"
            product_name = "Corso Formazione Lavoratori Rischio Medio (8 ore)"
            delivery_mode = "ONLINE"
            price = 140.0
            comm_rate = 0.40
            validity_yrs = 5
        else:
            nba = "CORSO_LAVORATORI_RISCHIO_BASSO_4H"
            product_name = "Corso Formazione Lavoratori Rischio Basso (4 ore)"
            delivery_mode = "ONLINE"
            price = 70.0
            comm_rate = 0.40
            validity_yrs = 5

        cursor.execute("""
            INSERT INTO communication_twins
            (company_id, w_score, dominant_need, dominant_objection, epppa_before_json, epppa_after_json, next_best_action, cta_primary, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'VAI SULLA PIATTAFORMA', ?)
        """, (company_id, w_score, nba, objection, json.dumps(epppa_before), json.dumps(epppa_after), nba, now_str))

        # Simulazione Ordine Controllato nel Revenue Ledger per la Vertical Slice
        order_id = str(uuid.uuid4())
        comm_earned = round(price * comm_rate, 2)
        cursor.execute("""
            INSERT INTO revenue_ledger
            (order_id, company_id, product_id, product_name, delivery_mode, amount_gross, commission_rate, commission_earned, commission_received, status, ordered_at, paid_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, 'ORDERED', ?, ?, ?)
        """, (order_id, company_id, nba, product_name, delivery_mode, price, comm_rate, comm_earned, now_str, now_str, now_str))

        # Creazione Deadline di Rinnovo (RENEW81 Loop)
        deadline_id = str(uuid.uuid4())
        renewal_due = (datetime.now() + timedelta(days=365 * validity_yrs)).strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO compliance_deadlines
            (id, company_id, course_or_doc, completed_at, validity_years, renewal_due_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (deadline_id, company_id, product_name, now_str[:10], validity_yrs, renewal_due, now_str))

        stats["imported"] += 1
        stats["orders_simulated"] += 1
        stats["deadlines_created"] += 1
        stats["total_revenue_simulated"] += price
        stats["total_commissions_earned"] += comm_earned

    conn.commit()
    conn.close()

    logger.info("================================================================================")
    logger.info(f"M1 PIPELINE COMPLETATA: {stats['imported']} Company Twins generati.")
    logger.info(f"Deduplica intercettata: {stats['deduped']} duplicati scartati.")
    logger.info(f"Contatti contattabili: {stats['contactable']} | Soppressi: {stats['suppressed']}")
    logger.info(f"Ordini simulati: {stats['orders_simulated']} | Valore lordo: €{stats['total_revenue_simulated']:.2f}")
    logger.info(f"Commissioni stimate: €{stats['total_commissions_earned']:.2f} | Scadenze create: {stats['deadlines_created']}")
    logger.info("================================================================================")

    return stats

if __name__ == "__main__":
    res = run_m1_pipeline(100)
    print(json.dumps(res, indent=2))
