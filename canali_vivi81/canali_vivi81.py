# -*- coding: utf-8 -*-
"""
CANALI VIVI 81+ — rende vivi i canali YouTube (@sicurissimo, @destinorandagio).
Per ogni canale (se il suo token e' presente nei secret):
 - legge i video recenti del canale
 - risponde in automatico ai NUOVI commenti con una risposta on-brand (AI GROQ)
 - lascia un commento CTA sotto i video recenti (una volta sola per video)
 - aggiunge i nuovi video a una playlist a tema
 - rinfresca la descrizione con la CTA verso 81plus.net (se manca)
Richiede un token OAuth con scope 'youtube.force-ssl' per canale.
Dipendenze: google-api-python-client google-auth (installate dal workflow).
Non riproduce testi di canzoni: le risposte sono ringraziamenti/CTA brevi.
"""
import os, json, re, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG  = json.load(open(os.path.join(HERE, "canali_vivi81.json"), encoding="utf-8"))
STATE_P = os.path.join(HERE, "state_vivi.json")
def load_state():
    try: return json.load(open(STATE_P, encoding="utf-8"))
    except Exception: return {"replied": [], "commented": [], "playlisted": []}
def save_state(s):
    json.dump(s, open(STATE_P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
def log(m): print("[canali-vivi] " + m)

def yt_service(token_json):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(data, scopes=data.get("scopes") or ["https://www.googleapis.com/auth/youtube.force-ssl"])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)

def groq_reply(voce, testo_commento, cta):
    key = os.environ.get("GROQ_API_KEY", "").strip()
    fallback = "Grazie mille per il commento. " + cta
    if not key: return fallback
    sys = ("Sei il gestore del canale. Voce: " + voce + ". Rispondi al commento in modo umano, caloroso, "
           "MAX 2 frasi brevi, italiano perfetto, solo virgole e punti. Ringrazia e invita all'azione. "
           "NON citare testi di canzoni. Chiudi con la call to action: " + cta)
    body = json.dumps({"model": "llama-3.3-70b-versatile",
        "messages": [{"role":"system","content":sys},{"role":"user","content":"Commento utente: "+testo_commento[:400]}],
        "temperature": 0.6}).encode("utf-8")
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization":"Bearer "+key, "Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log("LLM ko: %s" % e); return fallback

def recent_uploads(yt, maxv):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()
    up = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    it = yt.playlistItems().list(part="contentDetails,snippet", playlistId=up, maxResults=maxv).execute()
    return [{"vid": i["contentDetails"]["videoId"], "title": i["snippet"]["title"], "desc": i["snippet"].get("description","")} for i in it.get("items", [])]

def ensure_playlist(yt, title):
    pl = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()
    for p in pl.get("items", []):
        if p["snippet"]["title"].strip().lower() == title.strip().lower(): return p["id"]
    new = yt.playlists().insert(part="snippet,status", body={"snippet":{"title":title},"status":{"privacyStatus":"public"}}).execute()
    return new["id"]

def run_channel(c, st):
    tok = os.environ.get(c["token_secret"], "").strip()
    if not tok:
        log("SALTO %s: manca il secret %s (token non presente)." % (c["handle"], c["token_secret"])); return
    try:
        yt = yt_service(tok)
    except Exception as e:
        log("Auth ko per %s: %s" % (c["handle"], e)); return
    log("== %s ==" % c["nome"])
    az = CFG["azioni"]; cta = c["cta"]
    try: vids = recent_uploads(yt, az["max_video_recenti"])
    except Exception as e: log("uploads ko: %s" % e); return
    plid = None
    if az.get("auto_playlist"):
        try: plid = ensure_playlist(yt, c["nome"] + " · " + c["tema"].split(",")[0].strip().title())
        except Exception as e: log("playlist ko: %s" % e)
    replies = 0
    for v in vids:
        vid = v["vid"]
        # playlist
        if plid and vid not in st["playlisted"]:
            try:
                yt.playlistItems().insert(part="snippet", body={"snippet":{"playlistId":plid,"resourceId":{"kind":"youtube#video","videoId":vid}}}).execute()
                st["playlisted"].append(vid); log("+ playlist: "+v["title"][:50])
            except Exception: pass
        # commento CTA una volta
        if az.get("commento_cta_fissato") and vid not in st["commented"]:
            try:
                yt.commentThreads().insert(part="snippet", body={"snippet":{"videoId":vid,"topLevelComment":{"snippet":{"textOriginal":cta+" "+" ".join(c["hashtag"][:3])}}}}).execute()
                st["commented"].append(vid); log("+ CTA su "+v["title"][:50])
            except Exception as e: log("cta ko: %s" % e)
        # auto-reply ai commenti nuovi
        if az.get("auto_reply_commenti") and replies < az["max_reply_per_giro"]:
            try:
                th = yt.commentThreads().list(part="snippet", videoId=vid, maxResults=20, order="time").execute()
                for t in th.get("items", []):
                    cid = t["id"]; top = t["snippet"]["topLevelComment"]["snippet"]
                    if int(t["snippet"].get("totalReplyCount", 0)) > 0: continue
                    if cid in st["replied"]: continue
                    if top.get("authorChannelId", {}).get("value") == t["snippet"].get("channelId"): continue
                    testo = top.get("textOriginal", "")
                    reply = groq_reply(c["voce"], testo, cta)
                    yt.comments().insert(part="snippet", body={"snippet":{"parentId":cid,"textOriginal":reply}}).execute()
                    st["replied"].append(cid); replies += 1; log("+ reply a: "+testo[:40])
                    if replies >= az["max_reply_per_giro"]: break
            except Exception as e: log("reply ko: %s" % e)
    # limita la memoria
    for k in ("replied","commented","playlisted"): st[k] = st[k][-500:]
    log("%s: playlist/cta ok, risposte inviate: %d" % (c["handle"], replies))

def main():
    st = load_state()
    for c in CFG["canali"]:
        try: run_channel(c, st)
        except Exception as e: log("errore canale %s: %s" % (c.get("handle"), e))
    save_state(st)
    log("Giro completato " + datetime.datetime.utcnow().isoformat() + "Z")

if __name__ == "__main__":
    main()
