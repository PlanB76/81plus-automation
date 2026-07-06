# -*- coding: utf-8 -*-
"""KIE.AI Veo3 · render automatico degli SHORT SICURIX 9:16.
Genera i 3 short del giorno (da PROGRAMMA 365) via kie.ai: POST /veo/generate -> poll record-info -> scarica mp4.
CHIAVE: letta SOLO da env KIE_API_KEY (mai nel codice). Reference visiva opzionale (master visual SICURIX) per coerenza personaggi."""
import os,sys,json,time,datetime,pathlib,urllib.request,urllib.parse
HERE=pathlib.Path(__file__).resolve().parent; DATA=HERE/"data"
BASE="https://api.kie.ai"
KEY=os.environ.get("KIE_API_KEY","")
MODEL=os.environ.get("KIE_MODEL","veo3_fast")
REF=os.environ.get("KIE_REF_IMAGE","")  # es. URL raw del master visual SICURIX (coerenza personaggi)
OUT=HERE.parent/"shorts_out"; OUT.mkdir(exist_ok=True)
def _req(method,path,body=None):
    url=BASE+path
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=60) as resp: return json.loads(resp.read().decode())
def generate(prompt,aspect="9:16",image_urls=None):
    body={"prompt":prompt,"model":MODEL,"aspectRatio":aspect}
    if image_urls: body["imageUrls"]=image_urls
    d=_req("POST","/api/v1/veo/generate",body)
    return (d.get("data") or {}).get("taskId") or d.get("taskId")
def poll(task_id,timeout=600,every=15):
    t0=time.time()
    while time.time()-t0<timeout:
        d=_req("GET",f"/api/v1/veo/record-info?taskId={urllib.parse.quote(task_id)}")
        data=d.get("data") or {}
        flag=data.get("successFlag")
        if flag==1:
            resp=data.get("response") or {}
            urls=resp.get("resultUrls") or resp.get("videoUrls") or data.get("resultUrls") or []
            return urls[0] if urls else None
        if flag in (2,3): return None
        time.sleep(every)
    return None
def download(url,dest):
    with urllib.request.urlopen(url,timeout=120) as r, open(dest,"wb") as f: f.write(r.read())
    return os.path.getsize(dest)

def yt_upload_short(path,title,desc,tags):
    tj=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not tj: return "no-token"
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        yt=build("youtube","v3",credentials=Credentials.from_authorized_user_info(json.loads(tj),["https://www.googleapis.com/auth/youtube.upload"]),cache_discovery=False)
        body={"snippet":{"title":(title+" #Shorts")[:95],"description":desc[:4900],"tags":tags[:15],"categoryId":"27"},"status":{"privacyStatus":os.environ.get("YT_PRIVACY","private"),"selfDeclaredMadeForKids":False}}
        media=MediaFileUpload(path,mimetype="video/mp4",resumable=True)
        r=yt.videos().insert(part="snippet,status",body=body,media_body=media).execute()
        return r.get("id","ok")
    except Exception as e: return f"upload-err:{e}"

def run_today():
    if not KEY: print("KIE_API_KEY assente -> DRY-RUN (nessuna chiamata)."); return []
    PROG=json.load(open(DATA/"sicurix_program365.json",encoding="utf-8"))
    doy=int(os.environ.get("FORCE_DAY") or datetime.date.today().timetuple().tm_yday); day=((doy-1)%365)+1
    items=[r for r in PROG if r["day"]==day]; done=[]
    refs=[REF] if REF else None
    for r in items:
        try:
            tid=generate(r["gemini_prompt"],aspect="9:16",image_urls=refs)
            if not tid: done.append({"tema":r["theme"],"stato":"no-taskId"}); continue
            url=poll(tid)
            if not url: done.append({"tema":r["theme"],"taskId":tid,"stato":"fallito/timeout"}); continue
            fn=OUT/f"SICURIX_{day:03d}_{r['theme']}_{r['slot'].replace(':','')}.mp4"
            kb=download(url,fn)//1024
            import sys as _s; _s.path.insert(0,str(HERE)); import ytseo81 as _seo
            vid=yt_upload_short(str(fn),r["titolo"],r["descrizione"],_seo.keywords(r["titolo"],r["theme"],r["prodotto"]))
            done.append({"tema":r["theme"],"file":fn.name,"kb":kb,"yt":vid,"stato":"OK"})
            print(f"OK {r['theme']}: {fn.name} ({kb}KB)")
        except Exception as e: done.append({"tema":r["theme"],"stato":f"errore:{e}"})
    json.dump({"day":day,"render":done,"ts":datetime.datetime.now().isoformat()},open(HERE.parent/"KIE_SHORTS_REPORT.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("KIE render:",sum(1 for d in done if d.get('stato')=='OK'),"/",len(items),"ok")
    return done
if __name__=="__main__": run_today()
