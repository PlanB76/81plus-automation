#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compliance_profit_predictor.py — Profit Predictor & Digital Twin Compliance Engine
Ecosistema 81+ · SICURISSIMO81+ (Partner ID 2377 & 81plus.net)

Formula Economica:
ATECO -> Obblighi -> Ruoli -> Corsi -> Documenti -> Scadenze -> Rinnovi -> Acquisti -> Commissioni -> Ricorrenza

Funzionalità:
1. Mappatura dei 9.413 contatti nel 'compliance_digital_twin' di 81plus.db
2. Classificazione dinamica nella Scala Termica (W00 -> W20 -> W40 -> W60 -> W80 -> W100)
3. Assegnazione del Paniere Obblighi Normativi per codice/settore ATECO
4. Calcolo del Next Best Action (NBA) commerciale per ogni impresa
5. Previsione quantitativa del flusso di cassa e margini a 30, 60, 90 e 365 giorni (ARR / MRR)
6. Generazione e notifica Telegram SitRep a Mirco Pregnolato (@sicurissimo81_bot)
"""

import os
import sys
import json
import sqlite3
import datetime
import urllib.request

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "81plus.db")

# Telegram Config
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8939527194:AAFi56LHlyNJnBGzXC_a4Wqsht1G1DCLPbo")
TG_ADMIN_ID = os.getenv("TG_ADMIN_ID", "642593407")

def tg_notify(text):
    """Invia notifica Telegram a Mirco."""
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TG_ADMIN_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True
    except Exception as e:
        print(f"[-] Telegram Error: {e}")
        return False

def init_digital_twin_tables(conn):
    """Crea le tabelle del Digital Twin e del Profit Predictor."""
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS compliance_digital_twin (
        contact_id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        nome TEXT,
        cognome TEXT,
        rag_soc TEXT,
        macro_settore TEXT,
        classe_rischio TEXT DEFAULT 'MEDIO',
        temp_ladder TEXT DEFAULT 'W00',
        valore_paniere_annuo REAL DEFAULT 850.0,
        probabilita_conversione REAL DEFAULT 0.012,
        valore_atteso_annuo REAL DEFAULT 10.20,
        next_best_action TEXT,
        obblighi_normativi_json TEXT,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS compliance_profit_forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        totale_leads INTEGER,
        count_w00 INTEGER,
        count_w20 INTEGER,
        count_w40 INTEGER,
        count_w60 INTEGER,
        count_w80 INTEGER,
        count_w100 INTEGER,
        valore_pipeline_totale REAL,
        ricavi_attesi_30d REAL,
        ricavi_attesi_60d REAL,
        ricavi_attesi_90d REAL,
        ricavi_attesi_365d_arr REAL,
        mrr_stimato REAL
    );
    """)
    conn.commit()

# Matrice Obblighi e Valore Paniere per Settore
PANIERI_SETTORIALI = {
    "EDILIZIA": {
        "rischio": "ALTO",
        "paniere_valore": 2450.0,
        "obblighi": [
            "DVR Completo / Aggiornamento",
            "POS Cantiere D.Lgs. 81/08 All. XV",
            "Formazione Lavoratori Rischio Alto (16h)",
            "Preposto di Cantiere (Agg. Biennale)",
            "Addetto Primo Soccorso Gruppo B/C",
            "Addetto Antincendio Livello 2",
            "Abilitazione Carrelli / Gru / PLE",
            "Patente a Crediti Monitoraggio (D.L. 19/2024)"
        ]
    },
    "FOOD_HACCP": {
        "rischio": "MEDIO",
        "paniere_valore": 1350.0,
        "obblighi": [
            "Manuale Autocontrollo HACCP (Reg. CE 852/04)",
            "Registro Temperature Frigoriferi AM/PM",
            "Scheda Pulizie e Sanificazioni",
            "Tabella 14 Allergeni UE (Reg. 1169/11)",
            "Corso Alimentaristi / Manipolatori",
            "Formazione Lavoratori Rischio Basso/Medio (8-12h)",
            "Addetti Emergenze Primo Soccorso & Antincendio"
        ]
    },
    "INDUSTRIA": {
        "rischio": "ALTO",
        "paniere_valore": 1950.0,
        "obblighi": [
            "DVR + Valutazione Rumore e Vibrazioni",
            "Nomina & Formazione RSPP / RLS",
            "Formazione Lavoratori Rischio Alto (16h)",
            "Abilitazione Mulettisti (Carrelli Elevatori)",
            "Addetto Antincendio Livello 2/3",
            "Primo Soccorso Gruppo A/B"
        ]
    },
    "BENESSERE_SANITA": {
        "rischio": "MEDIO",
        "paniere_valore": 1150.0,
        "obblighi": [
            "DVR Rischio Biologico",
            "Protocollo Sanificazione Attrezzature",
            "Formazione Lavoratori Rischio Medio (12h)",
            "Informativa Privacy Clienti & Consensi",
            "Addetti Emergenze Primo Soccorso"
        ]
    },
    "PRIVACY_SERVIZI": {
        "rischio": "BASSO",
        "paniere_valore": 850.0,
        "obblighi": [
            "Registro Trattamenti Privacy GDPR art. 30",
            "DVR Semplificato / Standard",
            "Formazione Lavoratori Rischio Basso VDT (8h)",
            "Addetti Antincendio Livello 1",
            "Primo Soccorso Gruppo B/C"
        ]
    },
    "GENERALE_PMI": {
        "rischio": "BASSO",
        "paniere_valore": 850.0,
        "obblighi": [
            "DVR Obbligatorio art. 28 D.Lgs. 81/08",
            "Formazione Generale Lavoratori (4h) + Specifica",
            "Nomina RSPP Datore di Lavoro o Esterno",
            "Addetti Antincendio e Primo Soccorso",
            "Privacy GDPR Base"
        ]
    }
}

# Probabilità di Conversione per Scala Termica
PROB_LADDER = {
    "W00": 0.015,   # 1.5% - Freddo / Inattivo
    "W20": 0.050,   # 5.0% - Aperto / Cliccato
    "W40": 0.140,   # 14.0% - Interazione con Tool/Check
    "W60": 0.320,   # 32.0% - Calcolato Gap o Richiesto Preventivo
    "W80": 0.680,   # 68.0% - Iniziato Corso FAD o Carrello Aperto
    "W100": 0.850   # 85.0% - Cliente Attivo (Rinnovo / Cross-sell)
}

NBA_MAP = {
    "W00": "WARMUP_PROBLEM_DETECTOR_ATECO",
    "W20": "INVITO_CHECKLIST_OPERATIVA_GRATUITA",
    "W40": "PROPOSTA_SAFETY_CHECK_GUIDATO_90SEC",
    "W60": "OFFERTA_METODO_PROVA_PRIMA_CORSI",
    "W80": "NUDGE_ACCELERATORE_FAD_WHATSAPP",
    "W100": "MONITORAGGIO_SCADENZARIO_PERPETUO"
}

def build_compliance_digital_twin():
    """Genera e aggiorna il Digital Twin di conformità per tutti i lead in 81plus.db."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_digital_twin_tables(conn)
    cur = conn.cursor()

    # Pre-carica clienti attivi (W100) da network_documenti_emessi e network_corsisti completati
    cur.execute("SELECT DISTINCT utente_id, email, nome, cognome, rag_soc FROM network_corsisti WHERE stato = 'COMPLETATO'")
    clienti_completati = {r['email'].lower(): r for r in cur.fetchall() if r['email']}

    cur.execute("SELECT DISTINCT email FROM network_documenti_emessi WHERE email IS NOT NULL AND email != ''")
    clienti_documenti = set(r['email'].lower() for r in cur.fetchall())

    # Pre-carica corsi incompleti (W80)
    cur.execute("SELECT DISTINCT email FROM network_corsisti WHERE stato = 'INIZIATO_NON_FINITO' AND email IS NOT NULL")
    incompleti_fad = set(r['email'].lower() for r in cur.fetchall())

    # Recupera tutti i contatti da ghl_user360
    cur.execute("""
        SELECT u.contact_id, u.email, u.nome, u.cognome, u.azienda, u.macro_settore,
               u.temperatura, u.tags, u.tot_opened, u.tot_clicked
        FROM ghl_user360 u
    """)
    leads = cur.fetchall()
    tot_leads = len(leads)
    print(f"[*] Elaborazione Digital Twin per {tot_leads} imprese/contatti...")

    counts = {"W00": 0, "W20": 0, "W40": 0, "W60": 0, "W80": 0, "W100": 0}
    valore_pipeline_totale = 0.0
    valore_atteso_totale_annuo = 0.0

    for l in leads:
        cid = l['contact_id']
        em = (l['email'] or '').strip().lower()
        nome = l['nome'] or ''
        cognome = l['cognome'] or ''
        rag_soc = l['azienda'] or ''
        settore = l['macro_settore'] or 'GENERALE_PMI'
        status = (l['temperatura'] or 'FREDDO').upper()
        opened = l['tot_opened'] or 0
        clicked = l['tot_clicked'] or 0

        # Determina la scala termica
        if em in clienti_documenti or em in clienti_completati:
            temp = "W100"
        elif em in incompleti_fad:
            temp = "W80"
        elif status == "CALDO" or clicked > 0:
            temp = "W60"
        elif (status == "TIEPIDO" or opened > 0) and settore in ["EDILIZIA", "FOOD_HACCP", "INDUSTRIA"]:
            temp = "W40"
        elif status == "TIEPIDO" or opened > 0:
            temp = "W20"
        else:
            temp = "W00"

        counts[temp] += 1

        # Dati del Paniere Settoriale
        p_info = PANIERI_SETTORIALI.get(settore, PANIERI_SETTORIALI["GENERALE_PMI"])
        classe_rischio = p_info["rischio"]
        paniere_valore = p_info["paniere_valore"]
        obblighi_json = json.dumps(p_info["obblighi"], ensure_ascii=False)

        # Probabilità e Valore Atteso
        prob = PROB_LADDER[temp]
        valore_atteso = paniere_valore * prob
        nba = NBA_MAP[temp]

        valore_pipeline_totale += paniere_valore
        valore_atteso_totale_annuo += valore_atteso

        # Inserisci / Aggiorna Digital Twin
        cur.execute("""
            INSERT INTO compliance_digital_twin (
                contact_id, email, nome, cognome, rag_soc, macro_settore,
                classe_rischio, temp_ladder, valore_paniere_annuo,
                probabilita_conversione, valore_atteso_annuo, next_best_action,
                obblighi_normativi_json, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(contact_id) DO UPDATE SET
                email = excluded.email,
                temp_ladder = excluded.temp_ladder,
                macro_settore = excluded.macro_settore,
                valore_paniere_annuo = excluded.valore_paniere_annuo,
                probabilita_conversione = excluded.probabilita_conversione,
                valore_atteso_annuo = excluded.valore_atteso_annuo,
                next_best_action = excluded.next_best_action,
                last_updated = CURRENT_TIMESTAMP
        """, (
            cid, em, nome, cognome, rag_soc, settore,
            classe_rischio, temp, paniere_valore,
            prob, valore_atteso, nba, obblighi_json
        ))

    # Calcolo Previsionale Temporale Coorti
    # 30 Giorni: W80 (nudge FAD) + scadenze imminenti W100
    ricavi_30d = (counts["W80"] * 120.0 * 0.45) + (counts["W100"] * 0.08 * 85.0) + (counts["W60"] * 65.0 * 0.15)
    # 60 Giorni: Conversioni W60 -> W80 + Rinnovi a 60gg
    ricavi_60d = ricavi_30d + (counts["W60"] * 250.0 * 0.20) + (counts["W40"] * 90.0 * 0.08)
    # 90 Giorni: Flusso completo campagne ATECO (POS + HACCP)
    ricavi_90d = ricavi_60d + (counts["W40"] * 350.0 * 0.12) + (counts["W20"] * 85.0 * 0.04)
    # 365 Giorni (ARR Totale Attesa Basata su Modello Statistico)
    arr_stimata = valore_atteso_totale_annuo * 0.45 # Margine medio di realizzo al netto dei costi partner
    mrr_stimato = arr_stimata / 12.0

    # Registra nel log previsionale
    cur.execute("""
        INSERT INTO compliance_profit_forecasts (
            totale_leads, count_w00, count_w20, count_w40, count_w60,
            count_w80, count_w100, valore_pipeline_totale, ricavi_attesi_30d,
            ricavi_attesi_60d, ricavi_attesi_90d, ricavi_attesi_365d_arr, mrr_stimato
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tot_leads, counts["W00"], counts["W20"], counts["W40"], counts["W60"],
        counts["W80"], counts["W100"], valore_pipeline_totale, ricavi_30d,
        ricavi_60d, ricavi_90d, arr_stimata, mrr_stimato
    ))

    conn.commit()
    conn.close()

    sitrep = (
        f"💎 <b>81+ PROFIT PREDICTOR & DIGITAL TWIN SITREP</b>\n"
        f"📅 Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"🏛️ <b>Imprese a Digital Twin:</b> {tot_leads:,}\n"
        f"💰 <b>Valore Compliance Basket Totale:</b> € {valore_pipeline_totale:,.2f}\n\n"
        f"🌡️ <b>CANALIZZAZIONE SCALA TERMICA:</b>\n"
        f"• <b>W100 (Clienti Certificati/Attivi):</b> {counts['W100']} aziende\n"
        f"• <b>W80 (Iniziato FAD / Carrello Caldo):</b> {counts['W80']} aziende\n"
        f"• <b>W60 (Gap Normativo / Richiesta):</b> {counts['W60']} aziende\n"
        f"• <b>W40 (Audit Tool Operativo):</b> {counts['W40']} aziende\n"
        f"• <b>W20 (Aperto / Warmup Iniziato):</b> {counts['W20']} aziende\n"
        f"• <b>W00 (Freddo da Scaldare):</b> {counts['W00']} aziende\n\n"
        f"📈 <b>PREVISIONI RICAVI & MARGINI RICORRENTI:</b>\n"
        f"💵 <b>Cash Flow Atteso 30 Giorni:</b> € {ricavi_30d:,.2f}\n"
        f"💵 <b>Cash Flow Atteso 60 Giorni:</b> € {ricavi_60d:,.2f}\n"
        f"💵 <b>Cash Flow Atteso 90 Giorni:</b> € {ricavi_90d:,.2f}\n"
        f"🎯 <b>ARR Ricorrente Stimata (365d):</b> € {arr_stimata:,.2f}\n"
        f"🚀 <b>MRR Mensile Ricorrente:</b> € {mrr_stimato:,.2f} / mese\n\n"
        f"⚡ <i>Ogni azienda è ora mappata sul suo Next Best Action. La macchina attiva le vendite senza ripartire da zero.</i>"
    )

    print("\n" + sitrep + "\n")
    tg_notify(sitrep)
    return True

if __name__ == "__main__":
    build_compliance_digital_twin()
