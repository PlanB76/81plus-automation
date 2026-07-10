#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLOG81+ — VERO blog: 1 articolo/giorno con TITOLO CLICKBAIT, immagine SHOCK a tema,
firma 'Mirco Pregnolato', struttura da blog professionale, funnel + CTA obbligo-paura vs 81+.
Notizie reali via RSS. Ogni tanto un articolo sui LIBRI di Mirco (Amazon).
NIENTE link al Listino (privato): le CTA vanno a PACK81+/Offerte, AUDIT, YouTube, Telegram, social.
Header/footer universali (header81.js/footer81.js/promo81) come le altre pagine."""
import os, json, re, datetime, urllib.request, xml.etree.ElementTree as ET, html, random
from listino_loader import load_catalog
from images import theme_media, book_media, book_slug
from listino_loader import load_books
import yt
import reviews

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cfgload(): return json.load(open(os.path.join(ROOT,"config","blog81_config.json"),encoding="utf-8"))
def fondaload(cfg):
    try: return json.load(open(os.path.join(ROOT, cfg.get("fondamenta_file","config/fondamenta81.json")),encoding="utf-8"))
    except Exception: return {}
def _presell_context(cfg):
    d=fondaload(cfg)
    if not d: return ""
    met=d.get("metodo",{})
    ob="; ".join(o.get("o","")+" -> "+o.get("r","") for o in d.get("obiezioni",[]))
    return ("CONTESTO 81+ PER IL PRESELLING (usalo, non elencarlo):\n"
        "- Metodo: "+met.get("nome","Metodo 81+")+" - "+met.get("una_frase","")+"\n"
        "- Avatar: "+d.get("avatar","")+"\n"
        "- Credenze da spostare: "+"; ".join(d.get("credenze_da_spostare",[]))+"\n"
        "- Perche il comune fallisce: "+"; ".join(d.get("perche_il_comune_non_funziona",[]))+"\n"
        "- Obiezioni->risposte: "+ob+"\n"
        "- Costi nascosti: "+"; ".join(d.get("costi_nascosti_inazione",[]))+"\n"
        "- Scala offerte: AUDIT81+ gratuito -> SPECIAL PACK/PACK81+ -> Membership.\n"
        "OBIETTIVO: sposta UNA credenza, mostra il costo nascosto dell'inazione, presenta il Metodo 81+, "
        "gestisci UNA obiezione, chiudi con CTA a AUDIT81+ e alle offerte. NIENTE link al listino.")

def now(): return datetime.datetime.now(datetime.timezone.utc)

HEAD_INC='<link rel="stylesheet" href="/promo81.css">'
FOOT_INC='<script src="/promo81.js" defer></script><script src="/footer81.js?v=8" defer></script><script src="/header81.js?v=10" defer></script>'

# ---- immagine SHOCK a tema (SVG data-URI, nessun copyright) ----
THEME_ICON={}
def hero_svg(theme):
    col,ico=THEME_ICON.get(theme,("#FB6B00","⚠"))
    svg=(f"<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='500'>"
         f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
         f"<stop offset='0' stop-color='#0B0B0C'/><stop offset='1' stop-color='{col}'/></linearGradient>"
         f"<pattern id='p' width='40' height='40' patternUnits='userSpaceOnUse'>"
         f"<text x='2' y='30' font-family='Arial' font-size='22' font-weight='900' fill='#ffffff' fill-opacity='0.05'>81+</text></pattern></defs>"
         f"<rect width='1200' height='500' fill='url(#g)'/><rect width='1200' height='500' fill='url(#p)'/>"
         f"<rect y='0' width='1200' height='14' fill='{col}'/>"
         f"<text x='60' y='300' font-family='Arial' font-size='220' font-weight='900' fill='#ffffff' fill-opacity='0.12'>{ico}</text>"
         f"<text x='60' y='430' font-family='Arial' font-size='34' font-weight='900' fill='#ffffff' fill-opacity='0.9'>{html.escape(theme.upper())}</text></svg>")
    import urllib.parse as up
    return "data:image/svg+xml,"+up.quote(svg)

def fetch_rss(url, limit=6):
    try:
        req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 BLOG81+"})
        raw=urllib.request.urlopen(req,timeout=12).read()
        root=ET.fromstring(raw); items=[]
        for it in root.iter("item"):
            t=it.findtext("title") or ""; l=it.findtext("link") or ""; d=it.findtext("description") or ""
            d=re.sub("<[^>]+>","",html.unescape(d))[:300]
            if t: items.append({"title":html.unescape(t).strip(),"link":l.strip(),"desc":d.strip()})
            if len(items)>=limit: break
        return items
    except Exception as e:
        print("[rss]",url,e); return []

def gather_sources(cfg, theme):
    items=[]
    for f in cfg["blog"]["rss_by_theme"].get(theme,[]):
        items+=fetch_rss(f)
        if len(items)>=8: break
    seen=set(); out=[]
    for i in items:
        k=i["title"].lower()[:60]
        if k not in seen: seen.add(k); out.append(i)
    return out[:8]

def get_books(catalog):
    from blog_engine import cfgload as _c
    try:
        return [b for b in load_books(_c()) if "prossimi" not in b["name"].lower()]
    except Exception:
        return []

# ---- CLICKBAIT titolo ----
CLICK=["Nessuno te lo dice, ma","La verita scomoda su","Quello che rischi DAVVERO con",
 "Ho visto aziende chiudere per","3 errori che ti costano MIGLIAIA di euro su","Attenzione:","Perche il 90% sbaglia"]
def clickbait(theme, base=None):
    return f"{random.choice(CLICK)} {theme} (e come blindarti in 48 ore)"

# ---- LLM ----
def llm_write(cfg, theme, sources, pack_url, angle=None):
    p=cfg["llm"]
    sys=(f"Sei Mirco Pregnolato, fondatore di 81+/Sicurissimo, e scrivi in PRIMA PERSONA un VERO articolo di blog "
         f"(non un volantino) sul tema '{theme}'. Deve sembrare scritto da me: diretto, esperto, umano, con aneddoti e opinioni. "
         f"TITOLO clickbait ed esagerato ma vero (in <h1>). Struttura da blog professionale: gancio iniziale, "
         f"sottotitoli <h2>/<h3>, elenchi <ul>, una <blockquote> forte, chiusura con call to action. "
         f"Applica AIDA/EPPPA/REPPPA, PNL, neuro-marketing e leva emotiva OBBLIGO/PAURA vs SOLUZIONE 81+. "
         f"Usa le notizie reali fornite (cita fatti, non gossip). "
         f"CTA: NON linkare mai il listino. Rimanda a un PACK81+ in promo ({pack_url}), all'AUDIT81+ gratuito, "
         f"al canale YouTube @sicurissimo e a Telegram. HTML semplice (<h1><h2><h3><p><ul><li><blockquote><strong>), "
         f"niente <html>/<head>. 800-1100 parole, italiano.")
    sys = sys + "\n\n" + _presell_context(cfg) + (("\nANGOLO OBBLIGATO dell'articolo: " + angle) if angle else "")
    src="\n".join(f"- {s['title']}: {s['desc']}" for s in sources) or "(usa la tua esperienza e la normativa vigente)"
    user=f"NOTIZIE REALI DI OGGI:\n{src}\n\nScrivi l'articolo completo ora."
    gk=os.environ.get(p.get("groq_env",""),"")
    if gk:
        try:
            body=json.dumps({"model":p["model_groq"],"max_tokens":p["max_tokens"],"messages":[{"role":"system","content":sys},{"role":"user","content":user}]}).encode()
            r=json.loads(urllib.request.urlopen(urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+gk,"content-type":"application/json"}),timeout=60).read())
            return r["choices"][0]["message"]["content"]
        except Exception as e: print("[llm groq]",e)
    ak=os.environ.get(p["anthropic_env"],"")
    if ak:
        try:
            body=json.dumps({"model":p["model_anthropic"],"max_tokens":p["max_tokens"],"system":sys,
                "messages":[{"role":"user","content":user}]}).encode()
            r=json.loads(urllib.request.urlopen(urllib.request.Request("https://api.anthropic.com/v1/messages",
                data=body,headers={"x-api-key":ak,"anthropic-version":"2023-06-01","content-type":"application/json"}),timeout=60).read())
            return "".join(b.get("text","") for b in r.get("content",[]))
        except Exception as e: print("[llm anthropic]",e)
    ok=os.environ.get(p["openai_env"],"")
    if ok:
        try:
            body=json.dumps({"model":p["model_openai"],"max_tokens":p["max_tokens"],
                "messages":[{"role":"system","content":sys},{"role":"user","content":user}]}).encode()
            r=json.loads(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/chat/completions",
                data=body,headers={"Authorization":"Bearer "+ok,"content-type":"application/json"}),timeout=60).read())
            return r["choices"][0]["message"]["content"]
        except Exception as e: print("[llm openai]",e)
    return None

def template_article(cfg, theme, sources, pack_url, angle=None):
    L=cfg["links"]; d=fondaload(cfg)
    news="".join(f'<li><a href="{s["link"]}" target="_blank" rel="noopener">{html.escape(s["title"])}</a> - {html.escape(s["desc"][:140])}</li>' for s in sources[:4]) or "<li>Gli aggiornamenti normativi di questi giorni.</li>"
    cred=random.choice(d.get("credenze_da_spostare",["basti un corso una tantum e sei a posto per sempre"]))
    fail=random.choice(d.get("perche_il_comune_non_funziona",["il fai-da-te all'ultimo ti scopre proprio al controllo"]))
    cost=random.choice(d.get("costi_nascosti_inazione",["una sanzione e il fermo dell'attivita"]))
    ob=random.choice(d.get("obiezioni",[{"o":"costa troppo","r":"costa meno di una sola multa"}]))
    met=d.get("metodo",{}); pil="".join("<li>&#9989; "+html.escape(x)+"</li>" for x in met.get("3_pilastri",[]))
    return ("<h1>"+clickbait(theme)+"</h1>"
      "<p>Parliamoci chiaro, come tra imprenditori: se pensi che <em>"+html.escape(cred)+"</em>, questo articolo ti riguarda. Perche e' questa idea che tiene scoperte la maggior parte delle aziende, finche' non arriva il controllo.</p>"
      "<h2>La credenza che ti tiene scoperto</h2>"
      "<p>&laquo;"+html.escape(cred)+"&raquo;. Suona ragionevole. Ma nella pratica e' il modo piu' veloce per trovarti fuori regola senza accorgertene.</p>"
      "<h2>Perche' il modo comune non basta</h2>"
      "<p>"+html.escape(fail)+". E le notizie di questi giorni lo confermano:</p><ul>"+news+"</ul>"
      "<blockquote>La differenza tra chi rischia e chi dorme sereno non e' la fortuna. E' avere un sistema. Il mio si chiama 81+.</blockquote>"
      "<h2>Il costo nascosto di non fare niente</h2>"
      "<p>Non e' risparmiare: e' rimandare un conto che cresce. "+html.escape(cost)+". Piu' lo stress del &laquo;sono davvero a posto?&raquo;.</p>"
      "<h2>&laquo;"+html.escape(ob["o"])+"&raquo; - l'obiezione che sento sempre</h2>"
      "<p>"+html.escape(ob["r"])+".</p>"
      "<h2>Il Metodo 81+, in pratica</h2>"
      "<p>"+html.escape(met.get("una_frase",""))+"</p><ul>"+pil+"</ul>"
      "<h2>Il tuo prossimo passo (senza una call)</h2>"
      "<p>&#127919; <a href=\""+L["audit"]+"\"><strong>Fai l'AUDIT81+ gratuito</strong></a>: scopri in 2 minuti dove sei scoperto.</p>"
      "<p>&#128293; <a href=\""+pack_url+"\"><strong>Guarda le offerte SPECIAL PACK / PACK81+</strong></a>: metti in regola e diventa autonomo, a prezzo tagliato.</p>"
      "<p>&#9654; <a href=\""+L["youtube"]+"\" target=\"_blank\">YouTube @sicurissimo</a> &middot; &#9992; <a href=\""+L["telegram_channel"]+"\" target=\"_blank\">Telegram</a>.</p>"
      "<p><em>- Mirco</em></p>")

def book_article(cfg, books, feat=None):
    L=cfg["links"]; b=feat or (random.choice(books) if books else None)
    others="".join(f'<li><a href="{x.get("url")}" target="_blank" rel="noopener"><strong>{html.escape(x["name"])}</strong></a></li>' for x in books[:8])
    if not b:
        return "<h1>I miei libri</h1><p>In arrivo.</p>"
    title="Ho scritto un libro che puo salvarti: \u00ab"+html.escape(b['name'])+"\u00bb"
    return f'''<h1>{title}</h1>
<p>Ogni tanto mi fermo dalla consulenza e scrivo. \u00ab{html.escape(b['name'])}\u00bb nasce cosi: mettere nero su bianco quello che vedo ogni giorno sul campo.</p>
<h2>Perche l'ho scritto</h2>
<p>Perche mi sono stancato di vedere imprenditori bravissimi inciampare sugli stessi ostacoli: burocrazia, obblighi, scadenze. Qui ti spiego come trasformare un peso in un vantaggio.</p>
<blockquote>La sicurezza non e un costo. E il modo piu economico di dormire sereni.</blockquote>
<p>\U0001F4D5 <a href="{b.get('url')}" target="_blank" rel="noopener"><strong>Prendi il libro su Amazon \u2192</strong></a></p>
<h2>Tutti i miei libri</h2><ul>{others}</ul>
<h2>Dai libri ai fatti</h2>
<p>\U0001F525 <a href="{L['promo']}"><strong>Guarda le offerte PACK81+ \u2192</strong></a> \u00b7 \U0001F3AF <a href="{L['audit']}"><strong>AUDIT81+ gratuito \u2192</strong></a></p>
<p>\u25B6 <a href="{L['youtube']}" target="_blank">YouTube @sicurissimo</a> \u00b7 \u2708 <a href="{L['telegram_channel']}" target="_blank">Telegram</a></p>
<p><em>\u2014 Mirco Pregnolato</em></p>'''

def course_video_article(cfg, catalog):
    L=cfg["links"]; yt=cfg.get("youtube",{}); ch=yt.get("channel", L["youtube"])
    vids=yt.get("videos") or []
    if not vids:
        try:
            import yt as _yt; vids=_yt.fetch_channel_videos(cfg)
        except Exception: vids=[]
    if vids:
        vlist="".join('<li>&#9654; <a href="https://www.youtube.com/watch?v='+html.escape(str(v.get("id","")))+'" target="_blank" rel="noopener">'+html.escape(v.get("title","Video"))+'</a></li>' for v in vids[:6])
    else:
        vlist='<li>&#9654; <a href="'+ch+'" target="_blank">Vai al canale @sicurissimo e guarda i corsi</a></li>'
    corsi=[p for p in catalog if p.get("price",0)>0 and ("cors" in (p.get("cat","")+p.get("sub","")).lower() or "formazione" in (p.get("cat","")+p.get("sub","")).lower())][:6]
    clist="".join("<li>&#9989; "+html.escape(c["name"])+"</li>" for c in corsi)
    return ("<h1>I corsi che ogni azienda dovrebbe fare (te li spiego in video)</h1>"
      "<p>La formazione non e un obbligo da subire: e l'arma che ti evita multe e ti fa lavorare sereno. Sul mio canale @sicurissimo li spiego semplici.</p>"
      "<h2>Guardali qui</h2><ul>"+vlist+"</ul>"
      "<h2>I corsi 81+ piu richiesti</h2><ul>"+clist+"</ul>"
      "<blockquote>Un lavoratore formato e un lavoratore che torna a casa.</blockquote>"
      "<h2>Passa all'azione</h2>"
      '<p>&#128293; <a href="'+L["promo"]+'"><strong>Offerte PACK81+ formazione &rarr;</strong></a> &middot; <a href="'+L["audit"]+'"><strong>AUDIT81+ gratuito &rarr;</strong></a></p>'
      '<p>&#9654; <a href="'+ch+'" target="_blank">Iscriviti al canale @sicurissimo &rarr;</a></p>'
      "<p><em>&mdash; Mirco Pregnolato</em></p>")

def slugify(t):
    t=re.sub(r"[^a-z0-9]+","-",t.lower()).strip("-"); return t[:70]
def reading_time(htmltext):
    words=len(re.sub("<[^>]+>"," ",htmltext).split()); return max(2, round(words/200))

def _related_and_ladder(cfg, art):
    L=cfg["links"]
    try: reg=json.load(open(os.path.join(ROOT,"data","articles_registry.json"),encoding="utf-8"))["articles"]
    except Exception: reg=[]
    same=[a for a in reg if a.get("slug")!=art.get("slug") and a.get("theme")==art.get("theme")]
    rest=[a for a in reg if a.get("slug")!=art.get("slug") and a.get("theme")!=art.get("theme")]
    rel=(same+rest)[:3]; cards=""
    for a in rel:
        img=a.get("image") or ""
        cards+=('<a href="/blog/'+a["slug"]+'.html" style="flex:0 0 220px;width:220px;text-decoration:none;color:#0B0B0C;border:1px solid #E6E6E8;border-radius:12px;overflow:hidden">'
                '<span style="display:block;height:96px;background:#0B0B0C center/cover no-repeat;background-image:url('+chr(39)+img+chr(39)+')"></span>'
                '<span style="display:block;padding:8px 10px"><b style="color:#FB6B00;font-size:10px;text-transform:uppercase">'+html.escape(a.get("theme",""))+'</b>'
                '<span style="display:block;font-weight:700;font-size:13px;line-height:1.2">'+html.escape(a.get("title","")[:70])+'</span></span></a>')
    related=('<h2>Leggi anche</h2><div style="display:flex;gap:12px;overflow:auto;padding-bottom:6px">'+cards+'</div>') if rel else ''
    ladder=('<div style="background:#0B0B0C;color:#fff;border:3px solid #FB6B00;border-radius:16px;padding:18px;margin:22px 0">'
        '<div style="color:#FB6B00;font-weight:900;text-transform:uppercase;font-size:12px;letter-spacing:.1em">Il tuo prossimo passo</div>'
        '<p style="color:#eee;margin:6px 0 12px">Non serve una call. Scegli da dove partire:</p>'
        '<a href="'+L["audit"]+'" style="display:inline-block;background:#FB6B00;color:#0B0B0C;font-weight:900;text-decoration:none;padding:12px 18px;border-radius:10px;margin:4px">1) AUDIT81+ gratuito &rarr;</a> '
        '<a href="/promo/" style="display:inline-block;background:#fff;color:#0B0B0C;font-weight:900;text-decoration:none;padding:12px 18px;border-radius:10px;margin:4px">2) SPECIAL PACK / PACK81+ &rarr;</a> '
        '<a href="/membership.html" style="display:inline-block;background:transparent;color:#fff;border:1.5px solid #fff;font-weight:800;text-decoration:none;padding:12px 18px;border-radius:10px;margin:4px">3) Membership 81+ &rarr;</a></div>')
    return related+ladder

def render_article_page(cfg, art):
    L=cfg["links"]
    related_html=_related_and_ladder(cfg, art)
    if art.get("video"):
        heromedia=f'<video class="arthero" controls playsinline poster="{art["image"]}" style="width:100%"><source src="{art["video"]}" type="video/mp4"></video>'
    else:
        heromedia=f'<div class="arthero" style="background-image:url(\'{art["image"]}\')"></div>'
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(art["title"])} · Blog 81+</title>
<meta name="description" content="{html.escape(art["excerpt"])}">
<meta property="og:title" content="{html.escape(art["title"])}"><meta property="og:type" content="article">
<meta property="og:image" content="{art['image'] if art['image'].startswith('http') else cfg['site_base']}">
{HEAD_INC}
<style>.artwrap{{max-width:760px;margin:0 auto;padding:18px 18px 70px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0B0B0C;line-height:1.7}}
.arthero{{border-radius:16px;overflow:hidden;margin:10px 0 6px;aspect-ratio:12/5;background:#0B0B0C center/cover no-repeat}}
.artwrap h1{{font-size:clamp(26px,5.4vw,40px);font-weight:900;line-height:1.12;margin:14px 0 6px}}
.artwrap h2{{font-size:24px;margin:26px 0 8px}}.artwrap h3{{font-size:19px;margin:20px 0 6px}}
.artwrap p,.artwrap li{{font-size:17.5px;color:#222}}.artwrap blockquote{{border-left:4px solid #FB6B00;margin:18px 0;padding:8px 16px;color:#333;font-style:italic;background:#fff7f0;font-size:19px}}
.artwrap a{{color:#E8501A;font-weight:600}}.byline{{display:flex;align-items:center;gap:10px;color:#6E6E76;font-size:14px;margin:6px 0 8px}}
.byline .av{{width:38px;height:38px;border-radius:50%;background:#FB6B00;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900}}
.share{{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0;border-top:1px solid #eee;padding-top:16px}}
.share a{{border:1.5px solid #E6E6E8;border-radius:10px;padding:9px 12px;font-weight:800;text-decoration:none;color:#0B0B0C;font-size:13px}}</style></head>
<body>
<div class="artwrap">
<a href="/blog81.html" style="color:#6E6E76;text-decoration:none">← Blog 81+</a>
{heromedia}
<div style="color:#FB6B00;font-weight:800;letter-spacing:.12em;text-transform:uppercase;font-size:12px">{art['theme']}</div>
{art["html"].split('</h1>',1)[0]+'</h1>' if '</h1>' in art['html'] else '<h1>'+html.escape(art['title'])+'</h1>'}
<div class="byline"><span class="av">MP</span><span><strong>Mirco Pregnolato</strong> · {art['date'][:10]} · {art['read']} min di lettura</span></div>
{art["html"].split('</h1>',1)[1] if '</h1>' in art['html'] else art['html']}
{related_html}
<div class="share"><a href="{L['youtube']}" target="_blank">▶ YouTube</a><a href="{L['telegram_channel']}" target="_blank">✈ Telegram</a><a href="{L['telegram_groups']}">👥 Gruppi</a><a href="{L['instagram']}" target="_blank">📸 Instagram</a><a href="/promo/">🔥 Offerte</a></div>
</div>
{FOOT_INC}
</body></html>'''

def generate_article(cfg, catalog, theme, pack_url, angle=None):
    feat=None; sources=[]
    if theme=="I Libri di Mirco Pregnolato":
        books=get_books(catalog); feat=random.choice(books) if books else None
        body=book_article(cfg, books, feat)
    elif theme=="Casi reali (recensioni)":
        _t,body=reviews.build(cfg, reviews.load_reviews(cfg))
    elif theme=="Corsi di Formazione (video YT)":
        body=course_video_article(cfg, catalog)
    else:
        sources=gather_sources(cfg, theme)
        body=llm_write(cfg, theme, sources, pack_url, angle) or template_article(cfg, theme, sources, pack_url, angle)
    m=re.search(r"<h1>(.*?)</h1>", body, re.S)
    title=re.sub("<[^>]+>","",m.group(1)).strip() if m else clickbait(theme)
    excerpt=re.sub(r"\s+"," ",re.sub("<[^>]+>","",body)).strip()[:160]
    d=now().isoformat(); slug=now().strftime("%Y%m%d")+"-"+slugify(title)
    media=book_media(cfg, book_slug(feat["name"]), feat["name"]) if feat is not None else theme_media(cfg, theme, title)
    return {"theme":theme,"title":title,"excerpt":excerpt,"html":body,"date":d,"slug":slug,"read":reading_time(body),"image":media["image"],"video":media.get("video")}

def write_article(cfg, art):
    bd=os.path.join(ROOT, cfg["publish"]["blog_dir"]); os.makedirs(bd,exist_ok=True)
    open(os.path.join(bd,f"{art['slug']}.html"),"w",encoding="utf-8").write(render_article_page(cfg,art))
    idx=os.path.join(ROOT,"data","articles_registry.json")
    reg=json.load(open(idx,encoding="utf-8")) if os.path.exists(idx) else {"articles":[]}
    reg["articles"].insert(0,{k:art[k] for k in ("theme","title","excerpt","date","slug","read","image")})
    reg["articles"]=reg["articles"][:200]
    json.dump(reg,open(idx,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    # articles.json PUBBLICO per il ticker
    pub=[{"t":a["title"],"u":f"/blog/{a['slug']}.html","c":a["theme"],"i":a.get("image","")} for a in reg["articles"][:40]]
    json.dump(pub,open(os.path.join(bd,"articles.json"),"w",encoding="utf-8"),ensure_ascii=False)
    return reg

def render_blog_index(cfg, articles, promo_block):
    L=cfg["links"]
    def card(a):
        return (f'<a class="ba" href="/blog/{a["slug"]}.html">'
                f'<div class="baimg" style="background-image:url(\'{a.get("image") or hero_svg(a["theme"])}\')"></div>'
                f'<div class="bap"><span class="bt">{a["theme"]}</span>'
                f'<h3>{html.escape(a["title"])}</h3><p>{html.escape(a["excerpt"])}…</p>'
                f'<span class="bd">di Mirco Pregnolato · {a["date"][:10]} · {a.get("read",4)} min</span></div></a>')
    cards="".join(card(a) for a in articles[:30])
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blog 81+ · Sicurezza, HACCP, Privacy, Appalti, Formazione, Crescita</title>
<meta name="description" content="Il blog di Mirco Pregnolato e 81+: notizie vere e utili su sicurezza sul lavoro, HACCP, privacy, gare di appalto, formazione, economia. Ogni giorno un articolo che ti mette al riparo.">
{HEAD_INC}
<style>.bwrap{{max-width:1080px;margin:0 auto;padding:20px 16px 70px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0B0B0C}}
.bhero{{background:#0B0B0C;color:#fff;padding:40px 18px;text-align:center;border-radius:0 0 18px 18px}}
.bhero .k{{color:#FB6B00;font-weight:800;letter-spacing:.16em;text-transform:uppercase;font-size:12px}}
.bhero h1{{font-size:clamp(28px,6vw,44px);font-weight:900;margin:8px 0}}.bhero p{{color:#b9b9c4;max-width:720px;margin:0 auto}}
.bgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}}@media(max-width:820px){{.bgrid{{grid-template-columns:1fr}}}}
a.ba{{display:flex;flex-direction:column;background:#fff;border:1.5px solid #E6E6E8;border-radius:14px;overflow:hidden;text-decoration:none;color:#0B0B0C}}
a.ba:hover{{border-color:#FB6B00;box-shadow:0 10px 26px rgba(0,0,0,.08)}}
.baimg{{aspect-ratio:12/5;background:#0B0B0C center/cover no-repeat}}.bap{{padding:14px}}
.bt{{color:#FB6B00;font-weight:800;font-size:12px;text-transform:uppercase}}a.ba h3{{margin:4px 0;font-size:18px;line-height:1.2}}
a.ba p{{color:#555;font-size:14px}}.bd{{color:#9a9aa6;font-size:12px}}
.bchan{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:18px 0}}
.bchan a{{border:1.5px solid #E6E6E8;border-radius:10px;padding:9px 12px;font-weight:800;text-decoration:none;color:#0B0B0C;font-size:13px}}</style></head>
<body>
<div class="bhero"><div class="k">Blog 81+ · di Mirco Pregnolato</div>
<h1>Ogni giorno, quello che devi sapere per stare in regola</h1>
<p>Sicurezza sul lavoro, HACCP, privacy, gare di appalto, formazione, crescita ed economia.
Notizie vere, zero fuffa, con la soluzione già pronta.</p></div>
<div class="bwrap">
{promo_block}
<div class="bchan"><a href="{L['youtube']}" target="_blank">▶ YouTube @sicurissimo</a><a href="{L['telegram_channel']}" target="_blank">✈ Canale Telegram</a><a href="{L['telegram_groups']}">👥 Gruppi</a><a href="/promo/">🔥 Offerte</a></div>
<h2 style="margin-top:24px">Ultimi articoli</h2>
<div class="bgrid">{cards}</div>
</div>
{FOOT_INC}
</body></html>'''

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--theme"); a=ap.parse_args()
    cfg=cfgload(); cat=load_catalog(cfg)
    rot=cfg["blog"]["themes_rotation"]
    theme=a.theme or rot[now().timetuple().tm_yday % len(rot)]
    art=generate_article(cfg,cat,theme,cfg["links"]["promo"])
    reg=write_article(cfg,art)
    pb=os.path.join(ROOT,cfg["publish"]["promo_dir"],"_promo_block.html")
    promo=open(pb,encoding="utf-8").read() if os.path.exists(pb) else ""
    open(os.path.join(ROOT,cfg["publish"]["blog_index"]),"w",encoding="utf-8").write(render_blog_index(cfg,reg["articles"],promo))
    print("articolo:",art["title"]); print("blog81.html:",len(reg["articles"]),"articoli")
