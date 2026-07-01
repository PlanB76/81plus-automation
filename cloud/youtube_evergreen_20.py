import os, json, re, datetime, base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path.cwd()
STATE_DIR = ROOT / "cloud_state"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "evergreen_20_state.json"
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]

def yt():
    raw = base64.b64decode(os.environ["YOUTUBE_TOKEN_B64"]).decode("utf-8-sig")
    token = json.loads(raw)
    return build("youtube", "v3", credentials=Credentials.from_authorized_user_info(token, SCOPES))

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"index": 0, "updated": []}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")

def clean_title(t):
    t = re.sub(r"[🔥🚨⚠️❌✅🔴🟠]+", "", t or "").strip()
    t = t.replace("|", "-").replace("· SICURISSIMO81+", "").replace("- SICURISSIMO81+", "").strip()
    t = re.sub(r"\s+", " ", t)
    if len(t) > 52:
        t = t[:52].rsplit(" ", 1)[0]
    return f"{t}: cosa controllare davvero - SICURISSIMO81+"

def desc(title):
    return f"""🟠 {title}

Il punto non è avere un documento, un corso o una scadenza scritta da qualche parte.
Il punto è sapere cosa controllare, cosa manca e quale primo passo fare.

Con 81+ parti da una logica semplice:
Prima vedi.
Poi ordini.
Poi scegli.

✅ Sicurezza sul lavoro
✅ HACCP e igiene alimentare
✅ Privacy e GDPR
✅ Corsi e formazione
✅ Documenti, scadenze e audit

👉 Vai su 81plus.net:
https://81plus.net

Canale Telegram:
https://t.me/sicurissimi

#81plus #Sicurissimo81 #SicurezzaSulLavoro #HACCP #Privacy #Formazione #DVR #GDPR #CorsiSicurezza #Metodo81
"""

def font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def thumb(video_id, title):
    out_dir = STATE_DIR / "thumbs"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{video_id}.jpg"
    W,H = 1280,720
    img = Image.new("RGB",(W,H),(5,5,5))
    d = ImageDraw.Draw(img)
    orange=(251,107,0); white=(255,255,255); black=(5,5,5)
    d.rectangle([0,0,W,95], fill=black)
    d.text((45,28), "SICURISSIMO81+ - METODO81+", fill=orange, font=font(34))
    d.rectangle([0,95,W,H], fill=(12,12,12))
    d.polygon([(900,95),(1280,95),(1280,720),(720,720)], fill=orange)
    clean = title.replace("- SICURISSIMO81+","").strip()
    words = clean.split()
    lines=[]; line=""
    for w in words:
        if len(line+" "+w)<25:
            line=(line+" "+w).strip()
        else:
            lines.append(line); line=w
    if line: lines.append(line)
    d.multiline_text((60,185), "\n".join(lines[:4]), fill=white, font=font(60), spacing=10)
    d.rectangle([60,610,1220,690], fill=orange)
    d.text((90,632), "Prima vedi. Poi ordini. Poi scegli. 81plus.net", fill=black, font=font(34))
    img.save(out, quality=92)
    return str(out)

def videos(y):
    ch = y.channels().list(part="contentDetails,snippet", mine=True).execute()
    print("Canale:", ch["items"][0]["snippet"]["title"])
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    out=[]; token=None
    while True:
        res = y.playlistItems().list(part="snippet", playlistId=uploads, maxResults=50, pageToken=token).execute()
        for it in res.get("items", []):
            sn=it["snippet"]
            out.append({"id": sn["resourceId"]["videoId"], "title": sn.get("title","")})
        token=res.get("nextPageToken")
        if not token: break
    return out

def update(y, v):
    vid=v["id"]
    detail=y.videos().list(part="snippet", id=vid).execute()
    if not detail.get("items"): return
    sn=detail["items"][0]["snippet"]
    new=clean_title(sn.get("title",""))
    sn["title"]=new
    sn["description"]=desc(new)
    y.videos().update(part="snippet", body={"id":vid, "snippet":sn}).execute()
    try:
        y.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb(vid,new))).execute()
        ts="thumb ok"
    except Exception:
        ts="thumb skip"
    print("Aggiornato:", vid, new, ts)

def main():
    y=yt()
    s=load_state()
    allv=videos(y)
    limit=int(os.environ.get("LIMIT","20") or "20")
    print("Video trovati:", len(allv), "Limit:", limit)
    idx=int(s.get("index",0))
    for i in range(limit):
        v=allv[(idx+i)%len(allv)]
        update(y,v)
        s.setdefault("updated",[]).append({"date":datetime.datetime.utcnow().isoformat(), "video_id":v["id"], "old_title":v["title"]})
    s["index"]=idx+limit
    save_state(s)

if __name__ == "__main__":
    main()
