#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Autopromozione: post social (multi-canale) + flusso email 4 step, per una CAMPAGNA pack
o per un ARTICOLO. Invia su Telegram se i secret ci sono; gli altri: skip pulito."""
import os, json, urllib.request, urllib.parse
import emails
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def tg_send(text):
    tok=os.environ.get("TG_BOT_TOKEN","").strip(); ch=os.environ.get("TG_CHANNEL","").strip()
    if not tok or not ch: print("[tg] skip (secret assenti)"); return False
    try:
        data=urllib.parse.urlencode({"chat_id":ch,"text":text}).encode()
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",data=data),timeout=15)
        print("[tg] inviato"); return True
    except Exception as e: print("[tg] errore",e); return False

def pack_caption(c):
    m=c["tiers"][1]
    return (f"🔥 {c['name']} — offerta a tempo\n\n{c['promise']}\n\n"
            f"💶 da € {m['promo_price_eur']:.2f} (-{m['discount_pct']}%) · valore € {m['full_value_eur']:.2f}\n"
            f"🎁 +{m['bonus_pv_plus']} PV+ · 🔥 solo {m['seats_left']} posti\n\n"
            f"👉 {c['landing_url']}\n#sicurezza81 #HACCP #formazione #81plus")

def pack_email_flow(cfg, c):
    m=c["tiers"][1]; ef=cfg["email_flow"]
    subs=[f"È uscito: {c['name']} (-{m['discount_pct']}%)",
          f"Perché {m['seats_left']} aziende lo stanno prendendo ora",
          f"🎁 +{m['bonus_pv_plus']} PV+ in regalo dentro {c['name']}",
          f"⏳ Ultime ore per {c['name']}"]
    body=[f"Abbiamo aperto il {c['name']}. {c['promise']} Da € {m['promo_price_eur']:.2f}. 👉 {c['landing_url']}",
          f"Solo {m['seats_left']} posti a questo prezzo. 👉 {c['landing_url']}",
          f"Oltre allo sconto, {m['bonus_pv_plus']} PV+ in regalo. 👉 {c['landing_url']}",
          f"Tra poche ore torna a prezzo pieno. 👉 {c['landing_url']}"]
    steps=[]
    for i in range(4):
        inner="<h1 style=\"margin:0 0 14px;font-size:24px;color:#080808;\">"+subs[i]+"</h1><p style=\"margin:0 0 14px;color:#333;\">"+body[i]+"</p>"
        steps.append({"step":i+1,"label":ef["steps_labels"][i],"after_h":ef["steps_hours"][i],"subject":subs[i],"body":body[i],"html":emails.wrap(cfg,subs[i],inner,cta_url=c["landing_url"],cta_text="Vai all\'offerta")})
    return {"sequence":f"{ef['sequence_prefix']}_{c['id']}","deadline":c["deadline_utc"],"steps":steps}

def article_caption(a, cfg):
    return (f"📰 {a['title']}\n\n{a['excerpt']}…\n\n👉 {cfg['site_base']}/blog/{a['slug']}.html\n"
            f"▶ {cfg['links']['youtube']}")

def promote_campaign(cfg, c, send=False):
    out=os.path.join(ROOT,"data","promo_out"); os.makedirs(out,exist_ok=True)
    cap=pack_caption(c); flow=pack_email_flow(cfg,c)
    json.dump({"telegram":cap,"instagram":cap+"\n(IG)","facebook":cap,"linkedin":cap},
              open(os.path.join(out,f"social_{c['id']}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    json.dump(flow,open(os.path.join(out,f"email_{c['id']}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    md=f"# Flusso email — {c['name']}\n\n"+"".join(f"## {s['label']} (+{s['after_h']}h)\n**{s['subject']}**\n\n{s['body']}\n\n---\n" for s in flow["steps"])
    open(os.path.join(out,f"email_{c['id']}.md"),"w",encoding="utf-8").write(md)
    if send and cfg["channels"]["telegram"]["enabled"]: tg_send(cap)
    print(f"[promote] {c['name']} — materiali in data/promo_out/  (send={send})")

def promote_article(cfg, a, send=False):
    cap=article_caption(a,cfg)
    if send and cfg["channels"]["telegram"]["enabled"]: tg_send(cap)
    print(f"[promote] articolo '{a['title']}' (send={send})")

def special_caption(cfg, c):
    url=cfg["site_base"]+"/promo/"+c["slug"]+".html"
    return ("\u2b50 "+c["title"]+" \u2014 SPECIAL PACK 81+\n\n"
            "Diventa autonomo sulla sicurezza (ASR 2025) \u00b7 "+str(c["hours"])+" ore.\n"
            "\U0001F4B6 \u20ac "+("%.2f"%c["promo"])+" invece di \u20ac "+("%.2f"%c["full"])+" (-"+str(c["discount"])+"%)\n"
            "\U0001F381 + Order Bump Corso Stress -20%\n\n\U0001F449 "+url+"\n#sicurezza81 #formazione #81plus")

def promote_specials(cfg, cards, send=False):
    out=os.path.join(ROOT,"data","promo_out"); os.makedirs(out,exist_ok=True)
    for c in cards:
        cap=special_caption(cfg,c)
        json.dump({"telegram":cap,"facebook":cap,"instagram":cap+"\n(IG)","linkedin":cap},
                  open(os.path.join(out,"social_special_"+c["slug"]+".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    if send and cfg["channels"]["telegram"]["enabled"] and cards:
        import datetime; tg_send(special_caption(cfg, cards[datetime.date.today().toordinal()%len(cards)]))
    print("[promote] special:",len(cards),"(send="+str(send)+")")
