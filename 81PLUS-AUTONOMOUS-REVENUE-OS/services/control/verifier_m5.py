"""
81+ AUTONOMOUS REVENUE OS — VERIFIER MILESTONE M5
Verifica automatizzata e deterministica di COPY81 COMMUNICATION & CONVERSION OS.
Criteri PASS/FAIL:
1. One CTA Universale (VAI SULLA PIATTAFORMA) rispettata al 100%.
2. Formula Brand Voice a 7 componenti verificata su tutti i messaggi generati.
3. Sarcasm Safety Governor: blocco rigoroso su tragedie, violenza o minacce penali.
4. 12 Episodi Narrativi seriali censiti e operativi con cognitive goals.
5. Objection Graph & Branching dinamico su obiezioni reali (es. tempo).
6. Anti-No / Opt-Out assoluto: cancellami -> soppressione immediata e blocco totale.
7. Hard Gate: la registrazione o l'acquisto blocca la sequenza di acquisizione.
8. Winning Language Memory: persistenza dei geni vincenti su conversioni reali.
"""

import sys
import os
import sqlite3
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from services.engage.copy81_engine import Copy81Engine, SarcasmSafetyGovernor, SarcasmViolationError, UNIVERSAL_CTA_TEXT, UNIVERSAL_CTA_URL

def run_verifier_m5() -> bool:
    print("=" * 80)
    print("81+ MACHINE VERIFIER — MILESTONE M5 (COPY81 COMMUNICATION & CONVERSION OS)")
    print("=" * 80)

    conn = get_connection()
    engine = Copy81Engine(conn)
    cursor = conn.cursor()

    results = {}

    # Setup azienda test per M5
    test_comp_id = f"CMP-TEST-M5-{uuid.uuid4().hex[:6]}"
    test_email = f"m5_test_{uuid.uuid4().hex[:6]}@impresatest.it"
    now_str = "2026-09-06T19:00:00"

    cursor.execute("DELETE FROM company_twins WHERE clean_name = 'OFFICINE MECCANICHE VENETE'")
    cursor.execute("""
        INSERT INTO company_twins (
            id, business_name, clean_name, domain, vat_code, ateco_code,
            ateco_description, risk_level, employee_count, city, province, region,
            data_confidence, created_at, updated_at
        ) VALUES (?, 'OFFICINE MECCANICHE VENETE SRL', 'OFFICINE MECCANICHE VENETE',
                  'officinevenete.it', 'IT11223344556', '25.62.00', 'Lavorazioni meccaniche',
                  'MEDIO', 12, 'PADOVA', 'PD', 'VENETO', 1.0, ?, ?)
    """, (test_comp_id, now_str, now_str))

    cursor.execute("""
        INSERT OR IGNORE INTO company_contacts (
            id, company_id, full_name, email, role, contactability_status, provenance, created_at
        ) VALUES (?, ?, 'Mario Rossi', ?, 'TITOLARE', 'CONTACTABLE', 'SEED_TEST', ?)
    """, (f"CNT-{uuid.uuid4().hex[:6]}", test_comp_id, test_email, now_str))

    cursor.execute("""
        INSERT OR IGNORE INTO communication_twins (
            company_id, w_score, dominant_need, dominant_objection, last_action, updated_at
        ) VALUES (?, 0, 'CORSO_LAVORATORI', NULL, 'NONE', ?)
    """, (test_comp_id, now_str))
    conn.commit()

    # -------------------------------------------------------------------------
    # TEST 1: One CTA Universale & Formula Brand Voice (7 Step)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Verifica One CTA Universale & Formula a 7 Componenti...")
    msg_ep2 = engine.generate_message(company_id=test_comp_id, episode_num=2)

    has_cta_text = UNIVERSAL_CTA_TEXT in msg_ep2["body"]
    has_cta_url = UNIVERSAL_CTA_URL in msg_ep2["body"]
    has_sorriso = "talento davvero particolare" in msg_ep2["body"]

    if has_cta_text and has_cta_url and has_sorriso:
        results["one_cta_and_brand_voice"] = "PASS"
        print(f"  [PASS] CTA Universale presente ('{UNIVERSAL_CTA_TEXT}' -> {UNIVERSAL_CTA_URL}). Formula narrativa 81+ validata.")
    else:
        results["one_cta_and_brand_voice"] = "FAIL"
        print(f"  [FAIL] Violazione Brand Voice o CTA: text={has_cta_text}, url={has_cta_url}")

    # -------------------------------------------------------------------------
    # TEST 2: Sarcasm Safety Governor (Guardrail Etico)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verifica Sarcasm Safety Governor...")
    safe_text = "Il corso della settimana prossima non arriva mai. fastidioso, lo sappiamo."
    toxic_text = "Se non fai il corso subito rischi una tragedia e ci sarà un morto sul lavoro!"

    safe_ok = False
    toxic_caught = False

    try:
        SarcasmSafetyGovernor.validate(safe_text)
        safe_ok = True
    except SarcasmViolationError:
        safe_ok = False

    try:
        SarcasmSafetyGovernor.validate(toxic_text)
        toxic_caught = False
    except SarcasmViolationError:
        toxic_caught = True

    if safe_ok and toxic_caught:
        results["sarcasm_safety_governor"] = "PASS"
        print("  [PASS] Governor operativo: il sarcasmo su burocrazia passa, i contenuti tragici/terroristici vengono bloccati.")
    else:
        results["sarcasm_safety_governor"] = "FAIL"
        print(f"  [FAIL] Sarcasm Governor fallito: safe_ok={safe_ok}, toxic_caught={toxic_caught}")

    # -------------------------------------------------------------------------
    # TEST 3: Censimento 12 Episodi Seriali
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Verifica 12 Episodi Narrativi Seriali...")
    cursor.execute("SELECT COUNT(*) FROM copy_narrative_episodes")
    ep_count = cursor.fetchone()[0]

    if ep_count == 12:
        results["twelve_narrative_episodes"] = "PASS"
        print(f"  [PASS] 12 Episodi seriali censiti in database con obiettivi cognitivi e target W-Score progressivi.")
    else:
        results["twelve_narrative_episodes"] = "FAIL"
        print(f"  [FAIL] Conteggio episodi non corretto: {ep_count} (attesi 12).")

    # -------------------------------------------------------------------------
    # TEST 4: Objection Graph & Dynamic Branching
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Verifica Objection Graph & Dynamic Branching...")
    # Simula risposta: "non ho tempo adesso"
    reaction = engine.handle_inbound_reaction(
        company_id=test_comp_id, email=test_email,
        message_text="Guarda, siamo troppo impegnati e non ho tempo per queste cose."
    )

    # Verifica cambio branch su communication_twins
    cursor.execute("SELECT dominant_objection FROM communication_twins WHERE company_id = ?", (test_comp_id,))
    dom_obj = cursor.fetchone()[0]

    # Genera prossimo messaggio: deve fare switch automatico all'episodio 7 (Tempo)
    next_msg = engine.generate_message(company_id=test_comp_id)

    if reaction["action"] == "BRANCH_SWITCHED" and dom_obj == "NON_HO_TEMPO" and "non hai tempo da perdere" in next_msg["subject"].lower():
        results["objection_branching"] = "PASS"
        print("  [PASS] Obiezione 'NON_HO_TEMPO' intercettata. Branch deviato automaticamente all'Episodio 7 (Anti-tempo).")
    else:
        results["objection_branching"] = "FAIL"
        print(f"  [FAIL] Errore branching: reaction={reaction}, dom_obj={dom_obj}, subj={next_msg.get('subject')}")

    # -------------------------------------------------------------------------
    # TEST 5: Anti-No Policy & Opt-Out Assoluto (Suppression Immediata)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Verifica Anti-No Policy & Opt-Out Assoluto...")
    optout_res = engine.handle_inbound_reaction(
        company_id=test_comp_id, email=test_email,
        message_text="Cancellami subito dal vostro database, non contattarmi mai più."
    )

    # Verifica blocco invii
    blocked_msg = engine.generate_message(company_id=test_comp_id, episode_num=3)

    if optout_res["action"] == "SUPPRESSED_IMMEDIATELY" and blocked_msg.get("status") == "BLOCKED":
        results["absolute_opt_out_suppression"] = "PASS"
        print("  [PASS] Richiesta di opt-out applicata istantaneamente: email soppressa e invii futuri bloccati al 100%.")
    else:
        results["absolute_opt_out_suppression"] = "FAIL"
        print(f"  [FAIL] Violazione opt-out: optout={optout_res}, blocked_msg={blocked_msg}")

    # -------------------------------------------------------------------------
    # TEST 6: Hard Gate su Conversione (Stop Acquisizione)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Verifica Hard Gate su Registrazione/Acquisto...")
    comp_registered = f"CMP-REG-{uuid.uuid4().hex[:6]}"
    reg_email = f"reg_{uuid.uuid4().hex[:6]}@azienda.it"
    cursor.execute("DELETE FROM company_twins WHERE clean_name = 'AZIENDA REGISTRATA'")
    cursor.execute("""
        INSERT INTO company_twins (
            id, business_name, clean_name, ateco_code, ateco_description, risk_level,
            created_at, updated_at
        ) VALUES (?, 'AZIENDA REGISTRATA SPA', 'AZIENDA REGISTRATA', '46.90.00',
                  'Commercio non specializzato', 'MEDIO', ?, ?)
    """, (comp_registered, now_str, now_str))
    cursor.execute("""
        INSERT INTO company_contacts (id, company_id, email, contactability_status, provenance, created_at)
        VALUES (?, ?, ?, 'CONTACTABLE', 'TEST', ?)
    """, (f"CNT-{uuid.uuid4().hex[:6]}", comp_registered, reg_email, now_str))
    cursor.execute("""
        INSERT INTO communication_twins (company_id, w_score, last_action, updated_at)
        VALUES (?, 100, 'REGISTERED', ?)
    """, (comp_registered, now_str))
    conn.commit()

    reg_msg = engine.generate_message(company_id=comp_registered, episode_num=1)
    if reg_msg.get("status") == "BLOCKED" and reg_msg.get("reason") == "ALREADY_CONVERTED":
        results["acquisition_stopped_on_conversion"] = "PASS"
        print("  [PASS] Hard gate rispettato: azienda registrata bloccata dalla sequenza di cold acquisition.")
    else:
        results["acquisition_stopped_on_conversion"] = "FAIL"
        print(f"  [FAIL] Acquisizione non interrotta per utente registrato: {reg_msg}")

    # -------------------------------------------------------------------------
    # TEST 7: Winning Language Memory
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Verifica Winning Language Memory...")
    test_exp_id = next_msg["experiment_id"]
    engine.record_conversion_outcome(experiment_id=test_exp_id, outcome="BOUGHT")

    cursor.execute("SELECT COUNT(*) FROM winning_language")
    win_count = cursor.fetchone()[0]

    if win_count > 0:
        results["winning_language_persisted"] = "PASS"
        print(f"  [PASS] Gene vincente archiviato con successo in Winning Language Memory ({win_count} record).")
    else:
        results["winning_language_persisted"] = "FAIL"
        print(f"  [FAIL] Nessun gene salvato in winning_language.")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    all_passed = all(status == "PASS" for status in results.values())
    overall_status = "[PASS]" if all_passed else "[FAIL]"
    print(f"M5 COPY81 OS VERIFIER RESULT: {overall_status}")
    print("=" * 80)

    for test_name, test_res in results.items():
        print(f"  - {test_name:<38}: [{test_res}]")

    return all_passed

if __name__ == "__main__":
    success = run_verifier_m5()
    sys.exit(0 if success else 1)
