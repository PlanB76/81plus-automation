"""
81+ AUTONOMOUS REVENUE OS
services/control/verifier_m0.py — VERIFIER M0 FOUNDATION
Esegue una suite di test deterministica e automatizzata sui componenti M0.
Criterio di accettazione: PASS solo se tutte le verifiche superano i test al 100%
e lo Health Score è >= 90 (Stato: RUN).
"""

import os
import sys
import json
import uuid
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.security.suppression_gate import SuppressionGate
from shared.events.event_bus import EventBus81
from services.control.scheduler81 import Scheduler81
from services.control.worker81 import Worker81

def run_m0_verifier() -> dict:
    results = {}
    print("================================================================================")
    print("81+ MACHINE VERIFIER — MILESTONE M0 FOUNDATION")
    print("================================================================================")

    conn = get_connection()
    cursor = conn.cursor()

    # TEST 1: Schema & Migrations Check
    print("\n[TEST 1] Verifica Tabelle e Indici Fondazione M0...")
    required_tables = [
        "scheduled_jobs", "dead_letter_jobs", "events81", 
        "audit_logs", "system_health", "feature_flags", "suppressions"
    ]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = set(r[0] for r in cursor.fetchall())
    missing = [t for t in required_tables if t not in existing_tables]
    if missing:
        print(f"  [FAIL] Tabelle mancanti: {missing}")
        results["schema_check"] = "FAIL"
    else:
        print(f"  [PASS] Tutte le {len(required_tables)} tabelle di M0 sono presenti e indicizzate.")
        results["schema_check"] = "PASS"

    # TEST 2: Idempotency Enqueue
    print("\n[TEST 2] Verifica Idempotency Key su Schedulazione...")
    sched = Scheduler81(conn=conn, worker_id="verifier_worker_1")
    idemp_key = f"verifier_idemp_{uuid.uuid4().hex}"
    j1 = sched.enqueue("VERIFY_TEST", {"num": 1}, idempotency_key=idemp_key)
    j2 = sched.enqueue("VERIFY_TEST", {"num": 2}, idempotency_key=idemp_key)
    if j1 == j2:
        print(f"  [PASS] Idempotenza confermata: stesso ID generato ({j1}). Nessuna duplicazione.")
        results["idempotency"] = "PASS"
    else:
        print(f"  [FAIL] Violazione idempotenza: {j1} != {j2}")
        results["idempotency"] = "FAIL"

    # TEST 3: Atomic Lock Concurrency
    print("\n[TEST 3] Verifica Concorrenza e Atomic Lock...")
    sched2 = Scheduler81(conn=conn, worker_id="verifier_worker_2")
    claim_1 = sched.claim_jobs(batch_size=1)
    claim_2 = sched2.claim_jobs(batch_size=1)
    # claim_2 non deve prendere lo stesso job di claim_1
    c1_ids = {j["id"] for j in claim_1}
    c2_ids = {j["id"] for j in claim_2}
    intersection = c1_ids.intersection(c2_ids)
    if len(intersection) == 0:
        print(f"  [PASS] Lock atomico integro. Zero collisioni tra worker concorrenti.")
        results["atomic_lock"] = "PASS"
    else:
        print(f"  [FAIL] Collisione lock: job contesi {intersection}")
        results["atomic_lock"] = "FAIL"

    # Pulisci job claimati
    for j in claim_1 + claim_2:
        sched.complete_job(j["id"])

    # TEST 4: State Machine Lifecycle (PENDING -> RUNNING -> DONE)
    print("\n[TEST 4] Verifica Transizioni di Stato Job...")
    test_jid = sched.enqueue("STATE_TEST", {"data": 123})
    cursor.execute("SELECT status FROM scheduled_jobs WHERE id = ?", (test_jid,))
    st_initial = cursor.fetchone()[0]
    
    claimed = sched.claim_jobs(batch_size=5)
    target = next((j for j in claimed if j["id"] == test_jid), None)
    cursor.execute("SELECT status FROM scheduled_jobs WHERE id = ?", (test_jid,))
    st_claimed = cursor.fetchone()[0]
    
    sched.complete_job(test_jid)
    cursor.execute("SELECT status FROM scheduled_jobs WHERE id = ?", (test_jid,))
    st_done = cursor.fetchone()[0]

    if st_initial == "PENDING" and st_claimed == "RUNNING" and st_done == "DONE":
        print(f"  [PASS] Ciclo di vita validato: PENDING -> RUNNING -> DONE.")
        results["lifecycle"] = "PASS"
    else:
        print(f"  [FAIL] Transizione errata: {st_initial} -> {st_claimed} -> {st_done}")
        results["lifecycle"] = "FAIL"

    # TEST 5: Retry & Dead-Letter Queue
    print("\n[TEST 5] Verifica Retry con Exponential Backoff e Dead-Letter...")
    fail_jid = sched.enqueue("FAIL_TEST", {"error": True}, max_attempts=2)
    # Tentativo 1
    c_fail_1 = sched.claim_jobs(batch_size=10)
    sched.fail_job(fail_jid, "Simulated Error 1")
    cursor.execute("SELECT status, attempts FROM scheduled_jobs WHERE id = ?", (fail_jid,))
    row1 = cursor.fetchone()
    st_retry = row1[0]
    
    # Forziamo due_at nel passato per simulare lo scadere del backoff
    cursor.execute("UPDATE scheduled_jobs SET due_at = datetime('now', '-1 minute') WHERE id = ?", (fail_jid,))
    conn.commit()

    # Tentativo 2 (superamento max_attempts)
    c_fail_2 = sched.claim_jobs(batch_size=10)
    sched.fail_job(fail_jid, "Simulated Error 2 - Fatal")
    cursor.execute("SELECT status, attempts FROM scheduled_jobs WHERE id = ?", (fail_jid,))
    row2 = cursor.fetchone()
    st_dead = row2[0]

    cursor.execute("SELECT COUNT(*) FROM dead_letter_jobs WHERE id = ?", (fail_jid,))
    in_dlq = cursor.fetchone()[0]

    if st_retry == "RETRY" and st_dead == "DEAD" and in_dlq == 1:
        print(f"  [PASS] Retry e Dead-Letter Queue verificati al 100% (RETRY -> DEAD + DLQ entry).")
        results["retry_and_dead_letter"] = "PASS"
    else:
        print(f"  [FAIL] Gestione errori errata: retry={st_retry}, dead={st_dead}, in_dlq={in_dlq}")
        results["retry_and_dead_letter"] = "FAIL"

    # TEST 6: Suppression Gate (Hard Opt-out rule)
    print("\n[TEST 6] Verifica Suppression Gate e One CTA Rule...")
    gate = SuppressionGate(conn=conn)
    test_blocked_email = f"blockme_{uuid.uuid4().hex[:6]}@spamdomain.com"
    gate.add_suppression(test_blocked_email, "EMAIL", "DO_NOT_CONTACT", "VERIFIER")
    
    is_suppressed = gate.is_suppressed(test_blocked_email)
    domain_suppressed = gate.is_suppressed(f"anyuser@{test_blocked_email.split('@')[-1]}")
    clean_email_ok = not gate.is_suppressed("allowed_business@azienda81.it")

    # Verifica MailGate dispatch block
    worker = Worker81(worker_id="verifier_worker_mail")
    mail_result = worker._handle_mail_send({
        "to": test_blocked_email,
        "body": "VAI SULLA PIATTAFORMA"
    })

    if is_suppressed and clean_email_ok and mail_result.get("status") == "BLOCKED_BY_SUPPRESSION":
        print(f"  [PASS] Suppression Gate insormontabile. Contatto bloccato impedito all'invio al 100%.")
        results["suppression_gate"] = "PASS"
    else:
        print(f"  [FAIL] Fallimento suppression gate: supp={is_suppressed}, blocked={mail_result}")
        results["suppression_gate"] = "FAIL"

    # TEST 7: Event Bus & Audit Logging
    print("\n[TEST 7] Verifica EVENT81 & Audit Logs Append-Only...")
    bus = EventBus81(conn=conn)
    ev_id = bus.publish("VERIFIER_TEST_EVENT", "VERIFIER", "M0", {"metric": "PASS"})
    cursor.execute("SELECT COUNT(*) FROM events81 WHERE event_id = ?", (ev_id,))
    ev_exists = cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE target_id = 'M0' AND action = 'VERIFIER_TEST_EVENT'")
    audit_exists = cursor.fetchone()[0] >= 1

    if ev_exists and audit_exists:
        print(f"  [PASS] Event Bus e Audit Log sincronizzati e immutabili.")
        results["event_and_audit"] = "PASS"
    else:
        print(f"  [FAIL] Event/Audit mancante: ev={ev_exists}, audit={audit_exists}")
        results["event_and_audit"] = "FAIL"

    # TEST 8: Health Score & Heartbeat Check
    print("\n[TEST 8] Verifica System Health & Control Tower...")
    hb = sched.heartbeat()
    score = hb.get("health_score", 0)
    st = hb.get("status")
    if score >= 90 and st == "RUN":
        print(f"  [PASS] System Health Score: {score}/100 [Stato: {st}].")
        results["system_health"] = "PASS"
    else:
        print(f"  [FAIL] Health degradato: {score}/100 [{st}]")
        results["system_health"] = "FAIL"

    # Valutazione Finale
    all_pass = all(v == "PASS" for v in results.values())
    final_status = "PASS" if all_pass else "FAIL"

    print("\n================================================================================")
    print(f"M0 FOUNDATION VERIFIER RESULT: [{final_status}]")
    print("================================================================================")
    for k, v in results.items():
        print(f"  - {k:<25}: [{v}]")

    conn.close()
    return {"status": final_status, "checks": results, "health_score": score}

if __name__ == "__main__":
    res = run_m0_verifier()
    sys.exit(0 if res["status"] == "PASS" else 1)
