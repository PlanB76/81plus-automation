#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SCHEDULER BLOG81+ — giro giornaliero autonomo:
1) cicla i PACK: scadenza -> 'expired'; se >= next_promote -> RIAPRE (+90gg) e ri-promuove;
2) garantisce min campagne attive (crea nuove se servono);
3) scrive landing/scaduta/blocco index/promo index;
4) genera l'articolo del giorno e aggiorna blog81.html;
5) inietta il blocco promo nella index.html (sul marker) e stampa la voce menu."""
import os, json, datetime, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack_engine as PE, blog_engine as BE, promote as PR
import curated, newsletter, scadenzario
from listino_loader import load_catalog

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return datetime.datetime.now(datetime.timezone.utc)
def parse(s): return datetime.datetime.fromisoformat(s)

def inject_index(cfg, block):
    tgt=os.path.join(ROOT, cfg["publish"]["index_target"]); marker=cfg["publish"]["index_marker"]
    if not os.path.exists(tgt): print("[index] index.html non trovato, skip"); return
    s=open(tgt,encoding="utf-8",errors="ignore").read()
    if marker in s:
        # sostituisci dal marker fino al prossimo marker/fine sezione promo
        import re
        s=re.sub(re.escape(marker)+r".*?(?=<!--/PACK81_PROMO-->|$)", block+"\n<!--/PACK81_PROMO-->\n", s, count=1, flags=re.S)
        open(tgt,"w",encoding="utf-8").write(s); print("[index] blocco promo aggiornato sul marker")
    else:
        print("[index] marker non presente. Aggiungi in index.html dove vuoi la sezione:\n   "+marker)

def run(send=False):
    cfg=BE.cfgload(); cat=load_catalog(cfg); pk=cfg["pack"]; reg=PE.load_reg(); t=now()
    # 1) scadenze
    for c in reg["campaigns"]:
        if c["status"]=="active":
            allzero=all(tt["seats_left"]<=0 for tt in c["tiers"])
            if t>parse(c["deadline_utc"]) or allzero: c["status"]="expired"; print("scaduta:",c["name"])
    # 2) riapertura ogni 90gg
    for c in reg["campaigns"]:
        if c["status"]=="expired" and t>=parse(c["next_promote_utc"]):
            c["status"]="active"; c["cycle"]+=1
            c["deadline_utc"]=(t+datetime.timedelta(hours=pk["countdown_hours"])).isoformat()
            c["next_promote_utc"]=(t+datetime.timedelta(days=pk["repromo_cycle_days"])).isoformat()
            for i,tt in enumerate(c["tiers"]): tt["seats_left"]=pk["tiers"][i]["seats"]
            print("RIAPERTA (ciclo %d):"%c["cycle"],c["name"]); PR.promote_campaign(cfg,c,send)
    # 3) min attive
    active=[c for c in reg["campaigns"] if c["status"]=="active"]
    while len(active)<pk["min_active_campaigns"]:
        c=PE.build_campaign(cfg,cat); reg["campaigns"].append(c); active.append(c)
        print("nuova:",c["name"]); PR.promote_campaign(cfg,c,send)
    # 4) scrivi file pack
    for c in active: PE.write_campaign_files(c,cfg,active)
    pd=os.path.join(ROOT,cfg["publish"]["promo_dir"]); os.makedirs(pd,exist_ok=True)
    cur_cards=curated.publish(cfg)
    PR.promote_specials(cfg,cur_cards,send)
    block=PE.render_index_block(active,cfg)+curated.render_cards_html(cur_cards)
    open(os.path.join(pd,"_promo_block.html"),"w",encoding="utf-8").write(block)
    # promo/index.html (vetrina offerte)
    cards="".join(f'<a href="/promo/{c["slug"]}.html" style="display:block;padding:14px;border:1px solid #E6E6E8;border-radius:12px;margin:8px 0;text-decoration:none;color:#0B0B0C"><b>{c["name"]}</b> — da € {c["tiers"][1]["promo_price_eur"]:.2f} (-{c["tiers"][1]["discount_pct"]}%)</a>' for c in active)
    open(os.path.join(pd,"index.html"),"w",encoding="utf-8").write(
        f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offerte 81+</title><body style="font-family:system-ui;max-width:760px;margin:0 auto;padding:24px"><h1 style="color:#FB6B00">🔥 Offerte 81+ attive</h1>{cards}</body>')
    PE.save_reg(reg)
    # 5) articolo del giorno
    stp=os.path.join(ROOT,"data","state.json")
    st=json.load(open(stp,encoding="utf-8")) if os.path.exists(stp) else {"articles_since_nl":0,"last_scad_month":"","theme_idx":0}
    rot=cfg["blog"]["themes_rotation"]; theme=rot[st.get("theme_idx",0)%len(rot)]; st["theme_idx"]=st.get("theme_idx",0)+1
    ang=cfg["blog"].get("angles",[]); angle=(ang[st.get("angle_idx",0)%len(ang)]["gancio"] if ang else None); st["angle_idx"]=st.get("angle_idx",0)+1
    art=BE.generate_article(cfg,cat,theme,cfg["links"]["promo"],angle)
    areg=BE.write_article(cfg,art)
    st["articles_since_nl"]=st.get("articles_since_nl",0)+1
    # SCADENZARIO mensile (una volta al mese)
    ym=t.strftime("%Y-%m")
    if st.get("last_scad_month","")!=ym:
        from images import theme_media
        sc=scadenzario.article(cfg)
        sm=re.search(r"<h1>(.*?)</h1>",sc,re.S); stitle=re.sub("<[^>]+>","",sm.group(1)).strip() if sm else "Scadenzario 81+"
        media=theme_media(cfg,"Sicurezza del Lavoro",stitle)
        sc_art={"theme":"Scadenzario 81+","title":stitle,"excerpt":"Tutte le scadenze sicurezza e HACCP del mese, in un colpo d'occhio.","html":sc,"date":t.isoformat(),"slug":t.strftime("%Y%m%d")+"-scadenzario-sicurezza-haccp","read":4,"image":media["image"],"video":media.get("video")}
        areg=BE.write_article(cfg,sc_art)
        em=scadenzario.email(cfg); out=os.path.join(ROOT,"data","promo_out"); os.makedirs(out,exist_ok=True)
        json.dump({"sequence":"REMINDER_SCADENZE_"+ym,"subject":em["subject"],"body":em["body"],"html":em.get("html",""),"send":"mensile"},open(os.path.join(out,"scadenzario_"+ym+".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        st["last_scad_month"]=ym; print("scadenzario mensile + reminder generati")
    # indice blog (include scadenzario se creato)
    open(os.path.join(ROOT,cfg["publish"]["blog_index"]),"w",encoding="utf-8").write(
        BE.render_blog_index(cfg,areg["articles"],block))
    # NEWSLETTER settimanale (sabato oppure ogni 5 articoli)
    if t.weekday()==5 or st["articles_since_nl"]>=5:
        nl=newsletter.build(cfg,areg["articles"],active); st["articles_since_nl"]=0
        print("newsletter settimanale:",nl["subject"])
    json.dump(st,open(stp,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    PR.promote_article(cfg,art,send)
    # 6) inietta in index
    inject_index(cfg,block)
    print("\n=== VOCE MENU DA AGGIUNGERE in index.html (MI[]) ===")
    print('  ["Blog","/blog81.html"],  ["Offerte","/promo/"],')
    print("done. attive:",len(active)," articoli:",len(areg["articles"]))

if __name__=="__main__":
    run(send=("--send" in sys.argv))
