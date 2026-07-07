# -*- coding: utf-8 -*-
"""SICURIX VIDEO FACTORY (cloud, H24) — trasforma il brief (immagini + script) in uno SHORT 9:16 vero.
Voce italiana AI GRATIS via Hugging Face (Space TTS, es. Kokoro) + montaggio ffmpeg.
Per ogni riga IMG_OK dello sheet del giorno crea: voce + slideshow Ken-Burns delle immagini + titolo + CTA finale.
VIDEO = PRODOTTO: usa titolo_clickbait, corpo_post (SEO/PNL) e la CTA prodotto listino81+ gia' presenti nello sheet.
Output: cloud/out/videos/<nome>.mp4 (+ .txt con titolo/descrizione/hashtag per l'upload). Stato anti-doppione.
USO: HF_TOKEN=hf_xxx python sicurix_video.py [N]
Poi gli step successivi del workflow: upload YouTube (@sicurissimo) + Telegram + salvataggio Drive (rclone)."""
import os, sys, csv, json, glob, subprocess, pathlib, shutil, tempfile, textwrap

HERE = pathlib.Path(__file__).resolve().parent
OUTD = HERE/"out"; IMG = OUTD/"img"; VID = OUTD/"videos"; VID.mkdir(parents=True, exist_ok=True)
STATE = HERE/"data"/"sicurix_video_state.json"
TOKEN = (os.environ.get("HF_TOKEN") or "").strip() or None
TTS_SPACE = os.environ.get("TTS_SPACE", "hexgrad/Kokoro-TTS")
TTS_VOICE = os.environ.get("TTS_VOICE", "if_sara")  # voce italiana femminile Kokoro (fallback gestito)
N = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1].isdigit()) else int(os.environ.get("VIDEO_N", "3"))
W, H = 1080, 1920  # 9:16

def latest_csv():
    fs = sorted(x for x in glob.glob(str(OUTD/"SICURIX_GEN_*.csv")) if "MANIFEST" not in x)
    return fs[-1] if fs else None
def load_state():
    if STATE.exists():
        try: return set(json.load(open(STATE, encoding="utf-8")))
        except: return set()
    return set()
def save_state(s):
    STATE.parent.mkdir(parents=True, exist_ok=True); json.dump(sorted(s), open(STATE, "w", encoding="utf-8"))

def have_ffmpeg():
    return shutil.which("ffmpeg") is not None

def tts(text, out_wav):
    """Voce italiana gratis via HF Space. Se fallisce, ritorna None (video muto con musica/silenzio)."""
    try:
        from gradio_client import Client
        c = Client(TTS_SPACE, hf_token=TOKEN)
        # Kokoro-TTS: predict(text, voice, speed) -> audio filepath (varia per Space: si tenta piu' firme)
        for kw in (dict(text=text[:900], voice=TTS_VOICE, speed=1.0),
                   dict(text=text[:900], voice=TTS_VOICE),
                   dict(text=text[:900])):
            try:
                r = c.predict(**kw, api_name="/generate")
                p = r[0] if isinstance(r, (list, tuple)) else r
                if isinstance(p, str) and os.path.exists(p):
                    shutil.copy(p, out_wav); return out_wav
            except Exception:
                continue
    except Exception as e:
        print("   TTS non disponibile:", e)
    return None

def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")

def build_short(row, tmp):
    name = pathlib.Path(row.get("nome_file_webp", "video")).stem
    title = row.get("titolo_clickbait", "SICURIX")
    body = row.get("corpo_post", "")
    cta = f"{row.get('cta_prodotto','')} - 81plus.net"
    # immagini: la webp della riga + eventuali altre recenti come b-roll
    imgs = []
    main = IMG/row.get("nome_file_webp", "")
    if main.exists(): imgs.append(str(main))
    for extra in sorted(glob.glob(str(IMG/"*.webp")))[:6]:
        if extra not in imgs: imgs.append(extra)
        if len(imgs) >= 4: break
    if not imgs:
        return None
    # voce
    wav = tts(f"{title}. {body}", str(tmp/"voice.wav"))
    dur = 24.0
    if wav:
        try:
            dur = float(subprocess.check_output(["ffprobe","-i",wav,"-show_entries","format=duration","-v","quiet","-of","csv=p=0"]).decode().strip())
            dur = max(8.0, min(58.0, dur+0.6))
        except Exception: pass
    per = max(2.5, dur/len(imgs))
    # clip per immagine: cover 9:16 + leggero zoom (Ken Burns)
    clips = []
    for i, im in enumerate(imgs):
        c = tmp/f"c{i}.mp4"
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"zoompan=z='min(zoom+0.0009,1.12)':d={int(per*25)}:s={W}x{H}:fps=25,"
              f"drawtext=text='{esc(title)[:60]}':fontcolor=white:fontsize=54:box=1:boxcolor=0x05050A@0.72:boxborderw=18:x=(w-tw)/2:y=140:enable='lte(t,3)'")
        subprocess.run(["ffmpeg","-y","-loop","1","-t",f"{per:.2f}","-i",im,"-vf",vf,"-r","25","-pix_fmt","yuv420p",str(c)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        clips.append(c)
    # CTA end card
    cta_c = tmp/"cta.mp4"
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"color=c=0x05050A:s={W}x{H}:d=2.5",
        "-vf",(f"drawtext=text='Prima vedi. Poi sistemi.':fontcolor=0xFF6A1A:fontsize=64:x=(w-tw)/2:y=h/2-120,"
               f"drawtext=text='{esc(cta)[:48]}':fontcolor=white:fontsize=44:x=(w-tw)/2:y=h/2+10,"
               f"drawtext=text='81plus.net':fontcolor=0xFF6A1A:fontsize=52:x=(w-tw)/2:y=h/2+120"),
        "-r","25","-pix_fmt","yuv420p",str(cta_c)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    clips.append(cta_c)
    # concat
    lst = tmp/"list.txt"; lst.write_text("".join(f"file '{c}'\n" for c in clips))
    silent = tmp/"silent.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(silent)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    out = VID/f"{name}.mp4"
    if wav:
        subprocess.run(["ffmpeg","-y","-i",str(silent),"-i",wav,"-c:v","copy","-c:a","aac","-shortest",str(out)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    else:
        shutil.copy(silent, out)
    # metadati per l'upload (titolo + descrizione SEO + hashtag)
    meta = VID/f"{name}.txt"
    meta.write_text(f"TITLE: {title}\n\nDESCRIPTION:\n{body}\n\nHASHTAG: {row.get('hashtag','')}\nCTA: {row.get('cta_url','')}\n", encoding="utf-8")
    return out

def main():
    if not have_ffmpeg():
        print("ffmpeg assente: nel workflow viene installato. In locale: apt/choco install ffmpeg."); return
    csvp = latest_csv()
    if not csvp:
        print("Nessuno sheet: lancia prima sicurix_gen_daily.py / program365."); return
    rows = list(csv.DictReader(open(csvp, encoding="utf-8")))
    done = load_state()
    todo = [r for r in rows if r.get("stato") == "IMG_OK" and pathlib.Path(r.get("nome_file_webp","")).stem not in done][:N]
    print(f"VIDEO factory: {len(todo)} short da fare (da {pathlib.Path(csvp).name}). TTS={TTS_SPACE}")
    ok = 0
    for i, r in enumerate(todo, 1):
        nm = pathlib.Path(r.get("nome_file_webp","v")).stem
        try:
            with tempfile.TemporaryDirectory() as td:
                out = build_short(r, pathlib.Path(td))
            if out and out.exists():
                done.add(nm); ok += 1; print(f"  [{i}/{len(todo)}] {out.name} ({out.stat().st_size//1024} KB)"); save_state(done)
            else:
                print(f"  [{i}/{len(todo)}] SALTATO {nm} (immagini mancanti)")
        except Exception as e:
            print(f"  [{i}/{len(todo)}] ERRORE {nm}: {e}")
    save_state(done)
    print(f"FATTO: {ok} short in {VID}. Ora upload YouTube @sicurissimo + Telegram + Drive (step successivi del workflow).")

if __name__ == "__main__":
    main()
