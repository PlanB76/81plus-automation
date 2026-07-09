#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PACK81+ — genera CAMPAGNE offerta a 3 tier (SCUDO/CORAZZA/FORTEZZA) dal listino reale,
con landing (AIDA/EPPPA/FOMO/decoy), blocco per la index, pagina 'scaduta',
registry e ciclo repromo 90gg (oneshot + ricorrenti)."""
import os, json, random, hashlib, datetime, urllib.request
from listino_loader import load_catalog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cfgload(): return json.load(open(os.path.join(ROOT,"config","blog81_config.json"),encoding="utf-8"))
def now(): return datetime.datetime.now(datetime.timezone.utc)
def iso(dt): return dt.isoformat()

HOOK = {"sicurezza":"Sicurezza sul Lavoro","haccp":"HACCP & Alimentare","privacy":"Privacy & GDPR",
        "elettrico":"Rischio Elettrico","formazione":"Formazione del Team","presidio":"Presidio & Compliance",
        "starter":"Starter 81+"}
PROMISE = {"sicurezza":"Metti in regola l'azienda e togli di mezzo il rischio sanzioni, una volta per tutte.",
           "haccp":"Alimentare a norma in giorni, non mesi. Zero contestazioni ai controlli.",
           "privacy":"GDPR gestito e documenti pronti: la multa del Garante non ti riguarda piu.",
           "elettrico":"Personale abilitato e cantiere in sicurezza, subito e a norma.",
           "formazione":"Squadra formata e attestati validi, tutto in un unico pacchetto.",
           "presidio":"Compliance presidiata con dashboard e sigillo 81+: dormi sereno.",
           "starter":"Entri nell'ecosistema 81+ dalla porta giusta, spendendo pochissimo."}
TIER_DESC={"scudo":"La base che ti mette in regola e toglie subito il rischio piu urgente.",
 "corazza":"Il piu scelto: copertura completa al miglior rapporto valore/prezzo.",
 "fortezza":"Tutto incluso: protezione totale + presidio continuo, chiavi in mano."}
TIER_BULLETS={
 "scudo":["\U0001F6E1\uFE0F In regola in 48 ore, senza pensieri","\U0001F9FE Zero burocrazia: la gestiamo noi","\u2705 Attestati validi e verificabili subito"],
 "corazza":["\U0001F3F0 Copertura completa, nulla di scoperto","\U0001F4B0 Risparmio massimo vs acquisto singolo","\u26A1 Priorita di attivazione + assistenza","\U0001F381 Bonus PV+ piu alto incluso"],
 "fortezza":["\U0001F451 Tutto il CORAZZA + presidio continuo","\U0001F512 Sigillo/Dashboard di compliance inclusi","\U0001F9E0 Consulenza di setup: gia operativo","\U0001F634 Dormi sereno: blindato a 360\u00b0"]}

def psych(x, end=0.90):
    i=int(round(x)); return round(max(1,i-1)+end,2)

def pick_items(pool, k, rnd):
    if k>=len(pool): return list(pool)
    return rnd.sample(pool, k)

def build_campaign(cfg, catalog, force_theme=None, seed=None, recurring=None):
    rnd=random.Random(seed); pk=cfg["pack"]
    payable=[p for p in catalog if p.get("price",0)>0]
    theme=force_theme or rnd.choice(list(HOOK.keys()))
    pool=[p for p in payable if p.get("theme")==theme] or payable
    # ordina per prezzo per costruire tier annidati coerenti
    pool_sorted=sorted(pool, key=lambda p:p["price"])
    n=now(); deadline=n+datetime.timedelta(hours=pk["countdown_hours"])
    cid="C"+hashlib.sha1(f"{theme}{iso(n)}".encode()).hexdigest()[:8].upper()
    slug=f"pack81-{theme}-{cid.lower()}"
    tiers=[]; chosen=[]
    for t in pk["tiers"]:
        # tier annidato: parte dagli item del tier precedente + ne aggiunge
        need=t["items"]
        extra=[p for p in pool if p not in chosen]
        rnd.shuffle(extra)
        while len(chosen)<need and extra: chosen.append(extra.pop())
        items=list(chosen)
        full=round(sum(i["price"] for i in items),2)
        promo=psych(full*(1-t["discount_pct"]/100.0), pk["psychological_ending"])
        save=round(full-promo,2)
        handle=cfg["paypal"]["handle"]
        tiers.append({
            "key":t["key"],"label":t["label"],"tag":t["tag"],"badge":t.get("badge",""),
            "items":[{"name":i["name"],"price":i["price"],"recurring":i.get("recurring",False)} for i in items],
            "full_value_eur":full,"discount_pct":t["discount_pct"],"promo_price_eur":promo,"you_save_eur":save,
            "bonus_pv_plus":int(promo),"pv":promo,"cashback_pv_plus":round(promo*0.30,2),
            "seats_left":t["seats"],"paypal_url":f"https://www.paypal.me/{handle}/{promo:.2f}EUR"
        })
    is_rec = recurring if recurring is not None else any(any(i["recurring"] for i in t["items"]) for t in tiers)
    return {
        "id":cid,"slug":slug,"theme":theme,"kind":"ricorrente" if is_rec else "oneshot",
        "name":f"PACK {HOOK.get(theme,theme.upper())}","promise":PROMISE.get(theme,""),
        "tiers":tiers,"created_utc":iso(n),"deadline_utc":iso(deadline),
        "countdown_hours":pk["countdown_hours"],"status":"active","cycle":1,
        "next_promote_utc":iso(n+datetime.timedelta(days=pk["repromo_cycle_days"])),
        "landing_url":f"{cfg['site_base']}/promo/{slug}.html",
        "legal":cfg["legal"],"links":cfg["links"]
    }

# ---------------- RENDER ----------------
def _cards(c, links):
    out=""
    for i,t in enumerate(c["tiers"]):
        feat=i==1
        badge=f'<div class="tribbon">{t["badge"]}</div>' if t["badge"] else ""
        desc=TIER_DESC.get(t["key"],"")
        bl="".join(f'<li class="bpt">{b}</li>' for b in TIER_BULLETS.get(t["key"],[]))
        inc="".join(f'<li>+ {it["name"]}</li>' for it in t["items"][:5])
        more=f'<li class="more">+ altri {len(t["items"])-5} inclusi...</li>' if len(t["items"])>5 else ""
        pv=int(round(t["promo_price_eur"]))
        out+=f'''<div class="tier{" feat" if feat else ""}">{badge}
  <div class="tname">{t["label"]} <span>{t["tag"]}</span></div>
  <div class="tdesc">{desc}</div>
  <ul class="bullets">{bl}</ul>
  <details class="tinc"><summary>Cosa contiene</summary><ul>{inc}{more}</ul></details>
  <div class="tfull">Valore &euro; {t["full_value_eur"]:.2f}</div>
  <div class="tpromo">&euro; {t["promo_price_eur"]:.2f}</div>
  <div class="tsave">RISPARMI &euro; {t["you_save_eur"]:.2f} &middot; -{t["discount_pct"]}%</div>
  <div class="teco">= {pv} PV &middot; guadagni {t["bonus_pv_plus"]} PV+ nel wallet &middot; cashback 30% = {t["cashback_pv_plus"]:.0f} PV+</div>
  <div class="tseats">SOLO {t["seats_left"]} DISPONIBILI</div>
  <a class="tcta" href="{t["paypal_url"]}" target="_blank" rel="nofollow">VOGLIO {t["label"]} -></a>
  <div class="tpv">1&euro; speso = 1 PV+ nel tuo wallet 81+</div>
</div>'''
    return out

def render_landing(c, cfg):
    links=cfg["links"]
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{c["name"]} · Offerta 81+ (-{c["tiers"][1]["discount_pct"]}%)</title>
<meta name="description" content="{c["promise"]}">
<meta property="og:title" content="{c["name"]} — sconto fino a -{c["tiers"][-1]["discount_pct"]}%">
<meta property="og:description" content="{c["promise"]}">
<style>
:root{{--ink:#0B0B0C;--paper:#fff;--or:#FB6B00;--ord:#E8501A;--line:#E6E6E8;--g4:#6E6E76;--ok:#FB6B00;--red:#FB6B00}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--ink);background:var(--paper);line-height:1.5}}
.wrap{{max-width:1080px;margin:0 auto;padding:22px 16px 70px}}
.kic{{color:var(--or);font-weight:800;letter-spacing:.16em;text-transform:uppercase;font-size:12px;text-align:center}}
h1{{font-size:clamp(28px,6vw,46px);font-weight:900;text-align:center;line-height:1.1;margin:8px 0}}
.promise{{text-align:center;color:var(--g4);font-size:clamp(16px,3.5vw,20px);max-width:760px;margin:0 auto 8px}}
.fear{{text-align:center;background:#0B0B0C;border:2px solid var(--or);color:#fff;border-radius:12px;padding:12px 16px;margin:16px auto;max-width:760px;font-weight:600}}
.cd{{display:flex;gap:8px;justify-content:center;margin:14px 0}}
.cd div{{background:var(--ink);color:#fff;border-radius:12px;min-width:66px;padding:10px 6px;text-align:center}}
.cd b{{display:block;font-size:26px;color:var(--or)}}.cd span{{font-size:10px;text-transform:uppercase;opacity:.7}}
.exp{{display:none;text-align:center;color:#FB6B00;font-weight:900;font-size:22px;margin:8px 0}}
.tiers{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0}}
@media(max-width:820px){{.tiers{{grid-template-columns:1fr}}}}
.tier{{position:relative;isolation:isolate;overflow:hidden;border-radius:18px;padding:18px;display:flex;flex-direction:column;gap:8px;color:#f4f4f6;border:3px solid var(--or);background:linear-gradient(160deg,#15161c 0%,#0d0e12 55%,#1a1206 100%),url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Ctext x='4' y='90' font-family='Arial' font-size='20' font-weight='900' fill='%23FB6B00' fill-opacity='0.11' transform='rotate(-30 60 60)'%3E81%2B%3C/text%3E%3C/svg%3E\");background-blend-mode:normal;box-shadow:inset 0 3px 0 rgba(255,255,255,.35),inset 0 -5px 0 rgba(0,0,0,.7),0 24px 48px rgba(0,0,0,.6),0 5px 0 #000;transition:transform .35s cubic-bezier(.2,.8,.2,1),box-shadow .35s}}.tier::before{{content:'';position:absolute;inset:-40% -60%;z-index:-1;background:linear-gradient(115deg,transparent 40%,rgba(255,255,255,.16) 48%,rgba(255,255,255,.4) 50%,rgba(255,255,255,.16) 52%,transparent 60%);transform:translateX(-40%);animation:sheen81 6s ease-in-out infinite}}.tier::after{{content:'';position:absolute;inset:0;z-index:-1;pointer-events:none;background-image:radial-gradient(1.6px 1.6px at 20% 30%,#fff,transparent),radial-gradient(1.4px 1.4px at 70% 20%,#fff,transparent),radial-gradient(1.6px 1.6px at 85% 65%,#fff,transparent),radial-gradient(1.3px 1.3px at 35% 80%,#fff,transparent),radial-gradient(1.5px 1.5px at 55% 50%,#FB6B00,transparent);opacity:.55;animation:twinkle81 3.2s ease-in-out infinite}}.tier:hover{{transform:translateY(-8px) scale(1.015)}}
.tier.feat{{border:3px solid var(--or);box-shadow:inset 0 3px 0 rgba(255,255,255,.4),inset 0 0 0 2px rgba(251,107,0,.5),0 24px 56px rgba(251,107,0,.5),0 5px 0 #000;animation:float81 4s ease-in-out infinite}}.tier.feat:hover{{transform:translateY(-10px) scale(1.03)}}@keyframes sheen81{{0%,100%{{transform:translateX(-40%)}}50%{{transform:translateX(40%)}}}}@keyframes twinkle81{{0%,100%{{opacity:.35}}50%{{opacity:.8}}}}@keyframes float81{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}@media(prefers-reduced-motion:reduce){{.tier,.tier.feat,.tier::before,.tier::after{{animation:none!important}}}}
.tribbon{{position:absolute;top:15px;right:-48px;width:180px;text-align:center;transform:rotate(45deg);background:var(--or);color:#0B0B0C;font-weight:900;font-size:11px;letter-spacing:.02em;padding:6px 0;box-shadow:0 2px 10px rgba(0,0,0,.6);z-index:3;text-transform:uppercase}}
.tname{{font-weight:900;font-size:21px;color:#fff}}.tname span{{color:var(--or)}}
.tdesc{{color:#cfd0d6;font-size:14px;min-height:40px}}.bullets{{list-style:none;display:flex;flex-direction:column;gap:6px;min-height:110px}}.bpt{{font-size:14.5px;font-weight:600}}.tinc summary{{cursor:pointer;color:#FBB36B;font-size:13px;font-weight:700}}.tinc ul{{list-style:none;font-size:13px;color:#b9bac2;margin-top:6px;display:flex;flex-direction:column;gap:4px}}.tier .more{{color:#9a9aa6;font-style:italic}}.teco{{background:#fff;border:1px solid var(--or);border-radius:8px;padding:6px 8px;font-size:12px;color:#0B0B0C;font-weight:700}}
.tier .more{{color:var(--g4);font-style:italic}}
.tfull{{color:#9a9aa6;text-decoration:line-through;font-size:14px}}
.tpromo{{font-size:36px;font-weight:900;color:#fff;text-shadow:0 1px 0 #000,0 0 18px rgba(251,107,0,.35)}}
.tsave{{display:inline-block;background:var(--or);color:#0B0B0C;font-weight:800;border-radius:8px;padding:3px 10px;font-size:13px;width:fit-content}}
.tseats{{color:var(--or);font-weight:900;font-size:13px;text-transform:uppercase}}
.tcta{{display:block;text-align:center;background:linear-gradient(135deg,#ff8a2b,var(--or));color:#1a1300;font-weight:900;text-decoration:none;padding:14px;border-radius:12px;margin-top:6px}}
.tpv{{color:var(--or);font-size:12px;text-align:center}}
.sec{{max-width:820px;margin:26px auto;padding:0 4px}}
.sec h2{{font-size:22px;margin-bottom:8px}}.sec p,.sec li{{color:#333;font-size:15.5px}}
.sec ul{{padding-left:18px}}
.proof{{background:#f7f7f8;border:1px solid var(--line);border-radius:14px;padding:16px}}
.chan{{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin:18px 0}}
.chan a{{border:1.5px solid var(--line);border-radius:10px;padding:10px 14px;font-weight:800;text-decoration:none;color:var(--ink);font-size:14px}}
.foot{{color:#8a8a92;font-size:12px;text-align:center;margin-top:26px;line-height:1.7}}
</style></head><body><div class="wrap">
<div class="kic">OFFERTA {c["kind"].upper()} · 81+ · ID {c["id"]}</div>
<h1>{c["name"]}</h1>
<p class="promise">{c["promise"]}</p>
<div class="fear">⚠️ {random.choice(["L'obbligo di legge non aspetta: o sei in regola, o rischi sanzioni e responsabilita personali.","Un controllo INL/NAS puo arrivare domani. Chi e pronto non trema."])}</div>
<div class="cd" id="cd"><div><b data-d>00</b><span>giorni</span></div><div><b data-h>00</b><span>ore</span></div><div><b data-m>00</b><span>min</span></div><div><b data-s>00</b><span>sec</span></div></div>
<div class="exp" id="exp">⛔ Offerta chiusa</div>

<div class="tiers">{_cards(c, links)}</div>

<div class="sec"><h2>Perche' adesso (e non "quando avro' tempo")</h2>
<p>Ogni settimana che rimandi e' una settimana in cui la tua azienda e' scoperta. La formazione, l'HACCP,
la privacy, la sicurezza <b>non sono un costo: sono lo scudo</b> che ti evita multe, fermi attivita' e responsabilita' penali.
Con questo pacchetto metti tutto in ordine in un colpo solo, spendendo una frazione del valore reale.</p></div>

<div class="sec proof"><h2>Perche' 81+</h2>
<ul><li>Oltre 500 corsi accreditati e un ecosistema completo (Sicurissimo).</li>
<li>Documenti pronti, attestati validi, presidio continuo.</li>
<li>Migliaia di aziende gia' dentro il Metodo 81+. Leggi le <a href="/recensioni.html">recensioni reali</a>.</li></ul></div>

<div class="sec"><h2>Garanzia & serenita'</h2>
<p>Prezzo bloccato solo finche' il countdown corre e restano posti. Scaduto, si torna a prezzo pieno.
Quello che risparmi oggi non torna. {c["legal"]["disclaimer"]}</p></div>

<div class="chan">
<a href="{links['youtube']}" target="_blank">▶ YouTube @sicurissimo</a>
<a href="{links['telegram_channel']}" target="_blank">✈ Canale Telegram</a>
<a href="{links['telegram_groups']}">👥 Gruppi</a>
<a href="/promo/">🔥 Tutte le Offerte</a>
</div>

<p class="foot">{c["legal"]["price_note"]}<br>{c["legal"]["vendor"]}<br>
<a href="{cfg['site_base']}" style="color:var(--or)">81plus.net</a></p>
</div>
<script>
var DL="{c['deadline_utc']}";function pad(n){{return String(n).padStart(2,'0')}}
function tk(){{var d=new Date(DL)-new Date();if(d<=0){{document.getElementById('cd').style.display='none';document.getElementById('exp').style.display='block';document.querySelectorAll('.tcta').forEach(function(b){{b.style.filter='grayscale(1)';b.style.pointerEvents='none';b.textContent='CHIUSO';}});return;}}
var s=Math.floor(d/1000);document.querySelector('[data-d]').textContent=pad(s/86400|0);document.querySelector('[data-h]').textContent=pad(s%86400/3600|0);document.querySelector('[data-m]').textContent=pad(s%3600/60|0);document.querySelector('[data-s]').textContent=pad(s%60);}}
tk();setInterval(tk,1000);
</script></body></html>'''

P81_PATTERN = "url(\"data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27120%27 height=%27120%27%3E%3Ctext x=%274%27 y=%2790%27 font-family=%27Arial%27 font-size=%2730%27 font-weight=%27900%27 fill=%27%23FB6B00%27 fill-opacity=%270.11%27 transform=%27rotate(-30 60 60)%27%3E81%2B%3C/text%3E%3C/svg%3E\")"
LUX_CSS = (
 ".p81grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}"
 "@media(max-width:820px){.p81grid{grid-template-columns:1fr}}"
 ".p81grid a.p81c{position:relative;isolation:isolate;overflow:hidden;display:flex;flex-direction:column;gap:6px;padding:18px;text-decoration:none;color:#f4f4f6;border:3px solid #FB6B00;border-radius:16px;"
 "background:linear-gradient(160deg,#15161c,#0d0e12 55%,#1a1206)," + P81_PATTERN + ";"
 "box-shadow:inset 0 3px 0 rgba(255,255,255,.35),inset 0 -5px 0 rgba(0,0,0,.7),0 18px 40px rgba(0,0,0,.55),0 4px 0 #000;transition:transform .35s cubic-bezier(.2,.8,.2,1)}"
 ".p81grid a.p81c::before{content:'';position:absolute;inset:-40% -60%;z-index:0;background:linear-gradient(115deg,transparent 40%,rgba(255,255,255,.4) 50%,transparent 60%);transform:translateX(-40%);animation:p81sh 6s ease-in-out infinite}"
 ".p81grid a.p81c::after{content:'';position:absolute;inset:0;z-index:0;pointer-events:none;background-image:radial-gradient(1.6px 1.6px at 20% 30%,#fff,transparent),radial-gradient(1.4px 1.4px at 75% 25%,#FB6B00,transparent),radial-gradient(1.5px 1.5px at 60% 70%,#fff,transparent);opacity:.5;animation:p81tw 3.2s ease-in-out infinite}"
 ".p81grid a.p81c>*{position:relative;z-index:1}"
 ".p81grid a.p81c:hover{transform:translateY(-8px) scale(1.015)}"
 ".p81b{position:absolute;top:12px;right:12px;background:#FB6B00;color:#0B0B0C;font-weight:900;border-radius:8px;padding:2px 9px;font-size:12px;z-index:2}"
 ".p81c b{font-size:17px;color:#fff}"
 ".p81p{font-weight:900;font-size:20px;color:#fff}.p81p s{color:#9a9aa6;font-weight:600;font-size:14px}"
 ".p81s{color:#FB6B00;font-weight:800;font-size:13px;text-transform:uppercase}"
 "@keyframes p81sh{0%,100%{transform:translateX(-40%)}50%{transform:translateX(40%)}}"
 "@keyframes p81tw{0%,100%{opacity:.3}50%{opacity:.75}}"
 "@media(prefers-reduced-motion:reduce){.p81grid a.p81c::before,.p81grid a.p81c::after{animation:none}}"
)

def render_index_block(campaigns, cfg):
    if not campaigns:
        return "<!--PACK81_PROMO--><!-- nessuna offerta attiva -->"
    cards=""
    for c in campaigns[:3]:
        m=c["tiers"][1]
        cards+=('<a class="p81c" href="/promo/'+c["slug"]+'.html">'
                '<span class="p81b">-'+str(m["discount_pct"])+'%</span>'
                '<b>'+c["name"]+'</b>'
                '<span class="p81p">€ '+('%.2f'%m["promo_price_eur"])+' <s>€ '+('%.2f'%m["full_value_eur"])+'</s></span>'
                '<span class="p81s">solo '+str(m["seats_left"])+' disponibili · a tempo</span></a>')
    dl=campaigns[0]["deadline_utc"]
    js=("<script>(function(){var DL=\""+dl+"\";var e=document.getElementById('p81cd');function t(){var d=new Date(DL)-new Date();if(!e)return;if(d<=0){e.textContent='Offerta in aggiornamento';return}var s=d/1000|0;e.innerHTML=[(s/86400|0)+'g',(s%86400/3600|0)+'h',(s%3600/60|0)+'m',(s%60)+'s'].map(function(x){return '<span style=\\\"background:#0B0B0C;color:#FB6B00;border-radius:8px;padding:6px 10px\\\">'+x+'</span>'}).join('');}t();setInterval(t,1000);})();</script>")
    head=('<!--PACK81_PROMO-->\n<section id="pack81-promo" style="max-width:1080px;margin:26px auto;padding:0 16px">'
          '<div style="text-align:center;color:#FB6B00;font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:12px">Offerte 81+ a tempo</div>'
          '<h2 style="text-align:center;font-size:clamp(24px,5vw,34px);font-weight:900;margin:6px 0">\U0001F525 PACK81+ in promo</h2>'
          '<div id="p81cd" style="display:flex;gap:8px;justify-content:center;margin:10px 0;font-weight:900"></div>'
          '<div class="p81grid">'+cards+'</div>'
          '<div style="text-align:center;margin-top:14px"><a href="/promo/" style="background:#0B0B0C;color:#fff;text-decoration:none;font-weight:800;padding:12px 20px;border-radius:12px">Vedi tutte le offerte →</a></div>'
          '</section>')
    return head+"<style>"+LUX_CSS+"</style>"+js

def render_expired(c, cfg, active_others):
    links=cfg["links"]
    others="".join(f'<a href="/promo/{o["slug"]}.html" style="display:block;padding:10px 0;color:#FB6B00;font-weight:700">→ {o["name"]} (-{o["tiers"][1]["discount_pct"]}%)</a>' for o in active_others[:3])
    reopen=c.get("next_promote_utc","")[:10]
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{c["name"]} · Offerta chiusa</title>
<style>body{{font-family:-apple-system,Segoe UI,Arial;background:#0B0B0C;color:#eee;margin:0;padding:40px 18px;text-align:center}}
.b{{max-width:620px;margin:0 auto}}h1{{color:#FB6B00;font-size:30px}}a.cta{{display:inline-block;background:#FB6B00;color:#1a1300;font-weight:900;text-decoration:none;padding:14px 22px;border-radius:12px;margin-top:16px}}
.box{{background:#15151d;border:1px solid #26262f;border-radius:14px;padding:18px;margin:18px 0;text-align:left}}</style></head>
<body><div class="b"><h1>⛔ {c["name"]}: offerta chiusa</h1>
<p>I posti a prezzo bloccato sono esauriti o il tempo e' scaduto. Ma niente panico:
questa promo <b>ritorna</b>. La prossima finestra e' prevista intorno al <b>{reopen}</b>.</p>
<a class="cta" href="{links['audit']}">Avvisami e blocca il posto next round →</a>
<div class="box"><b>Nel frattempo, offerte attive ora:</b>{others or '<p>In arrivo a breve.</p>'}</div>
<div class="box"><b>Resta connesso:</b><br>
<a href="{links['youtube']}" style="color:#FB6B00">▶ YouTube @sicurissimo</a> ·
<a href="{links['telegram_channel']}" style="color:#FB6B00">✈ Telegram</a> ·
<a href="{links['listino']}" style="color:#FB6B00">📚 Listino81+</a></div>
</div></body></html>'''

# ---------------- REGISTRY / LIFECYCLE ----------------
def reg_path(): return os.path.join(ROOT,"data","campaigns_registry.json")
def load_reg():
    p=reg_path(); return json.load(open(p,encoding="utf-8")) if os.path.exists(p) else {"campaigns":[]}
def save_reg(r): json.dump(r,open(reg_path(),"w",encoding="utf-8"),ensure_ascii=False,indent=2)

def write_campaign_files(c, cfg, active_all):
    pd=os.path.join(ROOT, cfg["publish"]["promo_dir"]); os.makedirs(pd,exist_ok=True)
    open(os.path.join(pd,f"{c['slug']}.html"),"w",encoding="utf-8").write(render_landing(c,cfg))
    others=[o for o in active_all if o["id"]!=c["id"]]
    open(os.path.join(pd,f"{c['slug']}-scaduta.html"),"w",encoding="utf-8").write(render_expired(c,cfg,others))

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--count",type=int,default=1); ap.add_argument("--theme")
    a=ap.parse_args(); cfg=cfgload(); cat=load_catalog(cfg); reg=load_reg()
    for i in range(a.count):
        c=build_campaign(cfg,cat,a.theme,seed=None)
        reg["campaigns"].append(c)
        print("creata:",c["name"],c["kind"],"tier M €",c["tiers"][1]["promo_price_eur"])
    active=[c for c in reg["campaigns"] if c["status"]=="active"]
    for c in active: write_campaign_files(c,cfg,active)
    pd=os.path.join(ROOT,cfg["publish"]["promo_dir"])
    open(os.path.join(pd,"_promo_block.html"),"w",encoding="utf-8").write(render_index_block(active,cfg))
    save_reg(reg)
    print("attive:",len(active))
