"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/srv_demand/activation_friction_engine.py — Onboarding, Activation & Friction Engine

Raggruppa le capability di attivazione e ciclo post-vendita:
- ONBOARD81: Flusso post-click (Landing, Guida, Registrazione in 60s, Primo Successo).
- ACTIVATION81: Misura l'attivazione effettiva della piattaforma (First Action Completed).
- FRICTION81: Diagnostica colli di bottiglia e distingue problemi di Copy da frizioni UX.
- GUIDE81: Server interattivo della guida '81+ Senza Manuale'.
- POSTCOURSE81: Gestione completamento corso, rilascio attestato e scadenzario T-90..T0.
- LOST81: Rilevamento e catalogazione dei motivi di mancato acquisto.
"""

import os
import sys
import uuid
import sqlite3
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

class ActivationFrictionEngine:
    def __init__(self):
        self.conn = get_connection()

    def track_funnel_step(self, contact_id, step, durata_secondi=0, friction_detected=None, source_campaign="EMAIL_SERIES"):
        """ONBOARD81 + ACTIVATION81: Traccia i singoli passaggi del funnel."""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO funnel_activation_events 
            (contact_id, step, durata_secondi, friction_detected, source_campaign)
            VALUES (?, ?, ?, ?, ?)
        """, (contact_id, step, durata_secondi, friction_detected, source_campaign))
        self.conn.commit()

    def diagnose_friction(self):
        """
        FRICTION81: Analizza i tassi di caduta tra gli step.
        Distingue se il calo è imputabile a COPY (Open / Click) o a PIATTAFORMA (Reg / Activation).
        """
        cur = self.conn.cursor()
        cur.execute("SELECT step, count(1) as cnt FROM funnel_activation_events GROUP BY step")
        step_counts = dict(cur.fetchall())
        
        clicks = step_counts.get("PLATFORM_CLICK", 0)
        landings = step_counts.get("LANDING_VIEW", 0)
        registrations = step_counts.get("REGISTER_SUCCESS", 0)
        activations = step_counts.get("FIRST_CHECK_DONE", 0)
        purchases = step_counts.get("PURCHASE_SUCCESS", 0)
        
        # Tassi di conversione intermedi
        reg_rate = round((registrations / clicks) * 100, 1) if clicks > 0 else 0.0
        act_rate = round((activations / registrations) * 100, 1) if registrations > 0 else 0.0
        pur_rate = round((purchases / activations) * 100, 1) if activations > 0 else 0.0
        
        primary_bottleneck = "NESSUNO"
        diagnosi_tipo = "SISTEMA_BILANCIATO"
        
        if clicks > 50 and reg_rate < 30.0:
            primary_bottleneck = "FRIZIONE_REGISTRAZIONE (Form troppo lungo o dubbi su costo)"
            diagnosi_tipo = "PIATTAFORMA_UX"
        elif registrations > 20 and act_rate < 40.0:
            primary_bottleneck = "FRIZIONE_ONBOARDING (Utente non trova il Safety Check o catalogo)"
            diagnosi_tipo = "PIATTAFORMA_NAVIGAZIONE"
        elif clicks == 0:
            primary_bottleneck = "BASSO_CLICK_RATE (Copy o subject poco efficaci)"
            diagnosi_tipo = "COPY_COMUNICAZIONE"
            
        return {
            "metrics": {
                "clicks": clicks,
                "registrations": registrations,
                "registration_rate_pct": reg_rate,
                "activations": activations,
                "activation_rate_pct": act_rate,
                "purchases": purchases,
                "purchase_rate_pct": pur_rate
            },
            "primary_bottleneck": primary_bottleneck,
            "diagnosi_tipo": diagnosi_tipo,
            "raccomandazione": "Attivare Guida 81+ Senza Manuale a comparsa immediata post-click" if "PIATTAFORMA" in diagnosi_tipo else "Testare nuovi subject pattern-break"
        }

    def record_lost_reason(self, contact_id, codice_corso, motivo_chiave, dettagli="", canale="EMAIL_REPLY"):
        """LOST81: Registra il motivo di mancato acquisto."""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO lost_revenue_reasons
            (contact_id, codice_corso, motivo_chiave, dettagli, canale_rilevamento)
            VALUES (?, ?, ?, ?, ?)
        """, (contact_id, codice_corso, motivo_chiave, dettagli, canale))
        self.conn.commit()

    def complete_course_and_schedule_renewal(self, contact_id, codice_corso, nome_corsista, cf_corsista="", validita_anni=5):
        """POSTCOURSE81: Emette attestato univoco e imposta scadenziario T-90..T0."""
        cur = self.conn.cursor()
        today = datetime.now()
        data_oggi_str = today.strftime("%Y-%m-%d")
        data_scadenza = (today + timedelta(days=validita_anni * 365)).strftime("%Y-%m-%d")
        codice_attestato = f"81P-{uuid.uuid4().hex[:8].upper()}-{today.year}"
        
        # NBA complementare consigliata
        nba_next = "AGGIORNAMENTO_RLS_ANNUALE" if "RSPP" in codice_corso else "CORSO_ANTINCENDIO_L2"
        
        cur.execute("""
            INSERT INTO postcourse_lifecycle
            (contact_id, codice_corso, nome_corsista, codice_fiscale_corsista, data_completamento, data_scadenza_aggiornamento, codice_attestato_univoco, next_complementary_nba)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (contact_id, codice_corso, nome_corsista, cf_corsista, data_oggi_str, data_scadenza, codice_attestato, nba_next))
        self.conn.commit()
        
        return {
            "codice_attestato": codice_attestato,
            "data_completamento": data_oggi_str,
            "data_scadenza": data_scadenza,
            "validita_anni": validita_anni,
            "next_nba": nba_next,
            "promemoria_programmati": ["T-90 giorni", "T-60 giorni", "T-30 giorni", "T0"]
        }

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    engine = ActivationFrictionEngine()
    print("=" * 70)
    print("⚡ TEST ACTIVATION & FRICTION ENGINE — ONBOARD81 + FRICTION81 + POSTCOURSE81")
    print("=" * 70)
    
    # 1. Tracciamento funnel di un lead
    print("\n--- 1. TRACCIAMENTO STEP FUNNEL (ONBOARD81 / ACTIVATION81) ---")
    engine.track_funnel_step(1, "PLATFORM_CLICK", durata_secondi=2)
    engine.track_funnel_step(1, "LANDING_VIEW", durata_secondi=15)
    engine.track_funnel_step(1, "REGISTER_SUCCESS", durata_secondi=45)
    engine.track_funnel_step(1, "FIRST_CHECK_DONE", durata_secondi=80)
    engine.track_funnel_step(1, "PURCHASE_SUCCESS", durata_secondi=120)
    print("Simulati 5 step per Lead #1 (Click -> Landing -> Register -> First Check -> Purchase)")
    
    # 2. Diagnostica Frizioni (FRICTION81)
    print("\n--- 2. DIAGNOSTICA FRIZIONI UX vs COPY (FRICTION81) ---")
    diag = engine.diagnose_friction()
    print(f"Collo di Bottiglia Rilevato: {diag['primary_bottleneck']}")
    print(f"Tipo Diagnosi: {diag['diagnosi_tipo']}")
    print(f"Raccomandazione Automatica: {diag['raccomandazione']}")
    
    # 3. Completamento corso e Scadenzario (POSTCOURSE81)
    print("\n--- 3. COMPLETAMENTO CORSO & RILASCIO ATTESTATO (POSTCOURSE81) ---")
    cert = engine.complete_course_and_schedule_renewal(1, "AULA_MULETTO_CARRELLI_12H", "Mario Rossi", validita_anni=5)
    print(f"Attestato Univoco Emesso: {cert['codice_attestato']}")
    print(f"Data Scadenza Aggiornamento: {cert['data_scadenza']} ({cert['validita_anni']} anni)")
    print(f"Next Best Action Complementare: {cert['next_nba']}")
    print(f"Scadenziario Attivo: {cert['promemoria_programmati']}")
    
    print("\n" + "=" * 70)
    print("✅ Test Activation, Friction & Post-Course completato con successo!")
    engine.close()
