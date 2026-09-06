"""
81+ AUTONOMOUS REVENUE OS — VERIFIER MILESTONE M7
Verifica automatizzata e deterministica di M7: LEAD FACTORY H24 & SOURCE REGISTRY.
Criteri PASS/FAIL:
1. Source Policy Gate: blocco immediato per fonti con stato QUARANTINE o FORBIDDEN.
2. Esecuzione pipeline su fonte APPROVED: normalize -> dedupe -> ATECO -> contactability.
3. Inserimento automatico dei nuovi lead nella coda scheduled_jobs per il worker autonomo.
4. Tracciamento source_economics e metriche di provenienza.
5. Rate Limiting e quote giornaliere censite nel registro fonti.
"""

import sys
import os
import sqlite3
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.discover.lead_factory_h24 import LeadFactoryH24Engine, SourcePolicyQuarantineError

def run_verifier_m7() -> bool:
    print("=" * 80)
    print("81+ MACHINE VERIFIER — MILESTONE M7 (LEAD FACTORY H24 & SOURCE REGISTRY)")
    print("=" * 80)

    conn = get_connection()
    engine = LeadFactoryH24Engine(conn)
    cursor = conn.cursor()

    results = {}

    # -------------------------------------------------------------------------
    # TEST 1: Source Policy Gate (Quarantena e Divieto Rigorosi)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Verifica Source Policy Gate (Blocco Quarantena/Divieto)...")
    quarantine_caught = False
    forbidden_caught = False

    try:
        engine.run_source_policy_check("SRC_CAMERA_COMM_UNVERIFIED")
    except SourcePolicyQuarantineError:
        quarantine_caught = True

    try:
        engine.run_source_policy_check("SRC_ALBO_PROFESSIONALE_RESTRICTED")
    except SourcePolicyQuarantineError:
        forbidden_caught = True

    approved_check = engine.run_source_policy_check("SRC_OPEN_DATA_VENETO")

    if quarantine_caught and forbidden_caught and approved_check["status"] == "APPROVED":
        results["source_policy_gate"] = "PASS"
        print("  [PASS] Guardrail legale operativo: fonti non verificate o vietate bloccate al 100%. Fonte approvata autorizzata.")
    else:
        results["source_policy_gate"] = "FAIL"
        print(f"  [FAIL] Violazione gate: quarantine={quarantine_caught}, forbidden={forbidden_caught}")

    # -------------------------------------------------------------------------
    # TEST 2: Esecuzione Batch Acquisizione Fonte Approvata
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verifica Acquisizione Batch da Fonte Approvata...")
    test_token = uuid.uuid4().hex[:6]
    test_raw_leads = [
        {"company_name": f"TERMOIDRAULICA POLO NORD {test_token} SRL", "email": f"polo_nord_{test_token}@termoidraulica.it", "ateco": "43.22.01", "risk": "ALTO", "contact_name": "Davide Polo"},
        {"company_name": f"STUDIO GRAFICO DELTA {test_token} SNC", "email": f"delta_{test_token}@studiodelta.it", "ateco": "74.10.21", "risk": "BASSO", "contact_name": "Laura Delta"},
        {"company_name": "EMAIL NON VALIDA", "email": "senza_chiocciola_dominio", "ateco": "41.20.00", "risk": "ALTO"}  # Deve essere scartata
    ]

    res = engine.execute_acquisition_batch(source_id="SRC_OPEN_DATA_VENETO", raw_leads=test_raw_leads)

    if res["records_valid"] == 2 and res["quarantined"] == 1 and res["status"] == "COMPLETED":
        results["acquisition_execution"] = "PASS"
        print(f"  [PASS] Batch acquisito con successo: 2 record validi inseriti, 1 email invalida quarantenata in {res['duration_sec']}s.")
    else:
        results["acquisition_execution"] = "FAIL"
        print(f"  [FAIL] Risultato inatteso: {res}")

    # -------------------------------------------------------------------------
    # TEST 3: Accodamento Automatico in scheduled_jobs
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Verifica Accodamento in scheduled_jobs...")
    target_email = f"polo_nord_{test_token}@termoidraulica.it"
    cursor.execute("""
        SELECT id, job_type, status, idempotency_key
        FROM scheduled_jobs
        WHERE job_type = 'LEAD_NURTURE_DISPATCH' AND idempotency_key = ?
    """, (f"IDEM-{target_email}",))
    job = cursor.fetchone()

    if job and job[1] == "LEAD_NURTURE_DISPATCH" and job[2] == "PENDING":
        results["scheduled_jobs_enqueue"] = "PASS"
        print(f"  [PASS] Job accodato nel buffer autonomo: {job[0]} (Status: PENDING, Key: {job[3]}).")
    else:
        results["scheduled_jobs_enqueue"] = "FAIL"
        print(f"  [FAIL] Job non trovato nella coda scheduled_jobs.")

    # -------------------------------------------------------------------------
    # TEST 4: Tracciamento Source Economics & Audit Run
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Verifica Tracciamento Source Economics & Audit Runs...")
    cursor.execute("SELECT total_leads_acquired FROM source_economics WHERE source_id = 'SRC_OPEN_DATA_VENETO'")
    econ_leads = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM source_acquisition_runs WHERE source_id = 'SRC_OPEN_DATA_VENETO'")
    runs_count = cursor.fetchone()[0]

    if econ_leads >= 2 and runs_count >= 1:
        results["source_economics_and_audit"] = "PASS"
        print(f"  [PASS] Source Economics aggiornate: {econ_leads} lead acquisiti tracciati su {runs_count} run.")
    else:
        results["source_economics_and_audit"] = "FAIL"
        print(f"  [FAIL] Metriche non aggiornate: econ_leads={econ_leads}, runs={runs_count}")

    # -------------------------------------------------------------------------
    # TEST 5: Rate Limiter & Daily Quotas nel Registro Fonti
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Verifica Rate Limiter & Quote Giornaliere...")
    cursor.execute("SELECT COUNT(*) FROM source_registry WHERE rate_limit_per_min > 0 AND daily_quota > 0")
    rated_sources = cursor.fetchone()[0]

    if rated_sources >= 2:
        results["rate_limiting_and_quotas"] = "PASS"
        print(f"  [PASS] {rated_sources} fonti configurate con rate limits e quote giornaliere nel registro.")
    else:
        results["rate_limiting_and_quotas"] = "FAIL"
        print(f"  [FAIL] Fonti con quote insufficienti: {rated_sources}")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    all_passed = all(status == "PASS" for status in results.values())
    overall_status = "[PASS]" if all_passed else "[FAIL]"
    print(f"M7 LEAD FACTORY H24 VERIFIER RESULT: {overall_status}")
    print("=" * 80)

    for test_name, test_res in results.items():
        print(f"  - {test_name:<38}: [{test_res}]")

    return all_passed

if __name__ == "__main__":
    success = run_verifier_m7()
    sys.exit(0 if success else 1)
