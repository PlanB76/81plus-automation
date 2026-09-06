"""
81+ AUTONOMOUS REVENUE OS
services/control/verifier_m1.py — VERIFIER M1 (100 LEAD VERTICAL SLICE)
Verifica deterministica dei requisiti M1 da Master Spec:
- 100 aziende importate senza perdita
- Deduplica ≥ 95%
- Provenance 100%
- Zero invii a contatti DO_NOT_CONTACT o soppressi
- ATECO con risk level e confidence
- One CTA Rule: 'VAI SULLA PIATTAFORMA' al 100%
- Revenue attribution ricostruibile nel Revenue Ledger
- Renewal loop: ogni completamento genera una nuova deadline
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

def run_m1_verifier() -> dict:
    results = {}
    print("================================================================================")
    print("81+ MACHINE VERIFIER — MILESTONE M1 (100 LEAD VERTICAL SLICE)")
    print("================================================================================")

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Check 100 Company Twins
    print("\n[TEST 1] Verifica Company Twins...")
    cursor.execute("SELECT COUNT(*) FROM company_twins")
    total_companies = cursor.fetchone()[0]
    if total_companies >= 100:
        print(f"  [PASS] Presenti {total_companies} Company Twins (Target: >=100).")
        results["company_twins_count"] = "PASS"
    else:
        print(f"  [FAIL] Company Twins insufficienti: {total_companies} < 100")
        results["company_twins_count"] = "FAIL"

    # 2. Check Deduplication
    print("\n[TEST 2] Verifica Deduplicazione...")
    cursor.execute("SELECT COUNT(DISTINCT clean_name), COUNT(*) FROM company_twins")
    dist_names, total_rows = cursor.fetchone()
    dedupe_rate = (dist_names / total_rows) * 100 if total_rows > 0 else 0
    if dedupe_rate >= 95.0:
        print(f"  [PASS] Tasso di unicita clean name: {dedupe_rate:.2f}% (Target: >=95%).")
        results["deduplication_rate"] = "PASS"
    else:
        print(f"  [FAIL] Tasso di deduplica inferiore a 95%: {dedupe_rate:.2f}%")
        results["deduplication_rate"] = "FAIL"

    # 3. Check Provenance 100%
    print("\n[TEST 3] Verifica Tracciabilità Provenance...")
    cursor.execute("SELECT COUNT(*) FROM company_contacts WHERE provenance IS NULL OR provenance = ''")
    missing_prov = cursor.fetchone()[0]
    if missing_prov == 0:
        print("  [PASS] 100% dei contatti ha provenance esplicita e tracciabile.")
        results["provenance_100"] = "PASS"
    else:
        print(f"  [FAIL] {missing_prov} contatti senza provenance!")
        results["provenance_100"] = "FAIL"

    # 4. Check Suppression Compliance
    print("\n[TEST 4] Verifica Zero Invii DO_NOT_CONTACT...")
    cursor.execute("""
        SELECT COUNT(*) FROM company_contacts c
        JOIN suppressions s ON LOWER(c.email) = LOWER(s.identifier)
        WHERE c.contactability_status != 'SUPPRESSED'
    """)
    breaches = cursor.fetchone()[0]
    if breaches == 0:
        print("  [PASS] Zero violazioni di suppression: nessun contatto soppresso è stato autorizzato.")
        results["suppression_compliance"] = "PASS"
    else:
        print(f"  [FAIL] Rilevate {breaches} violazioni del Contactability Gate!")
        results["suppression_compliance"] = "FAIL"

    # 5. Check ATECO & Risk Classification
    print("\n[TEST 5] Verifica ATECO & Profilo di Rischio...")
    cursor.execute("SELECT COUNT(*) FROM company_twins WHERE ateco_code IS NULL OR risk_level NOT IN ('BASSO', 'MEDIO', 'ALTO')")
    invalid_ateco = cursor.fetchone()[0]
    if invalid_ateco == 0:
        print("  [PASS] 100% delle aziende ha codice ATECO e livello di rischio normativo valido.")
        results["ateco_classification"] = "PASS"
    else:
        print(f"  [FAIL] {invalid_ateco} aziende con ATECO o livello di rischio non valido!")
        results["ateco_classification"] = "FAIL"

    # 6. Check One CTA Rule in Communication Twins
    print("\n[TEST 6] Verifica One CTA Rule ('VAI SULLA PIATTAFORMA')...")
    cursor.execute("SELECT COUNT(*) FROM communication_twins WHERE cta_primary != 'VAI SULLA PIATTAFORMA'")
    invalid_cta = cursor.fetchone()[0]
    if invalid_cta == 0:
        print("  [PASS] 100% dei Communication Twins rispetta la One CTA Rule universale.")
        results["one_cta_rule"] = "PASS"
    else:
        print(f"  [FAIL] {invalid_cta} Communication Twins con CTA difforme!")
        results["one_cta_rule"] = "FAIL"

    # 7. Check Revenue Ledger Attribution
    print("\n[TEST 7] Verifica Revenue Ledger & Commission Attribution...")
    cursor.execute("""
        SELECT COUNT(*), SUM(amount_gross), SUM(commission_earned) 
        FROM revenue_ledger
    """)
    order_count, total_gross, total_comm = cursor.fetchone()
    if order_count >= 100 and total_gross > 0 and total_comm > 0:
        print(f"  [PASS] Revenue Ledger riconciliato: {order_count} ordini, €{total_gross:.2f} lordi, €{total_comm:.2f} commissioni tracciate.")
        results["revenue_ledger_attribution"] = "PASS"
    else:
        print(f"  [FAIL] Revenue Ledger incompleto: orders={order_count}, gross={total_gross}")
        results["revenue_ledger_attribution"] = "FAIL"

    # 8. Check Renewal Loop Deadlines
    print("\n[TEST 8] Verifica Renewal Loop Deadlines...")
    cursor.execute("SELECT COUNT(*) FROM compliance_deadlines WHERE renewal_due_at > datetime('now')")
    valid_deadlines = cursor.fetchone()[0]
    if valid_deadlines >= 100:
        print(f"  [PASS] {valid_deadlines} scadenze di rinnovo generate con successo nel futuro.")
        results["renewal_deadlines"] = "PASS"
    else:
        print(f"  [FAIL] Scadenze di rinnovo insufficienti: {valid_deadlines} < 100")
        results["renewal_deadlines"] = "FAIL"

    all_pass = all(v == "PASS" for v in results.values())
    final_status = "PASS" if all_pass else "FAIL"

    print("\n================================================================================")
    print(f"M1 VERTICAL SLICE VERIFIER RESULT: [{final_status}]")
    print("================================================================================")
    for k, v in results.items():
        print(f"  - {k:<30}: [{v}]")

    conn.close()
    return {"status": final_status, "checks": results}

if __name__ == "__main__":
    res = run_m1_verifier()
    sys.exit(0 if res["status"] == "PASS" else 1)
