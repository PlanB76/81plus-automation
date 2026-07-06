# -*- coding: utf-8 -*-
"""YTCASHCOW81+ v2 — canale @sicurissimo VIVO H24, 3 stream/giorno (tutti diversi ogni giorno, day-of-year ciclico):
 A) 3 SHORTS Tales verticali (da PROGRAMMA 365) — titolo clickbait, descrizione SEO, hashtag, KEYWORDS, CTA prodotto.
 B) 3 POST Tales (vignette WebP leggere da tales_web) — stessa copy SEO + CTA prodotto (YT community: pronto; TG/social: auto sendPhoto).
 C) 3 VECCHI VIDEO riciclati — nuovo titolo/descrizione/tag(keywords)/THUMBNAIL WOW (base = vignetta Tales tema + overlay brand).
Segreti da env: YOUTUBE_TOKEN_JSON, YOUTUBE_API_KEY, TELEGRAM_BOT_TOKEN. Senza token YT -> DRY-RUN (report)."""
import json,os,sys,datetime,pathlib,urllib.request,urllib.parse
HERE=pathlib.Path(__file__).resolve().parent; DATA=HERE/"data"; STATE=HERE.parent/"cloud_state"; STATE.mkdir(exist_ok=True)
sys.path.insert(0,str(HERE)); import ytseo81 as seo
def L(n,d=None):
    p=DATA/n; return json.load(open(p,encoding="utf-8")) if p.exists() else d
PROG=L("sicurix_program365.json",[]); TALES=L("tales_manifest.json",[]); PROD=L("product_links.json",[]); CH=L("channels.json") or []
doy=int(os.environ.get("FORCE_DAY") or datetime.date.today().timetuple().tm_yday); day=((doy-1)%365)+1
today=[dict(r) for r in PROG if r["day"]==day]
def tale(theme,i):
    pool=[m for m in TALES if m.get("theme")==theme] or TALES
    return pool[i%len(pool)] if pool else None
def tg(ep,payload):
    tok=os.environ.get("TELEGRAM_BOT_TOKEN"); ch=os.environ.get("TG_CHANNEL")
    if not tok or not ch: return "skip"
    payload["chat_id"]=ch
    try: urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/{ep}",data=urllib.parse.urlencode(payload).encode(),timeout=20); return "sent"
    except Exception as e: return f"err:{e}"
def yt_service():
    tj=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not tj: return None
    try:
        from google.oauth2.credentials import Credentials; from googleapiclient.discovery import build
        return build("youtube","v3",credentials=Credentials.from_authorized_user_info(json.loads(tj),["https://www.googleapis.com/auth/youtube"]),cache_discovery=False)
    except Exception as e: print("YT auth:",e); return None
def wow_thumb(title,theme,out):
    """Thumbnail WOW: base = vignetta Tales (webp leggero) tema-matched + overlay brand + hook grande (retina)."""
    try:
        from PIL import Image,ImageDraw,ImageFont,ImageEnhance
        base=None; t=tale(theme,seo._seed(title))
        if t:
            fp=HERE.parent/"tales_web"/t["file"]
            if fp.exists(): base=Image.open(fp).convert("RGB")
        W,H=1280,720; im=Image.new("RGB",(W,H),(5,5,10))
        if base:
            b=base.copy(); r=max(W/b.width,H/b.height); b=b.resize((int(b.width*r),int(b.height*r)))
            im.paste(b,((W-b.width)//2,(H-b.height)//2)); im=ImageEnhance.Brightness(im).enhance(0.72)
        d=ImageDraw.Draw(im); d.rectangle([0,0,W,16],fill=(232,80,26)); d.rectangle([0,H-16,W,H],fill=(232,80,26))
        try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",104)
        except: f=ImageFont.load_default()
        import textwrap; y=90
        for ln in textwrap.wrap(title[:64],width=15)[:4]:
            for ox,oy in [(-3,-3),(3,-3),(-3,3),(3,3)]: d.text((70+ox,y+oy),ln,font=f,fill=(5,5,10))
            d.text((70,y),ln,font=f,fill=(255,255,255)); y+=112
        d.text((72,H-92),"81plus.net",font=f,fill=(255,210,74))
        im.save(out,"JPEG",quality=88); return True
    except Exception as e: print("thumb:",e); return False
def main():
    rep=[]; ch=(CH[0] if CH else {"handle":"@sicurissimo","channel_id":os.environ.get("YT_CHANNEL_ID","")})
    out=[f"# 🐄 YTCASHCOW81+ — @sicurissimo · GIORNO {day}/365",""]
    # STREAM A — SHORTS
    out.append("## A) 3 SHORTS Tales verticali (da pubblicare)")
    for r in today:
        kw=seo.keywords(r["titolo"],r["theme"],r["prodotto"])
        out+=[f"\n### {r['slot']} · {r['theme']} — {r['titolo']}",
              f"- CTA prodotto: {r['cta_label']} → {r['cta_url']}",
              f"- KEYWORDS/tag: {', '.join(kw)}",f"- Hashtag: {r['hashtag']}",
              f"- Descrizione:\n{r['descrizione']}",f"- PROMPT GEMINI: {r['gemini_prompt']}"]
    # STREAM B — POST TALES (immagine leggera)
    out.append("\n## B) 3 POST Tales (vignette WebP leggere)")
    for idx,r in enumerate(today):
        t=tale(r["theme"],day+idx); url=(t.get("drive_url") if t else "")
        title=seo.viral_title(r["prodotto"],r["theme"],idx); desc=seo.magnetic_desc(title,PROD,ch["handle"],r["theme"])
        kw=seo.keywords(title,r["theme"],r["prodotto"])
        out+=[f"\n### {r['theme']} · POST — {title}",f"- Immagine: {url}",f"- CTA prodotto: {r['cta_url']}",
              f"- KEYWORDS: {', '.join(kw)}",f"- Descrizione:\n{desc}"]
        # auto TG/social come foto leggera
        st=tg("sendPhoto",{"photo":url,"caption":f"🟧 {title}\n👉 {r['cta_url']}\n👉 81plus.net"}) if url else "no-img"
        rep.append({"stream":"POST","tema":r["theme"],"tg":st,"img":os.path.basename(url) if url else ""})
    # STREAM C — RICICLO 3 vecchi video
    out.append("\n## C) 3 VECCHI VIDEO riciclati (titolo+descrizione+tag+THUMBNAIL WOW)")
    yt=yt_service(); s=json.load(open(STATE/"ytcashcow_v2_state.json",encoding="utf-8")) if (STATE/"ytcashcow_v2_state.json").exists() else {}
    themes=["Sicurezza","HACCP","Privacy"]
    s.setdefault("idx",0); s.setdefault("ids",[])
    if yt and ch.get("channel_id"):
        try:
            if not s.get("ids"):
                pl=yt.channels().list(part="contentDetails",id=ch["channel_id"]).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                ids=[]; tok=None
                while True:
                    rr=yt.playlistItems().list(part="contentDetails",playlistId=pl,maxResults=50,pageToken=tok).execute()
                    ids+=[it["contentDetails"]["videoId"] for it in rr["items"]]; tok=rr.get("nextPageToken")
                    if not tok: break
                s["ids"]=ids
            for k in range(3):
                vid=s["ids"][(s["idx"]+k)%len(s["ids"])]; th=themes[k]
                v=yt.videos().list(part="snippet",id=vid).execute()["items"][0]["snippet"]
                nt=seo.viral_title(v.get("title",""),th,day); nd=seo.magnetic_desc(v.get("title",""),PROD,ch["handle"],th)
                v["title"]=nt; v["description"]=nd; v["tags"]=seo.keywords(nt,th); v["categoryId"]=v.get("categoryId","27")
                yt.videos().update(part="snippet",body={"id":vid,"snippet":v}).execute()
                tp=str(STATE/f"th_{vid}.jpg")
                if wow_thumb(nt,th,tp):
                    from googleapiclient.http import MediaFileUpload
                    yt.thumbnails().set(videoId=vid,media_body=MediaFileUpload(tp)).execute()
                out.append(f"- ✅ {vid}: '{nt}' + thumbnail WOW")
                rep.append({"stream":"RICICLO","video":vid,"title":nt})
            s["idx"]=(s["idx"]+3)%max(len(s["ids"]),1)
        except Exception as e: out.append(f"- errore riciclo: {e}")
    else:
        for k in range(3):
            th=themes[k]; nt=seo.viral_title(f"video {th} #{s['idx']+k+1}",th,day)
            out.append(f"- DRY-RUN [{th}] nuovo titolo: {nt} (+thumbnail WOW) — manca YOUTUBE_TOKEN_JSON")
        s["idx"]=s["idx"]+3
    json.dump(s,open(STATE/"ytcashcow_v2_state.json","w",encoding="utf-8"),ensure_ascii=False)
    (HERE.parent/"YTCASHCOW_OGGI.md").write_text("\n".join(out),encoding="utf-8")
    json.dump({"day":day,"azioni":rep,"ts":datetime.datetime.now().isoformat()},open(HERE.parent/"YTCASHCOW_REPORT.json","w",encoding="utf-8"),ensure_ascii=False)
    print(f"YTCASHCOW v2 giorno {day}: 3 shorts + 3 post + 3 riciclo · azioni {len(rep)}")
if __name__=="__main__": main()
