# -*- coding: utf-8 -*-
"""SICU81 FLIKI DAILY DISPATCH — CICLICO 365 giorni.
Ogni giorno emette i 3 short del giorno-dell'anno dal piano editoriale 365gg (editorial_365.json);
dopo il giorno 365 il ciclo riparte automaticamente. Fliki non ha API: consegna i 3 prompt/copy pronti
+ notifica Telegram. Segreti letti SOLO da env (TELEGRAM_BOT_TOKEN, TG_CHANNEL)."""
import json,os,datetime,urllib.request,urllib.parse,pathlib
HERE=pathlib.Path(__file__).resolve().parent
DATA=HERE/"data"
def load(name):
    p=DATA/name
    return json.load(open(p,encoding="utf-8")) if p.exists() else None
plan=load("editorial_365.json")
today=datetime.date.today()
# giorno-dell'anno 1..365 (366 -> 365 per restare nel piano), ciclico
doy=int(os.environ.get("FORCE_DAY") or today.timetuple().tm_yday)
day=((doy-1)%365)+1
if plan:
    items=[x for x in plan if x["day"]==day]
    source=f"piano editoriale 365 (giorno {day}/365, ciclico)"
else:  # fallback: coda semplice
    q=load("fliki_queue.json") or []
    iso=today.isoformat(); items=[x for x in q if x.get("data")==iso][:3] or q[:3]
    source="coda fliki_queue"
out=HERE.parent/"OGGI_FLIKI.md"
L=[f"# 🎬 SICÙ81+ — PRODUZIONE FLIKI DI OGGI ({today.isoformat()})",
   f"> Fonte: {source} · 3 short · CTA unica → 81plus.net",""]
for i,x in enumerate(items,1):
    L+=[f"\n## {i}) {x.get('asset','')} [{x.get('tipo','')}/{x.get('area','')}] · ore {x.get('slot',x.get('ora',''))}",
        f"**Titolo YouTube:** {x.get('titolo','')}",
        f"**CTA:** {x.get('cta_url','')}",
        f"**Descrizione SEO:**\n{x.get('seo','')}",
        f"**Hashtag:** {x.get('hashtag','')}",
        f"**Telegram:** {x.get('telegram','')}",
        f"**IG/Reel:** {x.get('instagram','')}",
        f"**TikTok:** {x.get('tiktok','')}","---"]
out.write_text("\n".join(L),encoding="utf-8")
print(f"Giorno {day}/365 · scritti {len(items)} short in {out}")
tok=os.environ.get("TELEGRAM_BOT_TOKEN"); ch=os.environ.get("TG_CHANNEL")
if tok and ch and items:
    msg=f"🎬 Fliki oggi (giorno {day}/365) — {len(items)} short:\n"+"\n".join(f"• {x.get('titolo','')}" for x in items)
    try:
        data=urllib.parse.urlencode({"chat_id":ch,"text":msg,"disable_web_page_preview":"true"}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage",data=data,timeout=20); print("TG ok")
    except Exception as e: print("TG skip:",e)
