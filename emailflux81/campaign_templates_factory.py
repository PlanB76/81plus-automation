#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
campaign_templates_factory.py — Fabbrica Template Email 81+
Generatore di copy ad alta conversione per:
1. Corsi Gratuiti FAD (Lead Magnet)
2. Fabbrica Documenti (DVR, HACCP, Rischi a 50% margine)
3. Follow-up Corsi Incompleti (Promemoria per utenti registrati che non hanno finito il corso)
"""

import os
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "81plus.db")
PID_URL = "https://corsi.elearningsicurezza.com/pid/2377/"
DOCS_URL = "https://81plus.net/#servizi-aziende"
CHECK_URL = "https://81plus.net/check-documenti.html"

TEMPLATES = {
    # ═══════════════════════════════════════════════════════════════
    # FLUSSO 1: CORSI GRATUITI (LEAD MAGNET)
    # ═══════════════════════════════════════════════════════════════
    "CORSI_GRATIS_01": {
        "flow": "FLOW_CORSI_GRATIS",
        "subject": "🎓 {nome}, come formare i tuoi lavoratori a costo zero (frequenza libera)",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Presidio Tecnico Nazionale</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Formazione Sicurezza Lavoro: Formula Prova Prima</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Se gestisci un'attività o coordini collaboratori, sai bene che la formazione su <strong>Sicurezza D.Lgs. 81/08, Antincendio, Primo Soccorso, Carrelli e HACCP</strong> è un obbligo inderogabile.</p>
    <p>Su <strong>81+</strong> adottiamo una politica di assoluta trasparenza a <strong>Rischio Zero</strong>:</p>
    <div style="background:#FFF6F0;border-left:4px solid #FB6B00;padding:16px 20px;margin:20px 0;border-radius:0 8px 8px 0;">
      <p style="margin:0;font-weight:700;color:#0C0C14;">I tuoi lavoratori accedono, guardano tutte le video-lezioni ed effettuano i test di verifica GRATIS.</p>
      <p style="margin:6px 0 0;font-size:14px;color:#525266;">Paghi solo se e quando richiedi il rilascio dell'attestato ufficiale timbrato e valido a norma di legge per gli organi ispettivi.</p>
    </div>
    <p>Oltre 2.000 corsi online pronti all'uso, fruibili da PC, tablet o smartphone quando vuoi.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://corsi.elearningsicurezza.com/pid/2377/#login" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;box-shadow:0 4px 18px rgba(251,107,0,0.35);">
        INIZIA UN CORSO GRATUITO ORA ↗
      </a>
    </div>
    <p style="font-size:13px;color:#6E6E82;text-align:center;">Piattaforma formativa accreditata a livello nazionale · Assistenza continua 81+</p>
  </div>
  <div style="text-align:center;padding:18px;font-size:11px;color:#8E8E9E;">
    Ricevi questa comunicazione perché sei registrato nel network 81+. <a href="{unsubscribe_url}" style="color:#6E6E82;">Disiscriviti qui</a> se non desideri più ricevere aggiornamenti.
  </div>
</div>
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # FLUSSO 2: FABBRICA DOCUMENTI (ALTO MARGINE - 50% PROFITTO)
    # ═══════════════════════════════════════════════════════════════
    "FABBRICA_DOCS_01": {
        "flow": "FLOW_FABBRICA_DOCS",
        "subject": "⚠️ {nome}, il DVR e i manuali della tua azienda sono inattaccabili?",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Presidio Documentale Aziende</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Le sanzioni per mancato DVR superano i 7.000 €</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Durante un controllo SPISAL o dell'Ispettorato del Lavoro, la prima cosa richiesta non è una spiegazione: è il <strong>Documento di Valutazione dei Rischi (DVR) con data certa</strong> e le relative nomine (RSPP, RLS, Medico Competente).</p>
    <p>La Fabbrica Documenti di <strong>81+</strong> redige per te tutta la documentazione obbligatoria asseverata da tecnici qualificati in 48/72 ore:</p>
    <ul style="padding-left:20px;color:#242436;font-size:15px;line-height:1.7;">
      <li><strong>DVR Aziendale Completo o Standardizzato:</strong> Conforme Art. 28 D.Lgs 81/08 da € 300</li>
      <li><strong>Aggiornamento DVR periodico:</strong> € 250</li>
      <li><strong>Relazioni Specifiche (Rumore/Fonometria, Vibrazioni, Chimico, Stress):</strong> € 250 cad.</li>
      <li><strong>Manuale Autocontrollo HACCP & Legionella:</strong> Da € 300</li>
      <li><strong>POS (Piano Operativo di Sicurezza) Cantieri:</strong> € 250</li>
    </ul>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://81plus.net/#servizi-aziende" style="background:#0C0C14;color:#FFFFFF;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;border:2px solid #FB6B00;">
        RICHIEDI I TUOI DOCUMENTI ONLINE →
      </a>
    </div>
    <p style="font-size:13px;color:#6E6E82;text-align:center;">Asseverazione tecnica inclusa · Consegna urgente disponibile in tutta Italia</p>
  </div>
  <div style="text-align:center;padding:18px;font-size:11px;color:#8E8E9E;">
    Presidio 81+ · Labo Tecnic Studio. <a href="{unsubscribe_url}" style="color:#6E6E82;">Disiscriviti</a>
  </div>
</div>
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # FLUSSO 3: NUDGE / PROMEMORIA COMPLETAMENTO CORSO INCOMPLETO
    # ═══════════════════════════════════════════════════════════════
    "NUDGE_CORSO_INCOMPLETO_01": {
        "flow": "FLOW_NUDGE_INCOMPLETO",
        "subject": "⏳ {nome}, hai un corso in sospeso su 81+: ti mancano pochi moduli per l'attestato",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Piattaforma E-Learning Formazione</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Non lasciare la tua formazione a metà</h2>
    <p>Ciao <strong>{nome}</strong>,</p>
    <p>Risulta che hai effettuato l'accesso alla piattaforma formativa per il corso di sicurezza/HACCP, ma <strong>il percorso formativo non risulta ancora concluso o non hai ancora scaricato l'attestato ufficiale</strong>.</p>
    <div style="background:#FFF6F0;border-left:4px solid #FB6B00;padding:16px 20px;margin:20px 0;border-radius:0 8px 8px 0;">
      <p style="margin:0;font-weight:800;color:#0C0C14;">Perché è fondamentale completarlo adesso?</p>
      <ul style="margin:8px 0 0;padding-left:18px;font-size:14px;color:#454558;line-height:1.6;">
        <li>In caso di ispezione ASL o ITL, i corsi iniziati ma senza attestato timbrato non hanno valore legale.</li>
        <li>I tuoi progressi sono già salvati sul portale: puoi riprendere esattamente da dove avevi interrotto.</li>
        <li>I test intermedi e finali richiedono solo pochi minuti per essere convalidati.</li>
      </ul>
    </div>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://corsi.elearningsicurezza.com/pid/2377/#login" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;box-shadow:0 4px 18px rgba(251,107,0,0.35);">
        RIPRENDI E COMPLETA IL TUO CORSO ↗
      </a>
    </div>
    <p style="font-size:13px;color:#6E6E82;text-align:center;">Se hai dimenticato la password, puoi reimpostarla istantaneamente con un click nella schermata di login.</p>
  </div>
  <div style="text-align:center;padding:18px;font-size:11px;color:#8E8E9E;">
    Assistenza didattica 81+ · <a href="{unsubscribe_url}" style="color:#6E6E82;">Disiscriviti</a>
  </div>
</div>
"""
    }
}

def install_templates_in_db():
    """Registra i template nella tabella ghl_template di 81plus.db."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ghl_template(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sub_account_id INTEGER DEFAULT 1,
      nome TEXT,
      canale TEXT DEFAULT 'email',
      oggetto TEXT,
      corpo TEXT,
      flow_key TEXT UNIQUE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    inserted = 0
    for key, data in TEMPLATES.items():
        cur.execute("""
            INSERT INTO ghl_template (sub_account_id, nome, canale, oggetto, corpo, flow_key)
            VALUES (1, ?, 'email', ?, ?, ?)
            ON CONFLICT(flow_key) DO UPDATE SET
                oggetto = excluded.oggetto,
                corpo = excluded.corpo
        """, (key, data['subject'], data['body_html'], key))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"[+] Installati/Aggiornati {inserted} template strategici nel database.")

if __name__ == "__main__":
    install_templates_in_db()
