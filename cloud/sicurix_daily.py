# -*- coding: utf-8 -*-
"""SICURIX DAILY — 3 video/giorno dal PROGRAMMA 365 (Sicurezza+HACCP+Privacy), ciclico su giorno-dell'anno.
Ad ogni post allega una VIGNETTA SICURIX TALES (rotazione, tema-matched) dalla cartella TALES IMG (indicizzata in tales_manifest.json).
Scrive OGGI_SICURIX.md e notifica Telegram (sendPhoto se la vignetta ha un drive_url, altrimenti testo)."""
import json,os,datetime,urllib.request,urllib.parse,pathlib
HERE=pathlib.Path(__file__).resolve().parent; DATA=HERE/"data"
PROG=json.load(open(DATA/"sicurix_program365.json",encoding="utf-8"))
TALES=json.load(open(DATA/"tales_manifest.json",encoding="utf-8")) if (DATA/"tales_manifest.json").exists() else []
def vignetta(theme,i):
    pool=[m for m in TALES if m.get("theme")==theme] or TALES
    return pool[i%len(pool)] if pool else None
doy=int(os.environ.get("FORCE_DAY") or datetime.date.today().timetuple().tm_yday); day=((doy-1)%365)+1
items=[dict(r) for r in PROG if r["day"]==day]
for i,r in enumerate(items):
    v=vignetta(r["theme"],day+i)
    r["vignetta"]=v["file"] if v else ""; r["vignetta_url"]=(v.get("drive_url") if v else "")
out=HERE.parent/"OGGI_SICURIX.md"
L=[f"# 🎬 SICURIX — 3 VIDEO DI OGGI (giorno {day}/365) · Sicurezza + HACCP + Privacy",""]
for r in items:
    L+=[f"\n## {r['slot']} · {r['theme']} — {r['prodotto']}",
        f"**Titolo:** {r['titolo']}",
        f"**CTA (prodotto=tema):** {r['cta_label']} → {r['cta_url']}",
        f"**Cast:** SICURIX + {r['hero']} vs {r['villain']}",
        f"**Vignetta TALES da allegare:** {r.get('vignetta','')}  {r.get('vignetta_url','')}",
        f"**Descrizione (PNL/AIDA/EPPPA):**\n{r['descrizione']}",
        f"**>>> PROMPT GEMINI 9:16:**\n{r['gemini_prompt']}","---"]
out.write_text("\n".join(L),encoding="utf-8"); print(f"OGGI_SICURIX giorno {day}: {len(items)} video (+vignette)")
tok=os.environ.get("TELEGRAM_BOT_TOKEN"); ch=os.environ.get("TG_CHANNEL")
first_url=next((r.get("vignetta_url") for r in items if r.get("vignetta_url")),"")
if tok and ch and items:
    msg="🎬 SICURIX oggi (g.%d/365) — 3 video:\n"%day+"\n".join(f"• [{r['theme']}] {r['titolo']}" for r in items)
    ep=("sendPhoto",{"chat_id":ch,"photo":first_url,"caption":msg}) if first_url else ("sendMessage",{"chat_id":ch,"text":msg})
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/{ep[0]}",data=urllib.parse.urlencode(ep[1]).encode(),timeout=20); print("TG ok",ep[0])
    except Exception as e: print("TG skip:",e)
