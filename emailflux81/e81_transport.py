"""e81_transport.py · invio email. Provider: hostinger (SMTP, attivo) | brevo (standby)."""
import os, smtplib, ssl, json, urllib.request
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from e81_config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_FROM, REPLY_TO

def send_hostinger(to_email, subject, html, list_unsub_url):
    msg=MIMEText(html, "html", "utf-8")
    msg["Subject"]=subject; msg["From"]=MAIL_FROM; msg["To"]=to_email
    msg["Reply-To"]=REPLY_TO; msg["Message-ID"]=make_msgid(domain="81plus.net")
    msg["List-Unsubscribe"]=f"<{list_unsub_url}>"
    msg["List-Unsubscribe-Post"]="List-Unsubscribe=One-Click"
    ctx=ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [to_email], msg.as_string())
    return "smtp-ok"

def send_brevo(to_email, subject, html, list_unsub_url):
    # STANDBY: attivo solo se PROVIDER=brevo e BREVO_KEY presente.
    key=os.getenv("BREVO_KEY","")
    if not key: raise RuntimeError("BREVO in standby: manca BREVO_KEY")
    payload={"sender":{"name":"81+ · SICURISSIMO","email":"welcome@81plus.net"},
             "to":[{"email":to_email}],"subject":subject,"htmlContent":html,
             "headers":{"List-Unsubscribe":f"<{list_unsub_url}>"}}
    req=urllib.request.Request("https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode(), method="POST",
        headers={"api-key":key,"content-type":"application/json","accept":"application/json"})
    with urllib.request.urlopen(req) as r: return "brevo-"+str(r.status)

def send(to_email, subject, html, list_unsub_url):
    prov=os.getenv("PROVIDER","hostinger").lower()
    return (send_brevo if prov=="brevo" else send_hostinger)(to_email, subject, html, list_unsub_url)
