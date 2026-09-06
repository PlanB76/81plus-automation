"""
81+ AUTONOMOUS REVENUE OS — MASTER MACHINE VERIFIER (FULL SUITE END-TO-END)
Esegue l'intero set di verifier deterministici (M0 -> M8):
- M0: Foundation, Event Bus, Scheduler, Queue, Worker, Kill Switches, Suppressions.
- M1: 100 Lead Vertical Slice & Digital Twin.
- M2: Platform Activation, Guide81 Engine & Friction Detector.
- M3: Delivery, Routing (Online/Aula/Documenti), Class Logistics & Fulfillment.
- M4: Revenue Ledger, Commission Separation, Renewal Lifecycle & Recon Audit.
- M5: COPY81 Communication OS, Sarcasm Governor, Brand Voice & Objection Graph.
- M6: 7K Seed Batch Rollout & Staged Gating (100 -> 250 -> 500 -> 1000 -> 6350).
- M7: Lead Factory H24, Source Registry Legal Policies & Source Economics.
- M8: Autopilot Modes, Bottleneck Detector, ICP Learning & Daily Executive Briefing.
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

from services.control.verifier_m0 import run_m0_verifier
from services.control.verifier_m1 import run_m1_verifier
from services.control.verifier_m2 import run_m2_verifier
from services.control.verifier_m3 import run_m3_verifier
from services.control.verifier_m4 import run_verifier_m4
from services.control.verifier_m5 import run_verifier_m5
from services.control.verifier_m6 import run_verifier_m6
from services.control.verifier_m7 import run_verifier_m7
from services.control.verifier_m8 import run_verifier_m8

def run_master_suite() -> bool:
    print("\n" + "#" * 80)
    print(" 81+ AUTONOMOUS COMPLIANCE REVENUE OS — FULL MASTER VERIFICATION SUITE")
    print(" Target Progettuale: €1.000.000/anno | Regola: ZERO MANI | Metodo: SPEC -> VERIFIER")
    print("#" * 80 + "\n")

    milestones = [
        ("M0 — FOUNDATION & CORE SCHEDULER", run_m0_verifier),
        ("M1 — 100 LEAD VERTICAL SLICE & TWIN", run_m1_verifier),
        ("M2 — PLATFORM ACTIVATION & GUIDE81", run_m2_verifier),
        ("M3 — DELIVERY & AULA/ONLINE ROUTING", run_m3_verifier),
        ("M4 — REVENUE, COMMISSIONS & RENEWALS", run_verifier_m4),
        ("M5 — COPY81 COMMUNICATION & CONVERSION OS", run_verifier_m5),
        ("M6 — 7K SEED BATCH ROLLOUT", run_verifier_m6),
        ("M7 — LEAD FACTORY H24 & SOURCE REGISTRY", run_verifier_m7),
        ("M8 — AUTOPILOT, BOTTLENECK & BRIEFING", run_verifier_m8)
    ]

    suite_results = {}
    start_time = time.time()

    for name, verifier_fn in milestones:
        print(f"\n>>> AVVIO VERIFICA: {name}...")
        try:
            res = verifier_fn()
            if isinstance(res, dict):
                passed = res.get("status") == "PASS"
            else:
                passed = bool(res) is True
            suite_results[name] = "PASS" if passed else "FAIL"
        except Exception as e:
            print(f"  [CRITICAL EXCEPTION] {e}")
            suite_results[name] = "FAIL"

    elapsed = round(time.time() - start_time, 2)
    total_milestones = len(milestones)
    passed_count = sum(1 for res in suite_results.values() if res == "PASS")
    health_score = int((passed_count / total_milestones) * 100)

    if health_score >= 90:
        system_status = "RUN"
    elif health_score >= 70:
        system_status = "DEGRADED"
    else:
        system_status = "STOP"

    print("\n" + "=" * 80)
    print(" 81+ MASTER VERIFICATION SUITE — FINAL AUDIT REPORT")
    print("=" * 80)
    for m_name, res in suite_results.items():
        print(f"  - {m_name:<45}: [{res}]")

    print("-" * 80)
    print(f"  Milestones Verificate: {passed_count} / {total_milestones} ({health_score}%)")
    print(f"  Tempo Esecuzione Suite: {elapsed} secondi")
    print(f"  SYSTEM STATUS: [{system_status}] (Score: {health_score}/100)")
    print("=" * 80 + "\n")

    return health_score == 100

if __name__ == "__main__":
    all_passed = run_master_suite()
    sys.exit(0 if all_passed else 1)
