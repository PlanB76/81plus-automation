# -*- coding: utf-8 -*-
"""YTCASHCOW81+ · BASELINE — fotografia del canale PRIMA di ottimizzare.

Con solo YOUTUBE_API_KEY (lettura pubblica) estrae per OGNI video: titolo, data, views, like, commenti,
durata; calcola outlier (video che rendono di piu' a parita' di eta') e ordina per views.
Scrive cloud_state/yt_baseline.csv + cloud_state/yt_baseline.md (top 20 + coda).

Le FONTI DI TRAFFICO reali (YT_SEARCH vs BROWSE) richiedono la YouTube Analytics API con OAuth del
proprietario del canale: se e' presente YOUTUBE_TOKEN_JSON con scope yt-analytics.readonly, aggiunge la
colonna views_search_28d (ultimi 28 giorni da ricerca). Senza token, la baseline resta su dati pubblici.
ENV: YOUTUBE_API_KEY (obblig.), YT_CHANNEL_ID (o channels.json), YOUTUBE_TOKEN_JSON (opz.).
"""
import os,sys,json,csv,re,datetime,pathlib,urllib.request,urllib.parse

HERE=pathlib.Path(__file__).resolve().parent
STATE=HERE.parent/"cloud_state"; STATE.mkdir(parents=True,exist_ok=True)

def env(*n,default=""):
    for x in n:
        v=os.getenv(x)
        if v: return v.strip()
    return default

YT_KEY=env("YOUTUBE_API_KEY")

def api(path,**p):
    p["key"]=YT_KEY
    url="https://www.googleapis.com/youtube/v3/%s?%s"%(path,urllib.parse.urlencode(p))
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"cashcow81/1.0"}),timeout=40) as r:
        return json.loads(r.read().decode("utf-8","replace"))

def channel_id():
    cid=env("YT_CHANNEL_ID")
    if cid: return cid
    for cj in (HERE/"channels.json",HERE.parent/"cloud"/"channels.json"):
        if cj.exists():
            try: return json.load(open(cj,encoding="utf-8"))[0]["channel_id"]
            except Exception: pass
    return ""

def iso_dur_sec(d):
    m=re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",d or "")
    if not m: return 0
    h,mi,s=(int(x) if x else 0 for x in m.groups()); return h*3600+mi*60+s

def all_ids(cid):
    up=api("channels",part="contentDetails",id=cid)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids=[]; tok=None
    while True:
        d=api("playlistItems",part="contentDetails",playlistId=up,maxResults=50,**({"pageToken":tok} if tok else {}))
        ids+=[x["contentDetails"]["videoId"] for x in d.get("items",[]) if x["contentDetails"].get("videoId")]
        tok=d.get("nextPageToken")
        if not tok: break
    return ids

def analytics_search(cid):
    """views ultimi 28gg da ricerca YouTube, per video. Richiede OAuth yt-analytics.readonly."""
    tj=env("YOUTUBE_TOKEN_JSON")
    if not tj: return {}
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds=Credentials.from_authorized_user_info(json.loads(tj),
            ["https://www.googleapis.com/auth/yt-analytics.readonly"])
        ya=build("youtubeAnalytics","v2",credentials=creds,cache_discovery=False)
        end=datetime.date.today(); start=end-datetime.timedelta(days=28)
        res=ya.reports().query(ids="channel==MINE",startDate=str(start),endDate=str(end),
            metrics="views",dimensions="video",filters="insightTrafficSourceType==YT_SEARCH",
            maxResults=200,sort="-views").execute()
        return {row[0]:int(row[1]) for row in res.get("rows",[])}
    except Exception as e:
        print("[analytics]",str(e)[:140]); return {}

def main():
    if not YT_KEY: print("[STOP] manca YOUTUBE_API_KEY"); return
    cid=channel_id()
    if not cid: print("[STOP] manca YT_CHANNEL_ID/channels.json"); return
    print("[canale]",cid)
    ids=all_ids(cid); print("[video]",len(ids))
    search=analytics_search(cid)
    rows=[]
    for i in range(0,len(ids),50):
        d=api("videos",part="snippet,statistics,contentDetails",id=",".join(ids[i:i+50]))
        for it in d.get("items",[]):
            sn=it["snippet"]; st=it.get("statistics",{}); cd=it.get("contentDetails",{})
            pub=sn.get("publishedAt","")[:10]
            age=1
            try: age=max(1,(datetime.date.today()-datetime.date.fromisoformat(pub)).days)
            except Exception: pass
            views=int(st.get("viewCount",0) or 0)
            rows.append({"video_id":it["id"],"url":"https://youtu.be/"+it["id"],
                "titolo":sn.get("title",""),"pubblicato":pub,"eta_giorni":age,
                "views":views,"views_al_giorno":round(views/age,2),
                "like":int(st.get("likeCount",0) or 0),"commenti":int(st.get("commentCount",0) or 0),
                "durata_sec":iso_dur_sec(cd.get("duration","")),
                "views_search_28d":search.get(it["id"],"")})
    rows.sort(key=lambda r:-r["views"])
    cols=["video_id","url","titolo","pubblicato","eta_giorni","views","views_al_giorno","like","commenti","durata_sec","views_search_28d"]
    with open(STATE/"yt_baseline.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); [w.writerow(r) for r in rows]
    tot=sum(r["views"] for r in rows)
    out=["# YTCASHCOW81+ · BASELINE canale","",
         "Data snapshot: %s · Video: %d · Views totali: %d"%(datetime.date.today(),len(rows),tot),""]
    out.append("## Top 20 per views (gli outlier attuali)")
    for r in rows[:20]:
        out.append("- **%d views** (%s/gg) · %s"%(r["views"],r["views_al_giorno"],r["titolo"][:70]))
    out+=["","## 20 video piu' deboli (priorita' backfill SEO)"]
    for r in [x for x in rows if x["eta_giorni"]>30][-20:]:
        out.append("- %d views · %s"%(r["views"],r["titolo"][:70]))
    if search: out+=["","## Fonte ricerca (ultimi 28gg, YT_SEARCH) presente nella colonna views_search_28d."]
    else: out+=["","> Fonti di traffico reali non disponibili (manca OAuth yt-analytics.readonly)."]
    (STATE/"yt_baseline.md").write_text("\n".join(out),encoding="utf-8")
    print("[OK] baseline:",STATE/"yt_baseline.csv","+",STATE/"yt_baseline.md")

if __name__=="__main__": main()
