# -*- coding: utf-8 -*-
"""
YOUTUBE STUDIO 81+ · restyle81
Ringiovanisce a ROTAZIONE i video LUNGHI gia' presenti sul canale:
- nuovo TITOLO clickbait virale (AI, stile VidIQ)
- nuova DESCRIZIONE magnetica (AIDA/EPPPA/PNL/neuromarketing) + hashtag + CTA
- nuovi TAG SEO
- nuova THUMBNAIL "trend" generata (sfondo scuro brandizzato 81+ + testo gancio)
Cosi ogni video torna a sembrare nuovo e diventa EVERGREEN.
NOTA ONESTA: l'API YouTube NON puo' far risultare un video "ripubblicato oggi";
restyle81 aggiorna metadati + copertina (cio' che i sistemi di ranking rivalutano).
Richiede il token MGMT del canale con scope youtube.force-ssl (mgmt_secret).
Ruota scegliendo i video col restyle piu' vecchio; stato in state_restyle.json.
Dipendenze: google-api-python-client google-auth Pillow.
"""
import os, json, re, io, tempfile, datetime, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
CFG  = json.load(open(os.path.join(HERE, "youtube_studio81.json"), encoding="utf-8"))
STATE_P = os.path.join(HERE, "state_restyle.json")
def load_state():
    try: return json.load(open(STATE_P, encoding="utf-8"))
    except Exception: return {"last": {}}
def save_state(s): json.dump(s, open(STATE_P,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
def log(m): print("[restyle81] " + m)

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
def _font(sz):
    from PIL import ImageFont
    for p in FONTS:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

def make_thumb(gancio, badge="81+"):
    """Thumbnail 1280x720 brandizzata 81+ (nero/arancione) col gancio grande."""
    from PIL import Image, ImageDraw
    W,H = 1280,720
    img = Image.new("RGB",(W,H),(11,11,13))
    d = ImageDraw.Draw(img)
    # gradiente verticale scuro
    for y in range(H):
        t=y/H; d.line([(0,y),(W,y)], fill=(int(11+18*t),int(11+10*t),int(13+8*t)))
    # banda arancione a sinistra
    d.rectangle([0,0,18,H], fill=(251,107,0))
    # reticolo 81+ leggero
    for x in range(60,W,64):
        d.line([(x,0),(x,H)], fill=(255,255,255), width=1)
    ov = Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
    od.rectangle([0,0,W,H], fill=(11,11,13,150)); img.paste(Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB"),(0,0))
    d = ImageDraw.Draw(img)
    # badge tondo arancione
    d.ellipse([W-190,40,W-50,180], fill=(251,107,0))
    fb=_font(66); tb=d.textbbox((0,0),badge,font=fb)
    d.text((W-120-(tb[2]-tb[0])/2,110-(tb[3]-tb[1])/2),badge,font=fb,fill=(11,11,13))
    # gancio grande, a capo automatico, ombra
    gancio = (gancio or "").upper()[:80]
    fs=98
    while fs>44:
        f=_font(fs); wrap=textwrap.wrap(gancio, width=max(8,int(W*0.86/(fs*0.56))))
        hh=sum((d.textbbox((0,0),l,font=f)[3]-d.textbbox((0,0),l,font=f)[1])+16 for l in wrap)
        if hh<=H*0.72 and len(wrap)<=4: break
        fs-=6
    f=_font(fs); wrap=textwrap.wrap(gancio, width=max(8,int(W*0.86/(fs*0.56))))
    hh=sum((d.textbbox((0,0),l,font=f)[3]-d.textbbox((0,0),l,font=f)[1])+16 for l in wrap)
    y=(H-hh)//2
    for l in wrap:
        bb=d.textbbox((0,0),l,font=f); w=bb[2]-bb[0]; x=48
        d.text((x+3,y+3),l,font=f,fill=(0,0,0))
        d.text((x,y),l,font=f,fill=(255,255,255))
        y+=(bb[3]-bb[1])+16
    # striscia CTA in basso
    d.rectangle([0,H-70,W,H], fill=(251,107,0))
    fc=_font(40); cta="81plus.net"
    cb=d.textbbox((0,0),cta,font=fc); d.text((W-(cb[2]-cb[0])-40,H-58),cta,font=fc,fill=(11,11,13))
    out=os.path.join(tempfile.gettempdir(),"thumb81_%d.jpg"%int(datetime.datetime.utcnow().timestamp()))
    img.save(out,"JPEG",quality=90); return out

def groq_restyle(voce, tema, cta, hashtag, titolo_vecchio):
    key=os.environ.get("GROQ_API_KEY","").strip()
    fb={"title":titolo_vecchio[:95],
        "description":cta+"\n\n"+" ".join(hashtag),
        "tags":[tema.split(",")[0].strip(),"81plus"]+[h.lstrip("#") for h in hashtag],
        "gancio":(titolo_vecchio or "SICUREZZA")[:40]}
    if not key: return fb
    sys=("Sei un esperto YouTube SEO stile VidIQ. Voce canale: "+voce+". Tema: "+tema+". "
         "Devi RINGIOVANIRE un video gia' pubblicato. Genera JSON con: "
         "'title' (nuovo titolo clickbait virale, curiosita/urgenza, MAX 70 caratteri, keyword in testa), "
         "'description' (magnetica: hook prima riga, AIDA/EPPPA, tocchi PNL e neuromarketing, prime 3 righe con keyword+CTA, "
         "poi valore, poi 4-6 hashtag; italiano, frasi brevi, zero inventiva su norme/prezzi), "
         "'tags' (10-15 keyword SEO italiane), 'gancio' (2-4 PAROLE fortissime per la copertina, MAIUSCOLE). "
         "Chiudi description con CTA: "+cta+". Rispondi SOLO con JSON valido.")
    body=json.dumps({"model":"llama-3.3-70b-versatile",
        "messages":[{"role":"system","content":sys},{"role":"user","content":"Titolo attuale: "+titolo_vecchio}],
        "temperature":0.85,"response_format":{"type":"json_object"}}).encode("utf-8")
    import urllib.request
    req=urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",data=body,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            j=json.loads(json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"])
        j.setdefault("title",titolo_vecchio); j["title"]=j["title"][:95]
        j.setdefault("description",cta); j.setdefault("tags",fb["tags"]); j.setdefault("gancio",fb["gancio"])
        if not any(h in j["description"] for h in hashtag): j["description"]+="\n\n"+" ".join(hashtag)
        return j
    except Exception as e:
        log("restyle AI ko: %s"%e); return fb

def yt_service(token_json):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    data=json.loads(token_json)
    creds=Credentials.from_authorized_user_info(data, scopes=data.get("scopes") or ["https://www.googleapis.com/auth/youtube.force-ssl"])
    return build("youtube","v3",credentials=creds,cache_discovery=False)

def list_long_videos(yt, maxn=50):
    ch=yt.channels().list(part="contentDetails",mine=True).execute()
    items=ch.get("items",[])
    if not items: return []
    up=items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    vids=[]; tok=None
    while len(vids)<maxn:
        pl=yt.playlistItems().list(part="contentDetails",playlistId=up,maxResults=50,pageToken=tok).execute()
        for it in pl.get("items",[]): vids.append(it["contentDetails"]["videoId"])
        tok=pl.get("nextPageToken")
        if not tok: break
    return vids[:maxn]

def restyle_one(yt, vid, c):
    v=yt.videos().list(part="snippet",id=vid).execute().get("items",[])
    if not v: return False
    sn=v[0]["snippet"]
    meta=groq_restyle(c["voce"],c["tema"],c["cta"],c.get("hashtag",[]),sn.get("title",""))
    sn["title"]=meta["title"]; sn["description"]=meta["description"]
    sn["tags"]=meta.get("tags",[])[:30]; sn["categoryId"]=c.get("categoryId",sn.get("categoryId","22"))
    yt.videos().update(part="snippet",body={"id":vid,"snippet":sn}).execute()
    try:
        from googleapiclient.http import MediaFileUpload
        th=make_thumb(meta.get("gancio",""))
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(th)).execute()
        try: os.remove(th)
        except Exception: pass
        log("  + thumbnail aggiornata")
    except Exception as e:
        log("  thumbnail ko (custom thumb non abilitata?): %s"%e)
    log("RESTYLE %s %s -> %s"%(c["handle"],vid,meta["title"])); return True

def run_channel(c, st):
    tok=os.environ.get(c.get("mgmt_secret",""),"").strip()
    if not tok: log("SALTO %s: manca %s (token mgmt force-ssl)."%(c["handle"],c.get("mgmt_secret"))); return
    try: yt=yt_service(tok)
    except Exception as e: log("auth ko %s: %s"%(c["handle"],e)); return
    try: vids=list_long_videos(yt)
    except Exception as e: log("lista video ko %s: %s"%(c["handle"],e)); return
    if not vids: log("%s: nessun video."%c["handle"]); return
    last=st["last"]
    vids.sort(key=lambda x: last.get(x,""))   # prima i mai/piu' vecchi restyle
    n=CFG.get("restyle_per_giro",2); done=0
    for vid in vids[:n]:
        try:
            if restyle_one(yt,vid,c):
                last[vid]=datetime.datetime.utcnow().isoformat()+"Z"; done+=1
        except Exception as e:
            log("restyle ko %s: %s"%(vid,e))
    log("%s: restyle su %d video."%(c["handle"],done))

def main():
    st=load_state()
    for c in CFG["canali"]:
        try: run_channel(c,st)
        except Exception as e: log("errore canale %s: %s"%(c.get("handle"),e))
    save_state(st)
    log("Giro restyle completato "+datetime.datetime.utcnow().isoformat()+"Z")

if __name__=="__main__":
    main()
