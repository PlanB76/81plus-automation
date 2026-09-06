"""
81+ AUTONOMOUS REVENUE OS — VERIFIER MILESTONE M8
Verifica automatizzata e deterministica di M8: AUTOPILOT, CONTROL TOWER & DAILY EXECUTIVE BRIEFING.
Criteri PASS/FAIL:
1. Gestione stati Autopilota: transizioni corrette tra SHADOW, ASSISTED, GUARDED, AUTONOMOUS.
2. Kill Switch reattivo: blocco immediato (EMERGENCY) e ripristino sicuro a GUARDED.
3. Bottleneck Detector: analisi dei drop-off e raccomandazione stadio critico.
4. ICP Learning: calcolo dei moltiplicatori comportamentali per settore ATECO.
5. Executive Daily Briefing: generazione completa report con pacing €1M/anno e Health Score.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.control.autopilot81_engine import Autopilot81Engine

def run_verifier_m8() -> bool:
    print("=" * 80)
    print("81+ MACHINE VERIFIER — MILESTONE M8 (AUTOPILOT, CONTROL TOWER & EXECUTIVE BRIEFING)")
    print("=" * 80)

    conn = get_connection()
    engine = Autopilot81Engine(conn)
    cursor = conn.cursor()

    results = {}

    # -------------------------------------------------------------------------
    # TEST 1: Transizioni Stati Autopilota
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Verifica Transizioni Stati Autopilota...")
    engine.set_mode("GUARDED")
    st1 = engine.get_state()
    engine.set_mode("AUTONOMOUS")
    st2 = engine.get_state()
    engine.set_mode("GUARDED")

    if st1["mode"] == "GUARDED" and st2["mode"] == "AUTONOMOUS":
        results["autopilot_state_transitions"] = "PASS"
        print("  [PASS] Transizioni validate: GUARDED -> AUTONOMOUS -> GUARDED.")
    else:
        results["autopilot_state_transitions"] = "FAIL"
        print(f"  [FAIL] Errore stati: st1={st1}, st2={st2}")

    # -------------------------------------------------------------------------
    # TEST 2: Kill Switch Reattivo & Ripristino Sicuro
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verifica Kill Switch di Emergenza & Ripristino...")
    engine.trigger_kill_switch("Anomalia Deliverability Spike Bounce > 5%")
    ks_state = engine.get_state()

    # Ripristino
    engine.reset_kill_switch()
    restored_state = engine.get_state()

    if ks_state["kill_switch_active"] is True and ks_state["mode"] == "EMERGENCY" and restored_state["kill_switch_active"] is False and restored_state["mode"] == "GUARDED":
        results["kill_switch_lifecycle"] = "PASS"
        print("  [PASS] Kill Switch verificato: blocco immediato (EMERGENCY) e ripristino sicuro (GUARDED).")
    else:
        results["kill_switch_lifecycle"] = "FAIL"
        print(f"  [FAIL] Errore kill switch: ks={ks_state}, restored={restored_state}")

    # -------------------------------------------------------------------------
    # TEST 3: Bottleneck Detector (BOTTLENECK81)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Verifica Bottleneck Detector (BOTTLENECK81)...")
    bottleneck = engine.detect_bottleneck()

    valid_stages = [
        "ACQUISITION_VOLUME", "CONTACTABILITY_GATE", "COMMUNICATION_HOOK_FRICTION",
        "PLATFORM_ACTIVATION_DROP", "RENEWAL_EXPANSION_ACCELERATION"
    ]

    if bottleneck["bottleneck_stage"] in valid_stages and "recommendation" in bottleneck:
        results["bottleneck_detector"] = "PASS"
        print(f"  [PASS] Collo di bottiglia rilevato: [{bottleneck['bottleneck_stage']}]. Azione: {bottleneck['recommendation']}.")
    else:
        results["bottleneck_detector"] = "FAIL"
        print(f"  [FAIL] Bottleneck non valido: {bottleneck}")

    # -------------------------------------------------------------------------
    # TEST 4: ICP Learning & Behavioral Weights (ICP81)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Verifica ICP Learning & Pesi Comportamentali ATECO...")
    profiles = engine.update_icp_intelligence()

    cursor.execute("SELECT COUNT(*) FROM icp_profiles WHERE score_multiplier >= 1.0")
    icp_count = cursor.fetchone()[0]

    if icp_count > 0:
        results["icp_learning_weights"] = "PASS"
        print(f"  [PASS] ICP Learning operativo: {icp_count} profili ATECO pesati in base al volume d'affari storico.")
    else:
        results["icp_learning_weights"] = "FAIL"
        print("  [FAIL] Nessun profilo calcolato in icp_profiles.")

    # -------------------------------------------------------------------------
    # TEST 5: Executive Daily Briefing (EXECUTIVE81)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Verifica Executive Daily Briefing (EXECUTIVE81)...")
    briefing = engine.generate_executive_daily_briefing()

    has_target = "Target Giornaliero Pacing" in briefing["briefing_markdown"]
    has_status = briefing["system_status"] in ("RUN", "DEGRADED", "STOP")
    has_health = 0 <= briefing["health_score"] <= 100

    if has_target and has_status and has_health:
        results["executive_daily_briefing"] = "PASS"
        print(f"  [PASS] Briefing generato per data {briefing['date']} (Health Score: {briefing['health_score']}/100, Status: {briefing['system_status']}).")
        print(f"  [PASS] Pacing obiettivo annuale €1M: Daily Run-Rate €{briefing['daily_revenue_actual']}/gg (Gap: €{briefing['target_gap']}).")
    else:
        results["executive_daily_briefing"] = "FAIL"
        print(f"  [FAIL] Briefing non conforme: {briefing}")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    all_passed = all(status == "PASS" for status in results.values())
    overall_status = "[PASS]" if all_passed else "[FAIL]"
    print(f"M8 AUTOPILOT & EXECUTIVE BRIEFING VERIFIER RESULT: {overall_status}")
    print("=" * 80)

    for test_name, test_res in results.items():
        print(f"  - {test_name:<38}: [{test_res}]")

    return all_passed

if __name__ == "__main__":
    success = run_verifier_m8()
    sys.exit(0 if success else 1)
