import ast
f="engine/blog_engine.py"; s=open(f,encoding="utf-8").read()

# 1) import media
s=s.replace("from images import theme_image, book_image, book_slug",
            "from images import theme_media, book_media, book_slug",1)

# 2) Groq nel llm_write (prima di Anthropic)
anchor='    ak=os.environ.get(p["anthropic_env"],"")'
groq=('    gk=os.environ.get(p.get("groq_env",""),"")\n'
      '    if gk:\n'
      '        try:\n'
      '            body=json.dumps({"model":p["model_groq"],"max_tokens":p["max_tokens"],"messages":[{"role":"system","content":sys},{"role":"user","content":user}]}).encode()\n'
      '            r=json.loads(urllib.request.urlopen(urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+gk,"content-type":"application/json"}),timeout=60).read())\n'
      '            return r["choices"][0]["message"]["content"]\n'
      '        except Exception as e: print("[llm groq]",e)\n'
      +anchor)
assert anchor in s; s=s.replace(anchor,groq,1)

# 3) articolo Corsi con video YT (nuova funzione, inserita prima di slugify)
ins='''def course_video_article(cfg, catalog):
    L=cfg["links"]; yt=cfg.get("youtube",{}); ch=yt.get("channel", L["youtube"])
    vids=yt.get("videos") or []
    if vids:
        vlist="".join('<li>&#9654; <a href="https://www.youtube.com/watch?v='+html.escape(str(v.get("id","")))+'" target="_blank" rel="noopener">'+html.escape(v.get("title","Video"))+'</a></li>' for v in vids[:6])
    else:
        vlist='<li>&#9654; <a href="'+ch+'" target="_blank">Vai al canale @sicurissimo e guarda i corsi</a></li>'
    corsi=[p for p in catalog if p.get("price",0)>0 and ("cors" in (p.get("cat","")+p.get("sub","")).lower() or "formazione" in (p.get("cat","")+p.get("sub","")).lower())][:6]
    clist="".join("<li>&#9989; "+html.escape(c["name"])+"</li>" for c in corsi)
    return ("<h1>I corsi che ogni azienda dovrebbe fare (te li spiego in video)</h1>"
      "<p>La formazione non e un obbligo da subire: e l arma che ti evita multe e ti fa lavorare sereno. Sul mio canale @sicurissimo li spiego semplici.</p>"
      "<h2>Guardali qui</h2><ul>"+vlist+"</ul>"
      "<h2>I corsi 81+ piu richiesti</h2><ul>"+clist+"</ul>"
      "<blockquote>Un lavoratore formato e un lavoratore che torna a casa. Tutto il resto viene dopo.</blockquote>"
      "<h2>Passa all azione</h2>"
      "<p>&#128293; <a href=\\""+L["promo"]+"\\"><strong>Offerte PACK81+ formazione &rarr;</strong></a> &middot; <a href=\\""+L["audit"]+"\\"><strong>AUDIT81+ gratuito &rarr;</strong></a></p>"
      "<p>&#9654; <a href=\\""+ch+"\\" target=\\"_blank\\">Iscriviti al canale @sicurissimo &rarr;</a></p>"
      "<p><em>&mdash; Mirco Pregnolato</em></p>")

'''
s=s.replace("def slugify(",ins+"def slugify(",1)

# 4) generate_article: media (img+video) + tema corsi
old=s[s.index("def generate_article("):s.index("def write_article(")]
new='''def generate_article(cfg, catalog, theme, pack_url):
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
        body=llm_write(cfg, theme, sources, pack_url) or template_article(cfg, theme, sources, pack_url)
    m=re.search(r"<h1>(.*?)</h1>", body, re.S)
    title=re.sub("<[^>]+>","",m.group(1)).strip() if m else clickbait(theme)
    excerpt=re.sub(r"\\s+"," ",re.sub("<[^>]+>","",body)).strip()[:160]
    d=now().isoformat(); slug=now().strftime("%Y%m%d")+"-"+slugify(title)
    media=book_media(cfg, book_slug(feat["name"]), feat["name"]) if feat is not None else theme_media(cfg, theme, title)
    return {"theme":theme,"title":title,"excerpt":excerpt,"html":body,"date":d,"slug":slug,"read":reading_time(body),"image":media["image"],"video":media.get("video")}

'''
s=s.replace(old,new,1)

# 5) render_article_page: hero video se presente
s=s.replace('def render_article_page(cfg, art):\n    L=cfg["links"]\n',
            'def render_article_page(cfg, art):\n    L=cfg["links"]\n'
            '    if art.get("video"):\n'
            '        heromedia=f\\'<video class="arthero" controls playsinline poster="{art["image"]}" style="width:100%"><source src="{art["video"]}" type="video/mp4"></video>\\'\n'
            '    else:\n'
            '        heromedia=f\\'<div class="arthero" style="background-image:url(\\\\\\'{art["image"]}\\\\\\')"></div>\\'\n',1)
s=s.replace('''<div class="arthero" style="background-image:url('{art['image']}')"></div>''','{heromedia}',1)

ast.parse(s); open(f,"w",encoding="utf-8").write(s); print("blog_engine: groq+media+corsiYT OK")
