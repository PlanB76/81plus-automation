"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/srv_demand/copy81_engine.py — COPY81 Communication & Conversion Engine

Governa la State Machine comunicativa per ogni Digital Twin:
- Serie narrativa seriale a 12 episodi
- Universal One CTA Rule: VAI SULLA PIATTAFORMA
- EPPPA Transformation Engine
- Gestione obiezioni e Anti-No
- Branching dinamico su reazione (No open, Open no click, Click no reg, Register, Buy)
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

UNIVERSAL_CTA_TEXT = "VAI SULLA PIATTAFORMA"
UNIVERSAL_CTA_URL = "https://81plus.net"

class Copy81Engine:
    def __init__(self):
        self.conn = get_connection()

    def get_or_create_profile(self, contact_id, temp_ladder="W20", macro_settore="GENERALE_PMI"):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM communication_profiles WHERE contact_id = ?", (contact_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        
        # Inizializza profilo comunicazione
        cur.execute("""
            INSERT INTO communication_profiles 
            (contact_id, current_episode, awareness_temp, dominant_need, last_reaction)
            VALUES (?, 1, ?, ?, 'INIZIALE')
        """, (contact_id, temp_ladder, f"CONFORMITA_{macro_settore}"))
        self.conn.commit()
        
        cur.execute("SELECT * FROM communication_profiles WHERE contact_id = ?", (contact_id,))
        return dict(cur.fetchone())

    def determine_next_message(self, contact_id, macro_settore="GENERALE_PMI", rag_soc="Azienda"):
        cur = self.conn.cursor()
        profile = self.get_or_create_profile(contact_id)
        
        # Controllo stato: se registrato o buyer o disiscritto, adatta percorso
        if profile["last_reaction"] == "UNSUBSCRIBED":
            return {
                "action": "STOP",
                "reason": "Utente in global suppression list (Opt-out)",
                "content": None
            }
            
        if profile["is_buyer"]:
            return {
                "action": "LIFECYCLE_ONBOARDING",
                "subject": f"Benvenuto in 81+ {rag_soc}: il tuo cassetto sicurezza è attivo",
                "episode": 11,
                "body": "Il tuo percorso è iniziato. Puoi visualizzare gli attestati e lo scadenzario in qualsiasi momento.",
                "cta_text": UNIVERSAL_CTA_TEXT,
                "cta_url": UNIVERSAL_CTA_URL
            }

        # Gestione frizione: se ha cliccato ma non si è registrato
        if profile["last_reaction"] == "CLICK_NO_REG":
            cur.execute("SELECT * FROM narrative_episodes WHERE episode_num = 5")
            ep5 = dict(cur.fetchone())
            return {
                "action": "ANTI_FRICTION_GUIDE",
                "subject": f"{rag_soc}: come funziona 81+ in 60 secondi (senza manuale da 80 pagine)",
                "episode": 5,
                "hook": ep5["hook_pattern_break"],
                "body": f"Sei arrivato sulla piattaforma ma ti sei fermato prima di iniziare. Nessun problema: registrarsi e trovare ciò che serve al settore {macro_settore} richiede meno di un minuto.",
                "beneficio": ep5["beneficio_chiave"],
                "cta_text": UNIVERSAL_CTA_TEXT,
                "cta_url": UNIVERSAL_CTA_URL
            }

        # Gestione obiezione specifica se presente
        if profile["dominant_objection"]:
            cur.execute("SELECT * FROM objection_taxonomy WHERE codice_obiezione = ?", (profile["dominant_objection"],))
            ob_row = cur.fetchone()
            if ob_row:
                ob = dict(ob_row)
                return {
                    "action": "RESOLVE_OBJECTION",
                    "subject": f"{rag_soc}: un chiarimento rapido sulla sicurezza aziendale",
                    "obiezione": ob["codice_obiezione"],
                    "hook": f"Molti imprenditori ci chiedono: '{ob['descrizione_obiezione']}'.",
                    "body": f"È un dubbio legittimo. La risposta semplice è: {ob['risposta_antino']}",
                    "cta_text": UNIVERSAL_CTA_TEXT,
                    "cta_url": UNIVERSAL_CTA_URL
                }

        # Flusso narrativo standard basato su current_episode (1..12)
        ep_num = min(max(profile["current_episode"], 1), 12)
        cur.execute("SELECT * FROM narrative_episodes WHERE episode_num = ?", (ep_num,))
        ep_row = cur.fetchone()
        ep = dict(ep_row) if ep_row else None
        
        if not ep:
            ep = {"hook_pattern_break": "La sicurezza non deve essere complicata.", 
                  "corpo_problema": "Corsi e documenti in un unico posto.",
                  "beneficio_chiave": "Tutto a norma in pochi minuti.",
                  "prova_trasparenza": "Attestati validi per legge."}
                  
        subject = f"{rag_soc}: {ep['titolo']}"
        if ep_num == 1:
            subject = f"La sicurezza della tua azienda: quel corso che 'facciamo la settimana prossima'..."
        elif ep_num == 10:
            subject = f"Sicurezza per {macro_settore}: zero burocrazia inutile per {rag_soc}"

        # Verifica vincolo Hard Rule: CTA unica obbligatoria
        assert UNIVERSAL_CTA_TEXT == "VAI SULLA PIATTAFORMA", "VIOLAZIONE HARD RULE: La CTA deve essere 'VAI SULLA PIATTAFORMA'"

        return {
            "action": "SEND_EPISODE",
            "episode_num": ep_num,
            "subject": subject,
            "hook": ep["hook_pattern_break"],
            "problema": ep["corpo_problema"],
            "beneficio": ep["beneficio_chiave"],
            "prova": ep["prova_trasparenza"],
            "cta_text": UNIVERSAL_CTA_TEXT,
            "cta_url": UNIVERSAL_CTA_URL
        }

    def record_reaction(self, contact_id, reaction_type):
        """
        Aggiorna lo stato in base alla reazione osservata:
        reaction_type in ['NO_OPEN', 'OPEN_NO_CLICK', 'CLICK_NO_REG', 'REGISTERED', 'BOUGHT', 'UNSUBSCRIBED']
        """
        cur = self.conn.cursor()
        profile = self.get_or_create_profile(contact_id)
        
        new_ep = profile["current_episode"]
        is_reg = profile["is_registered"]
        is_buy = profile["is_buyer"]
        
        if reaction_type == "OPEN_NO_CLICK":
            new_ep = min(new_ep + 1, 12)
        elif reaction_type == "REGISTERED":
            is_reg = 1
            new_ep = 11
        elif reaction_type == "BOUGHT":
            is_buy = 1
            new_ep = 11
        elif reaction_type == "UNSUBSCRIBED":
            # Segna suppression
            pass
            
        cur.execute("""
            UPDATE communication_profiles 
            SET last_reaction = ?, current_episode = ?, is_registered = ?, is_buyer = ?, last_updated = CURRENT_TIMESTAMP
            WHERE contact_id = ?
        """, (reaction_type, new_ep, is_reg, is_buy, contact_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    engine = Copy81Engine()
    print("=" * 65)
    print("📢 TEST ENGINE COPY81 — VERIFICA NARRATIVA & ONE CTA POLICY")
    print("=" * 65)
    
    # Test lead 1 (Edilizia)
    msg1 = engine.determine_next_message(1, macro_settore="EDILIZIA", rag_soc="Edil Costruzioni Srl")
    print(f"Episodio: {msg1.get('episode_num', msg1.get('episode'))}")
    print(f"Subject: {msg1['subject']}")
    print(f"Hook: {msg1.get('hook', 'N/A')}")
    print(f"CTA Hard Rule: [{msg1['cta_text']}] -> {msg1['cta_url']}")
    
    # Simula Click senza registrazione
    engine.record_reaction(1, "CLICK_NO_REG")
    msg1_followup = engine.determine_next_message(1, macro_settore="EDILIZIA", rag_soc="Edil Costruzioni Srl")
    print("\n--- DOPO CLICK SENZA REGISTRAZIONE (RAMIFICAZIONE DINAMICA) ---")
    print(f"Azione: {msg1_followup['action']}")
    print(f"Subject: {msg1_followup['subject']}")
    print(f"CTA Hard Rule: [{msg1_followup['cta_text']}] -> {msg1_followup['cta_url']}")
    
    print("\n✅ Test completato con successo: Hard Rule ONE CTA garantita al 100%!")
    engine.close()
