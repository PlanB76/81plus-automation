# -*- coding: utf-8 -*-
"""YTCASHCOW81+ · motore GLOBALE H24 multi-canale (GitHub Actions).
Per OGNI canale in channels.json:
 A) RICICLO EVERGREEN: prende N video vecchi/giorno (rotazione ciclica, stato salvato) e AGGIORNA
    titolo->clickbait, descrizione->magnetica super-SEO (con CHECK + CTA prodotti reali dal LISTINO + iscrizione canale),
    tag/hashtag e THUMBNAIL brandizzata. Via YouTube Data API (serve OAuth write token).
 B) SOCIAL81+: pubblica lo short-del-giorno (piano editoriale 365 ciclico) su Telegram (canale pubblico + privato)
    con CTA al canale YT e a un prodotto reale su 81plus.net.
Senza token YT -> DRY-RUN: scrive un report di cosa cambierebbe (sicuro, testabile).
Segreti SOLO da env: YOUTUBE_TOKEN_JSON, YOUTUBE_API_KEY, TELEGRAM_BOT_TOKEN. Guard compliance in ytseo81."""
import json,os,sys,datetime,pathlib,urllib.request,urllib.parse
HERE=pathlib.Path(__file__).resolve().parent
DATA=HERE/"data"; STATE=HERE.parent/"cloud_state"; STATE.mkdir(exist_ok=True)
sys.path.insert(0,str(HERE)); import ytseo81 as seo
def L(n,d=None):
    p=DATA/n; return json.load(open(p,encoding="utf-8")) if p.exists() else d
PRODUCTS=L("product_links.json",[]); EDIT=L("editorial_365.json",[]); CH=L("channels.json") or json.load(open(HERE/"channels.json",encoding="utf-8"))
def st_load():
    p=STATE/"ytcashcow_state.json"; return json.load(open(p,encoding="utf-8")) if p.exists() else {}
def st_save(s): json.dump(s,open(STATE/"ytcashcow_state.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
def tg_send(chat,text):
    tok=os.environ.get("TELEGRAM_BOT_TOKEN")
    if not tok or not chat: return "skip(no token/chat)"
    try:
        data=urllib.parse.urlencode({"chat_id":chat,"text":text,"disable_web_page_preview":"false"}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage",data=data,timeout=20); return "sent"
    except Exception as e: return f"err:{e}"
def yt_service():
    tj=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not tj: return None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        info=json.loads(tj); creds=Credentials.from_authorized_user_info(info,["https://www.googleapis.com/auth/youtube"])
        return build("youtube","v3",credentials=creds,cache_discovery=False)
    except Exception as e: print("YT auth err:",e); return None
def thumb(title,path):
    try:
        from PIL import Image,ImageDraw,ImageFont
        W,H=1280,720; im=Image.new("RGB",(W,H),(13,15,20)); d=ImageDraw.Draw(im)
        d.rectangle([0,0,W,14],fill=(255,90,0)); d.rectangle([0,H-14,W,H],fill=(255,90,0))
        try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",96)
        except: f=ImageFont.load_default()
        import textwrap; y=140
        for ln in textwrap.wrap(title[:70],width=16)[:4]:
            d.text((70,y),ln,font=f,fill=(255,255,255)); y+=110
        d.text((70,H-90),"81plus.net",font=f,fill=(255,90,0))
        im.save(path,"JPEG",quality=88); return True
    except Exception as e: print("thumb err:",e); return False
def get_upload_ids(yt,channel_id,cache):
    if cache.get("ids"): return cache["ids"]
    ch=yt.channels().list(part="contentDetails",id=channel_id).execute()
    pl=ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids=[]; tok=None
    while True:
        r=yt.playlistItems().list(part="contentDetails",playlistId=pl,maxResults=50,pageToken=tok).execute()
        ids+=[it["contentDetails"]["videoId"] for it in r["items"]]
        tok=r.get("nextPageToken");
        if not tok: break
    cache["ids"]=ids; return ids
def recycle_channel(c,state,report):
    yt=yt_service(); key=c["handle"]; s=state.setdefault(key,{"idx":0,"ids":[]})
    n=int(c.get("recycle_per_day",3))
    if not yt:
        # DRY-RUN: mostra copy che verrebbe applicata a 'n' segnaposto
        for k in range(n):
            demo=f"[video vecchio #{s['idx']+k+1}]"
            report.append({"canale":key,"video":demo,"nuovo_titolo":seo.clickbait(f"Sicurezza sul lavoro {k}"),
                "azione":"DRY-RUN (manca YOUTUBE_TOKEN_JSON)"})
        s["idx"]+=n; return
    ids=get_upload_ids(yt,c["channel_id"],s)
    if not ids: report.append({"canale":key,"azione":"nessun video trovato"}); return
    for k in range(n):
        vid=ids[(s["idx"]+k)%len(ids)]
        try:
            v=yt.videos().list(part="snippet",id=vid).execute()["items"][0]["snippet"]
            old=v.get("title",""); area=""
            title=seo.clickbait(old); desc=seo.magnetic_desc(old,PRODUCTS,c["handle"],area)
            tags=[t.strip("#") for t in seo.hashtags(area,old).split()][:15]
            v["title"]=title; v["description"]=desc; v["categoryId"]=v.get("categoryId","27"); v["tags"]=tags
            yt.videos().update(part="snippet",body={"id":vid,"snippet":v}).execute()
            tp=str(STATE/f"thumb_{vid}.jpg")
            if thumb(title,tp):
                from googleapiclient.http import MediaFileUpload
                yt.thumbnails().set(videoId=vid,media_body=MediaFileUpload(tp)).execute()
            report.append({"canale":key,"video":vid,"nuovo_titolo":title,"azione":"AGGIORNATO (titolo+desc+tag+thumb)"})
        except Exception as e: report.append({"canale":key,"video":vid,"azione":f"errore:{e}"})
    s["idx"]=(s["idx"]+n)%max(len(ids),1)
def social_short(c,report):
    if not EDIT: return
    doy=int(os.environ.get("FORCE_DAY") or datetime.date.today().timetuple().tm_yday); day=((doy-1)%365)+1
    items=[x for x in EDIT if x["day"]==day][:1]
    if not items: return
    x=items[0]; ctas=seo.pick_ctas(PRODUCTS,x["titolo"],1)
    prod=(f"\n🛒 {ctas[0]['cta']}: {ctas[0]['url']}" if ctas else "")
    msg=(f"🟧 {x['titolo']}\n\n{x.get('telegram','')}\n\n▶️ Guarda su YouTube {c['handle']}\n"
         f"👉 Check gratuito: https://81plus.net/?src=tg{prod}\n\n{x.get('hashtag','')}")
    for chat in [c.get("tg_public"),c.get("tg_private")]:
        if chat: report.append({"canale":c["handle"],"tg":chat,"stato":tg_send(chat,msg)})
def main():
    state=st_load(); report=[]
    for c in CH:
        if not c.get("active",True): continue
        recycle_channel(c,state,report); social_short(c,report)
    st_save(state)
    out=HERE.parent/"YTCASHCOW_REPORT.md"; now=datetime.datetime.now().isoformat(timespec="seconds")
    lines=[f"# YTCASHCOW81+ — report {now}",""]
    for r in report: lines.append("- "+json.dumps(r,ensure_ascii=False))
    out.write_text("\n".join(lines),encoding="utf-8")
    print(f"YTCASHCOW81+ done · {len(report)} azioni · report -> {out}")
if __name__=="__main__": main()
