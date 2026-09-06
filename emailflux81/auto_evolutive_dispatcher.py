#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_evolutive_dispatcher.py — Motore di Invio Email Auto-Evolutivo 81+
Ecosistema 81+ · SICURISSIMO81+

Architettura Nurturing 365 Giorni a 4 Livelli:
1. FASE 1: Priorità Assoluta - Follow-up Corsi Incompleti (utenti registrati su elearningsicurezza che non hanno terminato)
2. FASE 2: Compleanni & Anniversari di Presidio (€ 50 Voucher Regalo COMPLEANNO81)
3. FASE 3: Ricorrenze Annuali, Feste & Promo Mensili (Natale, Pasqua, Ferragosto, Halloween, Black Friday, Cyber Monday, ecc.)
4. FASE 4: Nurturing Evergreen Profilato ATECO (Corsi Gratuiti FAD & Fabbrica Documenti)
"""

import os
import sys
import ssl
import csv
import json
import time
import random
import sqlite3
import smtplib
import argparse
import datetime
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from annual_calendar_engine import get_current_seasonal_campaign, install_all_calendar_templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "81plus.db")
LEAD_CSV = os.path.join(r"C:\81PLUS_GLOBAL_MASTER\81plus.net\LEAD81+", "LEAD81_MASTER_UNIFICATO_7445.csv")

# SMTP Hostinger
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "info@81plus.net")
SMTP_PASS = os.getenv("SMTP_PASS", "h29031976T.")
SMTP_FROM_NAME = "81+ · Presidio Sicurezza & Formazione"

SITE_URL = "https://81plus.net"

# Telegram
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8939527194:AAFi56LHlyNJnBGzXC_a4Wqsht1G1DCLPbo")
TG_ADMIN_ID = os.getenv("TG_ADMIN_ID", "642593407")

def tg_send(text):
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TG_ADMIN_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return True
    except Exception as e:
        print(f"[-] Telegram error: {e}")
        return False

def get_smtp_conn():
    ctx = ssl.create_default_context()
    s = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=25)
    s.login(SMTP_USER, SMTP_PASS)
    return s

def send_email_message(server, to_email, to_name, subject, html_body, unsubscribe_url):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_USER))
    msg["To"] = formataddr((to_name, to_email))
    msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"

    # Inietta unsubscribe_url nel corpo
    final_html = html_body.replace("{unsubscribe_url}", unsubscribe_url).replace("{nome}", to_name)
    msg.attach(MIMEText(final_html, "html", "utf-8"))

    server.sendmail(SMTP_USER, [to_email], msg.as_string())

def run_dispatch(batch_limit=50, dry_run=False):
    # Assicura che tutti i template del calendario siano installati/aggiornati
    try:
        install_all_calendar_templates()
    except Exception as e:
        print(f"[!] Warning install calendar templates: {e}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Prepara tabella send_log se non presente
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ghl_send_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sub_account_id INTEGER DEFAULT 1,
        contact_id INTEGER,
        email TEXT,
        canale TEXT DEFAULT 'email',
        template_id TEXT,
        stato TEXT,
        errore TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    # Recupera tutti i template da ghl_template
    cur.execute("SELECT flow_key, oggetto, corpo FROM ghl_template")
    templates = {r['flow_key']: {'subject': r['oggetto'], 'body': r['corpo']} for r in cur.fetchall()}

    sent_count = 0
    failed_count = 0
    incompleti_nudge_count = 0
    birthday_count = 0
    seasonal_promo_count = 0
    nurturing_count = 0

    # Rileva campagna stagionale / festa corrente attiva
    active_seasonal_key, active_seasonal_data = get_current_seasonal_campaign()
    print(f"[i] Campagna Stagionale attiva oggi: {active_seasonal_key} ({active_seasonal_data.get('badge', '')})")

    server = None
    if not dry_run:
        try:
            server = get_smtp_conn()
            print("[+] Connessione SMTP stabilita con successo.")
        except Exception as e:
            print(f"[-] Errore connessione SMTP: {e}")
            tg_send(f"⚠️ <b>81+ Email Machine</b>\nErrore SMTP: {e}")
            conn.close()
            return

    # ═══════════════════════════════════════════════════════════════
    # FASE 1: PRIORITÀ ASSOLUTA AGLI UTENTI CON CORSO INCOMPLETO
    # ═══════════════════════════════════════════════════════════════
    cur.execute("""
        SELECT utente_id, nome, cognome, email, rag_soc, corso_titolo, nudge_count
        FROM network_corsisti
        WHERE stato = 'INIZIATO_NON_FINITO' 
          AND email IS NOT NULL 
          AND email != ''
          AND (ultimo_nudge IS NULL OR ultimo_nudge < datetime('now', '-3 days'))
          AND nudge_count < 5
        LIMIT ?
    """, (batch_limit,))
    incompleti = cur.fetchall()

    for row in incompleti:
        if sent_count >= batch_limit:
            break
        email = row['email'].strip()
        nome = (row['nome'] or row['rag_soc'] or 'Gentile Corsista').strip()
        tpl = templates.get("NUDGE_CORSO_INCOMPLETO_01")
        if not tpl:
            continue

        subj = tpl['subject'].replace("{nome}", nome)
        unsub_url = f"https://81plus.net/api/unsub.php?e={email}"

        print(f"[*] Invio Nudge Corso Incompleto a {nome} <{email}>...")
        if not dry_run:
            try:
                send_email_message(server, email, nome, subj, tpl['body'], unsub_url)
                cur.execute("""
                    UPDATE network_corsisti 
                    SET nudge_count = nudge_count + 1, ultimo_nudge = CURRENT_TIMESTAMP
                    WHERE utente_id = ?
                """, (row['utente_id'],))
                cur.execute("""
                    INSERT INTO ghl_send_log (email, template_id, stato) VALUES (?, ?, 'INVIATO')
                """, (email, "NUDGE_CORSO_INCOMPLETO_01"))
                conn.commit()
                sent_count += 1
                incompleti_nudge_count += 1
                time.sleep(random.uniform(1.2, 2.5))
            except Exception as e:
                print(f"[-] Errore invio a {email}: {e}")
                failed_count += 1
        else:
            print(f"[DRY-RUN] Simulata email nudge a {email}")
            sent_count += 1
            incompleti_nudge_count += 1

    # ═══════════════════════════════════════════════════════════════
    # FASE 2: COMPLEANNI & ANNIVERSARI DI PRESIDIO (€50 VOUCHER)
    # ═══════════════════════════════════════════════════════════════
    rimanenti_fase2 = batch_limit - sent_count
    if rimanenti_fase2 > 0 and "FLOW_BIRTHDAY_GIFT" in templates:
        cur.execute("""
            SELECT id, nome, cognome, email 
            FROM ghl_contact 
            WHERE email IS NOT NULL 
              AND email != '' 
              AND (unsub = 0 OR unsub IS NULL)
              AND strftime('%m-%d', created_at) = strftime('%m-%d', 'now')
              AND id NOT IN (
                  SELECT contact_id FROM ghl_send_log 
                  WHERE contact_id IS NOT NULL 
                    AND template_id = 'FLOW_BIRTHDAY_GIFT'
                    AND created_at > datetime('now', '-300 days')
              )
            LIMIT ?
        """, (min(rimanenti_fase2, 15),))
        compleanni = cur.fetchall()

        for lead in compleanni:
            if sent_count >= batch_limit:
                break
            email = lead['email'].strip()
            nome = (lead['nome'] or 'Gentile Cliente').strip()
            tpl = templates["FLOW_BIRTHDAY_GIFT"]
            subj = tpl['subject'].replace("{nome}", nome)
            unsub_url = f"https://81plus.net/api/unsub.php?e={email}"

            print(f"[*] Invio VOUCHER COMPLEANNO a {nome} <{email}>...")
            if not dry_run:
                try:
                    send_email_message(server, email, nome, subj, tpl['body'], unsub_url)
                    cur.execute("""
                        INSERT INTO ghl_send_log (contact_id, email, template_id, stato) VALUES (?, ?, 'FLOW_BIRTHDAY_GIFT', 'INVIATO')
                    """, (lead['id'], email))
                    conn.commit()
                    sent_count += 1
                    birthday_count += 1
                    time.sleep(random.uniform(1.2, 2.5))
                except Exception as e:
                    print(f"[-] Errore invio compleanno {email}: {e}")
                    failed_count += 1
            else:
                print(f"[DRY-RUN] Simulata email compleanno a {email}")
                sent_count += 1
                birthday_count += 1

    # ═══════════════════════════════════════════════════════════════
    # FASE 3: PROMO STAGIONALE / RICORRENZE ANNUALI ATTIVE
    # ═══════════════════════════════════════════════════════════════
    rimanenti_fase3 = batch_limit - sent_count
    if rimanenti_fase3 > 0 and active_seasonal_key in templates:
        # Destiniamo fino al 50% del batch rimanente alla promo stagionale attiva (Natale, Pasqua, Ferragosto, Black Friday, Promo Settembre, ecc.)
        quota_stagionale = max(1, rimanenti_fase3 // 2)
        cur.execute("""
            SELECT id, nome, cognome, email, ateco 
            FROM ghl_contact 
            WHERE email IS NOT NULL 
              AND email != '' 
              AND (unsub = 0 OR unsub IS NULL)
              AND id NOT IN (
                  SELECT contact_id FROM ghl_send_log 
                  WHERE contact_id IS NOT NULL 
                    AND (created_at > datetime('now', '-7 days') OR template_id = ?)
              )
            LIMIT ?
        """, (active_seasonal_key, quota_stagionale))
        seasonal_leads = cur.fetchall()

        tpl = templates[active_seasonal_key]
        for lead in seasonal_leads:
            if sent_count >= batch_limit:
                break
            email = lead['email'].strip()
            nome = (lead['nome'] or 'Imprenditore').strip()
            subj = tpl['subject'].replace("{nome}", nome)
            unsub_url = f"https://81plus.net/api/unsub.php?e={email}"

            print(f"[*] Invio Promo Stagionale [{active_seasonal_key}] a {nome} <{email}>...")
            if not dry_run:
                try:
                    send_email_message(server, email, nome, subj, tpl['body'], unsub_url)
                    cur.execute("""
                        INSERT INTO ghl_send_log (contact_id, email, template_id, stato) VALUES (?, ?, ?, 'INVIATO')
                    """, (lead['id'], email, active_seasonal_key))
                    conn.commit()
                    sent_count += 1
                    seasonal_promo_count += 1
                    time.sleep(random.uniform(1.5, 2.8))
                except Exception as e:
                    print(f"[-] Errore invio promo stagionale {email}: {e}")
                    failed_count += 1
            else:
                print(f"[DRY-RUN] Simulata email promo stagionale [{active_seasonal_key}] a {email}")
                sent_count += 1
                seasonal_promo_count += 1

    # ═══════════════════════════════════════════════════════════════
    # FASE 4: CAMPAGNA NURTURING AI LEAD (CORSI GRATUITI & DOCS)
    # ═══════════════════════════════════════════════════════════════
    rimanenti_fase4 = batch_limit - sent_count
    if rimanenti_fase4 > 0:
        cur.execute("""
            SELECT id, nome, cognome, email, ateco 
            FROM ghl_contact 
            WHERE email IS NOT NULL 
              AND email != '' 
              AND (unsub = 0 OR unsub IS NULL)
              AND id NOT IN (
                  SELECT contact_id FROM ghl_send_log 
                  WHERE contact_id IS NOT NULL 
                    AND created_at > datetime('now', '-7 days')
              )
            LIMIT ?
        """, (rimanenti_fase4,))
        leads = cur.fetchall()

        for lead in leads:
            if sent_count >= batch_limit:
                break
            email = lead['email'].strip()
            nome = (lead['nome'] or 'Imprenditore').strip()
            ateco = str(lead['ateco'] or '')

            # Segmentazione intelligente per ATECO
            if ateco.startswith(('41', '42', '43', '10', '11', '56')):
                tpl_key = "FABBRICA_DOCS_01"
            else:
                tpl_key = "CORSI_GRATIS_01"

            tpl = templates.get(tpl_key)
            if not tpl:
                continue

            subj = tpl['subject'].replace("{nome}", nome)
            unsub_url = f"https://81plus.net/api/unsub.php?e={email}"

            print(f"[*] Invio Nurturing Evergreen {tpl_key} a {nome} <{email}>...")
            if not dry_run:
                try:
                    send_email_message(server, email, nome, subj, tpl['body'], unsub_url)
                    cur.execute("""
                        INSERT INTO ghl_send_log (contact_id, email, template_id, stato) VALUES (?, ?, ?, 'INVIATO')
                    """, (lead['id'], email, tpl_key))
                    conn.commit()
                    sent_count += 1
                    nurturing_count += 1
                    time.sleep(random.uniform(1.5, 3.0))
                except Exception as e:
                    print(f"[-] Errore invio lead {email}: {e}")
                    failed_count += 1
            else:
                print(f"[DRY-RUN] Simulata email {tpl_key} a {email}")
                sent_count += 1
                nurturing_count += 1

    if server:
        server.quit()

    conn.close()

    # Notifica Telegram riassuntiva
    report_msg = (
        f"🚀 <b>81+ EMAIL MARKETING MACHINE REPORT</b>\n"
        f"📅 Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"✉️ <b>Totale Email Inviate:</b> {sent_count}\n"
        f"⏳ <b>Nudge Corsi Incompleti:</b> {incompleti_nudge_count}\n"
        f"🎂 <b>Compleanni / Anniversari (€50 Voucher):</b> {birthday_count}\n"
        f"🎪 <b>Promo Stagionale / Feste ({active_seasonal_key}):</b> {seasonal_promo_count}\n"
        f"📚 <b>Nurturing Lead Evergreen:</b> {nurturing_count}\n"
        f"❌ <b>Errori/Respinti:</b> {failed_count}\n"
        f"⚙️ <b>Modalità:</b> {'DRY-RUN (Test)' if dry_run else 'PRODUZIONE (Live)'}\n\n"
        f"🎯 <i>Macchina copre 365 giorni di nurturing automatico con rotazione intelligente.</i>"
    )
    tg_send(report_msg)
    print(f"[+] Ciclo completato: {sent_count} totali (Incompleti: {incompleti_nudge_count}, Compleanni: {birthday_count}, Promo: {seasonal_promo_count}, Nurturing: {nurturing_count}), {failed_count} errori.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Numero email per batch")
    parser.add_argument("--dry-run", action="store_true", help="Esegui senza inviare realmente")
    args = parser.parse_args()

    run_dispatch(batch_limit=args.limit, dry_run=args.dry_run)
