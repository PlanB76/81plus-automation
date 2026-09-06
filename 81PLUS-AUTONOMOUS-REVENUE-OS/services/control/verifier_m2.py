"""
81+ AUTONOMOUS REVENUE OS
services/control/verifier_m2.py — VERIFIER M2 (PLATFORM ACTIVATION & GUIDE81)
Verifica deterministica dei requisiti M2 da Master Spec:
- GUIDE81: Guida Piattaforma completa con tutte le 15 sezioni obbligatorie
- ONE CTA RULE: 100% delle CTA primarie corrispondono rigorosamente a 'VAI SULLA PIATTAFORMA'
- ASSET KNOWLEDGE: Esportazione JSON machine-readable per COPY81 e HTML web per il portale
- ONBOARD81 & ACTIVATION81: Tracciamento eventi e misurazione attivazione distinta da registrazione
- FRICTION81: Calcolo dei tassi di drop-off e diagnostica frizioni
"""

import os
import sys
import json
import sqlite3
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.engage.guide81_engine import get_guide_sections, CTA_UNIVERSALE
from services.engage.funnel_activation81 import FunnelActivationEngine

def run_m2_verifier() -> dict:
    results = {}
    print("================================================================================")
    print("81+ MACHINE VERIFIER — MILESTONE M2 (PLATFORM ACTIVATION & GUIDE81)")
    print("================================================================================")

    conn = get_connection()
    cursor = conn.cursor()

    # TEST 1: Guida Piattaforma Sezioni Complete (15 sezioni)
    print("\n[TEST 1] Verifica Sezioni Obbligatorie Guida Piattaforma...")
    sections = get_guide_sections()
    if len(sections) == 15:
        print(f"  [PASS] Tutte le 15 sezioni canoniche della Guida 81+ sono presenti.")
        results["guide_sections_complete"] = "PASS"
    else:
        print(f"  [FAIL] Sezioni incomplete: {len(sections)} != 15")
        results["guide_sections_complete"] = "FAIL"

    # TEST 2: One CTA Strict Rule
    print("\n[TEST 2] Verifica One CTA Rule Universale ('VAI SULLA PIATTAFORMA')...")
    non_conforming_cta = [s for s in sections if s.get("cta") != CTA_UNIVERSALE]
    if len(non_conforming_cta) == 0:
        print(f"  [PASS] 100% delle sezioni rispetta la One CTA Rule: '{CTA_UNIVERSALE}'.")
        results["one_cta_strict_enforcement"] = "PASS"
    else:
        print(f"  [FAIL] {len(non_conforming_cta)} sezioni con CTA non conforme!")
        results["one_cta_strict_enforcement"] = "FAIL"

    # TEST 3: Knowledge Base JSON Export
    print("\n[TEST 3] Verifica File Knowledge Base JSON...")
    kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "platform_guide.json"))
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)
        if kb_data.get("one_cta") == CTA_UNIVERSALE and len(kb_data.get("sections", [])) == 15:
            print(f"  [PASS] File knowledge/platform_guide.json valido e strutturato ({len(kb_data['sections'])} sezioni).")
            results["knowledge_json_exported"] = "PASS"
        else:
            print("  [FAIL] Dati JSON knowledge non conformi.")
            results["knowledge_json_exported"] = "FAIL"
    else:
        print(f"  [FAIL] File {kb_path} non trovato!")
        results["knowledge_json_exported"] = "FAIL"

    # TEST 4: HTML Web Asset Exists
    print("\n[TEST 4] Verifica Asset HTML Web della Guida...")
    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "guida_piattaforma_81plus.html"))
    if os.path.exists(html_path) and os.path.getsize(html_path) > 2000:
        print(f"  [PASS] File HTML Web compilato e pronto per deploy: {html_path} ({os.path.getsize(html_path)} bytes).")
        results["html_web_asset_exists"] = "PASS"
    else:
        print("  [FAIL] Asset HTML mancante o vuoto.")
        results["html_web_asset_exists"] = "FAIL"

    # TEST 5: Active Version in DB
    print("\n[TEST 5] Verifica Versione Guida su DB...")
    cursor.execute("SELECT version_id, is_active FROM platform_guide_versions WHERE is_active = 1")
    row = cursor.fetchone()
    if row:
        print(f"  [PASS] Versione attiva registrata su DB: {row[0]}")
        results["db_guide_version_active"] = "PASS"
    else:
        print("  [FAIL] Nessuna versione attiva trovata in platform_guide_versions.")
        results["db_guide_version_active"] = "FAIL"

    # TEST 6: Funnel Events Tracking
    print("\n[TEST 6] Verifica Tracciamento Eventi Funnel (ONBOARD81)...")
    cursor.execute("SELECT COUNT(*) FROM platform_funnel_events")
    total_events = cursor.fetchone()[0]
    if total_events > 0:
        print(f"  [PASS] Eventi funnel tracciati nel database ({total_events} record).")
        results["funnel_events_tracking"] = "PASS"
    else:
        print("  [FAIL] Nessun evento presente in platform_funnel_events.")
        results["funnel_events_tracking"] = "FAIL"

    # TEST 7: Activation Status Measurement
    print("\n[TEST 7] Verifica Misurazione Attivazione vs Registrazione...")
    engine = FunnelActivationEngine(conn=conn)
    dummy_cid = f"comp_verify_m2_{uuid.uuid4().hex[:6]}"
    dummy_sid = f"sess_verify_m2_{uuid.uuid4().hex[:6]}"
    engine.record_step("REGISTRATION", dummy_sid, dummy_cid)
    st1 = engine.check_activation_status(dummy_cid)
    engine.record_step("ACTIVATION", dummy_sid, dummy_cid)
    st2 = engine.check_activation_status(dummy_cid)
    if st1["registered"] and not st1["activated"] and st2["registered"] and st2["activated"]:
        print("  [PASS] Distinzione tra Registration e Activation verificata correttamente.")
        results["activation_status_measurement"] = "PASS"
    else:
        print("  [FAIL] Errore distinzione registration/activation.")
        results["activation_status_measurement"] = "FAIL"

    # TEST 8: Friction & Drop-off Diagnostics
    print("\n[TEST 8] Verifica Calcolo Frizioni e Drop-off (FRICTION81)...")
    report = engine.compute_friction_metrics()
    if len(report) > 0:
        print(f"  [PASS] Motore FRICTION81 operativo: analizzate {len(report)} transizioni del funnel con diagnosi anomalie.")
        results["friction_diagnostics_calculation"] = "PASS"
    else:
        print("  [FAIL] Nessun dato generato da compute_friction_metrics.")
        results["friction_diagnostics_calculation"] = "FAIL"

    all_pass = all(v == "PASS" for v in results.values())
    final_status = "PASS" if all_pass else "FAIL"

    print("\n================================================================================")
    print(f"M2 PLATFORM ACTIVATION VERIFIER RESULT: [{final_status}]")
    print("================================================================================")
    for k, v in results.items():
        print(f"  - {k:<35}: [{v}]")

    conn.close()
    return {"status": final_status, "checks": results}

if __name__ == "__main__":
    res = run_m2_verifier()
    sys.exit(0 if res["status"] == "PASS" else 1)
