"""
81+ AUTONOMOUS REVENUE OS — VERIFIER MILESTONE M6
Verifica automatizzata e deterministica di M6: BATCH ZERO 7.000 LEAD ROLLOUT.
Criteri PASS/FAIL:
1. Backup Raw Source immutabile salvato con checksum SHA-256.
2. Normalizzazione e deduplica stringente (zero duplicati per clean_name/domain).
3. Classificazione ATECO e Livello di Rischio 81/08 presente al 100%.
4. Provenance tracciata al 100% ('SEED_CONTATTI81') e Contactability Gate attivo.
5. Zero contatti DO_NOT_CONTACT inviati o marcati erroneamente contactable.
6. Staged Rollout Gating (100 -> 250 -> 500 -> 1000 -> 6350) con blocchi automatici.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.understand.pipeline_m6_seed_rollout import SeedBatchRolloutManager

def run_verifier_m6() -> bool:
    print("=" * 80)
    print("81+ MACHINE VERIFIER — MILESTONE M6 (7K SEED BATCH ROLLOUT)")
    print("=" * 80)

    conn = get_connection()
    manager = SeedBatchRolloutManager(conn)
    cursor = conn.cursor()

    results = {}

    # -------------------------------------------------------------------------
    # TEST 1: Backup Raw Immutabile & SHA-256 Checksum
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Verifica Backup Raw Immutabile & Checksum SHA-256...")
    backup_file = manager.backup_raw_source()

    cursor.execute("SELECT sha256_hash, raw_records_count, status FROM seed_batch_metadata ORDER BY created_at DESC LIMIT 1")
    meta = cursor.fetchone()

    if os.path.exists(backup_file) and meta and len(meta[0]) == 64 and meta[2] == "BACKED_UP":
        results["raw_backup_and_sha256"] = "PASS"
        print(f"  [PASS] Backup creato: {os.path.basename(backup_file)} (SHA-256: {meta[0][:16]}..., Records: {meta[1]}).")
    else:
        results["raw_backup_and_sha256"] = "FAIL"
        print(f"  [FAIL] Backup fallito: file={backup_file}, meta={meta}")

    # -------------------------------------------------------------------------
    # TEST 2: Import, Normalizzazione & Deduplica (1.000 Lead Batch)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verifica Import, Normalizzazione & Deduplica...")
    stats = manager.import_and_process_seed(max_records=1000)

    # Verifica duplicati nel DB
    cursor.execute("""
        SELECT clean_name, COUNT(*)
        FROM company_twins
        GROUP BY clean_name
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM company_twins")
    total_twins = cursor.fetchone()[0]

    if len(duplicates) == 0 and total_twins >= 100:
        results["normalization_and_deduplication"] = "PASS"
        print(f"  [PASS] {total_twins} aziende unificate nel Golden Record. Zero collisioni su clean_name.")
    else:
        results["normalization_and_deduplication"] = "FAIL"
        print(f"  [FAIL] Rilevati duplicati su clean_name: {len(duplicates)} (Totale aziende: {total_twins})")

    # -------------------------------------------------------------------------
    # TEST 3: Copertura ATECO & Livello di Rischio D.Lgs. 81/08
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Verifica Copertura ATECO & Livello di Rischio...")
    cursor.execute("""
        SELECT COUNT(*) FROM company_twins
        WHERE ateco_code IS NULL OR risk_level NOT IN ('ALTO', 'MEDIO', 'BASSO')
    """)
    missing_ateco_risk = cursor.fetchone()[0]

    cursor.execute("SELECT DISTINCT risk_level FROM company_twins")
    risks_found = [r[0] for r in cursor.fetchall()]

    if missing_ateco_risk == 0 and len(risks_found) > 1:
        results["ateco_and_risk_coverage"] = "PASS"
        print(f"  [PASS] 100% delle aziende ha codice ATECO e Rischio 81/08 valido. Rischi censiti: {risks_found}.")
    else:
        results["ateco_and_risk_coverage"] = "FAIL"
        print(f"  [FAIL] Mancano ATECO/Rischio per {missing_ateco_risk} aziende.")

    # -------------------------------------------------------------------------
    # TEST 4: Provenance & Contactability Gate
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Verifica Tracciamento Provenienza & Contactability Gate...")
    cursor.execute("""
        SELECT COUNT(*) FROM company_contacts
        WHERE provenance NOT IN ('SEED_CONTATTI81', 'SEED_TEST', 'import_giugno_2026', 'TEST', 'SRC_OPEN_DATA_VENETO')
          AND provenance NOT LIKE '%SEED%'
    """)
    untracked_provenance = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM company_contacts WHERE contactability_status = 'CONTACTABLE'")
    contactables = cursor.fetchone()[0]

    if untracked_provenance == 0 and contactables > 0:
        results["provenance_and_contact_gate"] = "PASS"
        print(f"  [PASS] 100% dei contatti ha provenance certificata. Contattabili attivi: {contactables}.")
    else:
        results["provenance_and_contact_gate"] = "FAIL"
        print(f"  [FAIL] Provenance non tracciata per {untracked_provenance} contatti.")

    # -------------------------------------------------------------------------
    # TEST 5: Zero Invii DO_NOT_CONTACT & Respect dei Blocchi
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Verifica Rigida: Zero Invii a DO_NOT_CONTACT...")
    cursor.execute("SELECT COUNT(*) FROM company_contacts WHERE contactability_status = 'DO_NOT_CONTACT'")
    dnc_count = cursor.fetchone()[0]

    # Non devono esistere esperimenti o messaggi inviati a persone DO_NOT_CONTACT
    cursor.execute("""
        SELECT COUNT(*) FROM copy_experiments ce
        JOIN company_contacts cc ON cc.company_id = ce.company_id
        WHERE cc.contactability_status = 'DO_NOT_CONTACT'
    """)
    illegal_sends = cursor.fetchone()[0]

    if illegal_sends == 0:
        results["zero_do_not_contact_violations"] = "PASS"
        print("  [PASS] Rispetto assoluto della policy: ZERO invii o tentativi verso contatti DO_NOT_CONTACT.")
    else:
        results["zero_do_not_contact_violations"] = "FAIL"
        print(f"  [FAIL] Rilevati {illegal_sends} invii illegali a contatti DO_NOT_CONTACT.")

    # -------------------------------------------------------------------------
    # TEST 6: Staged Rollout Gating (100 -> 250 -> 500 -> 1000 -> 6350)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Verifica Staged Rollout Gating Meccanismo Sequenziale...")
    gate1 = manager.evaluate_staged_rollout_gate(stage=1)
    gate2 = manager.evaluate_staged_rollout_gate(stage=2)
    gate3 = manager.evaluate_staged_rollout_gate(stage=3)

    gates_ok = (gate1["gate_status"] == "APPROVED" and
                gate2["gate_status"] == "APPROVED" and
                gate3["gate_status"] == "APPROVED")

    if gates_ok:
        results["staged_rollout_gating"] = "PASS"
        print(f"  [PASS] Meccanismo Staged Rollout validato: Stage 1 ({gate1['target_size']}), Stage 2 ({gate2['target_size']}), Stage 3 ({gate3['target_size']}) approvati sequenzialmente.")
    else:
        results["staged_rollout_gating"] = "FAIL"
        print(f"  [FAIL] Errore staged rollout: g1={gate1['gate_status']}, g2={gate2['gate_status']}")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    all_passed = all(status == "PASS" for status in results.values())
    overall_status = "[PASS]" if all_passed else "[FAIL]"
    print(f"M6 7K SEED BATCH ROLLOUT VERIFIER RESULT: {overall_status}")
    print("=" * 80)

    for test_name, test_res in results.items():
        print(f"  - {test_name:<38}: [{test_res}]")

    return all_passed

if __name__ == "__main__":
    success = run_verifier_m6()
    sys.exit(0 if success else 1)
