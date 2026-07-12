# -*- coding: utf-8 -*-
"""YTCASHCOW81+ · BACKFILL SEO (DRY-RUN) — @sicurissimo (D.Lgs 81/08).

Protocollo (Quality Gate, niente upload automatico):
  1) Enumera TUTTI i video del canale via YouTube Data API (solo YOUTUBE_API_KEY, lettura, no OAuth).
  2) Per ogni video: statistiche (views/like/commenti) + TRANSCRIPT (sottotitoli auto, se disponibili).
  3) Invia (system prompt fisso + prompt JSON) all'AI (Groq gratis; fallback Anthropic/OpenAI; fallback euristico).
  4) Parsea SOLO il JSON, valida i campi, MAPPA su snippet.title/description/tags.
  5) SCRIVE un CSV di revisione (cloud_state/yt_seo_review.csv). L'owner revisiona e mette APPROVA=SI.
     -> L'upload lo fa un altro script (yt_cashcow_apply.py) solo sulle righe approvate.

ENV:
  YOUTUBE_API_KEY   (obbligatorio, lettura pubblica)  · YT_CHANNEL_ID (o CHANNELS_JSON con handle/id)
  GROQ_API_KEY      (consigliato, gratis)  · ANTHROPIC_API_KEY / OPENAI_API_KEY (fallback opzionali)
  YT_SEO_LIMIT      (opz. max video per giro, default 0 = tutti)
  YT_SEO_SKIP_DONE  (opz. '1' salta i video gia' in CSV con APPROVA compilato)
Nessun segreto viene stampato. Se manca YOUTUBE_API_KEY -> esce con messaggio, nessun errore fatale.
"""
import os,sys,json,csv,re,time,io,datetime,urllib.request,urllib.parse,urllib.error,pathlib

HERE=pathlib.Path(__file__).resolve().parent
STATE=HERE.parent/"cloud_state"
# quando gira sul repo, cloud_state e' accanto a cloud/; in locale, accanto al file
for cand in (HERE.parent/"cloud_state", HERE/"cloud_state"):
    pass
STATE=(HERE.parent/"cloud_state"); STATE.mkdir(parents=True,exist_ok=True)
REVIEW_CSV=STATE/"yt_seo_review.csv"

def env(*names,default=""):
    for n in names:
        v=os.getenv(n)
        if v: return v.strip()
    return default

YT_KEY=env("YOUTUBE_API_KEY")
CHANNEL_ID=env("YT_CHANNEL_ID")
LIMIT=int(env("YT_SEO_LIMIT",default="0") or "0")
SKIP_DONE=env("YT_SEO_SKIP_DONE",default="0")=="1"
AUTO=env("YT_SEO_AUTO",default="0")=="1"      # 1 = auto-approva le righe sicure (needs_human_review=NO)
VARIANT_FILE=STATE/"yt_variant.json"          # {video_id: n} numero di ri-ottimizzazione (angolo diverso)
def load_variants():
    try: return json.load(open(VARIANT_FILE,encoding="utf-8"))
    except Exception: return {}
VARIANTS=load_variants()

# ---------- compliance guard (niente promesse illecite) ----------
GUARD=[("zero multe","in regola"),("rischio zero","rischio ridotto"),("garantito","concreto"),
       ("garantita","concreta"),("nessun rischio","meno rischi"),("100% sicuro","piu' sicuro")]
def guard(t):
    t=t or ""
    for a,b in GUARD: t=re.sub(re.escape(a),b,t,flags=re.I)
    return t

# ---------- YouTube Data API (lettura, solo API key) ----------
def api(path,**params):
    params["key"]=YT_KEY
    url="https://www.googleapis.com/youtube/v3/%s?%s"%(path,urllib.parse.urlencode(params))
    req=urllib.request.Request(url,headers={"User-Agent":"cashcow81/1.0"})
    with urllib.request.urlopen(req,timeout=40) as r:
        return json.loads(r.read().decode("utf-8","replace"))

def uploads_playlist(channel_id):
    d=api("channels",part="contentDetails",id=channel_id)
    items=d.get("items") or []
    if not items: raise RuntimeError("canale non trovato: "+channel_id)
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def all_video_ids(channel_id):
    pl=uploads_playlist(channel_id); ids=[]; tok=None
    while True:
        d=api("playlistItems",part="contentDetails",playlistId=pl,maxResults=50,**({"pageToken":tok} if tok else {}))
        for it in d.get("items",[]):
            vid=it["contentDetails"].get("videoId")
            if vid: ids.append(vid)
        tok=d.get("nextPageToken")
        if not tok: break
    return ids

def videos_meta(ids):
    """titolo/descrizione/tag/statistiche a blocchi di 50."""
    out={}
    for i in range(0,len(ids),50):
        chunk=ids[i:i+50]
        d=api("videos",part="snippet,statistics",id=",".join(chunk))
        for it in d.get("items",[]):
            sn=it.get("snippet",{}); st=it.get("statistics",{})
            out[it["id"]]={"title":sn.get("title",""),"desc":sn.get("description",""),
                "tags":sn.get("tags",[]),"published":sn.get("publishedAt",""),
                "views":int(st.get("viewCount",0) or 0),"likes":int(st.get("likeCount",0) or 0),
                "comments":int(st.get("commentCount",0) or 0)}
    return out

# ---------- transcript (sottotitoli automatici, gratis, no auth) ----------
def transcript(video_id):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        for langs in (["it"],["it","en"],None):
            try:
                tr=YouTubeTranscriptApi.get_transcript(video_id,languages=langs) if langs else YouTubeTranscriptApi.get_transcript(video_id)
                txt=" ".join(x["text"] for x in tr if x.get("text"))
                if txt.strip(): return re.sub(r"\s+"," ",txt).strip()
            except Exception: continue
    except Exception:
        pass
    return ""

# ---------- AI: system prompt FISSO + prompt JSON ----------
SYSTEM=("Sei un esperto di Sicurezza sul Lavoro in Italia, specializzato nel D.Lgs 81/08. "
        "Il tuo tono deve essere autoritario, preciso, professionale, orientato alla conformita' normativa "
        "ma pragmatico. Non inventare mai normative inesistenti. Se il contenuto del video e' troppo breve o vago, "
        "non inventare dettagli tecnici: imposta \"needs_human_review\": true e non forzare dettagli.")

PROMPT_TMPL=(
"Agisci come esperto SEO YouTube per un canale di Sicurezza sul Lavoro (D.Lgs 81/08).\n"
"Analizza il video.\nTITOLO: {title}\nCONTENUTO: {content}\n\n"
"Genera output STRICTLY in JSON (nessuna introduzione, nessun saluto, solo il codice JSON). Struttura:\n"
"{{\n"
'  "titolo_seo": "titolo ottimizzato (max 100 caratteri)",\n'
'  "descrizione_seo": "descrizione SEO con hook, riassunto e CTA a consulenze professionali dell\'ente formatore (link 81plus.net)",\n'
'  "tag_youtube": ["tag1","tag2","tag3","tag4","tag5"],\n'
'  "hashtags": ["#sicurezzasullavoro","#formazione","#DPI","#preposto","#RSPP"],\n'
'  "thumbnail_design": {{ "testo_miniatura": "MAX 4 parole enormi", "colore_testo": "rosso|verde|arancione", "descrizione_grafica": "immagine per CTR alto" }},\n'
'  "thumbnail_prompt": "prompt image-gen 16:9 fotorealistico, luce naturale ufficio/cantiere, alta definizione; ELEMENTO VISIVO specifico e VARIABILE dedotto dalla trascrizione; TESTO massivo max 4 parole con bordo nero spesso a sinistra; spazio in basso a destra libero per il timestamp; alta leggibilita mobile; no loghi, no scritte minuscole",\n'
'  "needs_human_review": false\n'
"}}\n"
"Regole severe: 1) titolo orientato a ricerca o beneficio; 2) descrizione professionale con link contatto ente formatore https://81plus.net ; "
"3) nessun commento fuori dal JSON; 4) niente promesse illecite (no 'zero multe', 'rischio zero', 'garantito'); "
"5) thumbnail: testo MAX 4 parole enormi, elemento visivo VARIABILE dedotto dal contenuto (non generico), "
"colore testo per macro-tema: ROSSO per pericoli/rischi, VERDE per procedure corrette/DPI, ARANCIONE per normativa/formazione.")

def _http_json(url,headers,payload,timeout=90):
    headers=dict(headers)
    # User-Agent da browser: Groq/altri sono dietro Cloudflare che blocca 'Python-urllib' (errore 1010)
    headers.setdefault("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    headers.setdefault("Accept","application/json")
    req=urllib.request.Request(url,data=json.dumps(payload).encode("utf-8"),headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8","replace"))
    except urllib.error.HTTPError as e:
        try: body=e.read().decode("utf-8","replace")
        except Exception: body=""
        raise RuntimeError("HTTP %s: %s"%(e.code,body[:240]))

def ai_generate(title,content,variant=0):
    """Ritorna (dict_json, engine). Prova Groq -> Anthropic -> OpenAI -> euristico."""
    prompt=PROMPT_TMPL.format(title=title[:180],content=(content or title)[:900])
    if variant and variant>0:
        prompt+=("\n\nATTENZIONE: e' la RI-OTTIMIZZAZIONE numero %d di questo video: il titolo/descrizione/thumbnail "
                 "precedenti NON hanno aumentato le visualizzazioni. Genera un ANGOLO COMPLETAMENTE DIVERSO "
                 "(nuovo hook, nuovo beneficio, parole chiave diverse, testo thumbnail diverso). Non ripetere la versione precedente." % variant)
    gk=env("GROQ_API_KEY")
    if gk:
        for attempt in range(5):
            try:
                d=_http_json("https://api.groq.com/openai/v1/chat/completions",
                    {"Authorization":"Bearer "+gk,"Content-Type":"application/json"},
                    {"model":env("GROQ_MODEL",default="llama-3.1-8b-instant"),
                     "temperature":0.6,"response_format":{"type":"json_object"},
                     "messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]})
                return _parse(d["choices"][0]["message"]["content"]),"groq"
            except Exception as e:
                s=str(e)
                if "429" in s and attempt<4:
                    m=re.search(r"try again in ([\d.]+)s",s)
                    wait=(float(m.group(1))+1.5) if m else 10.0*(attempt+1)
                    print("  [groq] rate limit: attendo %.1fs e riprovo"%min(wait,40)); time.sleep(min(wait,40)); continue
                print("  [groq]",s[:240]); break
    ak=env("ANTHROPIC_API_KEY")
    if ak:
        try:
            d=_http_json("https://api.anthropic.com/v1/messages",
                {"x-api-key":ak,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
                {"model":env("ANTHROPIC_MODEL",default="claude-3-5-haiku-20241022"),"max_tokens":1200,
                 "system":SYSTEM,"messages":[{"role":"user","content":prompt}]})
            return _parse(d["content"][0]["text"]),"anthropic"
        except Exception as e: print("  [anthropic]",str(e)[:240])
    ok=env("OPENAI_API_KEY")
    if ok:
        try:
            d=_http_json("https://api.openai.com/v1/chat/completions",
                {"Authorization":"Bearer "+ok,"Content-Type":"application/json"},
                {"model":env("OPENAI_MODEL",default="gpt-4o-mini"),"temperature":0.6,
                 "response_format":{"type":"json_object"},
                 "messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]})
            return _parse(d["choices"][0]["message"]["content"]),"openai"
        except Exception as e: print("  [openai]",str(e)[:240])
    return _heuristic(title,content),"heuristic"

def _parse(txt):
    txt=txt.strip()
    m=re.search(r"\{.*\}",txt,re.S)
    if m: txt=m.group(0)
    return json.loads(txt)

def theme_color(text):
    s=(text or "").lower()
    if any(k in s for k in ["dpi","procedur","corrett","buone pratiche","come fare","guanti","casco","imbrag"]): return "verde"
    if any(k in s for k in ["rischio","pericolo","cadut","infortun","incendio","emergenza","scavo","elettric"]): return "rosso"
    return "arancione"

def _heuristic(title,content):
    t=re.sub(r"[\|•·—].*$","",title).strip()[:60] or "Sicurezza sul lavoro"
    col=theme_color(title+" "+content)
    short=" ".join(t.split()[:4]) or "Sicurezza"
    return {"titolo_seo":guard(("%s: cosa controllare davvero"%t))[:100],
        "descrizione_seo":guard("%s — spiegato semplice.\n\nIn questo video: il rischio reale e l'azione concreta per metterti in regola.\n\nHai bisogno di formazione o consulenza per la tua azienda? Contatta l'ente formatore: https://81plus.net/?src=yt\n\nContenuto informativo, verifica sempre il tuo caso con un professionista qualificato."%t),
        "tag_youtube":["sicurezza sul lavoro","d.lgs 81/08","formazione sicurezza","rspp","dvr","dpi","haccp","prevenzione"],
        "hashtags":["#sicurezzasullavoro","#formazione","#DPI","#preposto","#RSPP"],
        "thumbnail_design":{"testo_miniatura":short,"colore_testo":col,"descrizione_grafica":"Sfondo scuro, operaio con DPI, testo grande ad alto contrasto per CTR."},
        "thumbnail_prompt":("Thumbnail YouTube 16:9 fotorealistica sul tema '%s' (sicurezza sul lavoro, D.Lgs 81/08). "
            "Luce naturale ufficio/cantiere, alta definizione. Elemento visivo coerente col tema. "
            "Testo massivo max 4 parole '%s' colore %s, font sans-serif pesante, bordo nero spesso, a sinistra. "
            "Spazio in basso a destra libero per il timestamp. Alta leggibilita su mobile. No loghi, no scritte minuscole."
            % (t,short.upper(),col)),
        "needs_human_review":True}

# ---------- validazione + normalizzazione ----------
def normalize(j):
    def s(x): return (x if isinstance(x,str) else " ".join(x) if isinstance(x,list) else str(x or "")).strip()
    title=guard(s(j.get("titolo_seo")))[:100]
    desc=guard(s(j.get("descrizione_seo")))
    tags=j.get("tag_youtube") or []
    if isinstance(tags,str): tags=[t.strip() for t in tags.split(",") if t.strip()]
    tags=[str(t).strip() for t in tags if str(t).strip()][:15]
    hsh=j.get("hashtags") or []
    if isinstance(hsh,str): hsh=hsh.split()
    hsh=[("#"+h.lstrip("#")) for h in hsh if str(h).strip()][:6]
    th=j.get("thumbnail_design") or {}
    tt=th.get("testo_miniatura","");
    if isinstance(tt,list): tt=" ".join(tt)
    tt=" ".join(str(tt).split()[:4])   # forza max 4 parole
    tcol=(th.get("colore_testo") or theme_color(title+" "+desc)).strip().lower()
    if tcol not in ("rosso","verde","arancione"): tcol=theme_color(title+" "+desc)
    td=th.get("descrizione_grafica","")
    tp=s(j.get("thumbnail_prompt"))
    nhr=bool(j.get("needs_human_review"))
    # regole di qualita' -> forza revisione umana
    if not title or len(title)<12: nhr=True
    if not desc or len(desc)<80: nhr=True
    if len(tags)<3: nhr=True
    # append hashtag alla descrizione se non presenti
    if hsh and not any(h in desc for h in hsh):
        desc=desc.rstrip()+"\n\n"+" ".join(hsh)
    if not tp:
        tp=("Thumbnail YouTube 16:9 fotorealistica sul tema del video (sicurezza sul lavoro D.Lgs 81/08). "
            "Elemento visivo coerente. Testo massivo max 4 parole '%s' colore %s, bordo nero spesso, a sinistra. "
            "Spazio in basso a destra libero per timestamp. Alta leggibilita mobile. No loghi." % (str(tt).upper(),tcol))
    return {"titolo_seo":title,"descrizione_seo":desc,"tags":tags,"hashtags":hsh,
            "thumb_text":str(tt)[:60],"thumb_color":tcol,"thumb_desc":str(td)[:400],
            "thumb_prompt":tp[:600],"needs_human_review":"SI" if nhr else "NO"}

# ---------- CSV ----------
COLS=["video_id","url","APPROVA","needs_human_review","engine","titolo_attuale","views","likes","commenti",
      "titolo_seo","descrizione_seo","tags","hashtags","thumb_text","thumb_color","thumb_desc","thumb_prompt","ts"]

def load_done():
    """video_id gia' revisionati (APPROVA compilato) da non rifare se SKIP_DONE."""
    done=set()
    if REVIEW_CSV.exists():
        with open(REVIEW_CSV,encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("APPROVA") or "").strip(): done.add(row.get("video_id"))
    return done

def main():
    if not YT_KEY:
        print("[STOP] manca YOUTUBE_API_KEY (lettura pubblica). Nessuna azione."); return
    cid=CHANNEL_ID
    if not cid:
        cj=HERE/"channels.json"
        if not cj.exists(): cj=HERE.parent/"cloud"/"channels.json"
        if cj.exists():
            try: cid=(json.load(open(cj,encoding="utf-8"))[0]).get("channel_id","")
            except Exception: pass
    if not cid:
        print("[STOP] manca YT_CHANNEL_ID e channels.json."); return
    print("[canale]",cid)
    ids=all_video_ids(cid)
    print("[video trovati]",len(ids))
    done=load_done() if SKIP_DONE else set()
    todo=[v for v in ids if v not in done]
    if LIMIT>0: todo=todo[:LIMIT]
    meta=videos_meta(todo)
    rows=[]
    for n,vid in enumerate(todo,1):
        m=meta.get(vid,{})
        tit=m.get("title","");
        print("[%d/%d] %s | %s" % (n,len(todo),vid,tit[:60]))
        tx=transcript(vid)[:900]   # limita i token: piu' richieste stanno sotto il rate-limit Groq gratuito
        content=tx if len(tx)>120 else (tit+"\n"+(m.get("desc","")[:500]))
        var=int(VARIANTS.get(vid,0) or 0)
        try:
            j,eng=ai_generate(tit,content,variant=var)
            nz=normalize(j)
        except Exception as e:
            print("  [ai errore]",str(e)[:120]); nz=normalize(_heuristic(tit,content)); eng="heuristic"
            nz["needs_human_review"]="SI"
        # AUTO: approva da solo le righe sicure (contenuto sufficiente); le vaghe restano da rivedere
        approva="SI" if (AUTO and nz["needs_human_review"]=="NO") else ""
        rows.append({"video_id":vid,"url":"https://youtu.be/"+vid,"APPROVA":approva,
            "needs_human_review":nz["needs_human_review"],"engine":eng,
            "titolo_attuale":tit,"views":m.get("views",0),"likes":m.get("likes",0),"commenti":m.get("comments",0),
            "titolo_seo":nz["titolo_seo"],"descrizione_seo":nz["descrizione_seo"],
            "tags":", ".join(nz["tags"]),"hashtags":" ".join(nz["hashtags"]),
            "thumb_text":nz["thumb_text"],"thumb_color":nz["thumb_color"],
            "thumb_desc":nz["thumb_desc"],"thumb_prompt":nz["thumb_prompt"],
            "ts":datetime.datetime.utcnow().isoformat()})
        time.sleep(float(env("YT_SEO_DELAY",default="1.5") or "1.5"))
    # merge con CSV esistente (mantieni APPROVA gia' messi)
    prev={}
    if REVIEW_CSV.exists():
        with open(REVIEW_CSV,encoding="utf-8") as f:
            for r in csv.DictReader(f): prev[r["video_id"]]=r
    for r in rows:
        old=prev.get(r["video_id"])
        if old and (old.get("APPROVA") or "").strip(): r["APPROVA"]=old["APPROVA"]
        prev[r["video_id"]]=r
    with open(REVIEW_CSV,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLS); w.writeheader()
        for r in prev.values(): w.writerow({k:r.get(k,"") for k in COLS})
    print("[OK] CSV revisione:",REVIEW_CSV,"righe totali:",len(prev))
    print("Revisiona il CSV, metti APPROVA=SI sulle righe buone, poi lancia yt_cashcow_apply.py.")

if __name__=="__main__": main()
