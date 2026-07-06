"""81+ OMNIPRESENZA · dispatcher cloud SELF-CONTAINED (gira su GitHub Actions, PC spento).
Ogni ora: 1 azione Telegram + 1 azione YouTube = 2/ora = 48/giorno, tutte diverse,
sequenza che ruota ogni giorno (date-seeded). Nessuna dipendenza dai file locali.

ENV (GitHub Secrets/Variables, o api/.env locale):
  TELEGRAM_BOT_TOKEN   (segreto)         TG_CHANNEL=@sicurissimi
  YOUTUBE_API_KEY      (segreto, lettura) YT_CHANNEL_ID=UCTzVaIyeBUtP0pmAmk2c7FQ
  YOUTUBE_TOKEN_JSON   (segreto, opzionale: abilita l'evergreen che riscrive i metadati)
  TZ_OFFSET_IT=2

Uso:  python dispatch.py            (ora corrente)
      python dispatch.py --hour 13 --doy 200   (test)
"""
import argparse, datetime, json, os, sys, urllib.parse, urllib.request

TG_CHANNEL_DEFAULT = "@sicurissimi"
YT_CHANNEL_DEFAULT = "UCTzVaIyeBUtP0pmAmk2c7FQ"
TG_LINK = "https://t.me/sicurissimi"
CORSI = "https://corsi.elearningsicurezza.com/pid/2377#login"
CHECK = "https://81plus.net"

# ---------- piano orario (24h) ----------
TG_PLAN = ["quote","faq","checklist","news","quote","tip","tip","news",
           "ytvideo","checklist","poll","tip","ytvideo","libri","faq","news",
           "corsi","tip","ytvideo","membership","quote","poll","membership","news"]
YT_PLAN = ["evergreen"]*24  # cloud: solo metadati (gratis). Gli short/video AI restano su Gemini->local.

# ---------- banche testi (anti-paura, brand-safe) ----------
QUOTES = ["🟠 Prima vedi. Poi scegli. La sicurezza non deve fare paura: deve essere chiara.",
          "🛡️ La sicurezza non è un costo: è ciò che ti fa dormire sereno la notte.",
          "✅ Un controllo fatto oggi vale più di mille scuse domani.",
          "🧭 Non serve sapere tutto: serve sapere da dove iniziare.",
          "💡 Meglio un minuto di controllo che un giorno di guai.",
          "🤝 La sicurezza vera diventa abitudine, non emergenza.",
          "📈 Chi si organizza prima, lavora sereno dopo.",
          "🔍 Ciò che non controlli, prima o poi ti controlla."]
TIPS = ["3 cose da controllare oggi: formazione aggiornata, DVR a portata di mano, DPI usati davvero.",
        "Il corso fatto anni fa potrebbe non bastare più: controlla le scadenze formative.",
        "Appalti e documenti in un posto solo: se non sai dove sono, sei già in rincorsa.",
        "HACCP: il registro temperature è il primo rilievo. Due minuti al giorno, non a memoria.",
        "Privacy: una password su un post-it non è una password, è un invito.",
        "Cantiere: POS, patente a crediti, DPI. Tre spunte e parti sereno.",
        "Antincendio: estintori e vie di fuga, un controllo veloce ogni mese.",
        "Preposto: il ruolo c'è anche se nessuno te l'ha spiegato. Scopri cosa comporta."]
CHECKLISTS = ["🧾 Check rapido:\n☐ Formazione aggiornata\n☐ DVR a portata di mano\n☐ DPI usati davvero",
              "🧾 Documenti base:\n☐ DVR\n☐ Nomine\n☐ Attestati formazione",
              "🧾 Cantiere pronto:\n☐ POS\n☐ Patente a crediti\n☐ DPI",
              "🧾 HACCP del giorno:\n☐ Temperature\n☐ Pulizie\n☐ Scadenze prodotti",
              "🧾 Privacy minima:\n☐ Informativa\n☐ Registro trattamenti\n☐ Password sicure"]
FAQS = ["❓Ogni quanto va aggiornata la formazione? In media ogni 5 anni, alcuni aggiornamenti sono annuali.",
        "❓Il DVR serve anche con 1 solo dipendente? Sì.",
        "❓HACCP serve se non cucino? Spesso sì: anche somministrazione e vendita alimenti.",
        "❓Chi è il preposto? Chi sovrintende e vigila sul lavoro altrui: serve formazione specifica.",
        "❓La videosorveglianza è libera? No: servono informativa e regole privacy."]
NEWS = ["📰 Controlli sulla sicurezza in aumento: meglio arrivare preparati che rincorrere.",
        "📰 HACCP: i rilievi più comuni nascono da registri dimenticati.",
        "📰 Formazione: scadenze spesso ignorate finché non arriva la verifica.",
        "📰 Cantieri: la patente a crediti cambia le carte. Verifica la tua posizione.",
        "📰 Privacy: sanzioni anche per piccole attività. Bastano pochi accorgimenti."]
POLLS = [("Hai aggiornato la formazione sicurezza quest'anno?", ["Sì, in regola","No, devo farlo","Non lo so"]),
         ("Tieni i registri HACCP ogni giorno?", ["Sì","A volte","No"]),
         ("Trovi il DVR in 1 minuto se te lo chiedono?", ["Sì","Forse","No"]),
         ("I DPI vengono usati davvero?", ["Sempre","A volte","Raramente"])]
FOOT = "\n\n📲 Entra nel canale e attiva la membership per i GRUPPI PRIVATI del tuo livello: " + TG_LINK

GUARD = [("rischio zero","rischio ridotto"),("garantito","conforme"),("zero multe","in regola"),
         ("assicurato","tutelato")]
def guard(t):
    low = t
    for a,b in GUARD:
        low = low.replace(a,b).replace(a.capitalize(),b.capitalize())
    return low

def pick(pool, doy, h):
    return pool[(doy*24+h) % len(pool)]

# ---------- Telegram (urllib, no deps) ----------
def _tg(method, token, fields):
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    data = urllib.parse.urlencode(fields).encode("utf-8")
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=40).read())
    except Exception as e:
        print("[tg] errore:", e); return {}

def tg_post(token, chan, text):
    r = _tg("sendMessage", token, {"chat_id": chan, "text": text[:4096], "disable_web_page_preview":"false"})
    print("[tg]", "ok" if r.get("ok") else r)

def tg_poll(token, chan, q, opts):
    r = _tg("sendPoll", token, {"chat_id": chan, "question": q[:300],
            "options": json.dumps(opts[:10], ensure_ascii=False), "is_anonymous":"true"})
    print("[tg poll]", "ok" if r.get("ok") else r)

# ---------- YouTube READ (API key) ----------
def yt_get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

def yt_uploads(channel_id, key):
    d = yt_get("https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id=%s&key=%s" % (channel_id, key))
    return d["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def yt_recent(playlist_id, key, n=50):
    d = yt_get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=%d&playlistId=%s&key=%s" % (n, playlist_id, key))
    out=[]
    for it in d.get("items",[]):
        s=it["snippet"]; out.append({"id":s["resourceId"]["videoId"],"title":s["title"]})
    return out

# ---------- magnetic title + SEO (lite) ----------
PILLAR_KW = {"haccp":["haccp","aliment","igien","temperatur","ristorant","bar","cucina"],
             "privacy":["privacy","gdpr","dati","cookie","videosorvegli"],
             "cantieri":["cantier","dpi","edili","ponteggi","gru","altezza","patente"],
             "formazione":["corso","formazion","attestat","rspp","rls","aggiorn"],
             "antincendio":["antincendio","incendio","estintor","emergenz"],
             "primosoccorso":["primo soccorso","defibrill","blsd"],
             "documenti":["dvr","documento","nomin","registro","appalt","duvri"]}
def pillar_of(t):
    t=t.lower()
    for p,kws in PILLAR_KW.items():
        if any(k in t for k in kws): return p
    return "start"
SEO = {"haccp":"HACCP, igiene e sicurezza alimentare, allergeni, registri e temperature.",
       "privacy":"Privacy e GDPR per aziende: dati personali, informativa, consensi, cookie.",
       "cantieri":"Sicurezza in edilizia: cantieri, DPI, attrezzature, patente a crediti.",
       "formazione":"Sicurezza sul lavoro: corsi accreditati per lavoratori, preposti, RSPP, RLS.",
       "antincendio":"Antincendio: addetti, estintori, vie di fuga e controlli.",
       "primosoccorso":"Primo soccorso aziendale: addetti, formazione e cosa avere pronto.",
       "documenti":"DVR, documenti aziendali, nomine, attestati e adempimenti.",
       "start":"Sicurezza sul lavoro, HACCP, igiene alimentare e privacy spiegate semplici."}
HOOK = ["3 cose da controllare (la 2ª la dimenticano quasi tutti)","l'errore che fanno quasi tutti",
        "quello che nessuno ti spiega","la guida semplice","cosa controllare davvero","come metterti in regola senza ansia"]
def magnetic_title(orig, doy):
    base = orig.split("·")[0].split("|")[0].strip()
    base = base[:55].rstrip(" -–—")
    title = "%s: %s · SICURISSIMO81+" % (base, HOOK[doy % len(HOOK)])
    return guard(title[:100])
def seo_desc(title, doy):
    p = pillar_of(title)
    return guard(
        SEO.get(p, SEO["start"]) +
        "\n\n📲 ENTRA NEL CANALE TELEGRAM (gratis): " + TG_LINK +
        "\n   → Attiva la MEMBERSHIP ed entra nei GRUPPI PRIVATI del tuo livello"
        " (USER → MEMBER → NETWORKER → ELITE → VIP → FRANCHISER)." +
        "\n\n🎓 Corsi accreditati: " + CORSI +
        "\n👉 Check gratuito 81+: " + CHECK +
        "\n📚 Libri: https://81plus.net/libri.html  ·  💬 WhatsApp: 338 877 1737" +
        "\n\nSICURISSIMO81+ · La sicurezza sul lavoro in 1 click. Prima vedi. Poi scegli." +
        "\n\n#SicurezzaSulLavoro #HACCP #Privacy #81plus #Sicurissimo")[:4900]

# ---------- azioni ----------
def env(name, default=None):
    v = os.getenv(name)
    if v: return v.strip()
    p = "api/.env"
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,val=line.split("=",1)
                if k.strip()==name: return val.strip()
    return default

def do_tg(kind, token, chan, key, ch_id, doy, h):
    if not token:
        print("[tg] manca TELEGRAM_BOT_TOKEN -> skip"); return
    if kind=="quote":      tg_post(token, chan, pick(QUOTES,doy,h))
    elif kind=="tip":      tg_post(token, chan, "🛡️ "+pick(TIPS,doy,h)+FOOT)
    elif kind=="checklist":tg_post(token, chan, pick(CHECKLISTS,doy,h)+FOOT)
    elif kind=="faq":      tg_post(token, chan, pick(FAQS,doy,h)+FOOT)
    elif kind=="news":     tg_post(token, chan, pick(NEWS,doy,h)+FOOT)
    elif kind=="libri":    tg_post(token, chan, "📚 I libri di Mirco Pregnolato — la sicurezza spiegata semplice: https://81plus.net/libri.html"+FOOT)
    elif kind=="corsi":    tg_post(token, chan, "🎓 Corsi accreditati 81+ University — attestati validi: "+CORSI+FOOT)
    elif kind=="membership":tg_post(token, chan, "🟠 Membership 81+ = la chiave dei GRUPPI PRIVATI per status (USER→FRANCHISER): check, checklist, scadenziario, supporto, community."+FOOT)
    elif kind=="poll":
        q,opts = pick(POLLS,doy,h); tg_poll(token, chan, q, opts)
    elif kind=="ytvideo":
        if not key: print("[tg] manca YOUTUBE_API_KEY -> skip ytvideo"); return
        try:
            vids = yt_recent(yt_uploads(ch_id,key), key, 50)
            v = vids[(doy*24+h) % len(vids)]
            tg_post(token, chan, "🎬 %s\n▶️ https://youtu.be/%s%s" % (v["title"][:200], v["id"], FOOT))
        except Exception as e: print("[tg ytvideo] errore:", e)

def do_yt(kind, key, ch_id, doy, h):
    if kind!="evergreen": print("[yt] skip", kind); return
    if not key: print("[yt] manca YOUTUBE_API_KEY -> skip"); return
    # serve OAuth per scrivere i metadati
    tokjson = os.getenv("YOUTUBE_TOKEN_JSON")
    tokfile = "config/youtube_token.json"
    if not (tokjson or os.path.isfile(tokfile)):
        print("[yt] nessun OAuth token (YOUTUBE_TOKEN_JSON) -> evergreen disattivo finche' non lo aggiungi."); return
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        SCOPES=["https://www.googleapis.com/auth/youtube"]
        if tokjson and not os.path.isfile(tokfile):
            os.makedirs("config", exist_ok=True); open(tokfile,"w",encoding="utf-8").write(tokjson)
        creds = Credentials.from_authorized_user_file(tokfile, SCOPES)
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        yt = build("youtube","v3",credentials=creds)
        vids = yt_recent(yt_uploads(ch_id,key), key, 50)
        v = vids[(doy*24+h) % len(vids)]
        cur = yt.videos().list(part="snippet", id=v["id"]).execute()["items"][0]["snippet"]
        cur["title"] = magnetic_title(v["title"], doy)
        cur["description"] = seo_desc(v["title"], doy)
        yt.videos().update(part="snippet", body={"id":v["id"],"snippet":cur}).execute()
        print("[yt] evergreen ok:", v["id"], "->", cur["title"])
    except Exception as e:
        print("[yt] evergreen errore:", e)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--hour",type=int); ap.add_argument("--doy",type=int)
    a=ap.parse_args()
    off=int(env("TZ_OFFSET_IT","2") or 2)
    h = a.hour if a.hour is not None else (datetime.datetime.utcnow().hour+off)%24
    doy = a.doy if a.doy is not None else datetime.date.today().timetuple().tm_yday
    token=env("TELEGRAM_BOT_TOKEN") or env("TG_BOT_TOKEN")
    chan=env("TG_CHANNEL", TG_CHANNEL_DEFAULT); key=env("YOUTUBE_API_KEY")
    ch_id=env("YT_CHANNEL_ID", YT_CHANNEL_DEFAULT)
    tg_kind=TG_PLAN[(h+doy)%24]; yt_kind=YT_PLAN[(h+doy*7)%24]
    print("Ora IT:",h,"| doy:",doy,"| TG:",tg_kind,"| YT:",yt_kind)
    do_tg(tg_kind, token, chan, key, ch_id, doy, h)
    do_yt(yt_kind, key, ch_id, doy, h)

if __name__=="__main__":
    main()
