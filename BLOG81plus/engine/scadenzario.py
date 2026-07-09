#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Articolo + email SCADENZARIO mensile (Sicurezza + HACCP)."""
import emails
BODY = '''<h1>Scadenzario Sicurezza e HACCP: tutte le scadenze che NON puoi dimenticare</h1>
<p>Una dimenticanza qui vale una multa. Ho raccolto in un solo posto le scadenze che ogni azienda deve tenere sott'occhio. Salvalo, condividilo col tuo responsabile.</p>
<h2>Scadenzario Sicurezza sul Lavoro</h2>
<ul>
<li><strong>Redazione e modifica DVR</strong>: entro 90 giorni dall'inizio attivita; entro 30 giorni da ogni modifica (es. nuove assunzioni).</li>
<li><strong>Aggiornamento formazione RLS</strong>: annuale, 4 ore (&lt;50 dipendenti) o 8 ore (&gt;50). Obbligatorio sopra i 15 dipendenti.</li>
<li><strong>Aggiornamento RSPP Datore di Lavoro</strong>: ogni 5 anni — 6h rischio basso, 10h medio, 14h alto.</li>
<li><strong>Aggiornamento Addetto Antincendio</strong>: ogni 5 anni — 5h rischio medio, 8h alto.</li>
<li><strong>Aggiornamento Addetto Primo Soccorso</strong>: ogni 3 anni, 4/6 ore.</li>
<li><strong>Aggiornamento Formazione Lavoratori</strong>: ogni 5 anni, 6 ore.</li>
<li><strong>Aggiornamento Mulettisti/Carrellisti</strong>: ogni 5 anni, 4 ore.</li>
<li><strong>Aggiornamento Dirigenti</strong>: ogni 5 anni, 6 ore. <strong>Preposti</strong>: ogni 2 anni, 6 ore.</li>
</ul>
<h2>Scadenzario HACCP</h2>
<ul>
<li><strong>Manuale di Autocontrollo</strong>: redatto dall'inizio attivita; revisione consigliata annuale o a ogni modifica.</li>
<li><strong>Formazione Alimentaristi</strong>: rinnovo variabile per Regione — verifica la tua scadenza.</li>
</ul>
<blockquote>Le scadenze non aspettano. Un presidio che te le ricorda vale piu di mille buoni propositi.</blockquote>
<h2>Non perdere piu una scadenza</h2>
<p>🔥 <a href="{promo}"><strong>Guarda i PACK81+ formazione e aggiornamenti →</strong></a> · 🎯 <a href="{audit}"><strong>Fai l'AUDIT81+ e scopri cosa ti scade →</strong></a></p>
<p>▶ <a href="{yt}" target="_blank">YouTube @sicurissimo</a> · ✈ <a href="{tg}" target="_blank">Telegram</a></p>
<p><em>— Mirco Pregnolato</em></p>'''

def article(cfg):
    L=cfg["links"]
    return BODY.format(promo=L["promo"],audit=L["audit"],yt=L["youtube"],tg=L["telegram_channel"])

def email(cfg):
    L=cfg["links"]
    subj="📌 Scadenzario del mese: sicurezza e HACCP — cosa ti scade"
    inner=article(cfg)
    return {"subject":subj,"body":"Riepilogo scadenze del mese. Dettaglio: "+cfg["site_base"]+"/blog81.html",
            "html":emails.wrap(cfg,subj,inner,cta_url=L["audit"],cta_text="Fai l'AUDIT81+ gratuito")}
