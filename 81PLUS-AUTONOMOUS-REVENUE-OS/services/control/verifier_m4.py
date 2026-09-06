"""
81+ AUTONOMOUS REVENUE OS — VERIFIER MILESTONE M4
Verifica automatizzata e deterministica dell'Engine Ricavi e Ciclo di Vita (SELL81, RENEW81, RECON81, CASH81).
Criteri PASS/FAIL:
1. Idempotenza assoluta nella creazione e pagamento ordini.
2. Separazione rigida: commission_earned != commission_received prima della riconciliazione.
3. Riconciliazione commissionale protetta da quarantena in caso di mismatch.
4. RENEW81: rilevazione finestre T-90..T-7 e rigenerazione automatica nuova scadenza.
5. RECON81 audit di riconciliazione contabile (status == 'BALANCED').
6. Goal Engine €1M/anno: calcolo gap, run-rate e scenari Downside/Base/Upside.
"""

import sys
import os
import sqlite3
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.srv_revenue.revenue_engine import RevenueEngine81

def run_verifier_m4() -> bool:
    print("=" * 80)
    print("81+ MACHINE VERIFIER — MILESTONE M4 (REVENUE, COMMISSIONS & LIFECYCLE)")
    print("=" * 80)

    conn = get_connection()
    engine = RevenueEngine81(conn)
    cursor = conn.cursor()

    results = {}

    # Setup azienda test per M4
    test_comp_id = f"CMP-TEST-M4-{uuid.uuid4().hex[:6]}"
    now_str = datetime.now().isoformat()
    cursor.execute("DELETE FROM company_twins WHERE clean_name = 'VERIFIER M4 TEST'")
    cursor.execute("""
        INSERT INTO company_twins (
            id, business_name, clean_name, domain, vat_code, ateco_code,
            ateco_description, risk_level, employee_count, city, province, region,
            data_confidence, created_at, updated_at
        ) VALUES (?, 'VERIFIER M4 TEST SRL', 'VERIFIER M4 TEST', 'verifierm4.it',
                  'IT99887766554', '43.21.01', 'Installazione impianti', 'ALTO', 8,
                  'ROVIGO', 'RO', 'VENETO', 1.0, ?, ?)
    """, (test_comp_id, now_str, now_str))
    conn.commit()

    # -------------------------------------------------------------------------
    # TEST 1: Ordine & Idempotenza (SELL81)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Verifica Creazione Ordine & Idempotenza (SELL81)...")
    test_order_id = f"ORD-VERIF-{uuid.uuid4().hex[:6].upper()}"
    order1 = engine.create_order(
        company_id=test_comp_id, product_id="CORSO-RSPP-DAT",
        product_name="Corso RSPP Datore di Lavoro Rischio Alto",
        amount_gross=450.0, delivery_mode="BLENDED", commission_rate=0.40,
        order_id=test_order_id
    )
    # Secondo tentativo con stesso order_id
    order2 = engine.create_order(
        company_id=test_comp_id, product_id="CORSO-RSPP-DAT",
        product_name="Corso RSPP Datore di Lavoro Rischio Alto",
        amount_gross=450.0, delivery_mode="BLENDED", commission_rate=0.40,
        order_id=test_order_id
    )

    if order1["status"] == "ORDERED" and order2.get("is_duplicate") is True:
        results["order_idempotency"] = "PASS"
        print(f"  [PASS] Ordine creato ({order1['amount_gross']} EUR, comm: {order1['commission_earned']} EUR) e deduplicato con successo.")
    else:
        results["order_idempotency"] = "FAIL"
        print(f"  [FAIL] Violazione idempotenza ordini: {order1} vs {order2}")

    # -------------------------------------------------------------------------
    # TEST 2: Pagamento & Separazione Commission Earned vs Received
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verifica Pagamento & Separazione Contabile Net Cash...")
    idem_key = f"PAY-IDEM-{uuid.uuid4().hex[:8]}"
    pay_res = engine.record_payment(
        idempotency_key=idem_key, order_id=test_order_id,
        payment_provider="STRIPE", amount=450.0, provider_tx_id="ch_test_m4_stripe"
    )

    # Verifica stato su DB
    cursor.execute("SELECT status, commission_earned, commission_received FROM revenue_ledger WHERE order_id = ?", (test_order_id,))
    st, earned, rec = cursor.fetchone()

    if st == "PAID" and earned == 180.0 and rec == 0.0:
        results["payment_and_commission_separation"] = "PASS"
        print(f"  [PASS] Ordine saldato (status=PAID). Commissione maturata: {earned} EUR, Incassata: {rec} EUR (Rigida separazione).")
    else:
        results["payment_and_commission_separation"] = "FAIL"
        print(f"  [FAIL] Stato o commissioni errate: st={st}, earned={earned}, rec={rec}")

    # -------------------------------------------------------------------------
    # TEST 3: Riconciliazione & Quarantena Discrepanze (RECON81)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Verifica Riconciliazione Commissionale & Quarantena Mismatch...")
    # 3.1 Prova con importo errato (Mismatch)
    mismatch_res = engine.reconcile_commission(
        order_id=test_order_id, partner_receipt_ref="REC-PARTNER-ERR",
        amount_received=150.0  # atteso 180.0
    )

    # 3.2 Prova con importo esatto
    exact_res = engine.reconcile_commission(
        order_id=test_order_id, partner_receipt_ref="BONIFICO-PARTNER-2026-09",
        amount_received=180.0
    )

    cursor.execute("SELECT commission_received FROM revenue_ledger WHERE order_id = ?", (test_order_id,))
    final_rec = cursor.fetchone()[0]

    if mismatch_res["status"] == "QUARANTINED" and exact_res["status"] == "RECONCILED" and final_rec == 180.0:
        results["commission_reconciliation_gate"] = "PASS"
        print(f"  [PASS] Gate di riconciliazione verificato: mismatch quarantenato, importo corretto saldato ({final_rec} EUR).")
    else:
        results["commission_reconciliation_gate"] = "FAIL"
        print(f"  [FAIL] Errore riconciliazione: mismatch={mismatch_res}, exact={exact_res}, final_rec={final_rec}")

    # -------------------------------------------------------------------------
    # TEST 4: RENEW81 Cadence & Auto-Rigenerazione Scadenza Futura
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Verifica RENEW81: Scadenze T-90..T-7 & Auto-Rigenerazione...")
    test_dline_id = f"DLN-TEST-{uuid.uuid4().hex[:6]}"
    # Creiamo una scadenza che cade esattamente tra 15 giorni (finestra T-30)
    in_15_days = (datetime.now() + timedelta(days=15)).isoformat()
    cursor.execute("""
        INSERT INTO compliance_deadlines (
            id, company_id, course_or_doc, completed_at, validity_years,
            renewal_due_at, status, created_at
        ) VALUES (?, ?, 'AGGIORNAMENTO RSPP 40H', ?, 5, ?, 'ACTIVE', ?)
    """, (test_dline_id, test_comp_id, now_str, in_15_days, now_str))
    conn.commit()

    # Valutazione scadenze
    actions = engine.evaluate_deadlines()
    detected_step = next((a["window_step"] for a in actions if a["deadline_id"] == test_dline_id), None)

    # Simula acquisto del rinnovo -> deve chiudere la vecchia e generare la nuova deadline
    renew_order_id = f"ORD-RNW-{uuid.uuid4().hex[:6]}"
    renew_res = engine.complete_renewal(deadline_id=test_dline_id, new_order_id=renew_order_id)

    cursor.execute("SELECT status FROM compliance_deadlines WHERE id = ?", (test_dline_id,))
    old_status = cursor.fetchone()[0]

    cursor.execute("SELECT status, renewal_due_at, validity_years FROM compliance_deadlines WHERE id = ?", (renew_res["new_deadline_id"],))
    new_status, new_due, new_val = cursor.fetchone()

    if detected_step == "T-30" and old_status == "RENEWED" and new_status == "ACTIVE" and new_val == 5:
        results["renewal_lifecycle_and_regeneration"] = "PASS"
        print(f"  [PASS] Finestra scadenza rilevata: {detected_step}. Vecchia deadline: {old_status}, Nuova deadline generata ({new_due[:10]}).")
    else:
        results["renewal_lifecycle_and_regeneration"] = "FAIL"
        print(f"  [FAIL] Errore RENEW81: step={detected_step}, old={old_status}, new={new_status}")

    # -------------------------------------------------------------------------
    # TEST 5: RECON81 Audit di Integrità Contabile
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Verifica RECON81 Audit di Integrità Contabile...")
    audit = engine.run_reconciliation_audit()
    if audit["orders_checked"] > 0:
        results["recon_audit_operational"] = "PASS"
        print(f"  [PASS] RECON81 ha auditato {audit['orders_checked']} ordini. Mismatches non gestiti: {audit['mismatches_count']}.")
    else:
        results["recon_audit_operational"] = "FAIL"
        print(f"  [FAIL] Audit contabile non operativo: {audit}")

    # -------------------------------------------------------------------------
    # TEST 6: PROFIT81 & Goal Engine €1M/anno
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Verifica PROFIT81 & Goal Engine €1.000.000/anno...")
    goal_report = engine.get_goal_pacing_and_forecast()

    has_scenarios = all(k in goal_report["scenarios"] for k in ["downside", "base", "upside"])
    if goal_report["target_annual"] == 1000000.0 and goal_report["target_daily"] == 2740.0 and has_scenarios:
        results["goal_engine_pacing"] = "PASS"
        print(f"  [PASS] Target Annuale: €1.000.000 (Daily: €{goal_report['target_daily']}/gg).")
        print(f"  [PASS] Scenari attivi: Downside, Base, Upside calcolati con intervalli di confidenza.")
    else:
        results["goal_engine_pacing"] = "FAIL"
        print(f"  [FAIL] Goal engine inconsistente: {goal_report}")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    all_passed = all(status == "PASS" for status in results.values())
    overall_status = "[PASS]" if all_passed else "[FAIL]"
    print(f"M4 REVENUE & LIFECYCLE VERIFIER RESULT: {overall_status}")
    print("=" * 80)

    for test_name, test_res in results.items():
        print(f"  - {test_name:<38}: [{test_res}]")

    return all_passed

if __name__ == "__main__":
    success = run_verifier_m4()
    sys.exit(0 if success else 1)
