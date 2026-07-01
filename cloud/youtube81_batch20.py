import os, json, re, datetime, base64, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

ROOT = Path.cwd()
STATE_DIR = ROOT / "cloud_state"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "youtube81_batch20_state.json"
BACKUP_FILE = STATE_DIR / "youtube81_backup_originals.jsonl"
REPORT_FILE = STATE_DIR / "youtube81_batch20_last_report.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

FORBIDDEN = [
    "zero multe",
    "rischio zero",
    "garantito",
    "100% conforme",
    "sei a posto",
    "evita ogni sanzione",
    "nessun rischio",
]

def yt():
    raw = base64.b64decode(os.environ["YOUTUBE_TOKEN_B64"]).decode("utf-8-sig")
    token = json.loads(raw)
    creds = Credentials.from_authorized_user_info(token, SCOPES)
    return build("youtube", "v3", credentials=creds)

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def guard(text):
    out = text or ""
    for bad in FORBIDDEN:
        out = out.replace(bad, "controllo operativo")
        out = out.replace(bad.upper(), "CONTROLLO OPERATIVO")
    return out

def clean_title(t):
    t = re.sub(r"[ðŸ”¥ðŸš¨âš ï¸âŒâœ…ðŸ”´ðŸŸ ]+", "", t or "").strip()
    t = t.replace("|", "-")
    t = t.replace("Â· SICURISSIMO81+", "")
    t = t.replace("- SICURISSIMO81+", "")
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        t = "Sicurezza sul lavoro"
    if len(t) > 52:
        t = t[:52].rsplit(" ", 1)[0]
    return guard(f"{t}: cosa controllare davvero - SICURISSIMO81+")

def description(title):
    return guard(f"""ðŸŸ  {title}

Il punto non Ã¨ avere un documento, un corso o una scadenza scritta da qualche parte.
Il punto Ã¨ sapere cosa controllare, cosa manca e quale primo passo fare.

Con 81+ parti da una logica semplice:
Prima vedi.
Poi ordini.
Poi scegli.

âœ… Sicurezza sul lavoro
âœ… HACCP e igiene alimentare
âœ… Privacy e GDPR
âœ… Corsi e formazione
âœ… Documenti, scadenze e audit

ðŸ‘‰ Vai su 81plus.net e parti dal primo check:
https://81plus.net

Canale Telegram:
https://t.me/sicurissimi

#81plus #Sicurissimo81 #SicurezzaSulLavoro #HACCP #Privacy #Formazione #DVR #GDPR #CorsiSicurezza #Metodo81
""")

def font(size):
    for f in ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()

def thumbnail(video_id, title, n=0):
    out_dir = STATE_DIR / "thumbs"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{video_id}.jpg"

    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (5, 5, 5))
    d = ImageDraw.Draw(img)

    orange = (251, 107, 0)
    white = (255, 255, 255)
    black = (5, 5, 5)
    dark = (12, 12, 12)

    d.rectangle([0, 0, W, 95], fill=black)
    d.text((45, 28), "SICURISSIMO81+ - METODO81+", fill=orange, font=font(34))
    d.rectangle([0, 95, W, H], fill=dark)

    # Variation by batch position
    if n % 3 == 0:
        d.polygon([(900, 95), (1280, 95), (1280, 720), (720, 720)], fill=orange)
    elif n % 3 == 1:
        d.rectangle([970, 95, 1280, 720], fill=orange)
        d.rectangle([0, 610, 1280, 720], fill=orange)
    else:
        d.ellipse([850, 80, 1420, 650], fill=orange)

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
    size = 66
    f = font(size)
    while True:
        box = d.multiline_textbbox((0, 0), text, font=f, spacing=10)
        if box[2] < 1080 and box[3] < 395:
            break
        size -= 4
        f = font(size)
        if size <= 38:
            break

    d.multiline_text((60, 180), text, fill=white, font=f, spacing=10)

    d.rectangle([60, 610, 1220, 690], fill=orange)
    d.text((90, 632), "Prima vedi. Poi ordini. Poi scegli. 81plus.net", fill=black, font=font(34))

    img.save(out, quality=92)
    return str(out)

def uploads_playlist(youtube):
    ch = youtube.channels().list(part="contentDetails,snippet", mine=True).execute()
    if not ch.get("items"):
        raise RuntimeError("Nessun canale trovato con questo token.")
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
            title = sn.get("title", "")
            if title.lower() == "private video" or title.lower() == "deleted video":
                continue
            videos.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": title
            })
        token = res.get("nextPageToken")
        if not token:
            break
    return videos

def backup_original(video_id, snippet):
    record = {
        "date": datetime.datetime.utcnow().isoformat(),
        "video_id": video_id,
        "snippet": snippet,
    }
    with BACKUP_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def update(youtube, video, position=0):
    vid = video["video_id"]
    detail = youtube.videos().list(part="snippet", id=vid).execute()
    if not detail.get("items"):
        return {"video_id": vid, "status": "skip", "note": "not found"}

    sn = detail["items"][0]["snippet"]
    old = sn.get("title", "")
    new = clean_title(old)

    backup_original(vid, sn.copy())

    sn["title"] = new
    sn["description"] = description(new)

    youtube.videos().update(part="snippet", body={"id": vid, "snippet": sn}).execute()

    thumb_status = "not attempted"
    try:
        youtube.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumbnail(vid, new, position))).execute()
        thumb_status = "thumbnail ok"
    except Exception as e:
        thumb_status = "thumbnail skip: " + str(e)[:140]

    return {"video_id": vid, "old_title": old, "new_title": new, "status": "OK", "thumbnail": thumb_status}

def get_limit():
    val = os.environ.get("YOUTUBE81_LIMIT") or "20"
    try:
        return max(1, min(50, int(val)))
    except Exception:
        return 20

def main():
    youtube = yt()
    s = load_json(STATE_FILE, {"index": 0, "updated": []})

    playlist = uploads_playlist(youtube)
    videos = all_videos(youtube, playlist)
    print("Video trovati:", len(videos))

    if not videos:
        raise RuntimeError("Nessun video trovato.")

    limit = get_limit()
    print("Video da aggiornare:", limit)

    idx = int(s.get("index", 0))
    results = []

    for i in range(limit):
        video = videos[(idx + i) % len(videos)]
        print(f"[{i+1}/{limit}] {video['video_id']} - {video['title'][:80]}")
        try:
            res = update(youtube, video, i)
            print(" ->", res.get("status"), res.get("new_title", ""), res.get("thumbnail", ""))
            results.append(res)
        except HttpError as e:
            msg = str(e)[:300]
            print("HTTP ERROR:", msg)
            results.append({"video_id": video.get("video_id"), "status": "ERROR", "note": msg})
            # avoid hammering API if quota/permission issue
            if "quota" in msg.lower() or "forbidden" in msg.lower():
                break
        except Exception as e:
            msg = str(e)[:300]
            print("ERROR:", msg)
            results.append({"video_id": video.get("video_id"), "status": "ERROR", "note": msg})
        time.sleep(1)

    ok = [r for r in results if r.get("status") == "OK"]
    s["index"] = idx + len(ok)
    s.setdefault("updated", []).extend([{
        "date": datetime.datetime.utcnow().isoformat(),
        "video_id": r.get("video_id"),
        "new_title": r.get("new_title"),
        "thumbnail": r.get("thumbnail")
    } for r in ok])
    s["last_run"] = datetime.datetime.utcnow().isoformat()
    save_json(STATE_FILE, s)

    report = {
        "date": datetime.datetime.utcnow().isoformat(),
        "requested": limit,
        "ok": len(ok),
        "results": results
    }
    save_json(REPORT_FILE, report)

    if len(ok) == 0:
        raise RuntimeError("Nessun video aggiornato. Controllare report/log.")

if __name__ == "__main__":
    main()
