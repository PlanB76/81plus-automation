# -*- coding: utf-8 -*-
"""SICURIX TELEGRAM - pubblica post completi (fumetto WEBP + titolo clickbait + corpo PNL + CTA prodotto + hashtag).
Legge lo sheet del giorno (cloud/out/SICURIX_GEN_<data>.csv), sceglie N righe IMG_OK non ancora postate, e invia su Telegram.
Token SOLO da env: TELEGRAM_BOT_TOKEN + TG_CHANNEL (chat id o @canale). Anti-doppione via stato.
USO: TELEGRAM_BOT_TOKEN=... TG_CHANNEL=@canale python sicurix_telegram.py [N]"""
import os,sys,csv,json,glob,pathlib,urllib.request,urllib.parse
HERE=pathlib.Path(__file__).resolve().parent
OUTD=HERE/"out"; IMG=OUTD/"img"; DATA=HERE/"data"
STATE=DATA/"sicurix_tg_state.json"
TOKEN=((os.environ.get("SICURIX_TG_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_PUBLISHER_TOKEN") or "").strip()); CHAT=((os.environ.get("SICURIX_TG_CHANNEL") or os.environ.get("TG_CHANNEL") or "").strip())
API=f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None
def latest_csv():
    fs=sorted(x for x in glob.glob(str(OUTD/"SICURIX_GEN_*.csv")) if "MANIFEST" not in x); return fs[-1] if fs else None
def load_state():
    if STATE.exists():
        try: return set(json.load(open(STATE,encoding="utf-8")))
        except: return set()
    return set()
def save_state(s): json.dump(sorted(s),open(STATE,"w",encoding="utf-8"))
def caption(r):
    cap=f"\U0001F7E7 {r['titolo_clickbait']}\n\n{r['corpo_post']}\n\n{r['hashtag']}"
    return cap[:1020]
def send_photo(img_path,cap):
    import mimetypes,uuid
    b=b""; boundary="----sicurix"+uuid.uuid4().hex
    def part(name,val): return (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{val}\r\n").encode()
    b+=part("chat_id",CHAT)+part("caption",cap)
    data=open(img_path,"rb").read()
    b+=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{pathlib.Path(img_path).name}\"\r\nContent-Type: image/webp\r\n\r\n").encode()
    b+=data+b"\r\n"+f"--{boundary}--\r\n".encode()
    req=urllib.request.Request(f"{API}/sendPhoto",data=b,headers={"Content-Type":f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode()).get("ok")
def send_text(cap):
    data=urllib.parse.urlencode({"chat_id":CHAT,"text":cap,"disable_web_page_preview":"false"}).encode()
    with urllib.request.urlopen(f"{API}/sendMessage",data=data,timeout=40) as r: return json.loads(r.read().decode()).get("ok")
def main():
    n=int(sys.argv[1]) if len(sys.argv)>1 else 5
    if not TOKEN or not CHAT:
        print("TELEGRAM_BOT_TOKEN/TG_CHANNEL assenti: salto (mettili come secret)."); return
    csvp=latest_csv()
    if not csvp: print("Nessuno sheet."); return
    rows=list(csv.DictReader(open(csvp,encoding="utf-8"))); done=load_state(); sent=0
    # posta SOLO righe con immagine pronta (IMG_OK + webp esistente), non ancora inviate
    ready=[r for r in rows if r.get("stato")=="IMG_OK" and (IMG/r["nome_file_webp"]).exists() and r["nome_file_webp"] not in done]
    for r in ready:
        if sent>=n: break
        sig=r["nome_file_webp"]; img=IMG/sig; cap=caption(r); ok=False
        try: ok=send_photo(str(img),cap)
        except Exception as e: print("  err",sig,e)
        if ok: done.add(sig); sent+=1; print("  [tg] photo",r["codice_ateco"],r["settore"])
    save_state(done); print(f"Inviati {sent} post SICURIX (con fumetto) su Telegram. Righe pronte: {len(ready)}")
if __name__=="__main__": main()
