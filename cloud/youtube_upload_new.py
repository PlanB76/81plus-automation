# -*- coding: utf-8 -*-
"""YOUTUBE UPLOAD NEW — carica i nuovi Short SICURIX (cloud/out/videos/*.mp4) sul canale @sicurissimo.
Riusa il token OAuth gia' presente (secret YOUTUBE_TOKEN_B64, base64 del token.json). Anti-doppione via stato.
Titolo/descrizione/hashtag presi dal .txt gemello prodotto da sicurix_video.py.
USO: YOUTUBE_TOKEN_B64=... python youtube_upload_new.py [N]"""
import os, sys, json, glob, base64, pathlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
VID = HERE/"out"/"videos"
STATE = HERE/"data"/"youtube_upload_state.json"
N = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1].isdigit()) else int(os.environ.get("YT_N", "3"))
PRIVACY = os.environ.get("YT_PRIVACY", "public")

def load_state():
    if STATE.exists():
        try: return set(json.load(open(STATE, encoding="utf-8")))
        except: return set()
    return set()
def save_state(s):
    STATE.parent.mkdir(parents=True, exist_ok=True); json.dump(sorted(s), open(STATE, "w", encoding="utf-8"))

def creds():
    b64 = (os.environ.get("YOUTUBE_TOKEN_B64") or "").strip()
    if not b64: raise SystemExit("YOUTUBE_TOKEN_B64 assente: aggiungilo come secret (base64 del token OAuth YouTube).")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    info = json.loads(base64.b64decode(b64).decode("utf-8"))
    c = Credentials.from_authorized_user_info(info, ["https://www.googleapis.com/auth/youtube.upload"])
    if c and c.expired and c.refresh_token:
        c.refresh(Request())
    return c

def meta_for(mp4):
    txt = mp4.with_suffix(".txt")
    title = mp4.stem; desc = ""; tags = []
    if txt.exists():
        t = txt.read_text(encoding="utf-8")
        for line in t.splitlines():
            if line.startswith("TITLE:"): title = line[6:].strip()[:98]
        if "DESCRIPTION:" in t:
            desc = t.split("DESCRIPTION:", 1)[1].split("HASHTAG:", 1)[0].strip()
        if "HASHTAG:" in t:
            tags = [w.lstrip("#") for w in t.split("HASHTAG:", 1)[1].split("\n", 1)[0].split() if w.strip()][:15]
    full_desc = (desc + "\n\n" + " ".join("#"+x for x in tags) + "\n\nChiedilo a Sicurix - 81plus.net").strip()
    return title, full_desc[:4900], tags

def main():
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    vids = sorted(glob.glob(str(VID/"*.mp4")))
    done = load_state()
    todo = [v for v in vids if pathlib.Path(v).stem not in done][:N]
    if not todo:
        print("Nessun nuovo mp4 da caricare."); return
    yt = build("youtube", "v3", credentials=creds())
    ok = 0
    for i, v in enumerate(todo, 1):
        mp4 = Path(v); title, desc, tags = meta_for(mp4)
        body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "27"},
                "status": {"privacyStatus": PRIVACY, "selfDeclaredMadeForKids": False}}
        try:
            req = yt.videos().insert(part="snippet,status", body=body,
                                     media_body=MediaFileUpload(str(mp4), chunksize=-1, resumable=True))
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
            vidid = resp.get("id")
            done.add(mp4.stem); ok += 1; save_state(done)
            print(f"  [{i}/{len(todo)}] caricato {mp4.name} -> https://youtu.be/{vidid}")
        except Exception as e:
            print(f"  [{i}/{len(todo)}] ERRORE {mp4.name}: {e}")
    save_state(done)
    print(f"FATTO: {ok}/{len(todo)} caricati su @sicurissimo.")

if __name__ == "__main__":
    main()
