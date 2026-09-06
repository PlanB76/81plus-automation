#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
master_scadenze_monitor.py — Master Scadenzario & Promemoria Corsi Personalizzato
Ecosistema 81+ · SICURISSIMO81+ (Partner ID 2377 & 81plus.net)

Flusso Intelligente:
1. Sincronizzazione documenti/attestati emessi da elearningsicurezza (/api/partners/docemessi.asp)
2. Calcolo scadenze legali a norma D.Lgs. 81/08, Accordi Stato-Regioni e Reg. CE 852/04:
   - RLS / RLST: 1 anno (annuale obbligatorio)
   - Preposti: 2 anni (biennale Accordo 2025/2026)
   - Primo Soccorso: 3 anni (D.M. 388/2003)
   - Antincendio: 3 anni (D.M. 02/09/2021)
   - HACCP / Alimentaristi: 3 anni (Reg. CE 852/04)
   - Carrellisti/Muletti/PLE/Gru/Macchine: 5 anni (Accordo 22/02/2012)
   - Lavoratori Gen + Specifica: 5 anni (art. 37)
   - RSPP Datore di Lavoro: 5 anni
   - Standard generale: 5 anni
3. Incrocio anagrafica corsisti con 81plus.db (ghl_user360, ghl_contact, network_corsisti)
4. Invio automatico promemoria a 4 scaglioni:
   - PREAVVISO 60GG (tra 50 e 65 giorni) -> 01_AVVISO_60GG.html
   - ATTENZIONE 30GG (tra 20 e 35 giorni) -> 02_AVVISO_30GG.html
   - URGENTE 7GG (tra 1 e 10 giorni) -> 02b_AVVISO_7GG.html
   - BLOCCO SCADUTO (scaduto da <= 0 giorni) -> 03_SCADUTO.html
5. Protezione anti-duplicati su tabella `network_scadenze_alerts`
6. Invio SitRep su Telegram a Mirco (@sicurissimo81_bot)
"""

import os
import sys
import json
import sqlite3
import datetime
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request
import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "81plus.db")
TEMPLATES_DIR = os.path.join(BASE_DIR, "out", "FLOW_SCADENZE_CORSI")

# Credenziali Piattaforma Partner 2377
PARTNER_USER = os.getenv("PARTNER_USER", "mirco.pregnolato@geopec.it")
PARTNER_PASS = os.getenv("PARTNER_PASS", "h29031976T.")
PARTNER_ID = 2377
FAD_URL = "https://corsi.elearningsicurezza.com/pid/2377/#login"
WA_LINK = "https://wa.me/393388771737?text=Richiesta%20Rinnovo%20Attestato%20Scaduto"

# Configurazione SMTP Hostinger Blindato
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "info@81plus.net")
SMTP_PASS = os.getenv("SMTP_PASS", "h29031976T.")

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

def init_scadenze_tables(conn):
    """Inizializza tabelle del monitor scadenze."""
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS network_documenti_emessi (
        docid INTEGER PRIMARY KEY,
        utente_id INTEGER,
        nome TEXT,
        cognome TEXT,
        rag_soc TEXT,
        email TEXT,
        titolo TEXT,
        data_emissione TEXT,
        validita_anni INTEGER DEFAULT 5,
        data_scadenza TEXT,
        giorni_alla_scadenza INTEGER,
        stato_scadenza TEXT,
        last_checked TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS network_scadenze_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        docid INTEGER,
        utente_id INTEGER,
        email TEXT,
        corso_titolo TEXT,
        tipo_alert TEXT,
        data_invio TEXT DEFAULT CURRENT_TIMESTAMP,
        esito TEXT
    );
    """)
    conn.commit()

def calcola_validita_anni(titolo):
    """Determina gli anni di validità legale in base alla tipologia di corso."""
    t = (titolo or "").lower()
    if "rls" in t or "rlst" in t:
        return 1
    if "prepost" in t:
        return 2
    if "primo soccorso" in t:
        return 3
    if "antincendio" in t:
        return 3
    if "haccp" in t or "alimentar" in t or "aliment" in t:
        return 3
    if any(k in t for k in ["carrellist", "mulett", "ple", "gru", "trattor", "terra", "escavator"]):
        return 5
    if "lavorator" in t:
        return 5
    if "rspp" in t:
        return 5
    return 5

def parse_data_italiana(d_str):
    """Esegue il parsing di date in vari formati possibili restituiti da elearningsicurezza."""
    if not d_str:
        return None
    d_clean = d_str.strip()
    # Formati comuni: '5/04/2016 10:22:10 AM', '24/09/2023 15:30:00', '2023-09-24'
    formats = [
        "%d/%m/%Y %I:%M:%S %p",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(d_clean, fmt).date()
        except ValueError:
            pass
    # Tentativo con split sullo spazio
    if " " in d_clean:
        part0 = d_clean.split(" ")[0]
        try:
            parts = part0.split("/")
            if len(parts) == 3:
                return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
        except Exception:
            pass
    return None

def fetch_and_sync_docemessi():
    """Recupera docemessi.asp dalla piattaforma e aggiorna il DB."""
    print("[*] Connessione a elearningsicurezza per sync attestati emessi...")
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-HTTP-Method-Override': 'POST',
        'Origin': 'https://corsi.elearningsicurezza.com',
        'Referer': 'https://corsi.elearningsicurezza.com/network/'
    })
    login_payload = {
        'tx_utente': PARTNER_USER,
        'tx_pass': PARTNER_PASS,
        'UseCookies': '1'
    }
    try:
        r_login = s.post('https://corsi.elearningsicurezza.com/api/partners/login.asp', data=json.dumps(login_payload), timeout=20)
        if r_login.status_code != 200:
            print(f"[-] Login fallito (status {r_login.status_code})")
            return []
        r_doc = s.get('https://corsi.elearningsicurezza.com/api/partners/docemessi.asp', timeout=25).json()
        records = r_doc.get('records', [])
        print(f"[+] Ricevuti {len(records)} attestati/documenti emessi.")
        return records
    except Exception as e:
        print(f"[-] Errore sync docemessi: {e}")
        return []

def run_scadenze_monitor(dry_run=False):
    """Analizza le scadenze e invia i promemoria."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_scadenze_tables(conn)
    cur = conn.cursor()

    records = fetch_and_sync_docemessi()
    today = datetime.date.today()

    count_synced = 0
    count_60d = 0
    count_30d = 0
    count_7d = 0
    count_scaduto = 0
    count_ok = 0
    dispatched_alerts = 0

    for doc in records:
        docid = doc.get('docid')
        uid = doc.get('utente_id')
        nome = (doc.get('nome') or '').strip()
        cognome = (doc.get('cognome') or '').strip()
        rag_soc = (doc.get('rag_soc') or '').strip()
        titolo = (doc.get('titolo') or '').strip()
        created_str = doc.get('docemissione_created') or doc.get('data_incasso')

        d_emissione = parse_data_italiana(created_str)
        if not d_emissione:
            continue

        validita_anni = calcola_validita_anni(titolo)
        try:
            d_scadenza = datetime.date(d_emissione.year + validita_anni, d_emissione.month, d_emissione.day)
        except ValueError:
            # Gestione anni bisestili (29 febbraio)
            d_scadenza = datetime.date(d_emissione.year + validita_anni, d_emissione.month, 28)

        giorni_rimasti = (d_scadenza - today).days

        # Determina lo stato di scadenza
        if giorni_rimasti <= 0:
            stato = "SCADUTO"
            count_scaduto += 1
        elif 1 <= giorni_rimasti <= 10:
            stato = "SCADENZA_IMMINENTE_7D"
            count_7d += 1
        elif 11 <= giorni_rimasti <= 35:
            stato = "SCADENZA_PREAVVISO_30D"
            count_30d += 1
        elif 36 <= giorni_rimasti <= 65:
            stato = "SCADENZA_PREAVVISO_60D"
            count_60d += 1
        else:
            stato = "IN_REGOLA"
            count_ok += 1

        # Cerca email dell'utente
        email = None
        # 1. Da network_corsisti
        cur.execute("SELECT email FROM network_corsisti WHERE utente_id = ? AND email IS NOT NULL AND email != ''", (uid,))
        r_corsista = cur.fetchone()
        if r_corsista and r_corsista['email']:
            email = r_corsista['email'].strip()
        
        # 2. Da ghl_contact per nome/cognome/rag_soc
        if not email:
            cur.execute("""
                SELECT email FROM ghl_contact 
                WHERE (LOWER(nome) = LOWER(?) AND LOWER(cognome) = LOWER(?))
                   OR (LOWER(nome) = LOWER(?) AND LOWER(nome) != '')
                LIMIT 1
            """, (nome, cognome, rag_soc))
            r_ghl = cur.fetchone()
            if r_ghl and r_ghl['email']:
                email = r_ghl['email'].strip()

        # Salva / Aggiorna documento
        cur.execute("""
            INSERT INTO network_documenti_emessi (
                docid, utente_id, nome, cognome, rag_soc, email,
                titolo, data_emissione, validita_anni, data_scadenza,
                giorni_alla_scadenza, stato_scadenza, last_checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(docid) DO UPDATE SET
                email = COALESCE(network_documenti_emessi.email, excluded.email),
                giorni_alla_scadenza = excluded.giorni_alla_scadenza,
                stato_scadenza = excluded.stato_scadenza,
                last_checked = CURRENT_TIMESTAMP
        """, (
            docid, uid, nome, cognome, rag_soc, email,
            titolo, d_emissione.strftime("%d/%m/%Y"), validita_anni,
            d_scadenza.strftime("%d/%m/%Y"), giorni_rimasti, stato
        ))
        count_synced += 1

        # Verifica se inviare alert
        if email and stato in ["SCADUTO", "SCADENZA_IMMINENTE_7D", "SCADENZA_PREAVVISO_30D", "SCADENZA_PREAVVISO_60D"]:
            alert_type_map = {
                "SCADENZA_PREAVVISO_60D": ("60D", "01_AVVISO_60GG.html", f"📋 Preavviso 60 giorni: Il tuo attestato {titolo} è in scadenza"),
                "SCADENZA_PREAVVISO_30D": ("30D", "02_AVVISO_30GG.html", f"⚠️ Mancano 30 giorni: Scadenza imminente attestato {titolo}"),
                "SCADENZA_IMMINENTE_7D": ("7D", "02b_AVVISO_7GG.html", f"⚠️ URGENTE: Mancano solo 7 giorni alla scadenza dell'attestato {titolo}"),
                "SCADUTO": ("SCADUTO", "03_SCADUTO.html", f"🚨 ATTENZIONE: Il tuo attestato {titolo} è SCADUTO")
            }
            alert_code, template_file, email_subj = alert_type_map[stato]

            # Controlla se questo alert è già stato inviato per questo docid negli ultimi 30 giorni
            cur.execute("""
                SELECT id FROM network_scadenze_alerts
                WHERE docid = ? AND tipo_alert = ? AND data_invio >= date('now', '-30 days')
            """, (docid, alert_code))
            if not cur.fetchone():
                tpl_path = os.path.join(TEMPLATES_DIR, template_file)
                if os.path.exists(tpl_path):
                    with open(tpl_path, "r", encoding="utf-8") as f:
                        tpl_html = f.read()

                    # Personalizzazione Variabili
                    full_name = f"{nome} {cognome}".strip() or rag_soc or "Imprenditore"
                    html_content = tpl_html.replace("{{NOME}}", full_name)
                    html_content = html_content.replace("{{AZIENDA}}", rag_soc or "Azienda")
                    html_content = html_content.replace("{{CORSO_TITOLO}}", titolo)
                    html_content = html_content.replace("{{DATA_EMISSIONE}}", d_emissione.strftime("%d/%m/%Y"))
                    html_content = html_content.replace("{{DATA_SCADENZA}}", d_scadenza.strftime("%d/%m/%Y"))
                    html_content = html_content.replace("{{GIORNI_RIMASTI}}", str(abs(giorni_rimasti)))
                    html_content = html_content.replace("{{FAD_LINK}}", FAD_URL)
                    html_content = html_content.replace("{{WHATSAPP_LINK}}", WA_LINK)
                    html_content = html_content.replace("{{UNSUB}}", f"https://81plus.net/unsubscribe.php?email={email}")

                    print(f"[*] ALERT {alert_code} per docid {docid} -> {email} ({titolo}, rimasti: {giorni_rimasti}d)")

                    if not dry_run:
                        try:
                            msg = MIMEMultipart("alternative")
                            msg["Subject"] = email_subj
                            msg["From"] = f"81+ Monitor Sicurezza <{SMTP_USER}>"
                            msg["To"] = email
                            msg.attach(MIMEText(html_content, "html", "utf-8"))

                            context = ssl.create_default_context()
                            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=20) as server:
                                server.login(SMTP_USER, SMTP_PASS)
                                server.sendmail(SMTP_USER, email, msg.as_string())

                            cur.execute("""
                                INSERT INTO network_scadenze_alerts (docid, utente_id, email, corso_titolo, tipo_alert, esito)
                                VALUES (?, ?, ?, ?, ?, 'SENT')
                            """, (docid, uid, email, titolo, alert_code))
                            dispatched_alerts += 1
                        except Exception as e:
                            print(f"[-] Errore invio email a {email}: {e}")
                            cur.execute("""
                                INSERT INTO network_scadenze_alerts (docid, utente_id, email, corso_titolo, tipo_alert, esito)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (docid, uid, email, titolo, alert_code, f"ERROR: {e}"))
                    else:
                        print(f"    [DRY-RUN] Email simulata a {email}: '{email_subj}'")
                        dispatched_alerts += 1

    conn.commit()
    conn.close()

    sitrep = (
        f"📅 <b>81+ SITREP MASTER SCADENZARIO CORSI</b>\n"
        f"⏰ Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"📋 <b>Attestati Monitorati:</b> {count_synced}\n"
        f"🟢 <b>In Regola (>65gg):</b> {count_ok}\n"
        f"🟡 <b>Preavviso 60gg:</b> {count_60d}\n"
        f"🟠 <b>Preavviso 30gg:</b> {count_30d}\n"
        f"🔴 <b>Urgenza Imminente 7gg:</b> {count_7d}\n"
        f"🚨 <b>Scaduti (Ammenda Potenziale):</b> {count_scaduto}\n\n"
        f"🚀 <b>Promemoria Dispatched Oggi:</b> {dispatched_alerts} {'(DRY-RUN)' if dry_run else '(REALI)'}\n"
        f"🔗 <i>Rinnovi convogliati su Partner ID 2377 e canale prioritario WhatsApp.</i>"
    )
    print("\n" + sitrep + "\n")
    tg_notify(sitrep)
    return True

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_scadenze_monitor(dry_run=is_dry)
