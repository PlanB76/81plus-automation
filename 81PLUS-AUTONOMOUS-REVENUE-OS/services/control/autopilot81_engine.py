"""
81+ AUTONOMOUS REVENUE OS — ENGINE M8: AUTOPILOT, CONTROL TOWER & DAILY EXECUTIVE BRIEFING
Capability: AUTOPILOT81, EXECUTIVE81, BOTTLENECK81, ICP81, LEARN81, NORTHSTAR81.
Modalità: SHADOW, ASSISTED, GUARDED, AUTONOMOUS, EMERGENCY.
"""

import sqlite3
import uuid
import json
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.events.event_bus import emit_event

DAILY_TARGET_EUR = 2740.0

class Autopilot81Engine:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn or get_connection()
        self._ensure_init_state()

    def _ensure_init_state(self):
        """Inizializza lo stato dell'autopilota se non ancora configurato."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM autopilot_states")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO autopilot_states (id, mode, kill_switch_active, allowed_autonomous_actions, updated_at)
                VALUES ('MAIN_AUTOPILOT', 'GUARDED', 0, '["NURTURE_SEND", "RENEWAL_EVALUATE", "DEADLINE_CHECK"]', ?)
            """, (datetime.now().isoformat(),))
            self.conn.commit()

    def get_state(self) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT mode, kill_switch_active, active_incident_reason, updated_at FROM autopilot_states WHERE id = 'MAIN_AUTOPILOT'")
        row = cursor.fetchone()
        return {
            "mode": row[0],
            "kill_switch_active": bool(row[1]),
            "active_incident": row[2],
            "updated_at": row[3]
        }

    def set_mode(self, new_mode: str) -> str:
        valid_modes = ["SHADOW", "ASSISTED", "GUARDED", "AUTONOMOUS", "EMERGENCY"]
        if new_mode not in valid_modes:
            raise ValueError(f"Modalità '{new_mode}' non valida. Scegliere tra {valid_modes}.")

        cursor = self.conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("""
            UPDATE autopilot_states
            SET mode = ?, updated_at = ?
            WHERE id = 'MAIN_AUTOPILOT'
        """, (new_mode, now_str))
        self.conn.commit()

        emit_event("AUTOPILOT_MODE_CHANGED", {"new_mode": new_mode}, self.conn)
        return new_mode

    def trigger_kill_switch(self, reason: str):
        """Attivazione immediata del Kill Switch: stato EMERGENCY e blocco operativo."""
        cursor = self.conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("""
            UPDATE autopilot_states
            SET mode = 'EMERGENCY', kill_switch_active = 1, active_incident_reason = ?, updated_at = ?
            WHERE id = 'MAIN_AUTOPILOT'
        """, (reason, now_str))
        self.conn.commit()

        emit_event("KILL_SWITCH_ENGAGED", {"reason": reason, "severity": "CRITICAL"}, self.conn)

    def reset_kill_switch(self):
        """Ripristino operatività dopo audit."""
        cursor = self.conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("""
            UPDATE autopilot_states
            SET mode = 'GUARDED', kill_switch_active = 0, active_incident_reason = NULL, updated_at = ?
            WHERE id = 'MAIN_AUTOPILOT'
        """, (now_str,))
        self.conn.commit()

        emit_event("KILL_SWITCH_RESOLVED", {"status": "RESTORED_TO_GUARDED"}, self.conn)

    # =========================================================================
    # BOTTLENECK DETECTOR (BOTTLENECK81)
    # =========================================================================
    def detect_bottleneck(self) -> dict:
        """
        Analizza i drop-off lungo l'Equazione Madre:
        FONTI → LEAD → TWIN → CONTACTABLE → NURTURED → PLATFORM → BUYER → RENEWAL
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM company_contacts")
        total_leads = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM company_contacts WHERE contactability_status = 'CONTACTABLE'")
        contactable_leads = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM company_twins")
        twins_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM copy_experiments")
        messages_sent = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM copy_experiments WHERE outcome IN ('CLICKED', 'REGISTERED', 'BOUGHT')")
        clicks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM revenue_ledger WHERE status = 'PAID'")
        buyers = cursor.fetchone()[0]

        # Logica euristica collo di bottiglia
        bottleneck_stage = "ACQUISITION_VOLUME"
        recommendation = "Aumentare il flusso giornaliero di lead qualificati."

        if total_leads > 500 and contactable_leads / max(1, total_leads) < 0.60:
            bottleneck_stage = "CONTACTABILITY_GATE"
            recommendation = "Pulizia anagrafica e arricchimento email/PEC."
        elif messages_sent > 100 and clicks / max(1, messages_sent) < 0.05:
            bottleneck_stage = "COMMUNICATION_HOOK_FRICTION"
            recommendation = "Ottimizzare gli oggetti e il pattern break con COPY81."
        elif clicks > 30 and buyers / max(1, clicks) < 0.10:
            bottleneck_stage = "PLATFORM_ACTIVATION_DROP"
            recommendation = "Ridurre attrito onboarding su 81plus.net con GUIDE81 in evidenza."
        elif buyers > 50:
            bottleneck_stage = "RENEWAL_EXPANSION_ACCELERATION"
            recommendation = "Attivare campagne proattive T-60 / T-30 con narrative di rinnovo."

        return {
            "bottleneck_stage": bottleneck_stage,
            "metrics": {
                "total_leads": total_leads,
                "contactable_leads": contactable_leads,
                "company_twins": twins_count,
                "messages_sent": messages_sent,
                "clicks": clicks,
                "buyers": buyers
            },
            "recommendation": recommendation
        }

    # =========================================================================
    # ICP LEARNING & BEHAVIORAL WEIGHTS (ICP81)
    # =========================================================================
    def update_icp_intelligence(self) -> list:
        """
        Analizza gli acquirenti reali e calcola il moltiplicatore di priorità ICP per settore ATECO.
        """
        cursor = self.conn.cursor()
        now_str = datetime.now().isoformat()

        cursor.execute("""
            SELECT SUBSTR(ct.ateco_code, 1, 2) as ateco_macro,
                   ct.risk_level,
                   COUNT(rl.order_id) as buyers,
                   COALESCE(SUM(rl.amount_gross), 0.0) as revenue
            FROM company_twins ct
            JOIN revenue_ledger rl ON rl.company_id = ct.id AND rl.status = 'PAID'
            GROUP BY ateco_macro, ct.risk_level
        """)
        rows = cursor.fetchall()

        updated_profiles = []
        for macro, risk, buyers, rev in rows:
            if not macro:
                continue

            # Calcolo moltiplicatore: più revenue genera, più alto è il peso per LEAD81
            mult = 1.0 + min(2.0, (rev / 1000.0) + (buyers * 0.1))

            label_map = {
                "41": "Costruzioni & Edilizia", "43": "Impiantistica Specializzata",
                "25": "Carpenteria & Meccanica", "56": "Ristorazione & Food",
                "01": "Agricoltura & Verde", "70": "Servizi & Consulenza"
            }
            label = label_map.get(macro, f"Settore Macro {macro}")

            cursor.execute("""
                INSERT OR REPLACE INTO icp_profiles (
                    ateco_prefix, sector_label, risk_level, buyer_count, total_revenue,
                    score_multiplier, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (macro, label, risk or "MEDIO", buyers, rev, round(mult, 2), now_str))

            updated_profiles.append({"macro": macro, "label": label, "multiplier": round(mult, 2), "revenue": rev})

        self.conn.commit()
        return updated_profiles

    # =========================================================================
    # DAILY EXECUTIVE BRIEFING (EXECUTIVE81)
    # =========================================================================
    def generate_executive_daily_briefing(self) -> dict:
        """Genera il briefing giornaliero completo per la Control Tower e il Founder."""
        cursor = self.conn.cursor()
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        # 1. Metriche Economiche
        cursor.execute("""
            SELECT COALESCE(SUM(amount_gross), 0.0),
                   COALESCE(SUM(commission_earned), 0.0),
                   COALESCE(SUM(commission_received), 0.0),
                   COUNT(*)
            FROM revenue_ledger
        """)
        rev_row = cursor.fetchone()
        gross_rev, comm_earned, comm_received, total_orders = rev_row

        # Calcolo run-rate giornaliero (media ordini pagati ultimi 30 gg o proxy)
        cursor.execute("SELECT COALESCE(SUM(amount_gross), 0.0) FROM revenue_ledger WHERE status = 'PAID'")
        paid_rev = cursor.fetchone()[0]
        daily_actual = round(paid_rev / 30.0, 2)  # run rate indicativo
        gap = round(DAILY_TARGET_EUR - daily_actual, 2)

        # 2. Stato Autopilota e Bottleneck
        state = self.get_state()
        bottleneck = self.detect_bottleneck()

        # 3. Health Score del Sistema (0 - 100)
        health_score = 98 if not state["kill_switch_active"] else 30
        system_status = "RUN" if health_score >= 90 else ("DEGRADED" if health_score >= 70 else "STOP")

        # 4. Formattazione Markdown Executive
        briefing_md = f"""# 81+ AUTONOMOUS REVENUE OS — EXECUTIVE BRIEFING ({date_str})

## 1. NORTH STAR & PACING OBIETTIVO €1.000.000/ANNO
- **Target Giornaliero Pacing**: €{DAILY_TARGET_EUR:,.2f}
- **Run-Rate Attuale**: €{daily_actual:,.2f}/giorno
- **Gap Giornaliero**: €{gap:,.2f}
- **Fatturato Lordo Tracciato**: €{gross_rev:,.2f} (Ordini: {total_orders})
- **Commissioni Maturate**: €{comm_earned:,.2f} | **Incassate Riconciliate**: €{comm_received:,.2f}

## 2. MACHINE HEALTH & AUTOPILOT STATUS
- **System Status**: **[{system_status}]** (Score: {health_score}/100)
- **Modalità Autopilota**: `{state['mode']}`
- **Kill Switch**: {'[ATTIVO]' if state['kill_switch_active'] else '[DISATTIVATO - OPERATIVO]'}
{f"- **Incidente Attivo**: {state['active_incident']}" if state['active_incident'] else ""}

## 3. BOTTLENECK81 & COLLO DI BOTTIGLIA SISTEMICO
- **Stadio Critico Rilevato**: `{bottleneck['bottleneck_stage']}`
- **Azione Consigliata**: {bottleneck['recommendation']}
- **Metriche Imbuto**:
  - Lead Totali: {bottleneck['metrics']['total_leads']} (Contattabili: {bottleneck['metrics']['contactable_leads']})
  - Company Twins: {bottleneck['metrics']['company_twins']}
  - Clic Piattaforma: {bottleneck['metrics']['clicks']} | Buyer Pagati: {bottleneck['metrics']['buyers']}

## 4. DECISIONI STRATEGICHE RACCOMANDATE
1. Mantenere la **One CTA Universale** ('VAI SULLA PIATTAFORMA') su tutti i cluster.
2. Dare priorità di acquisizione ai settori a più alto moltiplicatore ICP (Costruzioni ed Impianti).
3. Monitorare i rinnovi a scadenza imminente (T-30 e T-7).
"""

        briefing_id = f"BRF-{date_str}-{uuid.uuid4().hex[:6]}"
        cursor.execute("""
            INSERT INTO executive_briefings (
                id, date_str, health_score, system_status, daily_revenue_actual,
                target_gap, bottleneck_stage, briefing_markdown, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (briefing_id, date_str, health_score, system_status, daily_actual,
              gap, bottleneck["bottleneck_stage"], briefing_md, now.isoformat()))
        self.conn.commit()

        emit_event("EXECUTIVE_BRIEFING_GENERATED", {
            "briefing_id": briefing_id, "health_score": health_score, "status": system_status
        }, self.conn)

        return {
            "briefing_id": briefing_id,
            "date": date_str,
            "health_score": health_score,
            "system_status": system_status,
            "daily_revenue_actual": daily_actual,
            "target_gap": gap,
            "bottleneck_stage": bottleneck["bottleneck_stage"],
            "briefing_markdown": briefing_md
        }

if __name__ == "__main__":
    engine = Autopilot81Engine()
    briefing = engine.generate_executive_daily_briefing()
    print("[EXECUTIVE BRIEFING SAMPLE]")
    print(briefing["briefing_markdown"])
