"""
81+ AUTONOMOUS REVENUE OS — ENGINE M4: REVENUE, COMMISSIONS, RENEWALS & RECONCILIATION
Capability coperte:
- SELL81: Ordini, pagamenti, commission attribution separata.
- RENEW81: Gestione scadenze T-90, T-60, T-30, T-7, DUE, GRACE, WINBACK e auto-rigenerazione.
- RECON81: Riconciliazione automatica con quarantena discrepanze.
- PROFIT81 & CASH81: Tracciamento net cash, margini e Goal Engine €1M/anno.
"""

import sqlite3
import uuid
import json
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.events.event_bus import emit_event

DAILY_REVENUE_TARGET = 2740.0  # €1M / 365 gg

class RevenueEngine81:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn or get_connection()

    # =========================================================================
    # 1. SELL81 & COMMERCE (ORDINI & PAGAMENTI IDEMPOTENTI)
    # =========================================================================
    def create_order(self, company_id: str, product_id: str, product_name: str,
                     amount_gross: float, delivery_mode: str, commission_rate: float = 0.35,
                     order_id: str = None) -> dict:
        """Crea un ordine in modo idempotente. Registra commission_earned ma non received."""
        cursor = self.conn.cursor()
        order_id = order_id or f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Verifica idempotenza
        cursor.execute("SELECT order_id, status, amount_gross FROM revenue_ledger WHERE order_id = ?", (order_id,))
        existing = cursor.fetchone()
        if existing:
            return {"order_id": existing[0], "status": existing[1], "amount_gross": existing[2], "is_duplicate": True}

        commission_earned = round(amount_gross * commission_rate, 2)
        now_str = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO revenue_ledger (
                order_id, company_id, product_id, product_name, delivery_mode,
                amount_gross, commission_rate, commission_earned, commission_received,
                status, ordered_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, 'ORDERED', ?, ?)
        """, (order_id, company_id, product_id, product_name, delivery_mode,
              amount_gross, commission_rate, commission_earned, now_str, now_str))

        self.conn.commit()

        emit_event("ORDER_CREATED", {
            "order_id": order_id, "company_id": company_id, "amount_gross": amount_gross,
            "commission_earned": commission_earned, "delivery_mode": delivery_mode
        }, self.conn)

        return {
            "order_id": order_id,
            "company_id": company_id,
            "amount_gross": amount_gross,
            "commission_earned": commission_earned,
            "status": "ORDERED",
            "is_duplicate": False
        }

    def record_payment(self, idempotency_key: str, order_id: str,
                       payment_provider: str, amount: float,
                       provider_tx_id: str = None) -> dict:
        """Registra un pagamento incassato in modo rigoroso e idempotente."""
        cursor = self.conn.cursor()

        # Check idempotency su payment_transactions
        cursor.execute("SELECT idempotency_key, status FROM payment_transactions WHERE idempotency_key = ?", (idempotency_key,))
        existing_tx = cursor.fetchone()
        if existing_tx:
            return {"idempotency_key": existing_tx[0], "status": existing_tx[1], "is_duplicate": True}

        cursor.execute("SELECT company_id, amount_gross, commission_earned, status FROM revenue_ledger WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError(f"Ordine {order_id} non trovato in revenue_ledger.")

        company_id, amount_gross, comm_earned, current_status = order

        if abs(amount - amount_gross) > 0.01:
            raise ValueError(f"Importo pagamento ({amount} EUR) non coincide con totale ordine ({amount_gross} EUR).")

        now_str = datetime.now().isoformat()

        # Registra transazione pagamento
        cursor.execute("""
            INSERT INTO payment_transactions (
                idempotency_key, order_id, payment_provider, amount, status,
                provider_transaction_id, created_at
            ) VALUES (?, ?, ?, ?, 'SETTLED', ?, ?)
        """, (idempotency_key, order_id, payment_provider, amount, provider_tx_id, now_str))

        # Aggiorna ordine a PAID
        cursor.execute("""
            UPDATE revenue_ledger
            SET status = 'PAID', paid_at = ?
            WHERE order_id = ?
        """, (now_str, order_id))

        # Inserimento partita doppia in cash_ledger
        cursor.execute("""
            INSERT INTO cash_ledger (
                id, order_id, company_id, entry_type, gross_amount, net_amount,
                is_reconciled, notes, created_at
            ) VALUES (?, ?, ?, 'ORDER_PAYMENT', ?, ?, 1, 'Incasso cliente confermato', ?)
        """, (f"CSH-{uuid.uuid4().hex[:8].upper()}", order_id, company_id, amount, amount, now_str))

        cursor.execute("""
            INSERT INTO cash_ledger (
                id, order_id, company_id, entry_type, gross_amount, net_amount,
                is_reconciled, notes, created_at
            ) VALUES (?, ?, ?, 'COMMISSION_EARNED', ?, ?, 0, 'Competenza provvigionale maturata non ancora liquidata', ?)
        """, (f"CSH-{uuid.uuid4().hex[:8].upper()}", order_id, company_id, comm_earned, comm_earned, now_str))

        self.conn.commit()

        emit_event("ORDER_PAID", {
            "order_id": order_id, "amount": amount, "provider": payment_provider,
            "provider_tx_id": provider_tx_id
        }, self.conn)

        return {
            "order_id": order_id,
            "amount": amount,
            "status": "SETTLED",
            "commission_earned": comm_earned,
            "commission_received": 0.0,
            "is_duplicate": False
        }

    def reconcile_commission(self, order_id: str, partner_receipt_ref: str,
                             amount_received: float) -> dict:
        """
        Riconciliazione commissionale: 'Mai considerare incassata una commissione non riconciliata.'
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT company_id, commission_earned, commission_received, status FROM revenue_ledger WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError(f"Ordine {order_id} inesistente.")

        company_id, comm_earned, comm_received_curr, status = order
        now_str = datetime.now().isoformat()

        # Verifica tolleranza
        if abs(amount_received - comm_earned) > 0.05:
            # Mismatch: Quarantena & Notifica HUMAN81
            cursor.execute("""
                INSERT INTO revenue_reconciliations (
                    id, cycle_date, orders_checked, commissions_checked, mismatches_count,
                    quarantined_count, status, details_json, created_at
                ) VALUES (?, ?, 1, 1, 1, 1, 'DISCREPANCY_DETECTED', ?, ?)
            """, (f"REC-{uuid.uuid4().hex[:8].upper()}", now_str[:10],
                  json.dumps({"order_id": order_id, "expected": comm_earned, "received": amount_received, "ref": partner_receipt_ref}),
                  now_str))
            self.conn.commit()

            emit_event("COMMISSION_MISMATCH_QUARANTINED", {
                "order_id": order_id, "expected": comm_earned, "received": amount_received,
                "reason": "Importo liquidato divergente da competenza maturata"
            }, self.conn)

            return {"status": "QUARANTINED", "reason": "MISMATCH_AMOUNT", "order_id": order_id}

        # Match perfetto: accredito commission_received
        cursor.execute("""
            UPDATE revenue_ledger
            SET commission_received = ?
            WHERE order_id = ?
        """, (amount_received, order_id))

        cursor.execute("""
            INSERT INTO cash_ledger (
                id, order_id, company_id, entry_type, gross_amount, net_amount,
                is_reconciled, reconciled_at, reconciliation_ref, notes, created_at
            ) VALUES (?, ?, ?, 'COMMISSION_RECEIVED', ?, ?, 1, ?, ?, 'Bonifico provvigioni partner accreditato', ?)
        """, (f"CSH-{uuid.uuid4().hex[:8].upper()}", order_id, company_id,
              amount_received, amount_received, now_str, partner_receipt_ref, now_str))

        self.conn.commit()

        emit_event("COMMISSION_RECONCILED", {
            "order_id": order_id, "amount_received": amount_received,
            "reconciliation_ref": partner_receipt_ref
        }, self.conn)

        return {
            "status": "RECONCILED",
            "order_id": order_id,
            "commission_received": amount_received,
            "reconciliation_ref": partner_receipt_ref
        }

    # =========================================================================
    # 2. RENEW81 (LIFECYCLE TIMELINE: T-90, T-60, T-30, T-7, DUE, GRACE, WINBACK)
    # =========================================================================
    def evaluate_deadlines(self, ref_date: datetime = None) -> list:
        """Valuta le scadenze rispetto al punto temporale corrente e pianifica la cadence."""
        ref_date = ref_date or datetime.now()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, company_id, course_or_doc, renewal_due_at, validity_years, status
            FROM compliance_deadlines
            WHERE status IN ('ACTIVE', 'UPCOMING', 'EXPIRED')
        """)
        deadlines = cursor.fetchall()

        actions_taken = []
        now_str = datetime.now().isoformat()

        for d_id, comp_id, course_doc, due_at_str, val_years, d_status in deadlines:
            due_date = datetime.fromisoformat(due_at_str)
            days_delta = (due_date - ref_date).days

            window_step = None
            if 61 <= days_delta <= 90:
                window_step = "T-90"
            elif 31 <= days_delta <= 60:
                window_step = "T-60"
            elif 8 <= days_delta <= 30:
                window_step = "T-30"
            elif 1 <= days_delta <= 7:
                window_step = "T-7"
            elif days_delta == 0:
                window_step = "DUE"
            elif -30 <= days_delta < 0:
                window_step = "GRACE"
            elif days_delta < -30:
                window_step = "WINBACK"

            if window_step:
                # Controlla se la cadence per questa specifica finestra è già pianificata
                cursor.execute("""
                    SELECT id FROM renewal_cadences
                    WHERE deadline_id = ? AND window_step = ?
                """, (d_id, window_step))
                if not cursor.fetchone():
                    cadence_id = f"CAD-{uuid.uuid4().hex[:8].upper()}"
                    cursor.execute("""
                        INSERT INTO renewal_cadences (
                            id, deadline_id, company_id, window_step, target_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                    """, (cadence_id, d_id, comp_id, window_step, due_at_str[:10], now_str))

                    actions_taken.append({
                        "deadline_id": d_id,
                        "company_id": comp_id,
                        "window_step": window_step,
                        "days_delta": days_delta,
                        "course": course_doc
                    })

        self.conn.commit()
        return actions_taken

    def complete_renewal(self, deadline_id: str, new_order_id: str) -> dict:
        """
        Quando un rinnovo viene acquistato:
        1. Segna la vecchia deadline RENEWED.
        2. Genera una nuova deadline proiettata nel futuro (ora + validity_years).
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT company_id, course_or_doc, validity_years FROM compliance_deadlines WHERE id = ?", (deadline_id,))
        record = cursor.fetchone()
        if not record:
            raise ValueError(f"Deadline {deadline_id} non trovata.")

        comp_id, course_doc, validity_years = record
        now = datetime.now()
        new_due = now + timedelta(days=365 * validity_years)
        now_str = now.isoformat()
        new_due_str = new_due.isoformat()

        # 1. Update old deadline
        cursor.execute("UPDATE compliance_deadlines SET status = 'RENEWED' WHERE id = ?", (deadline_id,))

        # 2. Insert new future deadline
        new_deadline_id = f"DLINE-{uuid.uuid4().hex[:8].upper()}"
        cursor.execute("""
            INSERT INTO compliance_deadlines (
                id, company_id, course_or_doc, completed_at, validity_years,
                renewal_due_at, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (new_deadline_id, comp_id, course_doc, now_str, validity_years, new_due_str, now_str))

        # Update renewal cadences status to CONVERTED
        cursor.execute("UPDATE renewal_cadences SET status = 'CONVERTED' WHERE deadline_id = ?", (deadline_id,))

        self.conn.commit()

        emit_event("RENEWAL_COMPLETED", {
            "old_deadline_id": deadline_id,
            "new_deadline_id": new_deadline_id,
            "new_due_date": new_due_str,
            "order_id": new_order_id
        }, self.conn)

        return {
            "old_deadline_id": deadline_id,
            "new_deadline_id": new_deadline_id,
            "new_renewal_due_at": new_due_str,
            "status": "RENEWED"
        }

    # =========================================================================
    # 3. RECON81 (CICLO DI RICONCILIAZIONE NOTTURNO INTEGRITY AUDIT)
    # =========================================================================
    def run_reconciliation_audit(self) -> dict:
        """Verifica la coerenza contabile tra ordini, pagamenti e cash ledger."""
        cursor = self.conn.cursor()
        now_str = datetime.now().isoformat()

        cursor.execute("SELECT order_id, amount_gross, commission_earned, commission_received, status FROM revenue_ledger")
        all_orders = cursor.fetchall()

        orders_checked = len(all_orders)
        commissions_checked = 0
        mismatches = []

        for ord_id, gross, comm_earned, comm_received, st in all_orders:
            commissions_checked += 1
            if st == 'PAID':
                # Check 1: deve esistere transazione SETTLED
                cursor.execute("SELECT status FROM payment_transactions WHERE order_id = ? AND status = 'SETTLED'", (ord_id,))
                if not cursor.fetchone():
                    mismatches.append({"order_id": ord_id, "error": "PAID_STATUS_WITHOUT_SETTLED_PAYMENT"})

                # Check 2: se commission_received > 0, deve esistere una voce riconciliata in cash_ledger
                if comm_received > 0:
                    cursor.execute("""
                        SELECT is_reconciled FROM cash_ledger
                        WHERE order_id = ? AND entry_type = 'COMMISSION_RECEIVED' AND is_reconciled = 1
                    """, (ord_id,))
                    if not cursor.fetchone():
                        mismatches.append({"order_id": ord_id, "error": "COMMISSION_RECEIVED_WITHOUT_RECONCILIATION_REF"})

        audit_status = "BALANCED" if len(mismatches) == 0 else "DISCREPANCY_DETECTED"
        rec_id = f"REC-{uuid.uuid4().hex[:8].upper()}"

        cursor.execute("""
            INSERT INTO revenue_reconciliations (
                id, cycle_date, orders_checked, commissions_checked, mismatches_count,
                quarantined_count, status, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rec_id, now_str[:10], orders_checked, commissions_checked, len(mismatches),
              len(mismatches), audit_status, json.dumps(mismatches), now_str))

        self.conn.commit()

        return {
            "reconciliation_id": rec_id,
            "status": audit_status,
            "orders_checked": orders_checked,
            "mismatches_count": len(mismatches),
            "mismatches": mismatches
        }

    # =========================================================================
    # 4. PROFIT81 & GOAL ENGINE (€1M/ANNO PACING & SCENARI)
    # =========================================================================
    def get_goal_pacing_and_forecast(self) -> dict:
        """Calcola il bilancio entrate, margini e andamento rispetto all'obiettivo di €1.000.000/anno."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COALESCE(SUM(amount_gross), 0.0) as gross_revenue,
                COALESCE(SUM(commission_earned), 0.0) as total_comm_earned,
                COALESCE(SUM(commission_received), 0.0) as total_comm_received,
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) as paid_orders
            FROM revenue_ledger
        """)
        row = cursor.fetchone()
        gross_rev = row[0]
        comm_earned = row[1]
        comm_received = row[2]
        total_orders = row[3]
        paid_orders = row[4] or 0

        # Pacing giornaliero
        avg_daily_actual = gross_rev / max(1, total_orders) * (paid_orders / max(1, total_orders)) * 5  # proxy run rate
        daily_gap = DAILY_REVENUE_TARGET - avg_daily_actual

        scenarios = {
            "downside": {
                "label": "DOWNSIDE (Conv 0.5%, Carrello €180)",
                "expected_30d": round(0.005 * 1000 * 180 * 30 / 7, 2),
                "expected_365d": round(0.005 * 1000 * 180 * 365 / 7, 2),
                "confidence": 0.90
            },
            "base": {
                "label": "BASE (Conv 1.5%, Carrello €250)",
                "expected_30d": round(0.015 * 1000 * 250 * 30 / 7, 2),
                "expected_365d": round(0.015 * 1000 * 250 * 365 / 7, 2),
                "confidence": 0.75
            },
            "upside": {
                "label": "UPSIDE (Conv 3.0%, Carrello €350)",
                "expected_30d": round(0.030 * 1000 * 350 * 30 / 7, 2),
                "expected_365d": round(0.030 * 1000 * 350 * 365 / 7, 2),
                "confidence": 0.50
            }
        }

        return {
            "target_annual": 1000000.0,
            "target_daily": DAILY_REVENUE_TARGET,
            "gross_revenue": gross_rev,
            "commission_earned": comm_earned,
            "commission_received": comm_received,
            "unreconciled_commission_gap": round(comm_earned - comm_received, 2),
            "paid_orders": paid_orders,
            "total_orders": total_orders,
            "run_rate_daily": round(avg_daily_actual, 2),
            "daily_gap_to_target": round(daily_gap, 2),
            "scenarios": scenarios
        }

if __name__ == "__main__":
    engine = RevenueEngine81()
    pacing = engine.get_goal_pacing_and_forecast()
    print("[REVENUE ENGINE TEST]")
    print(json.dumps(pacing, indent=2))
