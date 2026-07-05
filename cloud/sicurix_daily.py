# -*- coding: utf-8 -*-
"""SICURIX DAILY — emette i 3 video di OGGI dal PROGRAMMA 365 (Sicurezza+HACCP+Privacy), ciclico su giorno-dell'anno.
Scrive OGGI_SICURIX.md (titolo+descrizione PNL+CTA+hashtag+PROMPT GEMINI per ogni video) e notifica Telegram."""
import json,os,datetime,urllib.request,urllib.parse,pathlib
HERE=pathlib.Path(__file__).resolve().parent; DATA=HERE/"data"
PROG=json.load(open(DATA/"sicurix_program365.json",encoding="utf-8"))
doy=int(os.environ.get("FORCE_DAY") or datetime.date.today().timetuple().tm_yday); day=((doy-1)%365)+1
items=[r for r in PROG if r["day"]==day]
out=HERE.parent/"OGGI_SICURIX.md"
L=[f"# 🎬 SICURIX — 3 VIDEO DI OGGI (giorno {day}/365) · Sicurezza + HACCP + Privacy",""]
for r in items:
    L+=[f"\n## {r['slot']} · {r['theme']} — {r['prodotto']}",
        f"**Titolo:** {r['titolo']}",f"**CTA (prodotto=tema):** {r['cta_label']} → {r['cta_url']}",
        f"**Cast:** SICURIX + {r['hero']} vs {r['villain']}",
        f"**Descrizione (PNL/AIDA/EPPPA):**\n{r['descrizione']}",
        f"**>>> PROMPT GEMINI 9:16:**\n{r['gemini_prompt']}","---"]
out.write_text("\n".join(L),encoding="utf-8"); print(f"OGGI_SICURIX giorno {day}: {len(items)} video")
tok=os.environ.get("TELEGRAM_BOT_TOKEN"); ch=os.environ.get("TG_CHANNEL")
if tok and ch and items:
    msg=f"🎬 SICURIX oggi (g.{day}/365) — 3 video:\n"+"\n".join(f"• [{r['theme']}] {r['titolo']}" for r in items)
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage",data=urllib.parse.urlencode({"chat_id":ch,"text":msg}).encode(),timeout=20); print("TG ok")
    except Exception as e: print("TG skip:",e)
