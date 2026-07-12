# -*- coding: utf-8 -*-
"""YTCASHCOW81+ · APPLY — applica a YouTube SOLO le righe APPROVATE del CSV di revisione.

Legge cloud_state/yt_seo_review.csv. Per ogni riga con APPROVA in (SI,SÌ,S,YES,Y,X,OK,1):
  - videos.update: snippet.title = titolo_seo, snippet.description = descrizione_seo, snippet.tags = tags
    (mantiene categoryId e defaultLanguage esistenti; legge lo snippet attuale prima di scrivere).
  - thumbnails.set: genera al volo una thumbnail 1280x720 brandizzata (testo max 4 parole, colore per tema)
    e la carica. Disattivabile con YT_APPLY_THUMB=0.
Dopo l'apply mette APPROVA=FATTO sulla riga (idempotente: non ritocca due volte).

RICHIEDE: YOUTUBE_TOKEN_JSON (OAuth con scope youtube / youtube.force-ssl). Senza token -> DRY-RUN (stampa e basta).
ENV opz.: YT_APPLY_LIMIT (max righe per giro), YT_APPLY_THUMB (1/0).
Nessun segreto stampato.
"""
import os,sys,json,csv,datetime,pathlib,io

HERE=pathlib.Path(__file__).resolve().parent
STATE=pathlib.Path(os.environ.get("GITHUB_WORKSPACE") or HERE.parent.parent)/"cloud_state"; STATE.mkdir(parents=True,exist_ok=True)
REVIEW_CSV=STATE/"yt_seo_review.csv"
LOG=STATE/"yt_seo_applied.log"
ROLLBACK=STATE/"yt_seo_rollback.csv"      # metadati ORIGINALI salvati prima di sovrascrivere
PERF=STATE/"yt_perf_track.json"           # {video_id:{applied_at,views_at_apply,variant}}
VARIANT_FILE=STATE/"yt_variant.json"

def _loadj(p):
    try: return json.load(open(p,encoding="utf-8"))
    except Exception: return {}
def _savej(p,d): open(p,"w",encoding="utf-8").write(json.dumps(d,ensure_ascii=False,indent=1))
def save_rollback(vid,sn):
    exists=ROLLBACK.exists()
    with open(ROLLBACK,"a",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        if not exists: w.writerow(["video_id","orig_title","orig_desc","orig_tags","ts"])
        w.writerow([vid,sn.get("title",""),(sn.get("description","") or "").replace("\n","\\n"),
                    "|".join(sn.get("tags",[]) or []),datetime.datetime.utcnow().isoformat()])

def env(*n,default=""):
    for x in n:
        v=os.getenv(x)
        if v: return v.strip()
    return default

YES={"si","sì","s","yes","y","x","ok","1","true","approva","approvo"}
DONE_MARK="FATTO"
LIMIT=int(env("YT_APPLY_LIMIT",default="0") or "0")
DO_THUMB=env("YT_APPLY_THUMB",default="1")!="0"

COLORS={"rosso":(220,38,38),"verde":(22,163,74),"arancione":(232,120,26)}

def yt_service():
    tj=env("YOUTUBE_TOKEN_JSON")
    if not tj: return None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds=Credentials.from_authorized_user_info(json.loads(tj),
            ["https://www.googleapis.com/auth/youtube","https://www.googleapis.com/auth/youtube.force-ssl"])
        return build("youtube","v3",credentials=creds,cache_discovery=False)
    except Exception as e:
        print("[YT auth]",str(e)[:160]); return None

def make_thumb(text,color,out):
    try:
        from PIL import Image,ImageDraw,ImageFont
        import textwrap
        W,H=1280,720; im=Image.new("RGB",(W,H),(12,14,20)); d=ImageDraw.Draw(im)
        # bande brand 81+
        d.rectangle([0,0,W,18],fill=(232,120,26)); d.rectangle([0,H-18,W,H],fill=(232,120,26))
        col=COLORS.get((color or "arancione").lower(),COLORS["arancione"])
        try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",150)
        except Exception:
            try: f=ImageFont.truetype("DejaVuSans-Bold.ttf",150)
            except Exception: f=ImageFont.load_default()
        y=140
        for ln in textwrap.wrap((text or "SICUREZZA").upper(),width=11)[:4]:
            for ox,oy in [(-4,-4),(4,-4),(-4,4),(4,4),(0,0)]:
                d.text((70+ox,y+oy),ln,font=f,fill=(0,0,0))
            d.text((70,y),ln,font=f,fill=col); y+=158
        d.text((74,H-96),"81plus.net",font=f,fill=(255,210,74))
        im.save(out,"JPEG",quality=88); return True
    except Exception as e:
        print("  [thumb]",str(e)[:120]); return False

def rows():
    if not REVIEW_CSV.exists():
        print("[STOP] manca",REVIEW_CSV,"- lancia prima yt_cashcow_seo.py"); return [],[]
    with open(REVIEW_CSV,encoding="utf-8") as f:
        rd=csv.DictReader(f); cols=rd.fieldnames; data=[dict(r) for r in rd]
    return data,cols

def main():
    data,cols=rows()
    if not data: return
    yt=yt_service()
    dry = yt is None
    print("[MODE]","DRY-RUN (nessun token)" if dry else "APPLY LIVE")
    n=0; changed=False
    for r in data:
        ap=(r.get("APPROVA") or "").strip().lower()
        if ap in (DONE_MARK.lower(),"fatto"): continue
        if ap not in YES: continue
        vid=r["video_id"]; title=r.get("titolo_seo","").strip()[:100]
        desc=r.get("descrizione_seo","").strip()[:4900]
        tags=[t.strip() for t in (r.get("tags","") or "").split(",") if t.strip()][:15]
        print("[apply]",vid,"|",title[:60])
        if dry:
            print("   (dry) title/desc/tags pronti; thumb:",r.get("thumb_text","")); continue
        try:
            cur=yt.videos().list(part="snippet,statistics",id=vid).execute()
            it=(cur.get("items") or [{}])[0]; sn=it.get("snippet",{})
            views_now=int((it.get("statistics",{}) or {}).get("viewCount",0) or 0)
            save_rollback(vid,sn)   # salva l'originale PRIMA di sovrascrivere (recuperabile)
            sn["title"]=title or sn.get("title"); sn["description"]=desc or sn.get("description")
            sn["tags"]=tags or sn.get("tags",[])
            sn.setdefault("categoryId",sn.get("categoryId","27"))  # 27 = Education
            yt.videos().update(part="snippet",body={"id":vid,"snippet":sn}).execute()
            if DO_THUMB:
                out=STATE/("thumb_%s.jpg"%vid)
                if make_thumb(r.get("thumb_text",""),r.get("thumb_color",""),out):
                    try:
                        from googleapiclient.http import MediaFileUpload
                        yt.thumbnails().set(videoId=vid,media_body=MediaFileUpload(str(out))).execute()
                    except Exception as e: print("   [thumb set]",str(e)[:120])
            # tracciamento performance per il ciclo di ri-ottimizzazione a 18gg
            perf=_loadj(PERF); var=_loadj(VARIANT_FILE)
            perf[vid]={"applied_at":datetime.date.today().isoformat(),"views_at_apply":views_now,
                       "variant":int(var.get(vid,0) or 0)}
            _savej(PERF,perf)
            r["APPROVA"]=DONE_MARK; changed=True; n+=1
            with open(LOG,"a",encoding="utf-8") as lg:
                lg.write("%s\t%s\t%s\n"%(datetime.datetime.utcnow().isoformat(),vid,title[:80]))
            print("   [OK] aggiornato")
        except Exception as e:
            print("   [ERR]",str(e)[:160])
        if LIMIT and n>=LIMIT: break
    if changed:
        with open(REVIEW_CSV,"w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
            for r in data: w.writerow(r)
    print("[FINE] aggiornati:",n)

if __name__=="__main__": main()
