# -*- coding: utf-8 -*-
"""
YOUTUBE STUDIO 81+ · shorts_pub81
Pubblica i NUOVI short trovati nella cartella Drive del canale, con metadata
virali (titolo clickbait, descrizione magnetica AIDA/PNL, hashtag, tag SEO, CTA)
generati con AI (GROQ) secondo principi stile VidIQ.
- Drive: cartelle PUBBLICHE ("chiunque con il link") + chiave API Drive (GDRIVE_API_KEY)
- YouTube: token upload per canale (secret)
Traccia i file gia' pubblicati in state_pub.json (per file-id Drive).
Dipendenze: google-api-python-client google-auth (installate dal workflow).
"""
import os, json, re, urllib.request, urllib.parse, tempfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG  = json.load(open(os.path.join(HERE, "youtube_studio81.json"), encoding="utf-8"))
STATE_P = os.path.join(HERE, "state_pub.json")
def load_state():
    try: return json.load(open(STATE_P, encoding="utf-8"))
    except Exception: return {"published": []}
def save_state(s): json.dump(s, open(STATE_P,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
def log(m): print("[shorts-pub] " + m)

VID_EXT = (".mp4",".mov",".m4v",".webm",".mkv")

def drive_list(folder_id, api_key):
    q = urllib.parse.quote("'%s' in parents and trashed=false" % folder_id)
    url = ("https://www.googleapis.com/drive/v3/files?q=%s&key=%s"
           "&fields=files(id,name,mimeType,modifiedTime)&pageSize=100&orderBy=modifiedTime desc"
           "&supportsAllDrives=true&includeItemsFromAllDrives=true") % (q, api_key)
    with urllib.request.urlopen(url, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    out=[]
    for f in data.get("files", []):
        n=f.get("name","").lower()
        if ("video" in f.get("mimeType","")) or n.endswith(VID_EXT): out.append(f)
    return out

def drive_download(file_id, api_key, dest):
    url = "https://www.googleapis.com/drive/v3/files/%s?alt=media&key=%s&supportsAllDrives=true" % (file_id, api_key)
    urllib.request.urlretrieve(url, dest)
    return dest

def groq_meta(voce, tema, cta, hashtag, nome_file):
    key = os.environ.get("GROQ_API_KEY","").strip()
    base_tags = [tema.split(",")[0].strip(), "shorts", "81plus"]
    if not key:
        t = re.sub(r"[_\-\.]+"," ", os.path.splitext(nome_file)[0]).strip().title()[:60]
        return {"title": t or "SICURIX Short", "description": cta+"\n\n"+" ".join(hashtag), "tags": base_tags+hashtag}
    sys = ("Sei un esperto YouTube SEO stile VidIQ. Voce del canale: " + voce + ". Tema: " + tema + ". "
           "Genera per uno SHORT verticale un JSON con: 'title' (clickbait virale, curiosita, MAX 60 caratteri, "
           "parola chiave in testa), 'description' (magnetica: hook nella prima riga, AIDA, tocchi di PNL/neuromarketing, "
           "3 righe iniziali con keyword e la CTA, poi 3-5 hashtag; italiano, frasi brevi, zero inventiva su norme o prezzi), "
           "'tags' (lista di 10-15 keyword SEO in italiano). Chiudi la description con la CTA: " + cta + ". "
           "Rispondi SOLO con JSON valido.")
    body = json.dumps({"model":"llama-3.3-70b-versatile",
        "messages":[{"role":"system","content":sys},{"role":"user","content":"File short: "+nome_file}],
        "temperature":0.8, "response_format":{"type":"json_object"}}).encode("utf-8")
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            j = json.loads(json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"])
        j.setdefault("title","SICURIX Short"); j["title"]=j["title"][:95]
        j.setdefault("description", cta); j.setdefault("tags", base_tags)
        if not any(h in j["description"] for h in hashtag): j["description"] += "\n\n"+" ".join(hashtag)
        return j
    except Exception as e:
        log("meta AI ko: %s" % e)
        t = re.sub(r"[_\-\.]+"," ", os.path.splitext(nome_file)[0]).strip().title()[:60]
        return {"title": t or "SICURIX Short", "description": cta+"\n\n"+" ".join(hashtag), "tags": base_tags+hashtag}

def tg_post(c, meta, vid):
    tok = os.environ.get(c.get("tg_token_secret",""),"").strip()
    ch  = os.environ.get(c.get("tg_channel_secret",""),"").strip()
    if not tok or not ch: return
    prima_riga = (meta.get("description","").split("\n")[0])[:200]
    text = ("\U0001F3AC " + meta["title"] + "\n\n" + prima_riga +
            "\n\n\U0001F449 Guarda ora: https://youtu.be/" + vid + "\n" + c["cta"])
    try:
        body = urllib.parse.urlencode({"chat_id":ch,"text":text,"disable_web_page_preview":"false"}).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % tok, data=body), timeout=20)
        log("+ Telegram: postato su " + ch)
    except Exception as e:
        log("tg ko: %s" % e)

def yt_upload(token_json, video_path, meta, categoryId):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(data, scopes=data.get("scopes") or ["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube","v3",credentials=creds,cache_discovery=False)
    body = {"snippet":{"title":meta["title"],"description":meta["description"],
            "tags":meta.get("tags",[])[:20],"categoryId":categoryId},
            "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}}
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp=None
    while resp is None:
        status, resp = req.next_chunk()
    return resp["id"]

def _creds(token_json):
    from google.oauth2.credentials import Credentials
    data = json.loads(token_json)
    return Credentials.from_authorized_user_info(data, scopes=data.get("scopes"))

def drive_list_oauth(token_json, folder_id):
    from googleapiclient.discovery import build
    drv = build("drive","v3",credentials=_creds(token_json),cache_discovery=False)
    out=[]; page=None
    while True:
        resp = drv.files().list(q="'%s' in parents and trashed=false" % folder_id,
            fields="nextPageToken, files(id,name,mimeType,modifiedTime)",
            pageSize=100, orderBy="modifiedTime desc",
            includeItemsFromAllDrives=True, supportsAllDrives=True, pageToken=page).execute()
        for f in resp.get("files", []):
            n=f.get("name","").lower()
            if ("video" in f.get("mimeType","")) or n.endswith(VID_EXT): out.append(f)
        page = resp.get("nextPageToken")
        if not page: break
    return out

def drive_download_oauth(token_json, file_id, dest):
    import io
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    drv = build("drive","v3",credentials=_creds(token_json),cache_discovery=False)
    req = drv.files().get_media(fileId=file_id, supportsAllDrives=True)
    with open(dest,"wb") as fh:
        dl = MediaIoBaseDownload(fh, req); done=False
        while not done: _, done = dl.next_chunk()
    return dest

def run_channel(c, st):
    tok = os.environ.get(c["upload_secret"],"").strip()
    if not tok: log("SALTO %s: manca %s (token)." % (c["handle"], c["upload_secret"])); return
    api_key = os.environ.get(CFG.get("gdrive_api_key_secret",""),"").strip() or os.environ.get("YOUTUBE_API_KEY","").strip()
    # Preferisci Drive via OAuth (token con scope drive.readonly). Fallback: API key.
    modo="oauth"
    try:
        files = drive_list_oauth(tok, c["drive_folder_id"])
    except Exception as e:
        log("Drive OAuth ko per %s (%s). Provo API key." % (c["handle"], e))
        if not api_key: log("SALTO %s: Drive non accessibile (né OAuth né API key)." % c["handle"]); return
        try: files = drive_list(c["drive_folder_id"], api_key); modo="apikey"
        except Exception as e2: log("Drive list ko per %s: %s" % (c["handle"], e2)); return
    nuovi = [f for f in files if f["id"] not in st["published"]]
    log("%s: %d video nel Drive (%s), %d nuovi." % (c["handle"], len(files), modo, len(nuovi)))
    done=0
    for f in nuovi[:CFG.get("max_short_per_giro",3)]:
        try:
            tmp = os.path.join(tempfile.gettempdir(), f["id"]+"_"+re.sub(r"[^\w\.\-]","_",f["name"]))
            log("scarico: "+f["name"])
            if modo=="oauth": drive_download_oauth(tok, f["id"], tmp)
            else: drive_download(f["id"], api_key, tmp)
            meta = groq_meta(c["voce"], c["tema"], c["cta"], c["hashtag"], f["name"])
            vid = yt_upload(tok, tmp, meta, c["categoryId"])
            st["published"].append(f["id"]); done+=1
            log("PUBBLICATO %s -> https://youtu.be/%s | %s" % (c["handle"], vid, meta["title"]))
            tg_post(c, meta, vid)
            try: os.remove(tmp)
            except Exception: pass
        except Exception as e:
            log("upload ko (%s): %s" % (f.get("name"), e))
    st["published"]=st["published"][-2000:]
    log("%s: pubblicati %d short." % (c["handle"], done))

def main():
    st=load_state()
    for c in CFG["canali"]:
        try: run_channel(c, st)
        except Exception as e: log("errore canale %s: %s" % (c.get("handle"), e))
    save_state(st)
    log("Giro short completato "+datetime.datetime.utcnow().isoformat()+"Z")

if __name__ == "__main__":
    main()
