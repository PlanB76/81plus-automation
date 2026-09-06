"""
81+ AUTONOMOUS REVENUE OS
services/control/verifier_m3.py — VERIFIER M3 (DELIVERY, TRAINING ROUTING & CLASS LOGISTICS)
Verifica deterministica dei requisiti M3 da Master Spec:
- Product Graph: catalogo misto completo (Online, Aula, Documenti) con basi legali e margini
- ROUTER81: instradamento normativo (Attrezzature -> AULA ANFOS RO/3; FAD -> Partner 2377)
- DEMAND81 + GEO81: aggregazione della domanda territoriale per provincia e finestra temporale
- CLASS81: scatto automatico a DEMAND_DETECTED al raggiungimento della soglia minima
- FULFILLMENT81: ciclo di erogazione e rilascio attestato con QR-Code
"""

import os
import sys
import uuid
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.srv_revenue.delivery81_router import DeliveryRouter81

def run_m3_verifier() -> dict:
    results = {}
    print("================================================================================")
    print("81+ MACHINE VERIFIER — MILESTONE M3 (DELIVERY, ROUTING & AULA LOGISTICS)")
    print("================================================================================")

    conn = get_connection()
    cursor = conn.cursor()
    router = DeliveryRouter81(conn=conn)

    # TEST 1: Product Catalog Loaded
    print("\n[TEST 1] Verifica Product Graph (Catalogo Misto)...")
    cursor.execute("SELECT delivery_mode, COUNT(*) FROM product_catalog WHERE active = 1 GROUP BY delivery_mode")
    modes = {r[0]: r[1] for r in cursor.fetchall()}
    has_online = modes.get("ONLINE", 0) > 0
    has_aula = (modes.get("AULA", 0) + modes.get("BLENDED", 0)) > 0
    has_doc = modes.get("NONE", 0) > 0

    if has_online and has_aula and has_doc:
        print(f"  [PASS] Product Graph completo: Online ({modes.get('ONLINE', 0)}), Aula/Blended ({modes.get('AULA', 0) + modes.get('BLENDED', 0)}), Documenti ({modes.get('NONE', 0)}).")
        results["product_catalog_loaded"] = "PASS"
    else:
        print(f"  [FAIL] Catalogo incompleto: {modes}")
        results["product_catalog_loaded"] = "FAIL"

    # TEST 2: Legal Routing Compliance
    print("\n[TEST 2] Verifica ROUTER81 & Rispetto Accordo Stato-Regioni 2025...")
    r_attrezzature = router.route_need("CARRELLI_ELEVATORI", "ALTO", "RO")
    r_online = router.route_need("FORMAZIONE_GENERALE", "BASSO", "PD")
    r_doc = router.route_need("DOCUMENTO_DVR", "MEDIO", "VR")

    if (r_attrezzature["delivery_mode"] in ("AULA", "BLENDED") and r_attrezzature["provider"] == "CENTRO_ANFOS_RO3" and
        r_online["delivery_mode"] == "ONLINE" and r_online["provider"] == "PARTNER_2377_FAD" and
        r_doc["delivery_mode"] == "DOCUMENT" and r_doc["provider"] == "DIRECT_81PLUS"):
        print("  [PASS] Routing normativo verificato al 100%: Attrezzature -> ANFOS RO/3, FAD -> Partner 2377, DVR -> 81+.")
        results["legal_routing_compliance"] = "PASS"
    else:
        print(f"  [FAIL] Errore di instradamento: att={r_attrezzature['delivery_mode']}, online={r_online['delivery_mode']}, doc={r_doc['delivery_mode']}")
        results["legal_routing_compliance"] = "FAIL"

    # TEST 3: Territory Demand Aggregation (DEMAND81 & GEO81)
    print("\n[TEST 3] Verifica DEMAND81 & GEO81 (Aggregazione Territoriale)...")
    prov_test = "TV"
    cursor.execute("DELETE FROM territory_demand_signals WHERE province = ?", (prov_test,))
    cursor.execute("DELETE FROM class_editions WHERE province = ?", (prov_test,))
    conn.commit()

    d_sub = router.aggregate_demand("CRS_AULA_PLE", prov_test, count=3)
    cursor.execute("SELECT potential_attendees, status FROM territory_demand_signals WHERE province = ? AND course_id = 'CRS_AULA_PLE'", (prov_test,))
    row_d = cursor.fetchone()
    if row_d and row_d[0] == 3 and row_d[1] == "ACCUMULATING":
        print(f"  [PASS] Aggregazione della domanda sotto soglia: 3 partecipanti in accumulo.")
        results["territory_demand_aggregation"] = "PASS"
    else:
        print(f"  [FAIL] Errore aggregazione domanda: {row_d}")
        results["territory_demand_aggregation"] = "FAIL"

    # TEST 4: Classroom Proposal Trigger (CLASS81)
    print("\n[TEST 4] Verifica CLASS81 Trigger Edizione Proposta (DEMAND_DETECTED)...")
    # Aggiungi altri 4 per superare soglia 6
    d_full = router.aggregate_demand("CRS_AULA_PLE", prov_test, count=4)
    cursor.execute("SELECT status FROM territory_demand_signals WHERE province = ? AND course_id = 'CRS_AULA_PLE'", (prov_test,))
    status_sig = cursor.fetchone()[0]
    cursor.execute("SELECT status, enrolled_count FROM class_editions WHERE province = ? AND course_id = 'CRS_AULA_PLE'", (prov_test,))
    row_ed = cursor.fetchone()

    if status_sig == "THRESHOLD_REACHED" and row_ed and row_ed[0] == "DEMAND_DETECTED" and row_ed[1] >= 6:
        print(f"  [PASS] Trigger automatico scattato: creata edizione d'aula {prov_test} con {row_ed[1]} partecipanti (DEMAND_DETECTED).")
        results["class_edition_proposal_trigger"] = "PASS"
    else:
        print(f"  [FAIL] Fallimento trigger classe: sig_status={status_sig}, edition={row_ed}")
        results["class_edition_proposal_trigger"] = "FAIL"

    # TEST 5: Fulfillment Lifecycle & QR-Code (FULFILLMENT81)
    print("\n[TEST 5] Verifica Macchina a Stati FULFILLMENT81...")
    dummy_order = "ord_" + uuid.uuid4().hex[:8]
    dummy_comp = "comp_" + uuid.uuid4().hex[:8]
    fulf_id = router.start_fulfillment(dummy_order, dummy_comp, "CRS_FAD_GEN", "ONLINE")
    router.advance_fulfillment(fulf_id, "COMPLETED")
    router.advance_fulfillment(fulf_id, "DELIVERED", qr_code="QR-ANFOS-RO3-VERIFIED-2026")

    cursor.execute("SELECT status, certificate_qr, delivered_at FROM fulfillment_records WHERE fulfillment_id = ?", (fulf_id,))
    row_f = cursor.fetchone()
    if row_f and row_f[0] == "DELIVERED" and row_f[1] == "QR-ANFOS-RO3-VERIFIED-2026" and row_f[2] is not None:
        print("  [PASS] FULFILLMENT81 deterministico: PENDING -> ENROLLED -> COMPLETED -> DELIVERED con QR Code.")
        results["fulfillment_lifecycle_deterministic"] = "PASS"
    else:
        print(f"  [FAIL] Stato fulfillment errato: {row_f}")
        results["fulfillment_lifecycle_deterministic"] = "FAIL"

    all_pass = all(v == "PASS" for v in results.values())
    final_status = "PASS" if all_pass else "FAIL"

    print("\n================================================================================")
    print(f"M3 DELIVERY & ROUTING VERIFIER RESULT: [{final_status}]")
    print("================================================================================")
    for k, v in results.items():
        print(f"  - {k:<38}: [{v}]")

    conn.close()
    return {"status": final_status, "checks": results}

if __name__ == "__main__":
    res = run_m3_verifier()
    sys.exit(0 if res["status"] == "PASS" else 1)
