# -*- coding: utf-8 -*-
"""YTCASHCOW81+ · motore SEO virale (no API, funzioni pure).
Genera: titolo clickbait, descrizione magnetica/ipnotica super-SEO YT, hashtag, CTA prodotto rotanti.
Compliance-guard: niente 'zero multe/rischio zero/garantito'. CTA sito 81plus.net + canale + prodotto reale."""
import re,hashlib
SITE="81plus.net"
GUARD=[("zero multe","in regola"),("rischio zero","rischio ridotto"),("garantito","concreto"),("garantita","concreta"),("guadagno garantito","opportunità")]
def guard(t):
    for a,b in GUARD: t=re.sub(re.escape(a),b,t,flags=re.I)
    return t
def _seed(s): return int(hashlib.md5(s.encode()).hexdigest(),16)
CLICK=["{t}: l'errore che fanno (quasi) tutti","{t}: il dettaglio che ti costa caro","{t} spiegato semplice in 60 secondi",
 "{t}: cosa controllare DAVVERO oggi","La verità su {t} che nessuno ti dice","{t}: 3 cose da sistemare SUBITO"]
def clean_topic(title):
    t=re.sub(r"#\w+","",title); t=re.sub(r"[\|•·—-].*$","",t); t=re.sub(r"\s+"," ",t).strip()
    return t[:46].rstrip(" -") or "Sicurezza sul lavoro"
def clickbait(title,i=None):
    t=clean_topic(title); i=_seed(title) if i is None else i
    return guard(CLICK[i%len(CLICK)].format(t=t))[:95]
HOOKS=["Se lavori in azienda, questo ti riguarda.","Il 90% lo scopre troppo tardi.","Un dettaglio piccolo, un problema grande.",
 "Non è burocrazia: è la tua tranquillità.","Bastano 3 mosse per metterti in ordine."]
def pick_ctas(products,seed_str,n=2):
    if not products: return []
    s=_seed(seed_str); kws=[w for w in re.findall(r"[a-zà-ù]{4,}",seed_str.lower())]
    def score(pr):
        blob=(pr.get("name","")+" "+pr.get("area","")).lower()
        return sum(1 for w in kws if w in blob)
    ranked=sorted(products,key=lambda pr:(-score(pr),))
    rel=[pr for pr in ranked if score(pr)>0]
    pool=rel if len(rel)>=n else ranked
    out=[]; seen=set()
    for k in range(len(pool)):
        pr=pool[(s+k*7)%len(pool)]
        if pr.get("url") in seen: continue
        seen.add(pr.get("url")); out.append(pr)
        if len(out)>=n: break
    return out
def magnetic_desc(title,products,channel_handle,area=""):
    t=clean_topic(title); s=_seed(title)
    hook=HOOKS[s%len(HOOKS)]
    ctas=pick_ctas(products,title,2)
    lines=[f"🟧 {t} — spiegato semplice da Sicù81+.","",hook,
      "In questo video vedi il rischio reale e l'azione concreta per metterti in ordine, senza panico e senza parole difficili.","",
      "👉 CHECK GRATUITO della tua situazione: https://%s/?src=yt"%SITE,]
    for p in ctas:
        lines.append(f"👉 {p.get('cta','Scoprilo')}: {p.get('url')}")
    lines += [f"🔔 Iscriviti al canale {channel_handle} per un nuovo Sicù ogni giorno.","",
      "Sicurezza sul lavoro, HACCP, privacy, antincendio, DPI, formazione: un metodo semplice e ripetibile con l'ecosistema Sicurissimo81+.","",
      "Contenuto informativo. Verifica sempre il tuo caso specifico con un consulente qualificato.",
      "PV/PV+ sono utility interne 81+, non denaro né investimento (L.173/2005).","",
      hashtags(area,t)]
    return guard("\n".join(lines))
HB=["#Sicurissimo81","#81plus","#SicurezzaSulLavoro","#Prevenzione","#LavoroSicuro","#Sicù81","#Compliance"]
HA={"HACCP":["#HACCP","#IgieneAlimentare"],"Privacy":["#Privacy","#GDPR"],"Antincendio":["#Antincendio","#Emergenza"],
 "Attrezzature":["#Cantiere","#Patentino"],"DPI":["#DPI"],"Documenti":["#DVR"],"Formazione":["#Formazione","#RSPP"],
 "Elettrico":["#PES","#PAV"],"PrimoSoccorso":["#PrimoSoccorso"]}
def hashtags(area,topic=""):
    extra=[]
    for k,v in HA.items():
        if k.lower() in (area+" "+topic).lower(): extra=v; break
    return " ".join(HB+extra)
if __name__=="__main__":
    import json,sys
    prods=json.load(open(sys.argv[1],encoding="utf-8")) if len(sys.argv)>1 else []
    for demo in ["Microclima negli ambienti di lavoro","HACCP nel bar: le temperature","Carrello elevatore in magazzino"]:
        print("TITOLO:",clickbait(demo))
        print(magnetic_desc(demo,prods,"@sicurissimo","Attrezzature")[:600]); print("\n"+"="*60)

KW_BASE={"Sicurezza":["sicurezza sul lavoro","dvr","dpi","81/08","prevenzione","rspp","preposto","antincendio","formazione sicurezza"],
 "HACCP":["haccp","igiene alimentare","allergeni","temperature","autocontrollo","sanificazione","manuale haccp","ristorazione"],
 "Privacy":["privacy","gdpr","protezione dati","cyber security","password","data breach","dpo","informativa privacy"]}
def keywords(title,theme="Sicurezza",product=""):
    import re
    base=KW_BASE.get(theme,KW_BASE["Sicurezza"])[:]
    words=[w for w in re.findall(r"[a-zà-ù]{4,}", (title+" "+product).lower())]
    seen=[]; 
    for k in base+words+["sicurissimo81","81plus","metodo81","sicurix","corso online","tutorial","spiegazione semplice"]:
        if k not in seen: seen.append(k)
    return seen[:18]
def viral_title(name,theme,i=0):
    n=clean_topic(name); import re
    kw={"Sicurezza":"Sicurezza sul lavoro","HACCP":"HACCP","Privacy":"Privacy GDPR"}.get(theme,"")
    P=[f"{kw}: {n} (l'errore che quasi tutti fanno)",f"{n} — {kw} spiegato in 60 secondi",
       f"{n}: 3 cose da sistemare SUBITO | {kw}",f"{kw} · {n}: sei davvero in regola?"]
    return guard(P[i%len(P)])[:95]
