"""
81+ AUTONOMOUS REVENUE OS
services/engage/funnel_activation81.py — ONBOARD81, ACTIVATION81 & FRICTION81 ENGINE
Governa l'onboarding dell'utente e la diagnostica delle frizioni:
- Traccia gli eventi del funnel: EMAIL_CLICK -> PLATFORM_VISIT -> REGISTRATION -> ACTIVATION -> PRODUCT -> COMPLETED
- Misura l'attivazione effettiva (ACTIVATION81)
- Identifica dove si perdono gli utenti (FRICTION81)
- Impedisce a COPY81 di cambiare copy persuasivo quando il collo di bottiglia è una frizione tecnica/UX.
"""

import os
import sys
import json
import uuid
from datetime import datetime
import sqlite3
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

logger = logging.getLogger("FUNNEL81")

FUNNEL_STEPS_ORDER = [
    "EMAIL_CLICK",
    "PLATFORM_VISIT",
    "GUIDE_VIEW",
    "REGISTRATION",
    "ACTIVATION",
    "PRODUCT_VIEW",
    "CHECKOUT_START",
    "COMPLETED"
]

class FunnelActivationEngine:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn

    def _get_conn(self):
        return self.conn if self.conn is not None else get_connection()

    def record_step(self, step: str, session_id: str, company_id: str = None, 
                    url: str = None, referrer: str = None, device_type: str = "DESKTOP", metadata: dict = None) -> str:
        """Registra il passaggio di un utente attraverso uno step del funnel."""
        if step not in FUNNEL_STEPS_ORDER:
            raise ValueError(f"Step '{step}' non riconosciuto nel funnel ufficiale.")

        event_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO platform_funnel_events
            (id, company_id, session_id, step, url, referrer, device_type, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, company_id, session_id, step, url, referrer, device_type, meta_str, now))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return event_id

    def check_activation_status(self, company_id: str) -> dict:
        """
        Verifica lo stato di attivazione per una specifica azienda:
        - Registered: ha completato la registrazione account
        - Activated: ha eseguito almeno un check normativo o avviato una sessione
        - Product Viewed: ha visualizzato un corso/documento
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT step FROM platform_funnel_events 
            WHERE company_id = ?
        """, (company_id,))
        steps_done = set(r[0] for r in cursor.fetchall())

        is_registered = "REGISTRATION" in steps_done
        is_activated = "ACTIVATION" in steps_done
        has_purchased = "COMPLETED" in steps_done

        if self.conn is None:
            conn.close()

        return {
            "company_id": company_id,
            "registered": is_registered,
            "activated": is_activated,
            "purchased": has_purchased,
            "steps_completed": list(steps_done)
        }

    def compute_friction_metrics(self, period_date: str = None) -> list[dict]:
        """
        Calcola i tassi di drop-off percentuali tra step consecutivi del funnel.
        Identifica anomalie UX per non confondere problemi di piattaforma con problemi di copy.
        """
        p_date = period_date or datetime.now().strftime("%Y-%m-%d")
        conn = self._get_conn()
        cursor = conn.cursor()

        # Raccogli conteggi per step
        cursor.execute("""
            SELECT step, COUNT(DISTINCT session_id) as sessions
            FROM platform_funnel_events
            WHERE created_at LIKE ?
            GROUP BY step
        """, (f"{p_date}%",))
        step_counts = {r["step"]: r["sessions"] for r in cursor.fetchall()}

        friction_report = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Confronta coppie consecutive
        for i in range(len(FUNNEL_STEPS_ORDER) - 1):
            from_step = FUNNEL_STEPS_ORDER[i]
            to_step = FUNNEL_STEPS_ORDER[i + 1]

            entered = step_counts.get(from_step, 0)
            progressed = step_counts.get(to_step, 0)

            if entered == 0:
                continue

            drop_count = max(0, entered - progressed)
            drop_rate = round(drop_count / entered, 4)

            # Soglia anomalia: se drop-off > 70%
            anomaly = 1 if drop_rate > 0.70 else 0
            diagnosis = "NORMALE"
            if anomaly:
                if from_step == "PLATFORM_VISIT" and to_step == "REGISTRATION":
                    diagnosis = "FRIZIONE_UX_LANDING: Form di registrazione percepito come troppo lungo o poco chiaro."
                elif from_step == "REGISTRATION" and to_step == "ACTIVATION":
                    diagnosis = "FRIZIONE_ONBOARDING: Mancanza di primo task guidato immediato post-registrazione."
                elif from_step == "PRODUCT_VIEW" and to_step == "CHECKOUT_START":
                    diagnosis = "FRIZIONE_PRICING: Prezzo o modalità d'esame non abbastanza trasparenti."
                else:
                    diagnosis = f"FRIZIONE_ELEVATA tra {from_step} e {to_step}."

            cursor.execute("""
                INSERT INTO platform_friction_metrics
                (period_date, from_step, to_step, total_entered, total_progressed, drop_off_count, drop_off_rate, anomaly_flag, diagnosis, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (p_date, from_step, to_step, entered, progressed, drop_count, drop_rate, anomaly, diagnosis, now_str))

            friction_report.append({
                "from_step": from_step,
                "to_step": to_step,
                "entered": entered,
                "progressed": progressed,
                "drop_rate": f"{drop_rate * 100:.1f}%",
                "anomaly": bool(anomaly),
                "diagnosis": diagnosis
            })

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return friction_report

if __name__ == "__main__":
    engine = FunnelActivationEngine()
    print("Test FunnelActivationEngine...")
    test_sid = "sess_" + uuid.uuid4().hex[:8]
    test_cid = "comp_" + uuid.uuid4().hex[:8]
    
    # Simula percorso funnel
    engine.record_step("EMAIL_CLICK", test_sid, test_cid)
    engine.record_step("PLATFORM_VISIT", test_sid, test_cid)
    engine.record_step("REGISTRATION", test_sid, test_cid)
    engine.record_step("ACTIVATION", test_sid, test_cid)
    engine.record_step("PRODUCT_VIEW", test_sid, test_cid)

    status = engine.check_activation_status(test_cid)
    print("Activation Status:", json.dumps(status, indent=2))
    report = engine.compute_friction_metrics()
    print("Friction Report:", json.dumps(report, indent=2))
