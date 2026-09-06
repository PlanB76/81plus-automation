"""
81PLUS-AUTONOMOUS-REVENUE-OS
simulation_end_to_end_pipeline.py — Simulazione Integrale End-to-End di Tutte le Pipeline

Traccia completa dell'esperienza:
1. FASE 1: SCRAPING NOTTURNO & CATALOGAZIONE ATECO (Registrazione nel DB)
2. FASE 2: PRIVACY GATE L1 -> L3 & ASSEGNAZIONE DIGITAL TWIN (SIC-ID)
3. FASE 3: ROUTING & SELEZIONE TEMPLATE EMAIL (Tra gli 841 template disponibili)
4. FASE 4: SIMULAZIONE ATTERRAGGIO UTENTE SU 81PLUS.NET & IL BIVIO DELLE 2 PIATTAFORME:
   - RAMO A: Piattaforma 1 - E-LEARNING ANFOS 100% AUTOMATICO
     * Sub-ramo A1: Accesso USER (Singolo lavoratore fa corso online, paga Stripe, attestato emesso)
     * Sub-ramo A2: Accesso AZIENDA (Titolare gestisce 4 lavoratori, carica documenti, paga carrello multiplo)
   - RAMO B: Piattaforma 2 - CORSI IN AULA & ATTREZZATURE (Alto Margine)
     * Prenotazione corso pratico (es. Carrelli Elevatori / PLE), blocco posto, generazione scheda e fattura
5. FASE 5: FATTURAZIONE E RICONCILIAZIONE FINANZIARIA (Fatture SDI + Calcolo Utile Netto del Founder)
"""

import sys, os, json, uuid, sqlite3
from datetime import datetime

# Assicura encoding console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.database.db import get_connection

def log_step(title, desc):
    print("\n" + "="*80)
    print(f"🚀 {title}")
    print("="*80)
    print(desc)

def run_simulation():
    conn = get_connection()
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sim_id = uuid.uuid4().hex[:6].upper()

    # -------------------------------------------------------------------------
    # FASE 1: SCRAPING NOTTURNO & REGISTRAZIONE DB
    # -------------------------------------------------------------------------
    company_name = f"LOGISTICA VENETA NORD {sim_id} SRL"
    clean_name = f"LOGISTICA VENETA NORD {sim_id}"
    ateco = "49.41.00"
    ateco_desc = "Trasporto merci su strada e servizi di logistica"
    risk_level = "MEDIO"
    city = "ROVIGO"
    email_corporate = f"amministrazione@logisticaveneta{sim_id.lower()}.it"
    email_user = f"mario.rossi@logisticaveneta{sim_id.lower()}.it"
    piva = f"015{uuid.uuid4().int % 100000000:08d}"

    log_step("FASE 1: SCRAPING NOTTURNO & REGISTRAZIONE NEL DATABASE",
             f"• Orario simulato: 03:15:22 AM\n"
             f"• Fonte pubblica: Registro Imprese / Directory Logistica\n"
             f"• Nuova Impresa Trovata: {company_name} (P.IVA: {piva})\n"
             f"• Classificazione Automatica ATECO: {ateco} -> Rischio {risk_level}")

    # Registrazione su company_twins
    company_id = f"CMP-SIM-{sim_id}"
    cur.execute("""
        INSERT OR REPLACE INTO company_twins (
            id, business_name, clean_name, domain, ateco_code, ateco_description,
            risk_level, employee_count, city, province, region, data_confidence, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 6, ?, 'RO', 'VENETO', 0.95, ?, ?)
    """, (company_id, company_name, clean_name, f"logisticaveneta{sim_id.lower()}.it", ateco, ateco_desc, risk_level, city, now_str, now_str))

    # -------------------------------------------------------------------------
    # FASE 2: PRIVACY COMPLIANCE GATE (L1 -> L3) & DIGITAL TWIN
    # -------------------------------------------------------------------------
    log_step("FASE 2: VERIFICA PRIVACY GATE & CREAZIONE DIGITAL TWIN",
             f"• Controllo GDPR Gate: Legitimate Interest B2B verificato su email aziendale.\n"
             f"• Assegnazione Stato: CAN_CONTACT (Livello L3).\n"
             f"• Creazione Golden Twin di Conformità con scadenziario previsionale.")

    # Registrazione su compliance_digital_twin
    contact_id = int(uuid.uuid4().int % 900000 + 100000)
    cur.execute("""
        INSERT OR REPLACE INTO compliance_digital_twin (
            contact_id, rag_soc, email, macro_settore, classe_rischio, temp_ladder,
            valore_paniere_annuo, probabilita_conversione, valore_atteso_annuo, next_best_action,
            obblighi_normativi_json, last_updated
        ) VALUES (?, ?, ?, 'LOGISTICA_TRASPORTI', ?, 'W20', 1450.0, 0.085, 123.25, 'INVIA_TEMPLATE_FAD_OR_AULA', ?, ?)
    """, (contact_id, company_name, email_corporate, risk_level, json.dumps(["DVR", "CARRELLI", "PRIMO_SOCCORSO", "HACCP"]), now_str))

    cur.execute("""
        INSERT OR REPLACE INTO privacy_compliance_gate (
            contact_id, email, status_permesso, base_giuridica, fonte_acquisizione, updated_at
        ) VALUES (?, ?, 'CAN_CONTACT', 'LEGITIMATE_INTEREST_B2B', 'SCRAPER_PUBLIC_DATASET', ?)
    """, (contact_id, email_corporate, now_str))

    # -------------------------------------------------------------------------
    # FASE 3: ROUTING INTELLIGENTE & SELEZIONE TEMPLATE EMAIL
    # -------------------------------------------------------------------------
    log_step("FASE 3: SELEZIONE TEMPLATE EMAIL DALLA LIBRERIA (841 TEMPLATE)",
             f"• CORTEX Router analizza il settore (Logistica / Rischio Medio / Dipendenti: 6).\n"
             f"• Fabbisogno rilevato: Abilitazione Muletto (Carrelli) + Formazione Sicurezza Lavoratori.\n"
             f"• Template Selezionato: FLOW_ED_SIC_ATTREZZATURE/01.html + Invito Checkup 81plus.net\n"
             f"• Dispatching simulato con successo verso: {email_corporate}")

    # -------------------------------------------------------------------------
    # FASE 4: ATTERRAGGIO UTENTE & IL BIVIO DELLE 2 PIATTAFORME
    # -------------------------------------------------------------------------
    log_step("FASE 4: L'UTENTE ATTERRA SU 81PLUS.NET — IL BIVIO OPERATIVO",
             f"L'utente apre l'email, clicca sulla CTA 'ACCEDI ALLA PIATTAFORMA' e arriva su https://81plus.net.\n"
             f"Qui si aprono i due percorsi distinti:")

    # Sotto-simulazione A1: Piattaforma E-Learning - Accesso USER
    order_fad_user = f"ORD-FAD-USR-{sim_id}"
    lordo_fad_user = 55.0
    costo_anfos_user = 15.0
    fee_stripe_user = round(lordo_fad_user * 0.015 + 0.25, 2)
    netto_fad_user = round(lordo_fad_user - costo_anfos_user - fee_stripe_user, 2)

    print("\n   [RAMO A1] PIATTAFORMA 1: E-LEARNING ANFOS — ACCESSO USER (AUTOMATICO)")
    print(f"   ---------------------------------------------------------------------")
    print(f"   1. Il dipendente {email_user} si registra come 'Corsista Individuale'.")
    print(f"   2. Sceglie: 'Corso Formazione Specifica Rischio Basso/Medio (4 ore)'.")
    print(f"   3. Paga online con Stripe: € {lordo_fad_user:.2f}.")
    print(f"   4. Frequenta i moduli video e supera il test finale al 100%.")
    print(f"   5. Il sistema ANFOS genera istantaneamente l'attestato PDF con QR-Code di validazione.")
    print(f"   6. Bilancio Ramo A1: Incasso € {lordo_fad_user:.2f} | Costo ANFOS: € {costo_anfos_user:.2f} | UTILE NETTO: € {netto_fad_user:.2f} (Zero tuo tempo)")

    # Sotto-simulazione A2: Piattaforma E-Learning - Accesso AZIENDA
    order_fad_co = f"ORD-FAD-AZI-{sim_id}"
    num_dipendenti = 4
    lordo_fad_co = 240.0 # 4 corsi x €60
    costo_anfos_co = 60.0 # 4 attestati x €15
    fee_stripe_co = round(lordo_fad_co * 0.015 + 0.25, 2)
    netto_fad_co = round(lordo_fad_co - costo_anfos_co - fee_stripe_co, 2)

    print("\n   [RAMO A2] PIATTAFORMA 1: E-LEARNING ANFOS — ACCESSO AZIENDA (AUTOMATICO)")
    print(f"   ---------------------------------------------------------------------")
    print(f"   1. L'amministratore di {company_name} accede all'area riservata 'Azienda'.")
    print(f"   2. Inserisce i nominativi di {num_dipendenti} lavoratori per l'aggiornamento quinquennale.")
    print(f"   3. Carica il DVR aziendale per richiedere la custodia in cloud.")
    print(f"   4. Paga il carrello multiplo aziendale con bonifico/carta: € {lordo_fad_co:.2f}.")
    print(f"   5. I 4 lavoratori ricevono le credenziali personali e completano la formazione.")
    print(f"   6. Bilancio Ramo A2: Incasso € {lordo_fad_co:.2f} | Costo ANFOS: € {costo_anfos_co:.2f} | UTILE NETTO: € {netto_fad_co:.2f} (Zero tuo tempo)")

    # Sotto-simulazione B: Piattaforma Corsi in Aula
    order_aula = f"ORD-AULA-{sim_id}"
    lordo_aula = 360.0 # 2 operai per patentino muletto x €180
    costo_attestati_aula = 60.0 # 2 attestati x €30
    spese_pratiche_aula = 40.0
    netto_aula = round(lordo_aula - costo_attestati_aula - spese_pratiche_aula, 2)

    print("\n   [RAMO B] PIATTAFORMA 2: CORSI IN AULA & ATTREZZATURE (ALTO MARGINE)")
    print(f"   ---------------------------------------------------------------------")
    print(f"   1. L'azienda ha 2 magazzinieri che necessitano del 'Patentino Carrello Elevatore (12h)'.")
    print(f"   2. La parte pratica NON si può fare online per legge -> Viene prenotata l'aula.")
    print(f"   3. La piattaforma blocca 2 posti per la sessione del prossimo sabato presso il centro.")
    print(f"   4. Viene emessa la scheda di iscrizione ufficiale ANFOS.")
    print(f"   5. Frequenza aula e prova pratica con il carrello completata.")
    print(f"   6. Bilancio Ramo B: Incasso € {lordo_aula:.2f} | Costi Pratici: € {costo_attestati_aula + spese_pratiche_aula:.2f} | UTILE NETTO: € {netto_aula:.2f} (Richiede docenza)")

    # -------------------------------------------------------------------------
    # FASE 5: REGISTRAZIONE NEL LEDGER & FINE MESE
    # -------------------------------------------------------------------------
    log_step("FASE 5: REGISTRAZIONE NEI REGISTRI CONTABILI & REPORT FINE MESE",
             f"Tutte le transazioni concluse confluiscono automaticamente in founder_billing_ledger.")

    cur.execute("""
        INSERT INTO founder_billing_ledger (
            order_id, contact_id, rag_soc, piva_cf, indirizzo, pec_sdi,
            oggetto_servizio, importo_lordo, imponibile, iva_22, gateway_fee, costo_partner, utile_netto, stato_pagamento
        ) VALUES 
        (?, ?, ?, ?, 'Via delle Industrie 12', 'sdi001@pec.it', 'E-Learning Formazione Specifica (User)', ?, ?, ?, ?, ?, ?, 'PAID'),
        (?, ?, ?, ?, 'Via delle Industrie 12', 'sdi001@pec.it', 'E-Learning Pacchetto 4 Lavoratori (Azienda)', ?, ?, ?, ?, ?, ?, 'PAID'),
        (?, ?, ?, ?, 'Via delle Industrie 12', 'sdi001@pec.it', 'Corso in Aula Abilitazione Carrellisti (2 Pax)', ?, ?, ?, 0.0, ?, ?, 'PAID');
    """, (
        order_fad_user, contact_id, company_name, piva, lordo_fad_user, round(lordo_fad_user/1.22, 2), round(lordo_fad_user - lordo_fad_user/1.22, 2), fee_stripe_user, costo_anfos_user, netto_fad_user,
        order_fad_co, contact_id, company_name, piva, lordo_fad_co, round(lordo_fad_co/1.22, 2), round(lordo_fad_co - lordo_fad_co/1.22, 2), fee_stripe_co, costo_anfos_co, netto_fad_co,
        order_aula, contact_id, company_name, piva, lordo_aula, round(lordo_aula/1.22, 2), round(lordo_aula - lordo_aula/1.22, 2), costo_attestati_aula + spese_pratiche_aula, netto_aula
    ))
    conn.commit()

    tot_lordo = lordo_fad_user + lordo_fad_co + lordo_aula
    tot_netto = netto_fad_user + netto_fad_co + netto_aula

    print(f"\n================================================================================")
    print(f"💰 ESITO CONTABILE FINALE PER QUESTA SINGOLA AZIENDA CONVERTITA:")
    print(f"================================================================================")
    print(f"• Totale Fatturato Lordo Incassato:  € {tot_lordo:.2f}")
    print(f"  - Da E-Learning 100% Automatico:   € {lordo_fad_user + lordo_fad_co:.2f}  (Zero tuo tempo)")
    print(f"  - Da Corsi in Aula Pratici:         € {lordo_aula:.2f}  (Con docenza)")
    print(f"--------------------------------------------------------------------------------")
    print(f"• UTILE NETTO REALE SUL TUO CONTO:    € {tot_netto:.2f}  (Margine: {(tot_netto/tot_lordo)*100:.1f}%)")
    print(f"• File Fatturazione Elettronica SDI: Pronto per export commercialista.")
    print(f"================================================================================\n")

if __name__ == "__main__":
    run_simulation()
