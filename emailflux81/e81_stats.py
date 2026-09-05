"""e81_stats.py · Dashboard statistiche invii email 81+.
Scarica il DB, conta le email inviate, e invia report su Telegram."""
import sqlite3, datetime, os, json, urllib.request
from e81_config import DB

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_ADMIN_ID  = os.getenv("TG_ADMIN_ID", "642593407")

def tg(text):
    if not TG_BOT_TOKEN: print("[SKIP] TG_BOT_TOKEN non configurato"); return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_ADMIN_ID, "text": text, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e: print(f"[TG ERR] {e}")

def main():
    if not os.path.exists(DB):
        print(f"DB non trovato: {DB}"); return
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    
    # Conteggio totale email inviate
    try:
        tot = c.execute("SELECT count(*) n FROM ghl_send_log WHERE stato='inviato'").fetchone()["n"]
    except Exception: tot = 0
    try:
        tot_dry = c.execute("SELECT count(*) n FROM ghl_send_log WHERE stato='dry'").fetchone()["n"]
    except Exception: tot_dry = 0
    try:
        tot_err = c.execute("SELECT count(*) n FROM ghl_send_log WHERE stato='errore'").fetchone()["n"]
    except Exception: tot_err = 0
    try:
        tot_guard = c.execute("SELECT count(*) n FROM ghl_send_log WHERE stato='guard_block'").fetchone()["n"]
    except Exception: tot_guard = 0
    
    # Email oggi
    today = datetime.date.today().isoformat()
    try:
        today_sent = c.execute("SELECT count(*) n FROM ghl_send_log WHERE stato='inviato' AND created_at LIKE ?", (today+'%',)).fetchone()["n"]
    except Exception: today_sent = 0
    try:
        today_dry = c.execute("SELECT count(*) n FROM ghl_send_log WHERE stato='dry' AND created_at LIKE ?", (today+'%',)).fetchone()["n"]
    except Exception: today_dry = 0
    
    # Per workflow
    wf_stats = []
    try:
        rows = c.execute("""
            SELECT w.nome, 
                   count(CASE WHEN e.stato='active' THEN 1 END) active,
                   count(CASE WHEN e.stato='done' THEN 1 END) done,
                   count(CASE WHEN e.stato='error' THEN 1 END) err
            FROM ghl_workflow w
            LEFT JOIN ghl_workflow_enrollment e ON e.workflow_id=w.id
            GROUP BY w.nome ORDER BY w.nome
        """).fetchall()
        for r in rows:
            wf_stats.append(f"  - {r['nome']}: {r['active']} attivi, {r['done']} completati, {r['err']} errori")
    except Exception: pass
    
    # Contatti totali
    try:
        contacts = c.execute("SELECT count(*) n FROM ghl_contact").fetchone()["n"]
    except Exception: contacts = 0
    try:
        contacts_active = c.execute("SELECT count(*) n FROM ghl_contact WHERE unsub IS NOT 1 AND consenso=1").fetchone()["n"]
    except Exception: contacts_active = 0
    
    # Workflow totali
    try:
        wf_count = c.execute("SELECT count(*) n FROM ghl_workflow").fetchone()["n"]
    except Exception: wf_count = 0
    
    # Template totali
    try:
        tpl_count = c.execute("SELECT count(*) n FROM ghl_template").fetchone()["n"]
    except Exception: tpl_count = 0
    
    c.close()
    
    report = f"""
=== 81+ EMAILFLUX DASHBOARD ===
Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}

INVII TOTALI:
  Inviate reali:    {tot:,}
  Dry-run (test):   {tot_dry:,}
  Errori:           {tot_err:,}
  Guard block:      {tot_guard:,}
  TOTALE PROCESSATE: {tot+tot_dry+tot_err+tot_guard:,}

OGGI ({today}):
  Inviate reali:    {today_sent:,}
  Dry-run:          {today_dry:,}

DATABASE:
  Contatti totali:  {contacts:,}
  Contatti attivi:  {contacts_active:,}
  Workflow:         {wf_count}
  Template:         {tpl_count}

WORKFLOW DETTAGLIO:
{chr(10).join(wf_stats) if wf_stats else '  (nessun workflow trovato)'}
================================
"""
    print(report)
    
    # Report Telegram
    tg_msg = (
        f"*81+ EMAILFLUX DASHBOARD*\n"
        f"_{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}_\n\n"
        f"*Inviate reali:* `{tot:,}`\n"
        f"*Dry-run:* `{tot_dry:,}`\n"
        f"*Errori:* `{tot_err:,}`\n"
        f"*Oggi inviate:* `{today_sent:,}`\n"
        f"*Oggi dry-run:* `{today_dry:,}`\n\n"
        f"*Contatti attivi:* `{contacts_active:,}` / `{contacts:,}`\n"
        f"*Workflow:* `{wf_count}` · *Template:* `{tpl_count}`"
    )
    tg(tg_msg)

if __name__ == "__main__": main()
