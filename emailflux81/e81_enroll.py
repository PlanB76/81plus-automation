"""e81_enroll.py · Auto-enrollment: iscrive nuovi contatti ai workflow giusti.
Gira dopo il worker; per ogni contatto che NON ha enrollment attivi, crea quelli appropriati.
Logica:
  - TUTTI ricevono FLOW_WELCOME
  - Chi non ha completato il profilo: FLOW_PROFILO_REMINDER (gia' gestito in e81_run.py)
  - In base al tag/settore: FLOW_NURTURE_SICUREZZA, _HACCP, _PRIVACY
  - Se inattivo da 90gg: FLOW_WINBACK
"""
import json, datetime
from e81_db import con

FLOWS = {
    "FLOW_WELCOME": {
        "trigger": "new_contact",
        "azioni": [
            {"template": "FLOW_WELCOME/01_BENVENUTO", "delay_gg": 0, "subject": "Benvenuto nel Presidio 81+ \u00b7 {nome}"},
            {"template": "FLOW_WELCOME/02_VALORE",    "delay_gg": 2, "subject": "{nome}, la checklist che ogni imprenditore dovrebbe avere sulla scrivania"},
            {"template": "FLOW_WELCOME/03_PROFILO",    "delay_gg": 5, "subject": "{nome}, completa il tuo profilo e sblocca il Collaudo 81 personalizzato"},
        ]
    },
    "FLOW_NURTURE_SICUREZZA": {
        "trigger": "tag_sicurezza",
        "azioni": [
            {"template": "FLOW_NURTURE_SICUREZZA/01_PATENTE_CREDITI", "delay_gg": 0,  "subject": "\u26a0\ufe0f {nome}, la Patente a Crediti spiegata in 3 minuti"},
            {"template": "FLOW_NURTURE_SICUREZZA/02_SANZIONI",        "delay_gg": 3,  "subject": "\U0001f4b0 {nome}, le 7 sanzioni che il tuo consulente non ti ha mai detto"},
            {"template": "FLOW_NURTURE_SICUREZZA/03_CASO_STUDIO",     "delay_gg": 7,  "subject": "\U0001f3d7\ufe0f {nome}, il cantiere bloccato 20 giorni (storia vera)"},
            {"template": "FLOW_NURTURE_SICUREZZA/04_CHECKLIST",       "delay_gg": 10, "subject": "\U0001f4cb {nome}, ecco i 30 punti che l'ispettore controlla"},
            {"template": "FLOW_NURTURE_SICUREZZA/05_COLLAUDO81",      "delay_gg": 14, "subject": "\U0001f3af {nome}, \u00e8 il momento di blindare la tua azienda"},
        ]
    },
    "FLOW_NURTURE_HACCP": {
        "trigger": "tag_haccp",
        "azioni": [
            {"template": "FLOW_NURTURE_HACCP/01_NAS_ASL",     "delay_gg": 0,  "subject": "\U0001f37d\ufe0f {nome}, come funzionano davvero i controlli NAS"},
            {"template": "FLOW_NURTURE_HACCP/02_ERRORI",       "delay_gg": 3,  "subject": "\u274c {nome}, i 5 errori HACCP che costano la chiusura"},
            {"template": "FLOW_NURTURE_HACCP/03_FORMAZIONE",   "delay_gg": 7,  "subject": "\U0001f393 {nome}, forma il tuo staff HACCP a zero anticipo"},
            {"template": "FLOW_NURTURE_HACCP/04_CTA_CORSI",    "delay_gg": 12, "subject": "\u23f0 {nome}, gli attestati HACCP del tuo personale sono in regola?"},
        ]
    },
    "FLOW_NURTURE_PRIVACY": {
        "trigger": "tag_privacy",
        "azioni": [
            {"template": "FLOW_NURTURE_PRIVACY/01_TELECAMERE", "delay_gg": 0,  "subject": "\U0001f512 {nome}, le telecamere in azienda possono costarti il penale"},
            {"template": "FLOW_NURTURE_PRIVACY/02_GDPR_BASE",  "delay_gg": 3,  "subject": "\U0001f4cb {nome}, il GDPR spiegato in 10 minuti per la tua PMI"},
            {"template": "FLOW_NURTURE_PRIVACY/03_ISTANZA_ITL", "delay_gg": 7, "subject": "\U0001f4dd {nome}, come fare l'istanza ITL per le telecamere"},
            {"template": "FLOW_NURTURE_PRIVACY/04_CTA_PRIVACY", "delay_gg": 12,"subject": "\U0001f3af {nome}, metti in sicurezza la tua azienda dal rischio GDPR"},
        ]
    },
    "FLOW_POST_ACQUISTO": {
        "trigger": "purchase",
        "azioni": [
            {"template": "FLOW_POST_ACQUISTO/01_GRAZIE",     "delay_gg": 0, "subject": "\U0001f64f Grazie {nome}! Ecco cosa succede adesso"},
            {"template": "FLOW_POST_ACQUISTO/02_ONBOARDING", "delay_gg": 2, "subject": "\U0001f680 {nome}, come ottenere il massimo dal tuo servizio 81+"},
            {"template": "FLOW_POST_ACQUISTO/03_REFERRAL",   "delay_gg": 7, "subject": "\U0001f91d {nome}, porta un collega e ottieni un bonus esclusivo"},
        ]
    },
    "FLOW_WINBACK": {
        "trigger": "inactive_90d",
        "azioni": [
            {"template": "FLOW_WINBACK/01_CI_MANCHI",      "delay_gg": 0,  "subject": "{nome}, ci manchi! Ecco un'offerta speciale per te"},
            {"template": "FLOW_WINBACK/02_ULTIMO_TRENO",   "delay_gg": 5,  "subject": "\u23f0 {nome}, la tua offerta -15% scade tra 48 ore"},
            {"template": "FLOW_WINBACK/03_ARRIVEDERCI",    "delay_gg": 10, "subject": "{nome}, arrivederci dal Presidio 81+"},
        ]
    },
    "FLOW_BIRTHDAY_ANNUALE": {
        "trigger": "birthday",
        "azioni": [
            {"template": "FLOW_BIRTHDAY_ANNUALE/01_AUGURI",          "delay_gg": 0, "subject": "\U0001f382 Tanti auguri {nome}! Un regalo da 81+"},
            {"template": "FLOW_BIRTHDAY_ANNUALE/02_SCADENZA_BUONO",  "delay_gg": 25,"subject": "\u23f0 {nome}, il tuo buono compleanno scade tra 5 giorni!"},
        ]
    },
    "FLOW_SCADENZE_CORSI": {
        "trigger": "cert_expiry",
        "azioni": [
            {"template": "FLOW_SCADENZE_CORSI/01_AVVISO_60GG", "delay_gg": 0,  "subject": "\U0001f4cb {nome}, il tuo attestato scade tra 60 giorni"},
            {"template": "FLOW_SCADENZE_CORSI/02_AVVISO_30GG", "delay_gg": 30, "subject": "\u26a0\ufe0f {nome}, mancano 30 giorni alla scadenza del tuo attestato!"},
            {"template": "FLOW_SCADENZE_CORSI/03_SCADUTO",     "delay_gg": 60, "subject": "\U0001f6a8 {nome}, il tuo attestato \u00e8 SCADUTO"},
        ]
    },
}


def ensure_workflows(c, sub):
    """Garantisce che tutti i workflow e template esistano nel DB."""
    for wf_name, wf_data in FLOWS.items():
        # Workflow
        existing = c.execute("SELECT id FROM ghl_workflow WHERE nome=?", (wf_name,)).fetchone()
        if existing:
            wf_id = existing[0]
            c.execute("UPDATE ghl_workflow SET azioni_json=?, attivo=1 WHERE id=?",
                      (json.dumps(wf_data["azioni"]), wf_id))
        else:
            c.execute("INSERT INTO ghl_workflow(sub_account_id,nome,trigger_json,azioni_json,attivo) VALUES(?,?,?,?,1)",
                      (sub, wf_name, json.dumps({"event": wf_data["trigger"]}), json.dumps(wf_data["azioni"])))
            wf_id = c.execute("SELECT id FROM ghl_workflow WHERE nome=?", (wf_name,)).fetchone()[0]
        
        # Template per ogni step
        for step in wf_data["azioni"]:
            flow_key = step["template"]
            tpl_path_local = f"out/{flow_key.replace('/', chr(92)) if chr(92) in '' else flow_key}.html"
            # Prova a leggere il file HTML locale
            import os
            here = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(here, "out", *flow_key.split("/")) + ".html" if "/" in flow_key else ""
            corpo = ""
            if html_path and os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    corpo = f.read()
            
            existing_tpl = c.execute("SELECT id FROM ghl_template WHERE flow_key=?", (flow_key,)).fetchone()
            if existing_tpl:
                if corpo:
                    c.execute("UPDATE ghl_template SET corpo=?, oggetto=? WHERE flow_key=?",
                              (corpo, step["subject"], flow_key))
            else:
                c.execute("INSERT INTO ghl_template(sub_account_id,nome,canale,oggetto,corpo,flow_key) VALUES(?,?,?,?,?,?)",
                          (sub, flow_key, "email", step["subject"], corpo, flow_key))
    c.commit()
    print(f"[OK] {len(FLOWS)} workflow e relativi template sincronizzati nel DB.")


def auto_enroll_welcome(c):
    """Iscrive al FLOW_WELCOME tutti i contatti che non ci sono ancora."""
    wf = c.execute("SELECT id FROM ghl_workflow WHERE nome='FLOW_WELCOME'").fetchone()
    if not wf: print("[SKIP] FLOW_WELCOME non trovato"); return
    wf_id = wf[0]
    now = datetime.datetime.utcnow().isoformat()
    
    # Trova contatti attivi senza enrollment in FLOW_WELCOME
    new_contacts = c.execute("""
        SELECT k.id FROM ghl_contact k
        WHERE k.unsub IS NOT 1 AND k.consenso=1
        AND k.id NOT IN (SELECT contact_id FROM ghl_workflow_enrollment WHERE workflow_id=?)
        LIMIT 200
    """, (wf_id,)).fetchall()
    
    enrolled = 0
    for contact in new_contacts:
        try:
            c.execute("INSERT INTO ghl_workflow_enrollment(workflow_id,contact_id,step_corrente,next_at,stato) VALUES(?,?,0,?,'active')",
                      (wf_id, contact[0], now))
            enrolled += 1
        except Exception:
            pass  # UNIQUE constraint = gia' iscritto
    c.commit()
    print(f"[ENROLL] Welcome: {enrolled} nuovi contatti iscritti su {len(new_contacts)} candidati.")


def auto_enroll_nurture_all(c):
    """Iscrive tutti i contatti attivi ai 3 nurture (sicurezza, haccp, privacy).
    Per semplicita', tutti ricevono tutti e 3 i pilastri."""
    now = datetime.datetime.utcnow()
    for nurture in ["FLOW_NURTURE_SICUREZZA", "FLOW_NURTURE_HACCP", "FLOW_NURTURE_PRIVACY"]:
        wf = c.execute("SELECT id FROM ghl_workflow WHERE nome=?", (nurture,)).fetchone()
        if not wf: continue
        wf_id = wf[0]
        # Delay: nurture partono 7gg dopo il welcome
        start_at = (now + datetime.timedelta(days=7)).isoformat()
        
        new = c.execute("""
            SELECT k.id FROM ghl_contact k
            WHERE k.unsub IS NOT 1 AND k.consenso=1
            AND k.id NOT IN (SELECT contact_id FROM ghl_workflow_enrollment WHERE workflow_id=?)
            LIMIT 100
        """, (wf_id,)).fetchall()
        
        enrolled = 0
        for contact in new:
            try:
                c.execute("INSERT INTO ghl_workflow_enrollment(workflow_id,contact_id,step_corrente,next_at,stato) VALUES(?,?,0,?,'active')",
                          (wf_id, contact[0], start_at))
                enrolled += 1
            except Exception:
                pass
        print(f"[ENROLL] {nurture}: {enrolled} nuovi iscritti")
    c.commit()


def main():
    from e81_db import con as db_con, sub_id
    c = db_con()
    sub = sub_id(c)
    
    print("=== E81 ENROLL: Sincronizzazione workflow e auto-enrollment ===")
    ensure_workflows(c, sub)
    auto_enroll_welcome(c)
    auto_enroll_nurture_all(c)
    
    # Stats rapido
    tot_enr = c.execute("SELECT count(*) FROM ghl_workflow_enrollment").fetchone()[0]
    tot_active = c.execute("SELECT count(*) FROM ghl_workflow_enrollment WHERE stato='active'").fetchone()[0]
    print(f"\n[TOTALE] Enrollment: {tot_enr} totali, {tot_active} attivi")
    c.close()

if __name__ == "__main__": main()
