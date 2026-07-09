"""e81_db.py · connessione al DB UNICO universale (81plus.db).
NON crea DB separati. Usa le tabelle ghl_* gia' presenti; garantisce solo indici/colonne minime."""
import sqlite3
from e81_config import DB

def con():
    c=sqlite3.connect(DB, timeout=15); c.row_factory=sqlite3.Row
    c.execute("PRAGMA busy_timeout=15000")
    # sicurezza: tabelle ghl_* devono esistere (nel DB universale ci sono gia'); creo se mancano, schema reale
    c.executescript("""
    CREATE TABLE IF NOT EXISTS ghl_template(
      id INTEGER PRIMARY KEY AUTOINCREMENT, sub_account_id INTEGER, nome TEXT, canale TEXT,
      oggetto TEXT, corpo TEXT, flow_key TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS ghl_workflow(
      id INTEGER PRIMARY KEY AUTOINCREMENT, sub_account_id INTEGER, nome TEXT,
      trigger_json TEXT, condizioni_json TEXT, azioni_json TEXT, attivo INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS ghl_workflow_enrollment(
      id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id INTEGER, contact_id INTEGER,
      step_corrente INTEGER DEFAULT 0, next_at TEXT, stato TEXT DEFAULT 'active',
      enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS ghl_send_log(
      id INTEGER PRIMARY KEY AUTOINCREMENT, sub_account_id INTEGER, contact_id INTEGER,
      canale TEXT, template_id INTEGER, campaign_id INTEGER, stato TEXT, provider_id TEXT,
      errore TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE UNIQUE INDEX IF NOT EXISTS k_tpl_flow ON ghl_template(flow_key);
    CREATE UNIQUE INDEX IF NOT EXISTS k_wf_nome ON ghl_workflow(nome);
    CREATE UNIQUE INDEX IF NOT EXISTS k_enr_uni ON ghl_workflow_enrollment(workflow_id, contact_id);
    CREATE INDEX IF NOT EXISTS k_enr_due ON ghl_workflow_enrollment(next_at, stato);
    CREATE INDEX IF NOT EXISTS k_sl_created ON ghl_send_log(created_at);
    """)
    c.commit(); return c

def sub_id(c):
    """id del sub-account 81+ (lo crea se manca, con agency 81+). sub_account_id NOT NULL su ghl_template/workflow/send_log."""
    cur=c.cursor()
    r=cur.execute("SELECT id FROM ghl_sub_account ORDER BY id LIMIT 1").fetchone()
    if r: return r[0]
    a=cur.execute("SELECT id FROM ghl_agency ORDER BY id LIMIT 1").fetchone()
    if a: aid=a[0]
    else:
        cur.execute("INSERT INTO ghl_agency(nome,dominio) VALUES('81+ SICURISSIMO','81plus.net')"); aid=cur.lastrowid
    cur.execute("INSERT INTO ghl_sub_account(agency_id,nome,hub_code) VALUES(?,'SICURISSIMO 81+','06')",(aid,))
    sid=cur.lastrowid; c.commit(); return sid
