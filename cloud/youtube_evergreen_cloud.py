import os, json, re, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path.cwd()
STATE_DIR = ROOT / "cloud_state"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "evergreen_state.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

def yt():
    import base64; token = json.loads(base64.b64decode(os.environ["YOUTUBE_TOKEN_B64"]).decode("utf-8-sig"))
    creds = Credentials.from_authorized_user_info(token, SCOPES)
    return build("youtube", "v3", credentials=creds)

def state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"index": 0, "updated": []}

def save(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")

def clean_title(t):
    t = re.sub(r"[🔥🚨⚠️❌✅🔴🟠]+", "", t or "").strip()
    t = t.replace("|", "-").replace("· SICURISSIMO81+", "").strip()
    t = re.sub(r"\s+", " ", t)
    if len(t) > 52:
        t = t[:52].rsplit(" ", 1)[0]
    return f"{t}: cosa controllare davvero - SICURISSIMO81+"

def description(title):
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

👉 Vai su 81plus.net e parti dal primo check:
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

def thumbnail(video_id, title):
    out_dir = STATE_DIR / "thumbs"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{video_id}.jpg"

    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (5, 5, 5))
    d = ImageDraw.Draw(img)

    orange = (251, 107, 0)
    white = (255, 255, 255)
    black = (5, 5, 5)

    d.rectangle([0, 0, W, 95], fill=black)
    d.text((45, 28), "SICURISSIMO81+ - METODO81+", fill=orange, font=font(34))
    d.rectangle([0, 95, W, H], fill=(12, 12, 12))
    d.polygon([(900, 95), (1280, 95), (1280, 720), (720, 720)], fill=orange)

    clean = title.replace("- SICURISSIMO81+", "").strip()
    words = clean.split()
    lines, line = [], ""
    for w in words:
        if len(line + " " + w) < 25:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)

    text = "\n".join(lines[:4])
    size = 68
    f = font(size)
    while True:
        box = d.multiline_textbbox((0, 0), text, font=f, spacing=10)
        if box[2] < 1080 and box[3] < 400:
            break
        size -= 4
        f = font(size)
        if size <= 38:
            break

    d.multiline_text((60, 185), text, fill=white, font=f, spacing=10)
    d.rectangle([60, 610, 1220, 690], fill=orange)
    d.text((90, 632), "Prima vedi. Poi ordini. Poi scegli. 81plus.net", fill=black, font=font(34))

    img.save(out, quality=92)
    return str(out)

def uploads_playlist(youtube):
    ch = youtube.channels().list(part="contentDetails,snippet", mine=True).execute()
    item = ch["items"][0]
    print("Canale:", item["snippet"]["title"])
    return item["contentDetails"]["relatedPlaylists"]["uploads"]

def all_videos(youtube, playlist):
    videos, token = [], None
    while True:
        res = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist,
            maxResults=50,
            pageToken=token
        ).execute()

        for it in res.get("items", []):
            sn = it["snippet"]
            videos.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": sn.get("title", "")
            })

        token = res.get("nextPageToken")
        if not token:
            break
    return videos

def update(youtube, video):
    vid = video["video_id"]
    detail = youtube.videos().list(part="snippet", id=vid).execute()
    if not detail.get("items"):
        print("Skip:", vid)
        return

    sn = detail["items"][0]["snippet"]
    old = sn.get("title", "")
    new = clean_title(old)

    sn["title"] = new
    sn["description"] = description(new)

    youtube.videos().update(
        part="snippet",
        body={"id": vid, "snippet": sn}
    ).execute()

    try:
        youtube.thumbnails().set(
            videoId=vid,
            media_body=MediaFileUpload(thumbnail(vid, new))
        ).execute()
        thumb = "thumbnail ok"
    except Exception as e:
        thumb = "thumbnail skip"

    print("Aggiornato:", vid, "-", new, "-", thumb)

def main():
    youtube = yt()
    s = state()

    playlist = uploads_playlist(youtube)
    videos = all_videos(youtube, playlist)
    print("Video trovati:", len(videos))

    if not videos:
        raise RuntimeError("Nessun video trovato.")

    idx = int(s.get("index", 0))
    video = videos[idx % len(videos)]

    update(youtube, video)

    s["index"] = idx + 1
    s.setdefault("updated", []).append({
        "date": datetime.datetime.utcnow().isoformat(),
        "video_id": video["video_id"],
        "old_title": video["title"]
    })
    save(s)

if __name__ == "__main__":
    main()

