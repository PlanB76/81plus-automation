# -*- coding: utf-8 -*-
"""
sync_shorts81.py (cloud) — importa gli Shorts SICURIX dal canale YouTube @sicurissimo
e scrive tales_videos.json nella ROOT del repo (per deploy/FTP sul sito).
- ricava il canale dal video "seme" (oEmbed -> author_url -> channelId)
- legge il feed RSS del canale (ultimi ~15 upload)
- tiene solo i titoli che contengono "SICURIX"
- unisce ai pinned, deduplica, scrive tales_videos.json
Nessuna dipendenza esterna (solo urllib). Se la rete fallisce, non tocca il file esistente.
"""
import os, re, json, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.abspath(os.path.join(HERE, "..", "tales_videos.json"))  # root del repo

PINNED = ["8Zu6VMtfqbo", "y27HTmXr8vk", "xlfMmYrUZ-o", "Gx5KZPNw8vU"]
KEYWORD = "sicurix"
UA = {"User-Agent": "Mozilla/5.0 (81PLUS sync)"}

def log(m): print("[sync-shorts] " + m)

def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def channel_id_from_seed(vid):
    try:
        j = json.loads(get("https://www.youtube.com/oembed?format=json&url=" +
                            urllib.parse.quote("https://www.youtube.com/watch?v=" + vid, safe="")))
        au = j.get("author_url", "")
    except Exception as e:
        log("oEmbed fallita: %s" % e); return None
    m = re.search(r"/channel/(UC[0-9A-Za-z_-]{20,})", au)
    if m: return m.group(1)
    try:
        html = get(au)
        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{20,})"', html) or \
            re.search(r'"externalId":"(UC[0-9A-Za-z_-]{20,})"', html)
        if m: return m.group(1)
    except Exception as e:
        log("pagina canale non letta: %s" % e)
    return None

def feed_entries(cid):
    xml = get("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid)
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        vid = re.search(r"<yt:videoId>(.*?)</yt:videoId>", entry)
        tit = re.search(r"<title>(.*?)</title>", entry)
        if vid:
            out.append((vid.group(1), (tit.group(1) if tit else "").strip()))
    return out

def main():
    videos = []; seen = set()
    cid = channel_id_from_seed(PINNED[0]) if PINNED else None
    if cid:
        log("canale: " + cid)
        try:
            for vid, title in feed_entries(cid):
                if KEYWORD in title.lower() and vid not in seen:
                    videos.append((vid, title)); seen.add(vid)
            log("shorts SICURIX dal feed: %d" % len(videos))
        except Exception as e:
            log("feed non letto: %s" % e)
    else:
        log("canale non individuato: uso solo i pinned.")
    titles = {"8Zu6VMtfqbo": "SICURIX Short", "y27HTmXr8vk": "SICURIX Short",
              "xlfMmYrUZ-o": "SICURIX Short", "Gx5KZPNw8vU": "SICURIX GENESYS"}
    for vid in PINNED:
        if vid not in seen:
            videos.append((vid, titles.get(vid, "SICURIX Short"))); seen.add(vid)
    if not videos:
        log("nessun video: file invariato."); return
    data = {
        "_nota": "Shorts SICURIX. Aggiornato in automatico da sync_shorts81.py (solo titoli con 'SICURIX').",
        "drive_folder": "1hICKXdl9JTZBL1pemG19oE_661z-EH_k",
        "videos": [{"title": t or "SICURIX Short", "yt": v, "short": True} for v, t in videos]
    }
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log("scritti %d shorts SICURIX in %s" % (len(videos), OUT))

if __name__ == "__main__":
    main()
