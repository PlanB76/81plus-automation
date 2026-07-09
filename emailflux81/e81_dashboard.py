"""e81_dashboard.py · genera email81_report.html dal DB UNICO (ghl_*)."""
import os, datetime
from e81_db import con
def main():
    c=con()
    tot=c.execute("SELECT count(*) FROM ghl_contact").fetchone()[0]
    optin=c.execute("SELECT count(*) FROM ghl_contact WHERE consenso=1").fetchone()[0]
    unsub=c.execute("SELECT count(*) FROM ghl_contact WHERE unsub=1").fetchone()[0]
    tpl=c.execute("SELECT count(*) FROM ghl_template").fetchone()[0]
    wf=c.execute("SELECT count(*) FROM ghl_workflow").fetchone()[0]
    enr=c.execute("SELECT count(*) FROM ghl_workflow_enrollment WHERE stato='active'").fetchone()[0]
    sent=c.execute("SELECT count(*) FROM ghl_send_log WHERE stato='inviato'").fetchone()[0]
    dry=c.execute("SELECT count(*) FROM ghl_send_log WHERE stato='dry'").fetchone()[0]
    blk=c.execute("SELECT count(*) FROM ghl_send_log WHERE stato='guard_block'").fetchone()[0]
    top=c.execute("""SELECT w.nome, count(*) n FROM ghl_workflow_enrollment e
                     JOIN ghl_workflow w ON w.id=e.workflow_id GROUP BY w.nome ORDER BY n DESC LIMIT 10""").fetchall()
    c.close()
    rows="".join(f"<tr><td>{r['nome']}</td><td style='text-align:right'>{r['n']}</td></tr>" for r in top) or "<tr><td colspan=2>—</td></tr>"
    html=f"""<!doctype html><meta charset=utf-8><title>EMAIL81+ Report</title>
<body style="font:15px system-ui;background:#0b0e14;color:#e8eef7;max-width:820px;margin:24px auto;padding:0 16px">
<h1>📧 EMAIL81+ · Report</h1><p style="color:#8aa">DB unico universale · {datetime.datetime.now():%Y-%m-%d %H:%M}</p>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0">
{''.join(f'<div style="background:#151a24;border:1px solid #223;border-radius:12px;padding:14px"><div style="font-size:26px;font-weight:700">{v}</div><div style="color:#8aa;font-size:12px">{k}</div></div>' for k,v in [('Contatti',tot),('Opt-in',optin),('Disiscritti',unsub),('Template',tpl),('Flussi',wf),('Iscrizioni attive',enr),('Inviate',sent),('Dry / Bloccate',f'{dry}/{blk}')])}
</div>
<h3>Top flussi per iscrizioni</h3>
<table style="width:100%;border-collapse:collapse"><tr style="color:#8aa"><th style="text-align:left">Flusso</th><th style="text-align:right">Iscritti</th></tr>{rows}</table>
</body>"""
    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"email81_report.html")
    open(out,"w",encoding="utf-8").write(html); print("dashboard:", out)
if __name__=="__main__": main()
