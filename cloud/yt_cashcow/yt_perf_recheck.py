# -*- coding: utf-8 -*-
"""YTCASHCOW81+ · RECHECK ciclico — se un video ottimizzato NON cresce entro ~18 giorni,
rigenera titolo/descrizione/thumbnail con un ANGOLO DIVERSO (variante+1) e lo rimette in coda.

Come funziona:
  - Legge cloud_state/yt_perf_track.json (scritto da yt_cashcow_apply.py al momento dell'update):
    {video_id:{applied_at, views_at_apply, variant}}.
  - Per ogni video con eta' dall'apply >= RECHECK_DAYS (default 18): legge le views attuali (API key).
    crescita = views_ora - views_at_apply.  Se crescita < soglia (assoluta o % ) => SOTTO-PERFORMANTE:
      * bump cloud_state/yt_variant.json[video_id] += 1  (fino a MAX_VARIANTS)
      * azzera APPROVA di quel video nel CSV di revisione  -> il motore SEO lo rigenera (angolo diverso)
        e l'apply lo ri-applica al prossimo giro.
      * rimuove il video da yt_perf_track.json (verra' ri-tracciato al nuovo apply).
    Se e' cresciuto bene => e' un "winner", si lascia stare.
  - Scrive cloud_state/yt_recheck.log con l'esito.

ENV: YOUTUBE_API_KEY (obblig.), RECHECK_DAYS(18), MIN_GROWTH_ABS(15), MIN_GROWTH_PCT(0.15), MAX_VARIANTS(4).
Nessun segreto stampato.
"""
import os,json,csv,datetime,pathlib,urllib.request,urllib.parse

HERE=pathlib.Path(__file__).resolve().parent
STATE=pathlib.Path(os.environ.get("GITHUB_WORKSPACE") or HERE.parent.parent)/"cloud_state"; STATE.mkdir(parents=True,exist_ok=True)
REVIEW_CSV=STATE/"yt_seo_review.csv"; PERF=STATE/"yt_perf_track.json"
VARIANT_FILE=STATE/"yt_variant.json"; RLOG=STATE/"yt_recheck.log"

def env(*n,default=""):
    for x in n:
        v=os.getenv(x)
        if v: return v.strip()
    return default

YT_KEY=env("YOUTUBE_API_KEY")
RECHECK_DAYS=int(env("RECHECK_DAYS",default="18") or "18")
MIN_ABS=int(env("MIN_GROWTH_ABS",default="15") or "15")
MIN_PCT=float(env("MIN_GROWTH_PCT",default="0.15") or "0.15")
MAX_VAR=int(env("MAX_VARIANTS",default="4") or "4")

def _loadj(p,d=None):
    try: return json.load(open(p,encoding="utf-8"))
    except Exception: return {} if d is None else d
def _savej(p,d): open(p,"w",encoding="utf-8").write(json.dumps(d,ensure_ascii=False,indent=1))

def views_of(ids):
    out={}
    for i in range(0,len(ids),50):
        u="https://www.googleapis.com/youtube/v3/videos?%s"%urllib.parse.urlencode(
            {"part":"statistics","id":",".join(ids[i:i+50]),"key":YT_KEY})
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"cashcow81/1.0"}),timeout=40) as r:
                d=json.loads(r.read().decode("utf-8","replace"))
            for it in d.get("items",[]): out[it["id"]]=int((it.get("statistics",{}) or {}).get("viewCount",0) or 0)
        except Exception as e: print("[views]",str(e)[:120])
    return out

def clear_approva(vids):
    if not REVIEW_CSV.exists(): return
    with open(REVIEW_CSV,encoding="utf-8") as f:
        rd=csv.DictReader(f); cols=rd.fieldnames; data=[dict(r) for r in rd]
    ch=False
    for r in data:
        if r.get("video_id") in vids:
            r["APPROVA"]=""; r["needs_human_review"]="NO"; ch=True
    if ch:
        with open(REVIEW_CSV,"w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); [w.writerow(r) for r in data]

def main():
    if not YT_KEY: print("[STOP] manca YOUTUBE_API_KEY"); return
    perf=_loadj(PERF); var=_loadj(VARIANT_FILE)
    if not perf: print("[recheck] nessun video ancora applicato: niente da controllare."); return
    today=datetime.date.today(); due=[]
    for vid,info in perf.items():
        try: age=(today-datetime.date.fromisoformat(info.get("applied_at",""))).days
        except Exception: age=0
        if age>=RECHECK_DAYS: due.append(vid)
    print("[recheck] applicati:",len(perf),"| in scadenza (>=%dgg):"%RECHECK_DAYS,len(due))
    if not due: return
    now=views_of(due); reopt=[]; keep=0; log=[]
    for vid in due:
        base=int(perf[vid].get("views_at_apply",0) or 0); cur=now.get(vid,base)
        growth=cur-base; thr=max(MIN_ABS,int(base*MIN_PCT))
        v=int(var.get(vid,0) or 0)
        if growth<thr and v<MAX_VAR:
            var[vid]=v+1; reopt.append(vid)
            log.append("REOPT %s crescita=%d<soglia=%d variante->%d"%(vid,growth,thr,v+1))
        elif growth<thr and v>=MAX_VAR:
            log.append("STOP %s max varianti raggiunte (%d), crescita=%d"%(vid,v,growth))
        else:
            keep+=1; log.append("WINNER %s crescita=%d>=soglia=%d"%(vid,growth,thr))
    if reopt:
        _savej(VARIANT_FILE,var)
        clear_approva(set(reopt))
        for vid in reopt: perf.pop(vid,None)   # verra' ri-tracciato dopo il nuovo apply
        _savej(PERF,perf)
    with open(RLOG,"a",encoding="utf-8") as f:
        f.write("== %s ==\n"%datetime.datetime.utcnow().isoformat()+"\n".join(log)+"\n")
    print("[recheck] winner:",keep,"| ri-ottimizzo:",len(reopt))

if __name__=="__main__": main()
