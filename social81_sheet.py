# -*- coding: utf-8 -*-
"""SOCIAL81+ · MOTORE SHEET-DRIVEN (stdlib only).
Legge il MASTER PALINSESTO da Google Sheet (CSV pubblico), compone il post dell'ora
(titolo clickbait + descrizione Golden Circle/AIDA/EPPPA + CTA al SINGOLO prodotto + hashtag),
allega una vignetta Tales OF SICURIX (se disponibile) e pubblica su Telegram.

ENV (GitHub Secrets/Variables o api/.env):
  TELEGRAM_BOT_TOKEN (o BOT_PUBLISHER_TOKEN)   TG_CHANNEL=@sicurissimi
  SOCIAL81_SHEET_ID (default sotto)            TALES_BASE (URL raw immagini, opzionale)
Uso:  python social81_sheet.py            (ora corrente, pubblica)
      python social81_sheet.py --hour 8 --dry   (test, non pubblica)
"""
import argparse,csv,datetime,io,json,os,re,urllib.parse,urllib.request,urllib.error,time,random,hmac,hashlib,base64

SHEET_ID_DEFAULT="10gwruXienwqC6-lSvRXuDTs7kGd_SWiamkkTme3mJ5A"
SITE="https://81plus.net"; TG="https://t.me/sicurissimi"
YT_CH="https://www.youtube.com/@Sicurissimo81"
CORSI="https://corsi.elearningsicurezza.com/pid/2377#login"
# base pubblica delle vignette Tales (JPG Telegram-safe). Vuoto => post solo testo finché non è online.
TALES_BASE_DEFAULT=""  # es: https://raw.githubusercontent.com/PlanB76/81plus-automation/main/tales_web/

def env(name,default=None):
    v=os.getenv(name)
    if v: return v.strip()
    p="api/.env"
    if os.path.isfile(p):
        for line in open(p,encoding="utf-8"):
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,val=line.split("=",1)
                if k.strip()==name: return val.strip()
    return default

def _csv(tab):
    sid=env("SOCIAL81_SHEET_ID",SHEET_ID_DEFAULT)
    url="https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s"%(sid,urllib.parse.quote(tab))
    try:
        raw=urllib.request.urlopen(url,timeout=40).read().decode("utf-8","replace")
    except Exception as e:
        print("[sheet] errore",tab,e); return []
    rows=list(csv.reader(io.StringIO(raw)))
    # riga 0 = intestazione (con titolo unito): scarta; pulisci spazi
    return [[ (c or "").strip() for c in r] for r in rows[1:] if any((c or "").strip() for c in r)]

def load():
    d={}
    for t in ["PRODOTTI","PALINSESTO","COPY_LIBRARY","FESTIVITA","RECENSIONI","CASI_STUDIO","MOTIVAZIONALI","VIDEO_YT"]:
        d[t]=_csv(t)
    return d

def pick(pool,doy,h,off=0):
    return pool[(doy*24+h+off)%len(pool)] if pool else None

# --- filtro stretto: SOLO sicurezza lavoro / HACCP-igiene alimentare / privacy-GDPR ---
_SIC=["rspp","rls","preposto","dirigente","antincendio","primo soccorso","blsd","dpi","ponteggi","muletto","carrell","spazi confinati","d.lgs 81","dlgs 81","decreto 81","sicurezza sul lavoro","sicurezza nei luoghi","stress lavoro","movimentazione manuale","pes pav","pei","atex","atmosfere esplosive","rumore","vibrazioni","rischio chimico","cancerogeni","amianto","radiazioni","coordinatore sicurezza","patente a crediti","lavori in quota"," gru ","piattaforme elevabili"," ple ","saldatura","emergenza","evacuazione","videoterminale","vdt","formazione lavoratori","formazione generale","formazione specifica","addetto antincendio","addetto primo soccorso","duvri","audit","check ","pack completo","microimpresa","compliance"]
_HAC=["haccp","igiene aliment","sicurezza aliment","alimentarist","allergen","somministrazione aliment","autocontrollo","osa ","manipolazione aliment","notifica sanitaria","libretto sanitario"]
_PRI=["privacy","gdpr","protezione dei dati","protezione dati","dpo","videosorveglianza","trattamento dei dati","trattamento dati","reg. 679","2016/679","regolamento europeo","data protection","cyber security","cybersecurity","sicurezza informatica","cookie"]
def compliance_area(p):
    b=(" ".join(str(x) for x in p)).lower()
    if any(k in b for k in _HAC): return "HACCP"
    if any(k in b for k in _PRI): return "PRIVACY"
    if any(k in b for k in _SIC): return "SICUREZZA"
    return None

def guard(t):
    for a,b in [("rischio zero","rischio ridotto"),("zero multe","in regola"),("garantito","conforme"),("garantita","conforme")]:
        t=t.replace(a,b).replace(a.capitalize(),b.capitalize())
    return t

_TALES_CACHE=[]
def _tales_list():
    global _TALES_CACHE
    if _TALES_CACHE: return _TALES_CACHE
    repo=env("TALES_REPO","PlanB76/81plus-automation"); dr=env("TALES_DIR","tales_web")
    try:
        req=urllib.request.Request("https://api.github.com/repos/%s/contents/%s?ref=main"%(repo,dr),headers={"User-Agent":"social81"})
        items=json.loads(urllib.request.urlopen(req,timeout=30).read())
        _TALES_CACHE=[it["download_url"] for it in items if it.get("name","").lower().endswith(".jpg")]
    except Exception as e:
        print("[tales] lista errore",e); _TALES_CACHE=[]
    return _TALES_CACHE
def tales_url(d,doy,h):
    base=env("TALES_BASE")
    if base:
        n=((doy*24+h)%52)+1; return base.rstrip("/")+"/sicurix-%d.jpg"%n
    imgs=_tales_list()
    return imgs[(doy*24+h)%len(imgs)] if imgs else None

def compose(d,h,doy,today):
    pal=d["PRODOTTI"] and d["PALINSESTO"]
    if not d["PALINSESTO"]: return None
    slot=d["PALINSESTO"][ (h) % len(d["PALINSESTO"]) ]
    tipo=(slot[3] if len(slot)>3 else "").lower()
    area=(slot[4] if len(slot)>4 else "").upper()
    # override festività
    dm=today.strftime("%d/%m")
    for f in d["FESTIVITA"]:
        if f and f[0]==dm:
            titolo=f[3]; corpo=f[4]; cta=f[5]; hashtag=f[6] if len(f)>6 else ""
            return finalize(titolo,corpo,cta,hashtag,None,d,doy,h,fest=f[1])
    # per i tipi MIX (recensione/caso/motivazionale) l'area va derivata dal record, non dallo slot
    REAL={"SICUREZZA","HACCP","PRIVACY"}
    rec=cs=mo=None
    if "recens" in tipo and d["RECENSIONI"]:
        rec=pick(d["RECENSIONI"],doy,h); area=(rec[6].upper() if len(rec)>6 and rec[6] else "SICUREZZA")
    elif "caso" in tipo and d["CASI_STUDIO"]:
        cs=pick(d["CASI_STUDIO"],doy,h); area=(cs[2].upper() if len(cs)>2 and cs[2] else "SICUREZZA")
    elif "motiv" in tipo and d["MOTIVAZIONALI"]:
        mo=pick(d["MOTIVAZIONALI"],doy,h)
        if area not in REAL: area=pick(["SICUREZZA","HACCP","PRIVACY"],doy,h)
    if area not in REAL: area="SICUREZZA"
    # prodotti coerenti: stessa area, SOLO reali (mai ALTRO), con url
    # SOLO prodotti compliance: il foglio (476) ha già AREA corretta (sicurezza/HACCP/privacy).
    # Doppia rete: AREA del foglio in REAL E riclassifica stretta coerente (scarta hobby residui).
    def ok(p):
        if not(len(p)>9 and p[9] and p[1].upper() in REAL): return False
        ca=compliance_area(p); return ca is None or ca==p[1].upper() or p[1].upper() in REAL
    prods=[p for p in d["PRODOTTI"] if ok(p) and p[1].upper()==area] \
          or [p for p in d["PRODOTTI"] if ok(p)] \
          or d["PRODOTTI"]
    prod=pick(prods,doy,h) or (d["PRODOTTI"][0] if d["PRODOTTI"] else None)
    # copy del tipo giusto
    def copies(pred): return [c for c in d["COPY_LIBRARY"] if len(c)>5 and pred(c)]
    if tipo.startswith("corso"):
        pool=copies(lambda c:c[1].lower()=="corso" and c[2].upper()==area) or copies(lambda c:c[1].lower()=="corso")
    elif "video" in tipo:
        pool=copies(lambda c:c[1].lower()=="video")
    elif "recens" in tipo:
        pool=copies(lambda c:c[1].lower()=="recensione")
    elif "caso" in tipo:
        pool=copies(lambda c:c[1].lower()=="caso-studio")
    elif "motiv" in tipo:
        pool=copies(lambda c:c[1].lower()=="motivazionale")
    else:
        pool=copies(lambda c:c[1].lower()=="corso")
    cp=pick(pool,doy,h) or (d["COPY_LIBRARY"][0] if d["COPY_LIBRARY"] else ["","","","Sicurezza in 1 click","{PRODOTTO}","{URL}",""])
    titolo,corpo,cta,hashtag=cp[3],cp[4],cp[5],(cp[6] if len(cp)>6 else "")
    # riempi segnaposto dipendenti dal tipo
    nome=prod[3] if prod and len(prod)>3 else "Sicurezza 81+"
    prezzo=prod[5] if prod and len(prod)>5 else ""
    url=prod[9] if prod and len(prod)>9 and prod[9] else CORSI
    video=YT_CH
    if "recens" in tipo and d["RECENSIONI"]:
        r=pick(d["RECENSIONI"],doy,h)
        corpo=corpo.replace("{RECENSIONE_TESTO}",r[2] if len(r)>2 else "")
        titolo=titolo.replace("{RECENSIONE_NOME}",r[3] if len(r)>3 else "Un cliente")
    if "caso" in tipo and d["CASI_STUDIO"]:
        cs=pick(d["CASI_STUDIO"],doy,h)
        corpo=corpo.replace("{CASO_TESTO}",cs[4] if len(cs)>4 else "")
        titolo=titolo.replace("{SETTORE}",cs[1] if len(cs)>1 else "un'azienda")
    if "motiv" in tipo and d["MOTIVAZIONALI"]:
        mo=pick(d["MOTIVAZIONALI"],doy,h)
        titolo=titolo.replace("{FRASE_HOOK}",mo[1] if len(mo)>1 else "Prima vedi. Poi scegli.")
        corpo=corpo.replace("{FRASE_TESTO}",mo[2] if len(mo)>2 else "")
    return finalize(titolo,corpo,cta,hashtag,(nome,prezzo,url,video,area),d,doy,h)

def finalize(titolo,corpo,cta,hashtag,fields,d,doy,h,fest=None):
    def sub(s):
        s=s or ""
        if fields:
            nome,prezzo,url,video,area=fields
            s=s.replace("{PRODOTTO}",nome).replace("{PREZZO}",str(prezzo)).replace("{URL}",url).replace("{VIDEO}",video).replace("{AREA}",area).replace("{VIDEO_TITOLO}",nome)
        s=s.replace("{SITE}",SITE).replace("{VIDEO}",YT_CH).replace("{URL}",CORSI)
        return s
    head="🟠 "+sub(titolo)
    if fest: head="🎉 "+sub(titolo)
    body=sub(corpo); ctaln=sub(cta)
    text=guard(head+"\n\n"+body+"\n\n"+ctaln+("\n\n"+hashtag if hashtag else ""))
    return {"text":text[:1024],"image":tales_url(d,doy,h)}

# ---- Telegram ----
def tg_send(text,image):
    tok=env("TELEGRAM_BOT_TOKEN") or env("BOT_PUBLISHER_TOKEN")
    chan=env("TG_CHANNEL","@sicurissimi")
    if not tok:
        print("[tg] manca token -> skip (dry)"); return False
    def _msg():
        data=urllib.parse.urlencode({"chat_id":chan,"text":text[:4096],"disable_web_page_preview":"false"}).encode()
        r=urllib.request.urlopen(urllib.request.Request("https://api.telegram.org/bot%s/sendMessage"%tok,data=data),timeout=40).read()
        ok=json.loads(r).get("ok"); print("[tg msg]","ok" if ok else r[:200]); return ok
    try:
        if image:
            try:
                data=urllib.parse.urlencode({"chat_id":chan,"photo":image,"caption":text[:1024]}).encode()
                r=urllib.request.urlopen(urllib.request.Request("https://api.telegram.org/bot%s/sendPhoto"%tok,data=data),timeout=40).read()
                ok=json.loads(r).get("ok")
                if ok: print("[tg photo] ok"); return True
                print("[tg photo] fallita, fallback testo:",r[:120])
            except Exception as e:
                print("[tg photo] errore, fallback testo:",e)
            return _msg()
        return _msg()
    except Exception as e:
        print("[tg] errore",e); return False

# ---- Facebook Pagina (stessi contenuti di Telegram) ----
def fb_send(text,image):
    tok=env("META_TOKEN") or env("FB_PAGE_TOKEN"); pid=env("FB_PAGE_ID")
    if not(tok and pid): return
    g="https://graph.facebook.com/v19.0"
    try:
        if image:
            data=urllib.parse.urlencode({"url":image,"caption":text[:5000],"access_token":tok}).encode()
            r=urllib.request.urlopen(urllib.request.Request(g+"/%s/photos"%pid,data=data),timeout=40).read()
        else:
            data=urllib.parse.urlencode({"message":text[:5000],"access_token":tok}).encode()
            r=urllib.request.urlopen(urllib.request.Request(g+"/%s/feed"%pid,data=data),timeout=40).read()
        j=json.loads(r); print("[fb]","ok" if ("id" in j or "post_id" in j) else str(j)[:150])
    except urllib.error.HTTPError as e:
        print("[fb] errore",e.code,e.read().decode("utf-8","replace")[:150])
    except Exception as e:
        print("[fb] errore",e)

# ---- X / Twitter (OAuth 1.0a, testo <=280) ----
def _oauth1(method,url,ck,cs,tok,tsec):
    def q(s): return urllib.parse.quote(str(s),safe="")
    o={"oauth_consumer_key":ck,"oauth_nonce":hashlib.md5(str(random.random()).encode()).hexdigest(),
       "oauth_signature_method":"HMAC-SHA1","oauth_timestamp":str(int(time.time())),
       "oauth_token":tok,"oauth_version":"1.0"}
    base="&".join([method.upper(),q(url),q("&".join("%s=%s"%(q(k),q(o[k])) for k in sorted(o)))])
    sig=base64.b64encode(hmac.new(("%s&%s"%(q(cs),q(tsec))).encode(),base.encode(),hashlib.sha1).digest()).decode()
    o["oauth_signature"]=sig
    return "OAuth "+", ".join('%s="%s"'%(q(k),q(o[k])) for k in o)

def x_send(text,image):
    ck,cs=env("X_API_KEY"),env("X_API_SECRET"); tok,tsec=env("X_ACCESS_TOKEN"),env("X_ACCESS_SECRET")
    if not(ck and cs and tok and tsec): return
    url="https://api.twitter.com/2/tweets"
    try:
        hdr=_oauth1("POST",url,ck,cs,tok,tsec)
        data=json.dumps({"text":text[:280]}).encode()
        r=urllib.request.urlopen(urllib.request.Request(url,data=data,headers={"Authorization":hdr,"Content-Type":"application/json"}),timeout=40).read()
        j=json.loads(r); print("[x]","ok" if j.get("data") else str(j)[:150])
    except urllib.error.HTTPError as e:
        print("[x] errore",e.code,e.read().decode("utf-8","replace")[:150])
    except Exception as e:
        print("[x] errore",e)

# ---- LinkedIn (pagina aziendale, testo) ----
def li_send(text,image):
    tok=env("LINKEDIN_TOKEN"); org=env("LINKEDIN_ORG")
    if not(tok and org): return
    payload={"author":"urn:li:organization:%s"%org,"lifecycleState":"PUBLISHED",
             "specificContent":{"com.linkedin.ugc.ShareContent":{"shareCommentary":{"text":text[:3000]},"shareMediaCategory":"NONE"}},
             "visibility":{"com.linkedin.ugc.MemberNetworkVisibility":"PUBLIC"}}
    try:
        r=urllib.request.urlopen(urllib.request.Request("https://api.linkedin.com/v2/ugcPosts",data=json.dumps(payload).encode(),
            headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json","X-Restli-Protocol-Version":"2.0.0"}),timeout=40).read()
        print("[linkedin] ok")
    except urllib.error.HTTPError as e:
        print("[linkedin] errore",e.code,e.read().decode("utf-8","replace")[:150])
    except Exception as e:
        print("[linkedin] errore",e)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--hour",type=int); ap.add_argument("--dry",action="store_true")
    a=ap.parse_args()
    off=int(env("TZ_OFFSET_IT","2") or 2)
    now=datetime.datetime.utcnow()+datetime.timedelta(hours=off)
    h=a.hour if a.hour is not None else now.hour
    doy=now.timetuple().tm_yday
    d=load()
    post=compose(d,h,doy,now.date())
    if not post: print("nessun post (sheet vuoto?)"); return
    print("="*60); print("ORA",h,"| doy",doy); print(post["text"]);
    if post["image"]: print("[img]",post["image"])
    print("="*60)
    if not a.dry:
        tg_send(post["text"],post["image"])
        fb_send(post["text"],post["image"])
        x_send(post["text"],post["image"])
        li_send(post["text"],post["image"])

if __name__=="__main__": main()
