#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Newsletter SETTIMANALE (sabato / ogni 5 articoli): riepilogo ultimi articoli + offerte,
nello stile email 81+ (emails.wrap). Genera pagina web + email JSON/MD."""
import os, json, datetime, html
import emails
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build(cfg, articles, active_campaigns, n=6):
    L=cfg["links"]; today=datetime.date.today().isoformat()
    arts=articles[:n]
    rows=""
    for a in arts:
        url=cfg["site_base"]+"/blog/"+a["slug"]+".html"
        rows+=('<tr><td style="padding:12px 0;border-bottom:1px solid #eee;">'
               '<span style="color:#FB6B00;font-weight:800;font-size:11px;text-transform:uppercase;">'+html.escape(a["theme"])+'</span><br>'
               '<a href="'+url+'" style="color:#080808;font-weight:700;font-size:16px;text-decoration:none;">'+html.escape(a["title"])+'</a><br>'
               '<span style="color:#555;font-size:13px;">'+html.escape(a["excerpt"])+'&hellip;</span></td></tr>')
    offers=""
    for c in active_campaigns[:3]:
        ourl=cfg["site_base"]+"/promo/"+c["slug"]+".html"
        offers+='<a href="'+ourl+'" style="color:#FB6B00;font-weight:800;text-decoration:none;display:block;padding:5px 0;">&rarr; '+html.escape(c["name"])+' (da &euro; '+("%.2f"%c["tiers"][1]["promo_price_eur"])+')</a>'
    inner=('<h1 style="margin:0 0 8px;font-size:25px;color:#080808;">La settimana della tua sicurezza</h1>'
           '<p style="margin:0 0 14px;color:#444;">Gli articoli piu importanti, le scadenze e le offerte. In 3 minuti.</p>'
           '<table role="presentation" width="100%" style="border-collapse:collapse;">'+rows+'</table>'
           '<hr style="border:none;border-top:1px solid #eee;margin:18px 0;">'
           '<h2 style="font-size:18px;color:#080808;margin:0 0 8px;">Offerte a tempo</h2>'+(offers or '<p>In arrivo.</p>'))
    page=emails.wrap(cfg, "Riepilogo settimanale 81+ "+today, inner, cta_url=L["audit"], cta_text="Fai l'AUDIT81+ gratuito")
    nd=os.path.join(ROOT,"..","newsletters"); os.makedirs(nd,exist_ok=True)
    open(os.path.join(nd,today+".html"),"w",encoding="utf-8").write(page)
    out=os.path.join(ROOT,"data","promo_out"); os.makedirs(out,exist_ok=True)
    subj="\U0001F4C5 Riepilogo settimanale 81+ — "+today
    json.dump({"sequence":"NEWSLETTER_WEEKLY_"+today,"subject":subj,"send":"sabato 08:00","html":page},
              open(os.path.join(out,"newsletter_"+today+".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    open(os.path.join(out,"newsletter_"+today+".md"),"w",encoding="utf-8").write(
        "# Newsletter settimanale 81+ — "+today+"\n\nOggetto: "+subj+"\n\n"+
        "\n".join("- "+a["title"]+" — "+cfg["site_base"]+"/blog/"+a["slug"]+".html" for a in arts))
    return {"page":os.path.join(nd,today+".html"),"subject":subj}
