#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legge il LISTINO81+ UFFICIALE (data/catalog_data.js -> window.LISTINO81_DATA)
e lo normalizza. Fallback su seed locale. Mappa ogni voce a un 'tema' 81+."""
import re, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THEME_KEYS = {
    "sicurezza": ["sicurezza","antincendio","rls","rspp","aspp","dpi","primo soccorso","datori","preposti","ponteggi","quota"],
    "haccp":     ["haccp","alimentare","food"],
    "privacy":   ["privacy","gdpr"],
    "elettrico": ["elettric","pes","pav","pei"],
    "formazione":["corso","corsi","formazione","school","academy","master","lezione"],
    "presidio":  ["sigillo","compliance","dashboard","audit","documenti","membership","pass","kit","pack"],
    "starter":   ["plp","tripwire","gadget","shop","network","api","sdk","welfare"]
}

def theme_of(cat, sub, tags):
    blob = " ".join([str(cat or ""), str(sub or ""), " ".join(tags or [])]).lower()
    for th, keys in THEME_KEYS.items():
        if any(k in blob for k in keys):
            return th
    return "presidio"

def load_catalog(cfg):
    js = os.path.join(ROOT, cfg["listino"]["catalog_js"])
    products = []
    if os.path.exists(js):
        s = open(js, encoding="utf-8", errors="ignore").read()
        m = re.search(r'window\.LISTINO81_DATA\s*=\s*(\[.*\])\s*;?\s*$', s, re.S) \
            or re.search(r'(\[\s*\{.*\}\s*\])', s, re.S)
        raw = json.loads(m.group(1))
        for d in raw:
            eur = d.get("eur")
            if not isinstance(eur, (int, float)) or eur <= 0:
                continue
            products.append({
                "id": d.get("code") or (d.get("n","")[:40]),
                "name": d.get("n",""),
                "cat": d.get("cat",""),
                "sub": d.get("sub",""),
                "price": float(eur),
                "recurring": bool(d.get("ricorrente")),
                "url": d.get("url") or cfg["listino"]["listino_page"],
                "theme": theme_of(d.get("cat"), d.get("sub"), d.get("t"))
            })
    if not products:
        seed = os.path.join(ROOT, cfg["listino"]["seed_fallback"])
        if os.path.exists(seed):
            for p in json.load(open(seed, encoding="utf-8"))["products"]:
                p.setdefault("recurring", False)
                p.setdefault("theme", theme_of(p.get("category"), "", []))
                products.append(p)
    return products

if __name__ == "__main__":
    cfg = json.load(open(os.path.join(ROOT, "config", "blog81_config.json"), encoding="utf-8"))
    ps = load_catalog(cfg)
    from collections import Counter
    print("vendibili:", len(ps))
    print("per tema:", dict(Counter(p["theme"] for p in ps)))

def load_books(cfg):
    import re as _re
    js=os.path.join(ROOT, cfg["listino"]["catalog_js"])
    out=[]
    if os.path.exists(js):
        raw=open(js,encoding="utf-8",errors="ignore").read()
        m=_re.search(r'window\.LISTINO81_DATA\s*=\s*(\[.*\])\s*;?\s*$', raw, _re.S) or _re.search(r'(\[\s*\{.*\}\s*\])', raw, _re.S)
        for d in json.loads(m.group(1)):
            blob=(str(d.get("cat",""))+str(d.get("sub",""))+" ".join(d.get("t") or [])+str(d.get("n",""))).lower()
            url=d.get("url") or ""
            if ("libr" in blob or "pregnolato" in blob or "amzn" in url.lower() or "amazon" in url.lower()) and url:
                out.append({"name":d.get("n",""),"url":url,"cat":d.get("cat",""),"price":d.get("eur") or 0})
    return out
