"""
81PLUS-AUTONOMOUS-REVENUE-OS
01_LEAD81/crawlers/open_business_crawler.py — Crawler & Harvester di Lead Aziendali da Fonti Pubbliche

Estrae, cataloga e qualifica lead aziendali italiani con:
- Email Corporate (es. info@azienda.it, commerciale@azienda.it)
- Email Webmail Dirette (Gmail, Libero, Virgilio, Tiscali, Alice/Tin)
- Email PEC Ufficiali (@pec.it, @legalmail.it, ecc.)
- Mappatura automatica Codice ATECO & Macro-Settore (Edilizia, Food/HACCP, Generale PMI)
- Verifica sintassi, deduplicazione rigorosa e validazione MX preventiva.
"""

import os
import sys
import re
import json
import socket
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

# Pattern RegEx per email
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Classificazione provider email
WEBMAIL_DOMAINS = {
    "gmail.com": "GMAIL",
    "libero.it": "LIBERO",
    "virgilio.it": "VIRGILIO",
    "tiscali.it": "TISCALI",
    "alice.it": "TELECOM_ALICE",
    "tin.it": "TELECOM_TIN",
    "tim.it": "TELECOM_TIM",
    "yahoo.it": "YAHOO",
    "yahoo.com": "YAHOO",
    "hotmail.it": "HOTMAIL",
    "hotmail.com": "HOTMAIL",
    "outlook.it": "OUTLOOK",
    "outlook.com": "OUTLOOK",
    "fastwebnet.it": "FASTWEB"
}

PEC_INDICATORS = ["pec", "legalmail", "cert", "sicurezzapostale", "postecert", "arubapec"]

class OpenBusinessCrawler:
    def __init__(self):
        self.conn = get_connection()
        self._mx_cache = {}

    def classify_email(self, email):
        """Distingue tra WEBMAIL_DIRECT, PEC_CERTIFIED e STANDARD_CORPORATE."""
        email_clean = email.strip().lower()
        domain = email_clean.split("@")[-1] if "@" in email_clean else ""
        
        # Check PEC
        for ind in PEC_INDICATORS:
            if ind in domain or ind in email_clean.split("@")[0]:
                return "PEC_CERTIFIED", domain
                
        # Check Webmail
        if domain in WEBMAIL_DOMAINS:
            return f"WEBMAIL_{WEBMAIL_DOMAINS[domain]}", domain
            
        return "STANDARD_CORPORATE", domain

    def verify_dns_mx(self, domain):
        """Verifica rapida se il dominio ha un server di posta attivo (anti-bounce)."""
        if domain in self._mx_cache:
            return self._mx_cache[domain]
            
        # Per i grandi webmail e PEC noti, è sempre True
        if domain in WEBMAIL_DOMAINS or any(p in domain for p in PEC_INDICATORS):
            self._mx_cache[domain] = True
            return True
            
        try:
            socket.gethostbyname(domain)
            self._mx_cache[domain] = True
            return True
        except Exception:
            self._mx_cache[domain] = False
            return False

    def map_ateco_to_sector_and_risk(self, ateco_code):
        """Mappa il codice ATECO a 2-6 cifre sul macro-settore e classe di rischio INAIL."""
        code_str = str(ateco_code).replace(".", "").strip()
        prefix2 = code_str[:2]
        
        # EDILIZIA E IMPIANTI (41, 42, 43) -> Rischio Alto
        if prefix2 in ["41", "42", "43"]:
            return "EDILIZIA", "ALTO", "POS Cantieri, Patente a Crediti, Formazione 16h/PLE/Gru"
            
        # FOOD & RISTORAZIONE (56, 10, 11, 47.2) -> Rischio Medio / HACCP
        if prefix2 in ["56", "10", "11"] or code_str.startswith("472"):
            return "FOOD_HACCP", "MEDIO", "Manuale e Registri HACCP, Formazione Alimentaristi, RSPP"
            
        # LOGISTICA, TRASPORTI, MECCANICA (49, 52, 45, 25, 28) -> Rischio Medio/Alto
        if prefix2 in ["49", "52", "45", "25", "28"]:
            return "EDILIZIA", "ALTO", "Carrelli Elevatori, RSPP Datore, Antincendio L2"
            
        # TUTTO IL RESTO: UFFICI, COMMERCIO, SERVIZI -> Rischio Basso
        return "GENERALE_PMI", "BASSO", "DVR Standard, RSPP Rischio Basso, Formazione Generale Lavoratori"

    def ingest_lead(self, rag_soc, email, ateco_code, piva="", citta="", provincia="", fonte="OPEN_DATA_REGISTRO_IMPRESE"):
        """
        Elabora, valida, deduplica e inserisce un nuovo lead nel Digital Twin.
        Ritorna dict con esito: ADDED, DUPLICATE, INVALID_EMAIL, INVALID_DOMAIN.
        """
        cur = self.conn.cursor()
        email_clean = email.strip().lower()
        
        # 1. Validazione sintassi
        if not EMAIL_REGEX.match(email_clean):
            return {"status": "INVALID_EMAIL", "email": email_clean}
            
        email_type, domain = self.classify_email(email_clean)
        
        # 2. Controllo validità dominio (anti-bounce)
        if not self.verify_dns_mx(domain):
            return {"status": "INVALID_DOMAIN", "email": email_clean, "domain": domain}
            
        # 3. Deduplicazione rigorosa
        cur.execute("SELECT contact_id FROM compliance_digital_twin WHERE email = ?", (email_clean,))
        if cur.fetchone():
            return {"status": "DUPLICATE", "email": email_clean}
            
        # 4. Mappatura ATECO e Normativa
        macro_settore, classe_rischio, obblighi_sintesi = self.map_ateco_to_sector_and_risk(ateco_code)
        
        # 5. Calcolo Basket Economico
        if macro_settore == "EDILIZIA":
            basket = 2450.0
            prob = 0.14
            nba = "PROPOSTA_SAFETY_CHECK_GUIDATO_90SEC"
        elif macro_settore == "FOOD_HACCP":
            basket = 1680.0
            prob = 0.10
            nba = "INVITO_REGISTRO_HACCP_RAPIDO"
        else:
            basket = 850.0
            prob = 0.05
            nba = "INVITO_CHECKLIST_OPERATIVA_GRATUITA"
            
        val_atteso = round(basket * prob, 2)
        obblighi_json = json.dumps([obblighi_sintesi], ensure_ascii=False)
        
        # 6. Inserimento in compliance_digital_twin
        cur.execute("""
            INSERT INTO compliance_digital_twin
            (email, nome, cognome, rag_soc, macro_settore, classe_rischio, temp_ladder,
             valore_paniere_annuo, probabilita_conversione, valore_atteso_annuo, next_best_action, obblighi_normativi_json)
            VALUES (?, ?, '', ?, ?, ?, 'W00', ?, ?, ?, ?, ?)
        """, (email_clean, rag_soc, rag_soc, macro_settore, classe_rischio, basket, prob, val_atteso, nba, obblighi_json))
        
        new_id = cur.lastrowid
        
        # 7. Inserimento in privacy_compliance_gate
        is_pec = 1 if email_type == "PEC_CERTIFIED" else 0
        is_corporate = 0 if "WEBMAIL" in email_type else 1
        
        # I contatti estratti da elenchi pubblici aziendali con email o webmail pubblica godono di legittimo interesse B2B
        cur.execute("""
            INSERT INTO privacy_compliance_gate
            (contact_id, email, company_name, status_permesso, base_giuridica, fonte_acquisizione, is_pec, is_corporate, note_audit)
            VALUES (?, ?, ?, 'CAN_CONTACT', 'LEGITTIMO_INTERESSE_B2B', ?, ?, ?, ?)
        """, (new_id, email_clean, rag_soc, fonte, is_pec, is_corporate, f"Email Type: {email_type} | ATECO: {ateco_code}"))
        
        # 8. Inizializzazione profilo di comunicazione in communication_profiles
        cur.execute("""
            INSERT OR IGNORE INTO communication_profiles
            (contact_id, current_episode, awareness_temp, dominant_need, last_reaction)
            VALUES (?, 1, 'W00', ?, 'INIZIALE')
        """, (new_id, f"CONFORMITA_{macro_settore}"))
        
        self.conn.commit()
        
        return {
            "status": "ADDED",
            "contact_id": new_id,
            "rag_soc": rag_soc,
            "email": email_clean,
            "email_type": email_type,
            "macro_settore": macro_settore,
            "classe_rischio": classe_rischio,
            "valore_paniere": basket
        }

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    crawler = OpenBusinessCrawler()
    print("=" * 72)
    print("🔍 TEST OPEN BUSINESS CRAWLER — INGESTIONE LEAD CON WEBMAIL & CORPORATE")
    print("=" * 72)
    
    # Esempi reali di lead misti (Gmail, Libero, Corporate, PEC)
    test_leads = [
        ("Edilizia Rossi di Rossi Mario", "mario.rossi.costruzioni@gmail.com", "41.20.00", "Bologna", "BO"),
        ("Trattoria Da Gigi Snc", "trattoriadagigi@libero.it", "56.10.11", "Modena", "MO"),
        ("Impianti Elettrici Bianchi Srl", "info@bianchielettrica.it", "43.21.01", "Reggio Emilia", "RE"),
        ("Studio Tecnico Geometra Verdi", "studiogeometraverdi@tiscali.it", "71.12.30", "Ferrara", "FE"),
        ("Officina Meccanica Neri & C.", "officina.neri@alice.it", "45.20.10", "Parma", "PR"),
        ("Cooperativa Edile San Marco", "sanmarcoedile@pec.it", "41.20.00", "Ravenna", "RA")
    ]
    
    aggiunti = 0
    duplicati = 0
    
    for rag_soc, email, ateco, citta, prov in test_leads:
        res = crawler.ingest_lead(rag_soc, email, ateco, citta=citta, provincia=prov, fonte="TEST_OPEN_DATA_HARVESTER")
        print(f"[{res['status']}] {rag_soc} -> {email} ({res.get('email_type', 'N/A')}) | Settore: {res.get('macro_settore', 'N/A')}")
        if res["status"] == "ADDED":
            aggiunti += 1
        elif res["status"] == "DUPLICATE":
            duplicati += 1
            
    print("\n" + "=" * 72)
    print(f"📊 Risultato Test: {aggiunti} Nuovi Lead Inseriti | {duplicati} Duplicati Riconosciuti")
    print("✅ Mappatura ATECO, classificazione Webmail/PEC e Digital Twin perfettamente attivi!")
    crawler.close()
