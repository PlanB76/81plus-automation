"""
81+ AUTONOMOUS REVENUE OS
services/srv_revenue/delivery81_router.py — DELIVERY81, ROUTER81, CLASS81 & DEMAND81
Instrada automaticamente i bisogni formativi e documentali:
1. ROUTER81: Determina la modalita (ONLINE FAD Partner 2377 vs AULA Centro ANFOS RO/3 vs DOCUMENT).
2. DEMAND81 + GEO81: Aggrega fabbisogni per territorio e scatta ad edizione d'aula proposta quando raggiunta la soglia.
3. CLASS81: Gestisce capacita, posti minimi e stati dell'aula (IDEA -> DEMAND_DETECTED -> PROPOSED -> OPEN -> FULL).
4. FULFILLMENT81: Macchina a stati di erogazione e attestazione legale con QR code.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta
import sqlite3
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

logger = logging.getLogger("DELIVERY81")

class DeliveryRouter81:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn

    def _get_conn(self):
        return self.conn if self.conn is not None else get_connection()

    def route_need(self, need_key: str, ateco_risk: str = "MEDIO", province: str = "RO") -> dict:
        """
        Determina la modalità corretta di erogazione e il prodotto raccomandato
        in base alla normativa D.Lgs. 81/08 e Accordo Stato-Regioni 2025.
        """
        nk = need_key.upper()
        conn = self._get_conn()
        cursor = conn.cursor()

        # Regole di Instradamento
        if any(k in nk for k in ["CARRELLI", "MULETTO", "PLE", "GRU", "ESCAVATORI", "TRATTORI", "ANTINCENDIO", "PRIMO_SOCCORSO"]):
            # Corsi con parte pratica obbligatoria in presenza
            cursor.execute("SELECT * FROM product_catalog WHERE delivery_mode = 'AULA' AND active = 1 AND product_id LIKE ? LIMIT 1", (f"%{nk[:4]}%",))
            row = cursor.fetchone()
            if not row:
                cursor.execute("SELECT * FROM product_catalog WHERE product_id = 'CRS_AULA_CARRELLI'")
                row = cursor.fetchone()
            mode = "AULA"
            provider = "CENTRO_ANFOS_RO3"
        elif any(k in nk for k in ["DVR", "POS", "HACCP", "DOCUMENTO"]):
            # Documenti tecnici
            cursor.execute("SELECT * FROM product_catalog WHERE type = 'DOCUMENT' AND active = 1 AND product_id LIKE ? LIMIT 1", (f"%{nk[:4]}%",))
            row = cursor.fetchone()
            if not row:
                cursor.execute("SELECT * FROM product_catalog WHERE product_id = 'DOC_DVR_STD'")
                row = cursor.fetchone()
            mode = "DOCUMENT"
            provider = "DIRECT_81PLUS"
        else:
            # Formazione e-learning FAD (rischio basso / generale / aggiornamenti)
            if ateco_risk == "ALTO" and "SPECIFICA" in nk:
                cursor.execute("SELECT * FROM product_catalog WHERE product_id = 'CRS_AULA_ALTO'")
                row = cursor.fetchone()
                mode = "BLENDED"
                provider = "CENTRO_ANFOS_RO3"
            else:
                cursor.execute("SELECT * FROM product_catalog WHERE delivery_mode = 'ONLINE' AND active = 1 LIMIT 1")
                row = cursor.fetchone()
                mode = "ONLINE"
                provider = "PARTNER_2377_FAD"

        prod_data = dict(row) if row else {
            "product_id": "CRS_FAD_GEN",
            "title": "Formazione Lavoratori Generale",
            "price_gross": 50.0,
            "unit_cost": 15.0,
            "commission_rate": 0.40
        }

        if self.conn is None:
            conn.close()

        return {
            "need_key": need_key,
            "delivery_mode": mode,
            "provider": provider,
            "product": prod_data,
            "legal_rule": "Accordo Stato-Regioni 2025 / D.Lgs. 81/08",
            "cta": "VAI SULLA PIATTAFORMA"
        }

    def aggregate_demand(self, course_id: str, province: str, count: int = 1, estimated_value: float = 180.0) -> dict:
        """
        DEMAND81 + GEO81 + CLASS81:
        Aggrega la domanda territoriale per provincia e corso.
        Se supera la soglia minima di classe (6 partecipanti), promuove automaticamente a DEMAND_DETECTED.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT * FROM territory_demand_signals WHERE course_id = ? AND province = ?", (course_id, province))
        row = cursor.fetchone()

        if row:
            sig_id = row["id"]
            new_companies = row["company_count"] + 1
            new_attendees = row["potential_attendees"] + count
            new_rev = row["potential_revenue"] + (estimated_value * count)
            new_status = "THRESHOLD_REACHED" if new_attendees >= 6 else "ACCUMULATING"

            cursor.execute("""
                UPDATE territory_demand_signals
                SET company_count = ?, potential_attendees = ?, potential_revenue = ?, status = ?, last_signal_at = ?
                WHERE id = ?
            """, (new_companies, new_attendees, new_rev, new_status, now_str, sig_id))
        else:
            sig_id = str(uuid.uuid4())
            new_status = "THRESHOLD_REACHED" if count >= 6 else "ACCUMULATING"
            new_attendees = count
            new_rev = estimated_value * count
            cursor.execute("""
                INSERT INTO territory_demand_signals
                (id, course_id, province, company_count, potential_attendees, potential_revenue, status, last_signal_at, created_at)
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
            """, (sig_id, course_id, province, count, new_rev, new_status, now_str, now_str))

        # Se la soglia è raggiunta, crea un'edizione d'aula proposta (CLASS81)
        created_edition_id = None
        if new_status == "THRESHOLD_REACHED":
            cursor.execute("SELECT edition_id FROM class_editions WHERE course_id = ? AND province = ? AND status = 'DEMAND_DETECTED'", (course_id, province))
            ed_row = cursor.fetchone()
            if not ed_row:
                created_edition_id = str(uuid.uuid4())
                start_date = (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d 09:00:00")
                end_date = (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d 18:00:00")
                cursor.execute("""
                    INSERT INTO class_editions
                    (edition_id, course_id, title, location, province, starts_at, ends_at, capacity, min_participants, enrolled_count, status, created_at)
                    VALUES (?, ?, 'Edizione Territoriale Proposta', ?, ?, ?, ?, 15, 6, ?, 'DEMAND_DETECTED', ?)
                """, (created_edition_id, course_id, f"Sede Territoriale {province}", province, start_date, end_date, new_attendees, now_str))
                logger.info(f"[CLASS81] Soglia territoriale raggiunta per {province}: creata edizione {created_edition_id} (DEMAND_DETECTED)")

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return {
            "signal_id": sig_id,
            "province": province,
            "attendees": new_attendees,
            "status": new_status,
            "proposed_edition_id": created_edition_id
        }

    def start_fulfillment(self, order_id: str, company_id: str, product_id: str, delivery_mode: str) -> str:
        """Inizializza il record di fulfillment per un ordine."""
        fulf_id = str(uuid.uuid4())
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_status = "ENROLLED" if delivery_mode == "ONLINE" else "BOOKED"

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fulfillment_records
            (fulfillment_id, order_id, company_id, product_id, delivery_mode, status, started_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fulf_id, order_id, company_id, product_id, delivery_mode, initial_status, now_str, now_str))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return fulf_id

    def advance_fulfillment(self, fulfillment_id: str, next_status: str, qr_code: str = None) -> bool:
        """Avanza lo stato di fulfillment fino a DELIVERED con QR Code di certificazione."""
        valid_transitions = [
            "PENDING", "ENROLLED", "BOOKED", "IN_PROGRESS", "ATTENDED", "COMPLETED", "CERTIFIED", "DELIVERED"
        ]
        if next_status not in valid_transitions:
            raise ValueError(f"Stato {next_status} non ammesso in FULFILLMENT81.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fulfillment_records
            SET status = ?,
                certificate_qr = COALESCE(?, certificate_qr),
                completed_at = CASE WHEN ? IN ('COMPLETED', 'CERTIFIED', 'DELIVERED') THEN ? ELSE completed_at END,
                delivered_at = CASE WHEN ? = 'DELIVERED' THEN ? ELSE delivered_at END
            WHERE fulfillment_id = ?
        """, (next_status, qr_code, next_status, now_str, next_status, now_str, fulfillment_id))

        count = cursor.rowcount
        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return count > 0

if __name__ == "__main__":
    router = DeliveryRouter81()
    print("Testing DeliveryRouter81:")
    r1 = router.route_need("CARRELLI_ELEVATORI", "ALTO", "RO")
    print("Routing Carrelli:", r1["delivery_mode"], "| Provider:", r1["provider"])
    r2 = router.route_need("FORMAZIONE_GENERALE", "BASSO", "MI")
    print("Routing Generale:", r2["delivery_mode"], "| Provider:", r2["provider"])
    
    print("\nTesting Demand Aggregation:")
    d = router.aggregate_demand("CRS_AULA_CARRELLI", "RO", count=6)
    print("Demand Result:", json.dumps(d, indent=2))
