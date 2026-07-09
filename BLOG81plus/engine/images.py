#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Media reali per gli articoli: IMMAGINI e VIDEO.
Priorita immagine: file locale -> Pixabay (con PIXABAY_API_KEY) -> Openverse (no key) -> SVG a tema.
Video: Pixabay video (con PIXABAY_API_KEY) -> nessuno.
Libri: copertina locale /img/libri/<slug>.(jpg|png|webp) -> mockup SVG."""
import os, json, re, glob, urllib.request, urllib.parse, html
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COL={"Sicurezza del Lavoro":"#FB6B00","Igiene Alimentare HACCP":"#FB6B00","Privacy & GDPR":"#FB6B00",
 "Gare di Appalto":"#FB6B00","Crescita Personale":"#FB6B00","Corsi di Formazione":"#FB6B00",
 "Economia Personale":"#FB6B00","SICURIX":"#FB6B00"}

def _svg(theme, subtitle=""):
    sub=html.escape((subtitle or "")[:46])
    rot=(abs(hash(subtitle or theme))%24)-12
    svg=(f"<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='500'>"
         f"<rect width='1200' height='500' fill='#0B0B0C'/><rect width='1200' height='14' fill='#FB6B00'/>"
         f"<text x='60' y='250' font-family='Arial' font-size='190' font-weight='900' fill='#FB6B00' fill-opacity='0.1' transform='rotate({rot} 300 220)'>81+</text>"
         f"<text x='60' y='300' font-family='Arial' font-size='30' font-weight='900' fill='#FB6B00'>{html.escape(theme.upper())}</text>"
         f"<text x='60' y='360' font-family='Arial' font-size='26' font-weight='700' fill='#ffffff' fill-opacity='0.92'>{sub}</text></svg>")
    return "data:image/svg+xml,"+urllib.parse.quote(svg)

def _book_mockup(title):
    t=html.escape(title[:60])
    svg=(f"<svg xmlns='http://www.w3.org/2000/svg' width='800' height='500'>"
         f"<rect width='800' height='500' fill='#0B0B0C'/><rect x='300' y='60' width='200' height='300' rx='6' fill='#FB6B00'/>"
         f"<rect x='300' y='60' width='16' height='300' fill='#0B0B0C'/>"
         f"<text x='320' y='120' font-family='Georgia' font-size='16' font-weight='700' fill='#0B0B0C'>{t[:22]}</text>"
         f"<text x='320' y='150' font-family='Georgia' font-size='13' fill='#0B0B0C'>Mirco Pregnolato</text>"
         f"<text x='400' y='420' text-anchor='middle' font-family='Arial' font-size='18' fill='#fff'>Su Amazon</text></svg>")
    return "data:image/svg+xml,"+urllib.parse.quote(svg)

def _local(cfg, webdir, slug):
    root=os.path.join(ROOT, cfg["images"]["local_root"]); d=webdir.strip("/")
    for ext in ("jpg","jpeg","png","webp"):
        h=glob.glob(os.path.join(root, d, f"{slug}.{ext}"))
        if h: return webdir.rstrip("/")+"/"+os.path.basename(h[0])
    return None

def _pixabay_img(cfg, q):
    k=os.environ.get(cfg["images"]["pixabay_env"],"").strip()
    if not k: return None
    try:
        import random as _r;u=f"https://pixabay.com/api/?key={k}&q={urllib.parse.quote(q)}&image_type=photo&orientation=horizontal&safesearch=true&per_page=20&page=1";
        r=json.loads(urllib.request.urlopen(u,timeout=12).read()); h=r.get("hits",[])
        if h:
            import random as _r2;x=_r2.choice(h);return x.get("largeImageURL") or x.get("webformatURL")
    except Exception as e: print("[pixabay img]",e)
    return None

def _pixabay_video(cfg, q):
    k=os.environ.get(cfg["images"]["pixabay_env"],"").strip()
    if not k or not cfg["images"].get("enable_video"): return None
    try:
        u=f"https://pixabay.com/api/videos/?key={k}&q={urllib.parse.quote(q)}&per_page=3&safesearch=true"
        r=json.loads(urllib.request.urlopen(u,timeout=12).read()); h=r.get("hits",[])
        if h:
            v=h[0].get("videos",{})
            return (v.get("medium") or v.get("small") or {}).get("url")
    except Exception as e: print("[pixabay video]",e)
    return None

def _openverse_img(q):
    try:
        u="https://api.openverse.org/v1/images/?page_size=1&q="+urllib.parse.quote(q)
        r=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"BLOG81+"}),timeout=12).read())
        res=r.get("results",[])
        if res: return res[0].get("url") or res[0].get("thumbnail")
    except Exception as e: print("[openverse]",e)
    return None


def _pexels_img(cfg, q):
    k=os.environ.get(cfg["images"].get("pexels_env","PEXELS_API_KEY"),"").strip()
    if not k: return None
    try:
        import random as _r;u="https://api.pexels.com/v1/search?per_page=1&orientation=landscape&page="+str(_r.randint(1,8))+"&query="+urllib.parse.quote(q)
        r=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={"Authorization":k}),timeout=12).read())
        ph=r.get("photos",[])
        if ph: return ph[0]["src"].get("large") or ph[0]["src"].get("original")
    except Exception as e: print("[pexels img]",e)
    return None

def _pexels_video(cfg, q):
    k=os.environ.get(cfg["images"].get("pexels_env","PEXELS_API_KEY"),"").strip()
    if not k or not cfg["images"].get("enable_video"): return None
    try:
        u="https://api.pexels.com/videos/search?per_page=1&orientation=landscape&query="+urllib.parse.quote(q)
        r=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={"Authorization":k}),timeout=12).read())
        vids=r.get("videos",[])
        if vids:
            files=sorted(vids[0].get("video_files",[]), key=lambda x:0 if x.get("quality")=="hd" else 1)
            for vf in files:
                if vf.get("file_type")=="video/mp4": return vf.get("link")
    except Exception as e: print("[pexels video]",e)
    return None

def _query(cfg, theme, title=""):
    blob=(theme+" "+title).lower()
    for k,q in cfg["images"].get("keyword_query",{}).items():
        if k in blob: return q
    return cfg["images"]["theme_query"].get(theme, theme)

def theme_media(cfg, theme, title=""):
    key=re.sub(r"[^a-z0-9]+","-",theme.lower()).strip("-"); q=_query(cfg,theme,title)
    img=_local(cfg,cfg["images"]["theme_img_dir"],key) or _pexels_img(cfg,q) or _pixabay_img(cfg,q) or _openverse_img(q) or _svg(theme,title)
    vid=_pexels_video(cfg,q) or _pixabay_video(cfg,q)
    return {"image":img,"video":vid}

def book_media(cfg, slug, title):
    return {"image": _local(cfg,cfg["images"]["book_cover_dir"],slug) or _book_mockup(title), "video":None}

def book_slug(name):
    return re.sub(r"[^a-z0-9]+","-",name.lower()).strip("-")[:50]
