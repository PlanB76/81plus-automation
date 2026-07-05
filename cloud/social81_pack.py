# -*- coding: utf-8 -*-
"""SOCIAL81+ — dal PROGRAMMA 365 (3 video tematici/giorno) genera il pacchetto post multi-piattaforma.
VIDEO verticale dal canale YT @sicurissimo (tema Sicurezza/HACCP/Privacy) OPPURE immagine/fumetto SICURIX. CTA prodotto + canale + sito."""
import json,os,datetime,pathlib
HERE=pathlib.Path(__file__).resolve().parent; DATA=HERE/"data"
PROG=json.load(open(DATA/"sicurix_program365.json",encoding="utf-8"))
doy=int(os.environ.get("FORCE_DAY") or datetime.date.today().timetuple().tm_yday); day=((doy-1)%365)+1
items=[r for r in PROG if r["day"]==day]
out=HERE.parent/"SOCIAL81_OGGI.md"; L=[f"# 📣 SOCIAL81+ — POST DI OGGI (giorno {day}/365) · 3 tematici",""]
for r in items:
    base=f"{r['titolo']}\n▶️ Guarda su YouTube @sicurissimo\n👉 {r['cta_label']}: {r['cta_url']}\n👉 Check gratuito: https://81plus.net/?src=social"
    L+=[f"\n## {r['slot']} · {r['theme']} — {r['prodotto']}",
        f"**YouTube (titolo):** {r['titolo']}",f"**YouTube (descrizione):**\n{r['descrizione']}",
        f"**Instagram/Reel:** {base}\n{r['hashtag']}",
        f"**TikTok:** {r['titolo']} #{r['theme']} — 81plus.net/?src=tt",
        f"**Facebook:** {base}",f"**LinkedIn:** {r['titolo']} — Metodo81+. {r['cta_label']}: {r['cta_url']}",
        f"**Telegram:** 🟧 {base}\n{r['hashtag']}","---"]
out.write_text("\n".join(L),encoding="utf-8"); print(f"SOCIAL81_OGGI giorno {day}: {len(items)} x 6 piattaforme")
