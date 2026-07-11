"""81+ GUARDIAN · esecutore gating gruppi Telegram (GitHub Actions, PC spento).
Ogni run: scarica il PIANO da guardian_plan.php (cervello che legge il DB unico) ed esegue:
  - invite : crea invite-link monouso al gruppo del tier e lo manda in DM all'utente
  - kick   : banChatMember + unbanChatMember (rimuove ma consente rientro futuro)
  - remind : DM di promemoria scadenza
Poi manda un recap all'admin e fa ACK al sito (aggiorna tg_membership).
Sicuro: se il piano e' vuoto (nessun membro attivo/collegato) non fa nulla.

ENV (GitHub Secrets):
  BOT_GUARDIAN_TOKEN   token @sicurissimonewbot
  GUARDIAN_PLAN_URL    https://81plus.net/api/guardian_plan.php   (default)
  GUARDIAN_ACK_URL     https://81plus.net/api/guardian_ack.php    (default)
  ADMIN_KEY            chiave per il cervello/ack
  ADMIN_CHAT           642593407 (default)
"""
import os, json, time, urllib.parse, urllib.request

TOKEN = os.environ.get("BOT_GUARDIAN_TOKEN", "")
PLAN_URL = os.environ.get("GUARDIAN_PLAN_URL", "https://81plus.net/api/guardian_plan.php")
ACK_URL  = os.environ.get("GUARDIAN_ACK_URL",  "https://81plus.net/api/guardian_ack.php")
KEY = os.environ.get("ADMIN_KEY", "SCOUT81-OWNER-2026")
ADMIN = os.environ.get("ADMIN_CHAT", "642593407")

def api(method, fields):
    url = "https://api.telegram.org/bot%s/%s" % (TOKEN, method)
    data = urllib.parse.urlencode(fields).encode()
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=40).read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def http_json(url):
    try:
        return json.loads(urllib.request.urlopen(url, timeout=40).read())
    except Exception as e:
        return {"error": str(e)}

def dm(chat_id, text):
    return api("sendMessage", {"chat_id": chat_id, "text": text[:4096], "disable_web_page_preview": "true"})

def invite_link(chat_id):
    r = api("createChatInviteLink", {"chat_id": chat_id, "member_limit": 1,
            "name": "81+ member %d" % int(time.time())})
    return r.get("result", {}).get("invite_link") if r.get("ok") else None

def do_invite(item):
    link = invite_link(item["chat_id"])
    if not link:
        return {"action":"invite","sic":item["sic"],"chat_id":item["chat_id"],"result":"no-link"}
    r = dm(item["tg_id"],
           "\U0001F513 Il tuo accesso 81+ %s e' pronto.\nEntra nel gruppo privato del tuo livello:\n%s"
           % (item.get("tier", ""), link))
    return {"action":"invite","sic":item["sic"],"chat_id":item["chat_id"],
            "result":"ok" if r.get("ok") else r.get("error","dm-fail")}

def do_kick(item):
    api("banChatMember", {"chat_id": item["chat_id"], "user_id": item["tg_id"]})
    api("unbanChatMember", {"chat_id": item["chat_id"], "user_id": item["tg_id"], "only_if_banned": "true"})
    return {"action":"kick","sic":item["sic"],"chat_id":item["chat_id"],"result":"done"}

def do_remind(item):
    r = dm(item["tg_id"],
           "⏳ La tua membership 81+ %s scade tra %s giorni (%s).\nRinnova per restare nel gruppo privato: https://81plus.net"
           % (item.get("tier", ""), item.get("giorni", "?"), item.get("scade", "")))
    return {"action":"remind","sic":item["sic"],"chat_id":item.get("chat_id",0),
            "result":"ok" if r.get("ok") else "dm-fail"}

def main():
    if not TOKEN:
        print("[guardian] BOT_GUARDIAN_TOKEN mancante — skip"); return
    plan = http_json("%s?key=%s" % (PLAN_URL, urllib.parse.quote(KEY)))
    if plan.get("error") or not plan.get("ok"):
        print("[guardian] piano non disponibile:", plan); return
    st = plan.get("stats", {})
    print("[guardian] piano:", json.dumps(st))
    done = []
    for it in plan.get("invite", []): done.append(do_invite(it)); time.sleep(0.4)
    for it in plan.get("kick", []):   done.append(do_kick(it));   time.sleep(0.3)
    for it in plan.get("remind", []): done.append(do_remind(it)); time.sleep(0.3)
    # ACK al sito per aggiornare tg_membership (best effort)
    try:
        payload = urllib.parse.urlencode({"key": KEY, "done": json.dumps(done)}).encode()
        urllib.request.urlopen(urllib.request.Request(ACK_URL, data=payload), timeout=30).read()
    except Exception as e:
        print("[guardian] ack skip:", e)
    # recap admin solo se c'e' stato movimento
    if done:
        recap = "\U0001F6E1 GUARDIAN 81+\ninvite:%d kick:%d remind:%d\n" % (st.get("invite",0), st.get("kick",0), st.get("remind",0))
        recap += "\n".join("%s %s -> %s" % d for d in done[:40])
        dm(ADMIN, recap)
    print("[guardian] fatto:", len(done), "azioni")

if __name__ == "__main__":
    main()
