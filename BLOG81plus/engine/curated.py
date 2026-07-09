#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SPECIAL PACK 81+ — landing a FUNNEL (AIDA/EPPPA/REPPPA) con prezzi reali da listino (-30%),
countdown, Order Bump (Corso Stress -20%) dinamico, PayPal.me. Colori brand nero/bianco/arancione."""
import os, json, html
import emails
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _cfg(cfg): return cfg
def load(cfg):
    p=os.path.join(ROOT,"data","curated_packs.json")
    return json.load(open(p,encoding="utf-8")) if os.path.exists(p) else {"packs":[]}

def _landing(cfg, p, bump):
    L=cfg["links"]; handle=cfg["paypal"]["handle"]
    promo=p["promo"]; full=p["full"]; save=round(full-promo,2)
    pv=int(round(promo)); cash=round(promo*0.30)
    bump_price=bump["price"]; promo_bump=round(promo+bump_price,2)
    pay_base=f"https://www.paypal.me/{handle}/{promo:.2f}EUR"
    pay_bump=f"https://www.paypal.me/{handle}/{promo_bump:.2f}EUR"
    comps="".join(f'<li><span>{html.escape(c["n"])}</span><span class="cp">€ {c["eur"]:.0f}</span></li>' for c in p["components"])
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(p["title"])} · -{p["discount"]}% · 81+</title>
<meta name="description" content="{html.escape(p["desc"])}">
<meta property="og:title" content="{html.escape(p["title"])} — -{p["discount"]}%">
<link rel="stylesheet" href="/promo81.css">
<style>
:root{{--or:#FB6B00;--ink:#0B0B0C}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0B0B0C;background:#fff;line-height:1.55}}
.w{{max-width:820px;margin:0 auto;padding:22px 16px 80px}}
.kic{{text-align:center;color:var(--or);font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:12px}}
h1{{text-align:center;font-size:clamp(26px,5.4vw,42px);font-weight:900;line-height:1.12;margin:8px 0}}
.promise{{text-align:center;color:#555;font-size:clamp(16px,3.4vw,19px);max-width:680px;margin:0 auto 8px}}
.fear{{text-align:center;background:#0B0B0C;color:#fff;border:2px solid var(--or);border-radius:12px;padding:12px 16px;margin:16px auto;max-width:680px;font-weight:600}}
.cd{{display:flex;gap:8px;justify-content:center;margin:14px 0}}.cd div{{background:#0B0B0C;color:#fff;border-radius:12px;min-width:66px;padding:10px 6px;text-align:center}}.cd b{{display:block;font-size:26px;color:var(--or)}}.cd span{{font-size:10px;text-transform:uppercase;opacity:.75}}
.exp{{display:none;text-align:center;color:var(--or);font-weight:900;font-size:22px;margin:8px 0}}
.card{{position:relative;isolation:isolate;overflow:hidden;border-radius:18px;padding:22px;color:#f4f4f6;border:3px solid var(--or);
background:linear-gradient(160deg,#15161c,#0d0e12 55%,#1a1206),url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Ctext x='4' y='90' font-family='Arial' font-size='30' font-weight='900' fill='%23FB6B00' fill-opacity='0.11' transform='rotate(-30 60 60)'%3E81%2B%3C/text%3E%3C/svg%3E");
box-shadow:inset 0 3px 0 rgba(255,255,255,.35),inset 0 -5px 0 rgba(0,0,0,.7),0 24px 48px rgba(0,0,0,.6),0 5px 0 #000;margin:18px 0}}
.card::before{{content:'';position:absolute;inset:-40% -60%;z-index:0;background:linear-gradient(115deg,transparent 40%,rgba(255,255,255,.4) 50%,transparent 60%);transform:translateX(-40%);animation:csh 6s ease-in-out infinite}}.card::after{{content:'';position:absolute;inset:0;z-index:0;pointer-events:none;background-image:radial-gradient(1.6px 1.6px at 20% 30%,#fff,transparent),radial-gradient(1.4px 1.4px at 78% 22%,#FB6B00,transparent),radial-gradient(1.5px 1.5px at 60% 72%,#fff,transparent);opacity:.5;animation:ctw 3.2s ease-in-out infinite}}.card>*{{position:relative;z-index:1}}.card{{transition:transform .35s cubic-bezier(.2,.8,.2,1);animation:cfloat 4.5s ease-in-out infinite}}.card:hover{{transform:translateY(-6px)}}@keyframes csh{{0%,100%{{transform:translateX(-40%)}}50%{{transform:translateX(40%)}}}}@keyframes ctw{{0%,100%{{opacity:.3}}50%{{opacity:.7}}}}@keyframes cfloat{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}@media(prefers-reduced-motion:reduce){{.card,.card::before,.card::after{{animation:none}}}}.card h3{{font-size:15px;color:var(--or);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}}
.card ul{{list-style:none;display:flex;flex-direction:column;gap:7px;margin-bottom:12px}}
.card li{{display:flex;justify-content:space-between;gap:12px;font-size:15px;font-weight:600;border-bottom:1px dashed #333;padding-bottom:6px}}
.card li .cp{{color:#9a9aa6;text-decoration:line-through}}
.full{{color:#9a9aa6;text-decoration:line-through;font-size:16px}}.promo{{font-size:44px;font-weight:900;color:#fff}}
.save{{display:inline-block;background:var(--or);color:#0B0B0C;font-weight:800;border-radius:8px;padding:3px 10px;font-size:13px}}
.eco{{background:#fff;border:1px solid var(--or);border-radius:8px;padding:6px 8px;font-size:12px;color:#0B0B0C;font-weight:700;margin-top:8px;width:fit-content}}
.bump{{background:#fff7f0;border:2px dashed var(--or);border-radius:12px;padding:14px;margin:14px 0;color:#0B0B0C}}
.bump label{{display:flex;gap:10px;align-items:flex-start;cursor:pointer;font-weight:700}}
.bump input{{width:20px;height:20px;margin-top:2px}}
.bump .bp{{color:var(--or);font-weight:900}}.bump small{{display:block;color:#7a3d00;font-weight:600;margin-top:4px}}
.tot{{text-align:center;font-size:15px;color:#333;margin:6px 0}}.tot b{{font-size:22px;color:#0B0B0C}}
.cta{{display:block;text-align:center;background:linear-gradient(135deg,#ff8a2b,var(--or));color:#0B0B0C;font-weight:900;font-size:19px;text-decoration:none;padding:16px;border-radius:14px;box-shadow:0 8px 24px rgba(251,107,0,.35)}}
.seats{{text-align:center;color:var(--or);font-weight:900;text-transform:uppercase;font-size:13px;margin-top:8px}}
.sec{{max-width:700px;margin:26px auto}}.sec h2{{font-size:22px;margin-bottom:8px}}.sec p,.sec li{{color:#333;font-size:16px}}.sec ul{{padding-left:18px}}
.proof{{background:#f7f7f8;border:1px solid #E6E6E8;border-radius:14px;padding:16px}}
.chan{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:18px 0}}.chan a{{border:1.5px solid #E6E6E8;border-radius:10px;padding:10px 13px;font-weight:800;text-decoration:none;color:#0B0B0C;font-size:13px}}
.foot{{color:#8a8a92;font-size:12px;text-align:center;margin-top:24px}}
</style></head><body><div class="w">
<div class="kic">SPECIAL PACK 81+ · {html.escape(p.get("sector",""))} · {p.get("hours","")} ore · ASR 2025</div>
<h1>{html.escape(p["title"])}</h1>
<p class="promise">{html.escape(p["desc"])}</p>
<div class="fear">⚠️ Senza questi requisiti NON puoi lavorare e rischi sanzioni e chiusura attivita.</div>
<div class="cd" id="cd"><div><b data-d>00</b><span>giorni</span></div><div><b data-h>00</b><span>ore</span></div><div><b data-m>00</b><span>min</span></div><div><b data-s>00</b><span>sec</span></div></div>
<div class="exp" id="exp">⛔ Offerta chiusa</div>

<div class="card">
  <h3>Cosa contiene</h3>
  <ul>{comps}</ul>
  <div class="full">Valore pieno € {full:.2f}</div>
  <div class="promo">€ <span id="pp">{promo:.2f}</span></div>
  <div class="save">RISPARMI € {save:.2f} · -{p["discount"]}%</div>
  <div class="eco">= {pv} PV · +{pv} PV+ nel wallet · cashback 30% = {cash} PV+ · 1€ speso = 1 PV+</div>
</div>

<div class="bump">
  <label><input type="checkbox" id="bump" onchange="upd()">
  <span>SÌ, aggiungi al carrello il <span class="bp">{html.escape(bump["name"])}</span> a soli € {bump_price:.2f}
  <small>invece di € {bump["full"]:.2f} (-{bump["discount"]}%) — solo ora, in abbinamento a questo pacchetto.</small></span></label>
</div>
<div class="tot">Totale: <b>€ <span id="tot">{promo:.2f}</span></b></div>
<a class="cta" id="buy" href="{pay_base}" data-base="{pay_base}" data-bump="{pay_bump}" target="_blank" rel="nofollow">✅ ATTIVA ORA IL TUO SPECIAL PACK →</a>
<div class="seats">🔥 SOLO {p["seats"]} DISPONIBILI A QUESTO PREZZO</div>

<div class="sec"><h2>Perché adesso (Accordo Stato-Regioni 2025)</h2>
<p>Il Datore di Lavoro con i requisiti RSPP <strong>può formare direttamente lavoratori, preposti e dirigenti</strong> (ASR 7/7/2016, confermato 17/4/2025). Unendo il percorso al Corso Formatori 24h (D.I. 6/3/2013) <strong>diventi autonomo</strong>: niente più fatture di formazione ogni anno.</p></div>
<div class="sec proof"><h2>Cosa ottieni davvero</h2>
<ul><li>Sei in regola e <strong>formi i tuoi</strong> quando vuoi.</li><li>Tagli i costi di consulenza per sempre.</li><li>Documenti e attestati validi e verificabili.</li><li>Un unico pacchetto invece di comprare corso per corso.</li></ul></div>
<div class="sec"><h2>Perché 81+</h2>
<p>Oltre 32.000 aziende hanno scelto Sicurissimo, oltre 225.000 persone formate. Non un fornitore: un <strong>metodo</strong>. Leggi le <a href="/recensioni.html">recensioni reali</a>.</p></div>
<div class="sec"><h2>Garanzia & serenità</h2>
<p>Prezzo bloccato solo mentre il countdown corre e restano posti. Quello che risparmi oggi (-{p["discount"]}%) non torna. {cfg["legal"]["disclaimer"]}</p></div>

<div class="chan"><a href="{L['youtube']}" target="_blank">▶ YouTube @sicurissimo</a><a href="{L['telegram_channel']}" target="_blank">✈ Telegram</a><a href="/promo/">🔥 Tutte le offerte</a></div>
<p class="foot">{cfg['legal']['price_note']}<br>{cfg['legal']['vendor']}</p>
</div>
<script>
var PROMO={promo}, BUMP={bump_price};
function upd(){{var on=document.getElementById('bump').checked;var t=(on?PROMO+BUMP:PROMO);
 document.getElementById('tot').textContent=t.toFixed(2);
 var b=document.getElementById('buy');b.href=on?b.getAttribute('data-bump'):b.getAttribute('data-base');}}
var DL="__DL__";function pad(n){{return String(n).padStart(2,'0')}}
function tk(){{var d=new Date(DL)-new Date();if(d<=0){{document.getElementById('cd').style.display='none';document.getElementById('exp').style.display='block';var b=document.getElementById('buy');b.style.filter='grayscale(1)';b.style.pointerEvents='none';b.textContent='⛔ CHIUSO';return;}}
var s=Math.floor(d/1000);document.querySelector('[data-d]').textContent=pad(s/86400|0);document.querySelector('[data-h]').textContent=pad(s%86400/3600|0);document.querySelector('[data-m]').textContent=pad(s%3600/60|0);document.querySelector('[data-s]').textContent=pad(s%60);}}
tk();setInterval(tk,1000);
</script>
<script src="/promo81.js" defer></script><script src="/footer81.js?v=8" defer></script><script src="/header81.js?v=10" defer></script>
</body></html>'''

def publish(cfg):
    import datetime
    data=load(cfg); bump=data.get("order_bump",{"name":"Corso Stress","full":150,"discount":20,"price":119.90})
    pd=os.path.join(ROOT,cfg["publish"]["promo_dir"]); os.makedirs(pd,exist_ok=True)
    dl=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=cfg["pack"]["countdown_hours"])).isoformat()
    cards=[]
    for p in data.get("packs",[]):
        slug=f"special-{p['id'].lower()}"
        page=_landing(cfg,p,bump).replace("__DL__",dl)
        open(os.path.join(pd,f"{slug}.html"),"w",encoding="utf-8").write(page)
        cards.append({"slug":slug,"title":p["title"],"sector":p.get("sector",""),"hours":p.get("hours",""),
                      "full":p["full"],"promo":p["promo"],"discount":p["discount"]})
        try:
            out=os.path.join(ROOT,"data","promo_out");os.makedirs(out,exist_ok=True)
            json.dump(email_flow(cfg,p,bump),open(os.path.join(out,"email_special_"+p["id"].lower()+".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        except Exception as _e: print("[email special]",_e)
    return cards


def email_flow(cfg, p, bump):
    L=cfg["links"]; ef=cfg["email_flow"]; url=cfg["site_base"]+"/promo/special-"+p["id"].lower()+".html"
    subs=["Puoi formare i tuoi (e smettere di pagare consulenti): "+p["title"],
          "Perche aziende come la tua scelgono lo SPECIAL PACK "+p.get("sector",""),
          "Aggiungi il Corso Stress a -20% (solo con questo pacchetto)",
          "Ultime ore: "+p["title"]+" a -"+str(p["discount"])+"%"]
    bodies=["Con lo SPECIAL PACK 81+ diventi autonomo sulla sicurezza: Datore-RSPP + Formatore 24h. Valore EUR "+("%.0f"%p["full"])+" -> oggi EUR "+("%.2f"%p["promo"])+" (-"+str(p["discount"])+"%).",
            "Oltre 32.000 aziende hanno scelto Sicurissimo. Con questo pacchetto formi lavoratori, preposti e dirigenti da solo, quando vuoi. Solo "+str(p["seats"])+" posti a questo prezzo.",
            "Solo in abbinamento a questo pacchetto: il Corso Rischio Stress Lavoro-Correlato a EUR "+("%.2f"%bump["price"])+" invece di EUR "+("%.2f"%bump["full"])+" (-"+str(bump["discount"])+"%).",
            "Tra poche ore lo SPECIAL PACK torna a prezzo pieno (EUR "+("%.0f"%p["full"])+"). Blocca ora EUR "+("%.2f"%p["promo"])+"."]
    steps=[]
    for i in range(4):
        inner="<h1 style=\"margin:0 0 14px;font-size:24px;color:#080808;\">"+subs[i]+"</h1><p style=\"margin:0 0 14px;color:#333;\">"+bodies[i]+"</p>"
        steps.append({"step":i+1,"label":ef["steps_labels"][i],"after_h":ef["steps_hours"][i],"subject":subs[i],
                      "body":bodies[i],"html":emails.wrap(cfg,subs[i],inner,cta_url=url,cta_text="Attiva lo SPECIAL PACK")})
    return {"sequence":ef["sequence_prefix"]+"_SPECIAL_"+p["id"],"steps":steps}

def render_cards_html(cards):
    if not cards: return ""
    out='<h2 style="text-align:center;font-size:clamp(22px,5vw,30px);font-weight:900;margin:24px 0 8px">⭐ SPECIAL PACK 81+ (-30%)</h2><div class="p81grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">'
    for c in cards:
        out+=(f'<a class="p81c" href="/promo/{c["slug"]}.html"><span class="p81b">-{c["discount"]}%</span>'
              f'<b>{html.escape(c["title"])}</b><span class="p81s">{c["hours"]} ore · {html.escape(c["sector"])}</span>'
              f'<span class="p81p">€ {c["promo"]:.2f} <s>€ {c["full"]:.2f}</s></span></a>')
    out+='</div>'
    return out
