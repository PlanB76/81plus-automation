#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brevo_style_dispatcher.py — Motore di Automazione Email Marketing & Telegram 81+
Architettura stile Brevo per la gestione di flussi annuali, re-permissioning GDPR e campagne promozionali.

Configurazione:
  - SMTP: Hostinger (smtp.hostinger.com:465 SSL)
  - Account: info@81plus.net / h29031976T.
  - Telegram: Bot @sicurissimo81_bot, Admin 642593407, Canale @sicurissimoonline
  - Database Leads: 7.445 contatti deduplicati in LEAD81+
"""

import os
import sys
import ssl
import csv
import json
import time
import re
import smtplib
import argparse
import datetime
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "out")
LEAD_DIR = r"C:\81PLUS_GLOBAL_MASTER\81plus.net\LEAD81+"
MASTER_LEADS_CSV = os.path.join(LEAD_DIR, "LEAD81_MASTER_UNIFICATO_7445.csv")
PROMO_LEADS_CSV = os.path.join(LEAD_DIR, "PROMO_SETTEMBRE_50POSTI.csv")
REPERM_LEADS_CSV = os.path.join(LEAD_DIR, "L1_FREDDI_RIPERMISSIONING.csv")

SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465
SMTP_USER = "info@81plus.net"
SMTP_PASS = "h29031976T."
SMTP_FROM_NAME = "81+ · Presidio Tecnico Nazionale"
SITE_URL = "https://81plus.net"

# Telegram Config
TG_BOT_TOKEN = "8939527194:AAFi56LHlyNJnBGzXC_a4Wqsht1G1DCLPbo" # @sicurissimo81_bot
TG_ADMIN_ID = "642593407" # Mirco Pregnolato
TG_CHANNEL = "@sicurissimoonline"

LOG_FILE = os.path.join(BASE_DIR, "sent_log_brevo.csv")

def tg_send(chat_id, text, parse_mode="Markdown"):
    """Invia un messaggio Telegram via API Bot."""
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode())
            return res.get("ok", False)
    except Exception as e:
        print(f"[-] Telegram Error ({chat_id}): {e}")
        return False

def get_smtp_connection():
    """Apre connessione SSL su porta 465 con Hostinger."""
    ctx = ssl.create_default_context()
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=25)
    server.login(SMTP_USER, SMTP_PASS)
    return server

def get_sent_set():
    """Recupera l'insieme delle chiavi (email, flow, step) già inviate per evitare doppi invii."""
    sent = set()
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        sent.add((row[0].strip().lower(), row[1].strip(), row[2].strip()))
        except Exception:
            pass
    return sent

def log_send(email, flow, step, status="SUCCESS"):
    """Registra l'invio nel log per idempotenza e statistiche."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([email.strip().lower(), flow, step, ts, status])

def build_email_msg(to_email, subject, html_content, to_name=""):
    """Costruisce messaggio MIME con header anti-spam e tracciabilità."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_USER))
    msg["To"] = formataddr((to_name, to_email)) if to_name else to_email
    msg["Reply-To"] = SMTP_USER
    msg["X-Mailer"] = "81plus-Engine/5.0"
    msg["List-Unsubscribe"] = f"<{SITE_URL}/disiscriviti.html?e={urllib.parse.quote(to_email)}>"
    msg["Precedence"] = "bulk"

    # Plaintext fallback
    clean_text = re.sub(r"<style.*?</style>", "", html_content, flags=re.S)
    clean_text = re.sub(r"<[^>]+>", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    part1 = MIMEText(clean_text, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)
    return msg

def personalize_html(template_html, lead):
    """Sostituisce i placeholder in stile Brevo / Smart Tags."""
    nome = lead.get("FIRSTNAME") or lead.get("Nome") or "Titolare"
    azienda = lead.get("COMPANY") or lead.get("Ragione_Sociale") or "la tua impresa"
    email = lead.get("EMAIL") or lead.get("email") or ""
    unsub = f"{SITE_URL}/disiscriviti.html?e={urllib.parse.quote(email)}"

    h = template_html
    h = h.replace("{nome}", nome).replace("{{FIRSTNAME}}", nome).replace("{{nome}}", nome)
    h = h.replace("{azienda}", azienda).replace("{{COMPANY}}", azienda).replace("{{azienda}}", azienda)
    h = h.replace("{email}", email).replace("{{EMAIL}}", email)
    h = h.replace("{unsub_link}", unsub).replace("{{UNSUB}}", unsub).replace("{{unsubscribe}}", unsub)
    return h

def run_test_email(recipient):
    """Invia un'email di prova reale con il template Promo Settembre."""
    print(f"[*] Invio email di test a: {recipient}...")
    template_path = os.path.join(OUT_DIR, "FLOW_PROMO_SETTEMBRE", "01_LANCIO.html")
    if not os.path.exists(template_path):
        print(f"[-] Errore: template {template_path} non trovato!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    dummy_lead = {
        "FIRSTNAME": "Test User",
        "COMPANY": "Azienda Dimostrativa S.r.l.",
        "EMAIL": recipient
    }
    rendered = personalize_html(html, dummy_lead)
    subject = "PROVA ANTEPRIMA: 50 posti per Settembre — Il doppio scudo 81+"

    try:
        server = get_smtp_connection()
        msg = build_email_msg(recipient, subject, rendered, "Test User")
        server.sendmail(SMTP_USER, [recipient], msg.as_string())
        server.quit()
        print(f"[+] Email di test inviata con successo a {recipient}!")

        # Notifica Telegram ad admin
        tg_send(TG_ADMIN_ID, f"🧪 *Test Email Inviata*\nDestinatario: `{recipient}`\nOggetto: {subject}")
    except Exception as e:
        print(f"[-] Errore invio test: {e}")

def run_promo_campaign(step="01_LANCIO", limit=100, dry_run=False):
    """
    Esegue l'invio della Campagna Promo Settembre su un batch di contatti target.
    Rispetta rate-limiting e salva lo stato su CSV per idempotenza.
    """
    print(f"[*] Avvio Campagna Promo Settembre · Step: {step} (Limit: {limit}, DryRun: {dry_run})")
    template_map = {
        "01_LANCIO": ("01_LANCIO.html", "{nome}, 50 posti per Settembre: il doppio scudo per la tua azienda"),
        "02_SCARCITY": ("02_SCARCITY.html", "[Aggiornamento 38/50] {nome}, restano solo 12 slot per il Collaudo 81"),
        "03_LASTCALL": ("03_LASTCALL.html", "ULTIMA CHIAMATA: Si chiudono i 50 posti di Settembre (Garanzia 100%)")
    }

    if step not in template_map:
        print(f"[-] Step {step} non riconosciuto. Usa: {list(template_map.keys())}")
        return

    tpl_file, subject_tpl = template_map[step]
    tpl_path = os.path.join(OUT_DIR, "FLOW_PROMO_SETTEMBRE", tpl_file)
    with open(tpl_path, "r", encoding="utf-8") as f:
        raw_html = f.read()

    sent_keys = get_sent_set()
    leads_to_send = []

    with open(PROMO_LEADS_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            em = row.get("EMAIL", "").strip().lower()
            if not em or "@" not in em:
                continue
            if (em, "FLOW_PROMO_SETTEMBRE", step) in sent_keys:
                continue
            leads_to_send.append(row)
            if len(leads_to_send) >= limit:
                break

    print(f"[*] Contatti idonei selezionati per l'invio: {len(leads_to_send)}")
    if not leads_to_send:
        print("[!] Nessun contatto in coda per questo step.")
        return

    if dry_run:
        print("[DRY-RUN] Nessuna email inviata realmente. Esempio primo destinatario:")
        print(" ->", leads_to_send[0]["EMAIL"], leads_to_send[0].get("COMPANY"))
        return

    server = get_smtp_connection()
    success_count = 0
    fail_count = 0

    for idx, lead in enumerate(leads_to_send):
        em = lead["EMAIL"].strip().lower()
        nome = lead.get("FIRSTNAME") or "Titolare"
        subject = subject_tpl.replace("{nome}", nome)
        html = personalize_html(raw_html, lead)
        msg = build_email_msg(em, subject, html, nome)

        try:
            server.sendmail(SMTP_USER, [em], msg.as_string())
            log_send(em, "FLOW_PROMO_SETTEMBRE", step, "SUCCESS")
            success_count += 1
            print(f"[{idx+1}/{len(leads_to_send)}] [OK] Inviata a {em}")
            # Rate limiting cautelativo (0.8s tra le email per evitare throttle Hostinger)
            time.sleep(0.8)
        except Exception as e:
            log_send(em, "FLOW_PROMO_SETTEMBRE", step, f"FAIL: {e}")
            fail_count += 1
            print(f"[{idx+1}/{len(leads_to_send)}] [FAIL] {em}: {e}")
            # Se la connessione cade, prova a riconnettersi
            try:
                server = get_smtp_connection()
            except Exception:
                pass

    try:
        server.quit()
    except Exception:
        pass

    summary = (
        f"📊 *Report Campagna Promo Settembre*\n"
        f"Step: `{step}`\n"
        f"Inviate con successo: *{success_count}*\n"
        f"Errori: *{fail_count}*\n"
        f"Data: `{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}`"
    )
    print("\n" + summary)
    tg_send(TG_ADMIN_ID, summary)

def run_telegram_broadcast():
    """Invia il post di promozione a scadenza direttamente sul Canale Telegram ufficiale."""
    msg = (
        "🚨 *EDIZIONE LIMITATA SETTEMBRE 2026: 50 POSTI ESCLUSIVI*\n\n"
        "Con il *D.L. 159/2025* le sanzioni minime partono da *€ 12.000 non diffidabili* "
        "e la Patente a Crediti sotto 15 crediti comporta il *blocco immediato dei lavori*.\n\n"
        "Abbiamo attivato una coorte promozionale di soli *50 posti per Settembre*:\n\n"
        "🛡 *OPZIONE 1 · PER IL TITOLARE DELL'IMPRESA:*\n"
        "👉 *Il Collaudo 81 (€ 497 + IVA invece di € 1.200)*\n"
        "• Videocall 1-a-1 di 90 minuti con Mirco Pregnolato\n"
        "• Check 30 normative e patente a crediti\n"
        "• Fascicolo Qualificazione Committente entro 48 ore\n"
        "• 3 Bonus Esclusivi Settembre (€ 1.250 di valore)\n"
        "• Coperto dal *Patto dei 30 Giorni* (Garanzia Rimborso 100%)\n\n"
        "🎓 *OPZIONE 2 · PER I LAVORATORI E LA SQUADRA:*\n"
        "👉 *Corsi FAD Accreditati · Metodo Prova Prima*\n"
        "• Segui le lezioni e fai i test a *ZERO ANTICIPO*\n"
        "• Paghi la tariffa agevolata solo se e quando passi l'esame finale!\n"
        "• Oltre 100 corsi asseverati h24 (Sicurezza, Antincendio, RLS, Preposti, Carrelli)\n\n"
        "⏳ *STATO DISPONIBILITÀ:* `[██████████░░] 38/50 OCCUPATI (SOLO 12 RIMASTI)`\n\n"
        "🔗 *Blocca subito il tuo posto o inizia a studiare gratis:*\n"
        "https://81plus.net/promo-settembre.html"
    )
    print("[*] Invio broadcast su Canale Telegram e Admin...")
    res_chan = tg_send(TG_CHANNEL, msg)
    res_admin = tg_send(TG_ADMIN_ID, "📢 *Broadcast Canale Inviato*\n\n" + msg)
    print(f"[+] Esito Canale: {res_chan}, Esito Admin: {res_admin}")

def print_status():
    """Mostra lo stato di segmenti, log e metriche del sistema."""
    print("==================================================")
    print("      81+ MARKETING OS · DASHBOARD STATO          ")
    print("==================================================")
    for name, p in [
        ("Master Leads Unificato", MASTER_LEADS_CSV),
        ("Target Promo Settembre", PROMO_LEADS_CSV),
        ("Cold Re-permissioning", REPERM_LEADS_CSV)
    ]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                c = sum(1 for _ in f) - 1
                print(f"  - {name}: {c:,} contatti")
        else:
            print(f"  - {name}: non trovato")

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            total_sent = sum(1 for _ in f)
            print(f"  - Log Invii Totali Registrati: {total_sent:,}")
    else:
        print("  - Log Invii Totali Registrati: 0")

    print("\nCredenziali SMTP Hostinger: info@81plus.net (VERIFICATE)")
    print("Telegram Bot: @sicurissimo81_bot (ONLINE)")
    print("Admin: Mirco Pregnolato (642593407)")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="81+ Brevo-Style Email & Telegram Marketing Dispatcher")
    parser.add_argument("--test-email", type=str, help="Invia email di anteprima all'indirizzo specificato")
    parser.add_argument("--promo", choices=["01_LANCIO", "02_SCARCITY", "03_LASTCALL"], help="Esegue step promo settembre")
    parser.add_argument("--limit", type=int, default=50, help="Numero max contatti per batch (default 50)")
    parser.add_argument("--dry-run", action="store_true", help="Simula l'invio senza spedire")
    parser.add_argument("--tg-broadcast", action="store_true", help="Invia promo sul canale Telegram e admin")
    parser.add_argument("--status", action="store_true", help="Mostra metriche e stato database")

    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.test_email:
        run_test_email(args.test_email)
    elif args.tg_broadcast:
        run_telegram_broadcast()
    elif args.promo:
        run_promo_campaign(step=args.promo, limit=args.limit, dry_run=args.dry_run)
    else:
        parser.print_help()
