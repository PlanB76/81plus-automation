#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Articoli 'CASO REALE' dalle 10k+ recensioni verificate (recensioni_seed.js -> window.RECENSIONI_SEED).
Riprova sociale = alto valore. Ogni articolo racconta un caso vero, con la recensione verbatim,
problema (obbligo/paura) -> soluzione 81+ -> CTA a PACK81+/AUDIT/canali."""
import os, re, json, random, html
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_reviews(cfg):
    root=os.path.join(ROOT, cfg["images"]["local_root"])
    fp=os.path.join(root,"recensioni_seed.js")
    if not os.path.exists(fp): return []
    s=open(fp,encoding="utf-8",errors="ignore").read()
    m=re.search(r'RECENSIONI_SEED\s*=\s*(\[.*\])\s*;?', s, re.S)
    if not m: return []
    try: return json.loads(m.group(1))
    except Exception: return []

def build(cfg, reviews):
    L=cfg["links"]
    pool=[r for r in reviews if int(r.get("r",5))>=5 and len(r.get("t",""))>120]
    if not pool: pool=reviews
    r=random.choice(pool) if pool else {"t":"Servizio concreto, ci ha messo in regola senza bloccare il lavoro.","n":"Cliente 81+","c":"Italia","cat":"Sicurezza"}
    stars="★"*int(r.get("r",5))
    cat=r.get("cat") or r.get("type") or "Sicurezza"
    title=f"«{html.escape(r['t'][:60].strip())}…» — la storia vera di {html.escape(r.get('n','un cliente').split('·')[0].strip())}"
    body=f'''<h1>Caso reale: come {html.escape(cat.lower())} è passata dall'ansia dei controlli alla serenità</h1>
<p>Oggi non ti parlo di teoria. Ti racconto una storia vera, di un'azienda come la tua. È una delle oltre
<strong>10.000 recensioni verificate</strong> che abbiamo raccolto in questi anni. L'ho scelta perché dice tutto.</p>
<h2>Il punto di partenza (forse ti ci riconosci)</h2>
<p>{html.escape(cat)}. Scadenze rimandate, il timore del controllo, la sensazione di non essere mai davvero a posto.
È la condizione in cui trovo il 90% delle aziende prima di conoscermi.</p>
<blockquote>{stars}<br>«{html.escape(r['t'])}»<br><em>— {html.escape(r.get('n','Cliente 81+'))}, {html.escape(r.get('c',''))}</em></blockquote>
<h2>Cosa è cambiato con 81+</h2>
<p>Nessuna magia: un <strong>sistema</strong>. Mettiamo ordine, prepariamo i documenti, formiamo le persone,
presidiamo le scadenze. Il risultato non è "un altro fornitore": è dormire sereni sapendo di essere in regola.</p>
<blockquote>La differenza tra chi rischia e chi è tranquillo non è la fortuna. È il metodo.</blockquote>
<h2>Vuoi lo stesso risultato?</h2>
<p>🔥 <a href="{L['promo']}"><strong>Guarda le offerte PACK81+ a tempo →</strong></a> ·
🎯 <a href="{L['audit']}"><strong>Fai l'AUDIT81+ gratuito →</strong></a></p>
<p>Ti mostro altri casi e ti spiego tutto: ▶ <a href="{L['youtube']}" target="_blank">YouTube @sicurissimo</a> ·
✈ <a href="{L['telegram_channel']}" target="_blank">Telegram</a> · 👥 <a href="{L['telegram_groups']}">gruppi</a>.</p>
<p><em>— Mirco Pregnolato</em></p>'''
    return title, body
