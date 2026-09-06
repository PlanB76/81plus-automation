#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
annual_calendar_engine.py — Motore Calendario Ricorrente Annuale 81+
Copertura Nurturing 365 Giorni:
1. Feste Nazionali & Ricorrenze (Natale, Capodanno, Pasqua, Ferragosto, Halloween, Black Friday, Cyber Monday)
2. Compleanni Contatti & Anniversari di Presidio
3. Le 12 Promo Mensili Tematiche (Gennaio - Dicembre)
"""

import os
import sys
import json
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "81plus.db")
PID_URL = "https://corsi.elearningsicurezza.com/pid/2377/#login"
DOCS_URL = "https://81plus.net/#servizi-aziende"

# ══════════════════════════════════════════════════════════════════
# CALENDARIO DELLE RICORRENZE E PROMO MENSILI
# ══════════════════════════════════════════════════════════════════

CALENDAR_CAMPAIGNS = {
    # ── GENNAIO ──
    "PROMO_GENNAIO_RIPARTENZA": {
        "start_mmdd": (1, 2), "end_mmdd": (1, 31),
        "badge": "RIPARTENZA 2026 · SCADENZIARIO OBBLIGATORIO",
        "subject": "🚀 {nome}, nuovo anno, nuove regole: la checklist per evitare sanzioni nel 2026",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Ripartenza & Scadenziario Annuale</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Come ripartire nel 2026 senza sorprese nei controlli</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Con l'inizio del nuovo anno si azzerano i calendari, ma <strong>le scadenze di legge sulla sicurezza aziendale non perdonano</strong>: corsi periodici lavoratori, nomine RSPP/RLS, visite mediche e aggiornamento del DVR.</p>
    <div style="background:#FFF6F0;border-left:4px solid:#FB6B00;padding:16px 20px;margin:20px 0;border-radius:0 8px 8px 0;">
      <p style="margin:0;font-weight:800;color:#0C0C14;">Formula Prova Prima 81+:</p>
      <p style="margin:6px 0 0;font-size:14px;color:#525266;">I tuoi collaboratori si formano online a costo zero. Paghi solo se e quando richiedi l'attestato ufficiale certificato a norma di legge.</p>
    </div>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        ATTIVA LA FORMAZIONE GRATUITA DI GENNAIO ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── FEBBRAIO ──
    "PROMO_FEBBRAIO_PROTEZIONE": {
        "start_mmdd": (2, 1), "end_mmdd": (2, 28),
        "badge": "PROTEZIONE AZIENDALE · FEBBRAIO",
        "subject": "🛡️ {nome}, ama la tua azienda: proteggila prima del primo controllo",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Presidio Sicurezza Totale</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Proteggi ciò che hai costruito con anni di lavoro</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Non aspettare che sia un verbale dell'Ispettorato a segnalarti cosa manca. Il nostro servizio <strong>Fabbrica Documenti</strong> redige il tuo DVR completo da € 300 o aggiorna la valutazione rischi a € 250 in 48/72 ore.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{docs_url}" style="background:#0C0C14;color:#FFF;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;border:2px solid #FB6B00;">
        VERIFICA IL TUO DVR ONLINE →
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── MARZO ──
    "PROMO_MARZO_PRIMAVERA_AUDIT": {
        "start_mmdd": (3, 1), "end_mmdd": (3, 31),
        "badge": "AUDIT DI PRIMAVERA · VERIFICHE ATTREZZATURE",
        "subject": "🌱 {nome}, audit di primavera: attrezzature, cantieri e scadenze in ordine",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Audit di Primavera</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">La stagione riparte: macchine, patentini e POS a norma</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Con la ripresa piena delle attività, i controlli su gru, muletti, piattaforme PLE e ponteggi si intensificano. Assicurati che ogni operatore abbia il patentino in corso di validità.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        RINNOVA I PATENTINI ONLINE ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── PASQUA (APRILE) ──
    "PROMO_PASQUA": {
        "start_mmdd": (4, 1), "end_mmdd": (4, 20),
        "badge": "RICORRENZA PASQUA · PROMO FORMATIVA",
        "subject": "🕊️ Buona Pasqua da 81+ {nome}: ecco il tuo bonus formativo aziendale",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Auguri di Buona Pasqua</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">I migliori auguri di serenità da tutto il Presidio 81+</h2>
    <p>Caro <strong>{nome}</strong>,</p>
    <p>In occasione delle festività pasquali ti riserviamo un'attivazione prioritaria per qualsiasi corso o perizia documentale con sconti a volume su tutta la FAD aziendale.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        ACCEDI ALLA PIATTAFORMA CORSI ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── 28 APRILE: GIORNATA MONDIALE SICUREZZA ──
    "PROMO_GIORNATA_MONDIALE_SICUREZZA": {
        "start_mmdd": (4, 21), "end_mmdd": (4, 30),
        "badge": "28 APRILE · GIORNATA MONDIALE SICUREZZA SUL LAVORO",
        "subject": "🌍 28 Aprile: Giornata Mondiale Sicurezza sul Lavoro · {nome}, la conformità che salva",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Giornata Mondiale Sicurezza sul Lavoro</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">La sicurezza non è un costo: è la garanzia che tutti tornino a casa</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>In occasione della ricorrenza internazionale della sicurezza sul lavoro, rinnoviamo la nostra promessa: formazione accessibile a tutti a costo zero e documenti asseverati con data certa.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://81plus.net" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        SCOPRI L'ECOSISTEMA 81+ →
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── MAGGIO: FESTA LAVORATORI & SICUREZZA CANTIERI ──
    "PROMO_MAGGIO_CANTIERI": {
        "start_mmdd": (5, 1), "end_mmdd": (5, 31),
        "badge": "MAGGIO DEI CANTIERI · D.LGS 81/08 TITOLO IV",
        "subject": "🏗️ {nome}, cantieri aperti a maggio: POS, PSC e patentini macchine a norma",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Sicurezza Cantieri & Opere</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Maggio è il mese dei cantieri: non rischiare il blocco dei lavori</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>L'ingresso in cantiere richiede documenti asseverati e corsi attrezzature sempre validi: PLE, gru, escavatori e trabattelli. Con 81+ formi i tuoi operai gratis online e richiedi la perizia POS in 48 ore.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        ATTIVA I PATENTINI CANTIERE ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── GIUGNO: HACCP & RISTORAZIONE ESTATE ──
    "PROMO_GIUGNO_HACCP_ESTATE": {
        "start_mmdd": (6, 1), "end_mmdd": (6, 30),
        "badge": "STAGIONE ESTIVA · CONTROLLI HACCP & NAS",
        "subject": "🍽️ {nome}, controlli estivi NAS e ASL: il tuo locale è a prova di sigilli?",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">HACCP & Ristorazione</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Con la stagione estiva i controlli sulle cucine aumentano del 200%</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Metti a norma il personale stagionale e la tracciabilità alimentare prima che un controllo rovini l'incasso del tuo locale. Corsi HACCP online a frequenza gratuita con attestato immediato.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        FORMA IL PERSONALE HACCP GRATIS ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── LUGLIO: EMERGENZA CALDO & STRESS TERMICO ──
    "PROMO_LUGLIO_STRESS_TERMICO": {
        "start_mmdd": (7, 1), "end_mmdd": (7, 31),
        "badge": "EMERGENZA ONDATE DI CALORE · CIRCOLARE INL",
        "subject": "☀️ {nome}, allerta calore estremo nei luoghi di lavoro: obbligo valutazione microclima",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Protocollo Emergenza Calore</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Come gestire i lavoratori con temperature sopra i 35°C a norma di legge</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>L'Ispettorato Nazionale del Lavoro sanziona pesantemente la mancata integrazione del DVR con il rischio microclima e stress termico. Proteggi i tuoi operai e la tua responsabilità legale.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{docs_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        AGGIORNA IL TUO DVR ORA →
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── FERRAGOSTO (AGOSTO) ──
    "PROMO_FERRAGOSTO_PRESIDIO": {
        "start_mmdd": (8, 1), "end_mmdd": (8, 25),
        "badge": "PRESIDIO FERRAGOSTO · ATTIVI H24",
        "subject": "🏖️ {nome}, buon Ferragosto! 81+ resta attivo per le tue urgenze",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Presidio Estivo 81+</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Buone vacanze! Il nostro presidio tecnico non va in ferie</h2>
    <p>Caro <strong>{nome}</strong>,</p>
    <p>Se devi preparare l'ingresso in cantiere per settembre o hai bisogno di un attestato urgente, la nostra piattaforma eroga corsi e certificati anche ad agosto.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        ACCEDI ALL'AREA FORMAZIONE ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── SETTEMBRE: RIAPERTURA / PROMO 50 POSTI ──
    "PROMO_SETTEMBRE_RIAPERTURA": {
        "start_mmdd": (9, 1), "end_mmdd": (9, 30),
        "badge": "RIAPERTURA UFFICIALE · PROMO SETTEMBRE",
        "subject": "🔥 {nome}, Riapertura Ufficiale: solo 50 posti per il Presidio Continuativo 81+",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Promo Settembre 50 Posti</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Rientro dalle ferie: blinda la tua azienda prima dell'autunno</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>A settembre gli ispettori tornano a bussare nelle aziende per verificare corsi e documenti. Con la promo di settembre hai accesso privilegiato al Collaudo 81 e alla Fabbrica Documenti con consegna asseverata in 48 ore.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://81plus.net/promo-settembre.html" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        BLOCCA IL TUO POSTO IN PROMOZIONE →
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── HALLOWEEN (FINE OTTOBRE) ──
    "PROMO_HALLOWEEN_SANZIONI": {
        "start_mmdd": (10, 20), "end_mmdd": (10, 31),
        "badge": "HALLOWEEN · I MOSTRI DELLE SANZIONI",
        "subject": "🎃 {nome}, non avere paura di Halloween: abbi paura degli scheletri nel tuo archivio sicurezza",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Operazione Trasparenza Halloween</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">I mostri peggiori non sono mascherati: sono i verbali di contestazione</h2>
    <p>Caro <strong>{nome}</strong>,</p>
    <p>Sai se nel tuo cassetto c'è un corso scaduto o una nomina non rinnovata? Fai un Safety Check rapido di 90 secondi e scopri se la tua azienda rischia brutte sorprese.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://81plus.net/check-documenti.html" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        FAI IL SAFETY CHECK GRATUITO →
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── BLACK FRIDAY (NOVEMBRE) ──
    "SUPERPROMO_BLACK_FRIDAY": {
        "start_mmdd": (11, 15), "end_mmdd": (11, 28),
        "badge": "BLACK FRIDAY · IL MASSIMO SCONTO DELL'ANNO",
        "subject": "🖤 BLACK FRIDAY 81+: Pacchetti Documenti e Corsi con Sconto Straordinario",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Black Friday 81+</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">La sicurezza della tua azienda al prezzo più basso dell'anno</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Solo durante il Black Friday 81+: sconti eccezionali sui pacchetti di redazione documentale (DVR + HACCP + Fonometrie) e coupon formativi per tutta la tua squadra.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://81plus.net/offerte.html" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        SBLOCCA LE OFFERTE BLACK FRIDAY ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── CYBER MONDAY (FINE NOVEMBRE / INIZIO DICEMBRE) ──
    "SUPERPROMO_CYBER_MONDAY": {
        "start_mmdd": (11, 29), "end_mmdd": (12, 5),
        "badge": "CYBER MONDAY · SCONTO DIGITALE SULLA FORMAZIONE ONLINE",
        "subject": "⚡ CYBER MONDAY 81+: Ultimissime ore per bloccare gli attestati FAD scontati",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Cyber Monday 81+</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Le ultime ore di sconti digitali su tutti i corsi e-learning</h2>
    <p>Gentile <strong>{nome}</strong>,</p>
    <p>Chiudi l'anno formativo approfittando dell'extra sconto Cyber Monday su tutti gli attestati emessi per lavoratori, preposti, dirigenti e RSPP.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{pid_url}" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        APPROFITTA DEL CYBER MONDAY ↗
      </a>
    </div>
  </div>
</div>
"""
    },

    # ── NATALE & FINE ANNO (DICEMBRE) ──
    "PROMO_NATALE_CAPODANNO": {
        "start_mmdd": (12, 1), "end_mmdd": (12, 31),
        "badge": "CHIUSURA D'ANNO & NATALE · IL REGALO DI 81+",
        "subject": "🎄 Buone Feste da 81+ {nome}: il tuo regalo per chiudere l'anno al sicuro",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Auguri di Buone Feste</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Chiudi l'anno senza debiti con la conformità di legge</h2>
    <p>Caro <strong>{nome}</strong>,</p>
    <p>Ti auguriamo un Natale sereno con la tua famiglia e collaboratori. Per iniziare il nuovo anno senza pensieri, approfitta del nostro check-up gratuito dei documenti aziendali.</p>
    <div style="text-align:center;margin:30px 0;">
      <a href="https://81plus.net" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        VISITA IL SITO 81+ →
      </a>
    </div>
  </div>
</div>
"""
    }
}

# ══════════════════════════════════════════════════════════════════
# COMPLEANNI & ANNIVERSARI PERSONALI
# ══════════════════════════════════════════════════════════════════

SPECIAL_EVENT_TEMPLATES = {
    "FLOW_BIRTHDAY_GIFT": {
        "subject": "🎂 Tanti auguri {nome}! Il tuo regalo esclusivo dal Presidio 81+",
        "body_html": """
<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;color:#181820;line-height:1.6;">
  <div style="background:#0C0C14;padding:22px 28px;border-radius:10px 10px 0 0;text-align:center;">
    <span style="background:#FB6B00;color:#07070C;font-weight:900;font-size:16px;padding:4px 10px;border-radius:4px;">81+</span>
    <span style="color:#FFF;font-weight:800;font-size:18px;margin-left:8px;">Buon Compleanno da 81+!</span>
  </div>
  <div style="background:#FFFFFF;padding:32px 28px;border:1px solid #EAEAEF;border-top:none;border-radius:0 0 10px 10px;">
    <h2 style="color:#0C0C14;font-size:22px;margin-top:0;">Oggi si festeggia: 50 € di Buono Regalo per te</h2>
    <p>Caro <strong>{nome}</strong>,</p>
    <p>A nome di tutto il team di <strong>81plus.net</strong> e di Mirco Pregnolato, ti facciamo i nostri più calorosi auguri di buon compleanno!</p>
    <div style="background:#FFF6F0;border:2px dashed #FB6B00;padding:20px;margin:24px 0;border-radius:8px;text-align:center;">
      <span style="font-size:12px;font-weight:800;color:#6E6E82;letter-spacing:1px;text-transform:uppercase;">IL TUO CODICE VOUCHER COMPLEANNO:</span>
      <div style="font-size:24px;font-weight:900;color:#0C0C14;letter-spacing:2px;margin:8px 0;">COMPLEANNO81</div>
      <p style="margin:0;font-size:14px;color:#FB6B00;font-weight:700;">Valore € 50,00 spendibile su qualsiasi documento o corso FAD</p>
    </div>
    <div style="text-align:center;margin:28px 0;">
      <a href="https://81plus.net/offerte.html" style="background:#FB6B00;color:#07070C;font-weight:900;text-decoration:none;padding:16px 32px;border-radius:8px;display:inline-block;font-size:16px;">
        UTILIZZA IL TUO REGALO DI COMPLEANNO →
      </a>
    </div>
  </div>
</div>
"""
    }
}

def get_current_seasonal_campaign():
    """Restituisce la campagna stagionale attiva in base alla data odierna."""
    today = datetime.date.today()
    mm_dd = (today.month, today.day)

    for key, c in CALENDAR_CAMPAIGNS.items():
        s = c["start_mmdd"]
        e = c["end_mmdd"]
        if s <= mm_dd <= e:
            return key, c

    # Fallback predefinito di Nurturing se fuori dalle finestre speciali
    return "PROMO_GENNAIO_RIPARTENZA", CALENDAR_CAMPAIGNS["PROMO_GENNAIO_RIPARTENZA"]

def install_all_calendar_templates():
    """Inserisce tutti i template del calendario annuale nel database 81plus.db."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    count = 0

    # Inserimento campagne calendario
    for key, c in CALENDAR_CAMPAIGNS.items():
        html = c["body_html"].replace("{pid_url}", PID_URL).replace("{docs_url}", DOCS_URL)
        cur.execute("""
            INSERT INTO ghl_template (sub_account_id, nome, canale, oggetto, corpo, flow_key)
            VALUES (1, ?, 'email', ?, ?, ?)
            ON CONFLICT(flow_key) DO UPDATE SET
                oggetto = excluded.oggetto,
                corpo = excluded.corpo
        """, (key, c["subject"], html, key))
        count += 1

    # Inserimento compleanni
    for key, c in SPECIAL_EVENT_TEMPLATES.items():
        cur.execute("""
            INSERT INTO ghl_template (sub_account_id, nome, canale, oggetto, corpo, flow_key)
            VALUES (1, ?, 'email', ?, ?, ?)
            ON CONFLICT(flow_key) DO UPDATE SET
                oggetto = excluded.oggetto,
                corpo = excluded.corpo
        """, (key, c["subject"], c["body_html"], key))
        count += 1

    conn.commit()
    conn.close()
    print(f"[+] Installati/Aggiornati con successo {count} template annuali e ricorrenti nel database.")

if __name__ == "__main__":
    install_all_calendar_templates()
    active_key, active_data = get_current_seasonal_campaign()
    print(f"[i] Campagna Stagionale attiva oggi: {active_key} ({active_data['badge']})")
