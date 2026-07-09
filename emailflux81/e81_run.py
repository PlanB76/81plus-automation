"""e81_run.py · WORKER H24 sul DB UNICO. Invia lo step scaduto, avanza.
Extra: i flussi FLOW_PROFILO_* ESCONO da soli quando users.profilo_completo=1.
FLOW_PROFILO_REMINDER e' CICLICO: riparte ogni REMINDER_DAYS finche' il profilo non e' completo.
DRY_RUN=1 (default) NON invia. Rispetta DAILY_CAP e BATCH."""
import json, datetime, time, urllib.parse, re
from e81_db import con, sub_id
from e81_config import BASE_URL, DRY_RUN, DAILY_CAP, BATCH, THROTTLE
from e81_guard import violations
from e81_transport import send

REMINDER_DAYS = 14  # cadenza del reminder ciclico profilo

def profilo_completo(c, sic):
    """1 se il profilo utente e' completo, 0 se no, None se non determinabile."""
    if not sic: return None
    try:
        r=c.execute("SELECT profilo_completo FROM users WHERE sic=?",(sic,)).fetchone()
        if r is None: return 0
        return 1 if (r[0]==1 or r[0]=='1') else 0
    except Exception:
        return None  # tabella users assente in questo DB

def render(html, subject, contact, send_id):
    nome=contact["nome"] or "titolare"; email=contact["email"]; sic=contact["sic"] or ""
    unsub=f"{BASE_URL}/u/?e="+urllib.parse.quote(email)
    for k,v in {"{nome}":nome,"{{NOME}}":nome,"{{EMAIL}}":email,"{email}":email,
                "{{UNSUB}}":unsub,"{unsub_url}":unsub,"{tg_group_url}":BASE_URL+"/area"}.items():
        html=html.replace(k,v); subject=subject.replace(k,v)
    def _wrap(m):
        url=m.group(1)
        if url.startswith("mailto:") or "/u/?" in url or "/track_" in url: return m.group(0)
        return 'href="%s/track_click.php?c=%s&s=%s&u=%s"'%(BASE_URL,urllib.parse.quote(sic),send_id,urllib.parse.quote(url,safe=""))
    html=re.sub(r'href="([^"]+)"',_wrap,html)
    pixel=f'<img src="{BASE_URL}/track_open.php?c={urllib.parse.quote(sic)}&s={send_id}" width="1" height="1" alt="" style="display:none">'
    footer=(f'<div style="font:12px system-ui;color:#8a8a8a;text-align:center;padding:18px">'
            f'81+ · SICURISSIMO · welcome@81plus.net<br>Ricevi questa email come cliente storico Sicurissimo/81+. '
            f'<a href="{unsub}" style="color:#8a8a8a">Disiscriviti</a></div>')
    if "</body>" in html.lower(): html=re.sub(r"</body>",pixel+footer+"</body>",html,count=1,flags=re.I)
    else: html=html+pixel+footer
    return subject, html

def sent_today(c):
    d=datetime.date.today().isoformat()
    return c.execute("SELECT count(*) FROM ghl_send_log WHERE stato='inviato' AND created_at LIKE ?", (d+'%',)).fetchone()[0]

def main():
    c=con(); sub=sub_id(c); now=datetime.datetime.utcnow(); nows=now.isoformat()
    cap_left=max(0, DAILY_CAP - sent_today(c))
    if cap_left<=0 and not DRY_RUN: print("DAILY_CAP raggiunto per oggi."); c.close(); return
    limit=min(BATCH, cap_left if not DRY_RUN else BATCH)
    due=c.execute("""SELECT e.id eid, e.workflow_id, e.contact_id, e.step_corrente, w.nome wf_nome,
                            k.email,k.nome,k.sic,k.consenso,k.unsub
                     FROM ghl_workflow_enrollment e
                     JOIN ghl_contact k ON k.id=e.contact_id
                     JOIN ghl_workflow w ON w.id=e.workflow_id
                     WHERE e.stato='active' AND e.next_at<=? AND (k.unsub IS NOT 1) AND k.consenso=1
                     ORDER BY e.next_at LIMIT ?""",(nows,limit)).fetchall()
    print(f"da processare: {len(due)} · DRY_RUN={DRY_RUN} · cap_left={cap_left}")
    done=0
    for e in due:
        wfname=e["wf_nome"] or ""
        # USCITA automatica: se e' un flusso profilo e il profilo e' completo -> esci
        if wfname.startswith("FLOW_PROFILO") and profilo_completo(c,e["sic"])==1:
            c.execute("UPDATE ghl_workflow_enrollment SET stato='done' WHERE id=?",(e["eid"],)); continue
        wf=c.execute("SELECT azioni_json FROM ghl_workflow WHERE id=?",(e["workflow_id"],)).fetchone()
        steps=json.loads(wf["azioni_json"] or "[]"); i=e["step_corrente"]
        if i>=len(steps): c.execute("UPDATE ghl_workflow_enrollment SET stato='done' WHERE id=?",(e["eid"],)); continue
        step=steps[i]
        tpl=c.execute("SELECT id,oggetto,corpo FROM ghl_template WHERE flow_key=?",(step["template"],)).fetchone()
        if not tpl: c.execute("UPDATE ghl_workflow_enrollment SET stato='error' WHERE id=?",(e["eid"],)); continue
        subj,html=render(tpl["corpo"], step.get("subject") or tpl["oggetto"], e, e["eid"])
        v=violations(subj)+violations(html)
        if v:
            c.execute("INSERT INTO ghl_send_log(sub_account_id,contact_id,canale,template_id,stato,errore) VALUES(?,?,?,?,?,?)",
                      (sub,e["contact_id"],'email',tpl["id"],"guard_block",",".join(v)))
        else:
            try:
                if DRY_RUN: stato="dry"; err=None
                else:
                    unsub=f"{BASE_URL}/u/?e="+urllib.parse.quote(e["email"]); send(e["email"],subj,html,unsub); stato="inviato"; err=None; time.sleep(THROTTLE)
            except Exception as ex: stato="errore"; err=str(ex)[:300]
            c.execute("INSERT INTO ghl_send_log(sub_account_id,contact_id,canale,template_id,stato,errore) VALUES(?,?,?,?,?,?)",
                      (sub,e["contact_id"],'email',tpl["id"],stato,err))
        # AVANZAMENTO
        ni=i+1
        is_reminder = (wfname=="FLOW_PROFILO_REMINDER")
        if ni>=len(steps):
            if is_reminder and profilo_completo(c,e["sic"])!=1:
                # CICLICO: riparte da capo tra REMINDER_DAYS finche' il profilo non e' completo
                nxt=(now+datetime.timedelta(days=REMINDER_DAYS)).isoformat()
                c.execute("UPDATE ghl_workflow_enrollment SET step_corrente=0, next_at=?, stato='active' WHERE id=?",(nxt,e["eid"]))
            else:
                c.execute("UPDATE ghl_workflow_enrollment SET step_corrente=?, stato='done' WHERE id=?",(ni,e["eid"]))
        else:
            delta=max(0, steps[ni]["delay_gg"]-step["delay_gg"])
            nxt=(now+datetime.timedelta(days=delta)).isoformat()
            c.execute("UPDATE ghl_workflow_enrollment SET step_corrente=?, next_at=? WHERE id=?",(ni,nxt,e["eid"]))
        done+=1
    c.commit(); c.close(); print(f"processate: {done}")
if __name__=="__main__": main()
