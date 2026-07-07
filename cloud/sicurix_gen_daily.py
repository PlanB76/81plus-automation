# -*- coding: utf-8 -*-
"""SICURIX GEN DAILY (cloud) - genera N pagine/giorno diverse dal power set globale, casting random dei 49 personaggi.
Ogni riga: image_prompt (pagina fumetto vignette stile SICURIX) + titolo_clickbait + corpo_post (PNL/neuromarketing) + CTA prodotto listino81+ + hashtag.
Portabile: legge/scrive tutto dentro il repo (cloud/data, cloud/out). Stato anti-ripetizione committato -> nel tempo copre lo spazio.
USO: python sicurix_gen_daily.py [N]      (default 1000)"""
import json,csv,os,sys,random,datetime,pathlib
HERE=pathlib.Path(__file__).resolve().parent
DATA=HERE/"data"; OUTD=HERE/"out"; OUTD.mkdir(exist_ok=True)
ATOMS_CSV=DATA/"sicurix_vignette_atoms.csv"; CHARS=json.load(open(DATA/"sicurix_characters.json",encoding="utf-8"))
STATE=DATA/"sicurix_gen_state.json"; MANIFEST=OUTD/"SICURIX_GEN_MANIFEST.csv"
DRIVE=os.environ.get("SICURIX_DRIVE","https://drive.google.com/drive/folders/1hICKXdl9JTZBL1pemG19oE_661z-EH_k")
SITE="81plus.net"
HEROES=[c for c in CHARS if c.get("group")=="EROI"]
def area_vill(area):
    g={"Sicurezza":("CATTIVI SICUREZZA","CATTIVI UNIVERSALI"),"HACCP":("CATTIVI HACCP","CATTIVI UNIVERSALI"),
       "Privacy":("CATTIVI PRIVACY","CATTIVI UNIVERSALI"),"Ambientale":("CATTIVI UNIVERSALI",)}.get(area,("CATTIVI UNIVERSALI",))
    return [c for c in CHARS if c.get("group") in g] or [c for c in CHARS if c.get("group","").startswith("CATTIVI")]
def load_atoms():
    idx={}
    with open(ATOMS_CSV,encoding="utf-8") as f:
        for r in csv.DictReader(f): idx.setdefault(r["codice_ateco"],[]).append(r)
    return idx
ATOMS=load_atoms(); CODES=list(ATOMS.keys())
def load_state():
    if STATE.exists():
        try: return set(json.load(open(STATE,encoding="utf-8")))
        except: return set()
    return set()
def save_state(s): json.dump(sorted(s),open(STATE,"w",encoding="utf-8"))
# ---- PNL / neuromarketing: gancio curiosita + loss aversion + autorita/norma + specificita ----
HOOKS=["Quello che l'ispettore controlla per primo in {s} (e quasi nessuno lo sa)",
       "In {s} c'e' un obbligo che in tanti scoprono solo con la sanzione",
       "{s}: 3 minuti oggi o un problema enorme domani. Scegli tu.",
       "La differenza tra chi in {s} dorme sereno e chi trema al controllo",
       "In {s} non e' 'se' arriva il controllo, e' 'quando'. Sei pronto?"]
CLOSERS=["Non e' burocrazia: e' la tua tranquillita.","Chi si mette in regola prima, dorme meglio dopo.",
         "Mettere ordine ora costa poco. Rimediare dopo costa caro.","La regola c'e' gia': tu falla lavorare per te."]
def copy_pnl(sett,temi,pr,rng):
    hook=rng.choice(HOOKS).format(s=sett); closer=rng.choice(CLOSERS)
    return (f"{hook}\n\nIn {sett.lower()} gli adempimenti obbligatori non aspettano: {temi}. "
            f"In questa pagina TALES OF SICURIX il PERICOLO prende forma... e il METODO81+ lo rimette in ordine, passo dopo passo. "
            f"Immagina la scena: prima il caos, poi la checklist che sistema tutto. {closer}\n"
            f"\U0001F449 {pr['cta']}: {pr['prodotto']} -> {pr['url']}\n"
            f"\u25B6\uFE0F YouTube: youtube.com/@sicurissimo\n"
            f"Contenuto informativo. Prima vedi. Poi sistemi. {SITE}")
def image_prompt(code,sett,atoms_sel,cast):
    heroes=list(dict.fromkeys([c.split(">")[0] for c in cast]))
    villains=list(dict.fromkeys([c.split(">")[1] for c in cast]))
    beats=[]
    for i,(a,c) in enumerate(zip(atoms_sel,cast),1):
        h,v=c.split(">")
        beats.append(f"{i}) {v} causa il pericolo '{a['rischio']}' ({a['adempimento']}); poi {h}+SICURIX applicano il METODO81+")
    story="; ".join(beats)
    return (
      "Crea una PAGINA A FUMETTI a STORIA COMPLETA, verticale A4 (1024x1536), QUALITA' EDITORIALE DA STAMPA, "
      "stile ufficiale 'SICURIX TALES' IDENTICO alle immagini di riferimento allegate (stessi personaggi a mattoncini 3D, stessa impaginazione, stessi colori, stesse rese): "
      "minifigure espressive, ambientazioni ricche e dettagliate del settore, luci morbide, profondita', bordi vignetta netti. "
      "IMPAGINAZIONE OBBLIGATORIA: da 10 a 12 VIGNETTE numerate che raccontano UNA STORIA con arco narrativo completo "
      "(1 situazione normale -> 2-4 arrivano i pericoli coi cattivi -> 5-6 tensione/conseguenza -> 7-9 arriva SICURIX con gli eroi e applica il METODO81+ passo per passo -> 10-11 risoluzione ordinata -> 12 finale). "
      f"HEADER in alto: SICURIX (mantello, medaglione arancione '81+', bussola) che presenta in un fumetto; grande titolo 'SICURIX TALES'; sottotitolo '{sett.upper()}: Pericolo vs Soluzione con Metodo 81+'; legenda 3 voci (verde Sicurezza, rosso Rischio, blu 81+ Soluzione); fila di EROI coi nomi: {', '.join(heroes[:6])}. "
      "FOOTER in basso: grande 'Prima vedi. Poi sistemi.'; banner scudo verde 'PROTEGGIAMO. PREVENIAMO. MIGLIORIAMO.' e triangolo rosso 'DISATTENZIONE. RISCHI. COSTI. CAOS.'; logo '81+' + '81plus.net'. "
      "TRAMA (usa questi eventi come vignette; se sono meno di 10 aggiungi vignette di contesto, dialogo e reazione per arrivare a 10-12): "+story+". "
      "PALETTE BRAND ESCLUSIVA: nero #05050A, bianco panna, arancione #FF6A1A/#E8501A; ROSSO solo per 'PERICOLO', VERDE per la checklist 'Metodo 81+'. Logo '81+' ben visibile in OGNI vignetta. "
      "REGOLA STORIA: SICURIX NON agisce mai da solo - in OGNI vignetta di soluzione si fa AIUTARE dai suoi colleghi EROI (lavoro di squadra, ognuno col suo ruolo). "
      "TESTO: didascalie e fumetti MOLTO BREVI (1-4 parole), GRANDI, centrati, in ITALIANO con ORTOGRAFIA PERFETTA, senza parole inventate, lettere doppie errate o testo tagliato. "
      f"CATTIVI (coerenti col canone): {', '.join(villains)}. EROI: {', '.join(heroes)}. "
      "NEGATIVE: nessun marchio LEGO reale, nessun personaggio protetto (Asterix ecc.), niente gore/horror, niente claim assoluti ('rischio zero','garantito','zero multe').")
def build(code,idxs,rng):
    ats=ATOMS[code]; sel=[ats[i] for i in idxs]; sett=sel[0]["settore"]; sez=sel[0]["sezione"]
    mix="+".join(dict.fromkeys(a["area"] for a in sel))
    cast=[]
    for a in sel:
        h=rng.choice(HEROES); v=rng.choice(area_vill(a["area"])); cast.append(f"{h['name']}>{v['name']}")
    temi=", ".join(dict.fromkeys(a["rischio"] for a in sel))
    pr={"prodotto":sel[0]["prodotto"],"cta":sel[0]["prodotto_cta"],"url":sel[0]["prodotto_url"]}
    if len(sel)==1: titolo=f"{sett}: la verita su {sel[0]['adempimento']} (in 30 secondi)"
    else: titolo=rng.choice(HOOKS).format(s=sett)
    areas=list(dict.fromkeys(a["area"] for a in sel))
    htag=" ".join(dict.fromkeys(["#TalesOfSicurix","#SICURIX","#Metodo81","#81plus","#Sicurissimo"]+[f"#{x}" for x in areas]+["#SicurezzaSulLavoro"]))
    return {"codice_ateco":code,"settore":sett,"sezione":sez,"area_mix":mix,"n_vignette":len(sel),
            "adempimenti":" | ".join(a["adempimento"] for a in sel),"fonti":" | ".join(dict.fromkeys(a["fonte_normativa"] for a in sel)),
            "cast_personaggi":", ".join(cast),"image_prompt":image_prompt(code,sett,sel,cast),
            "titolo_clickbait":titolo,"corpo_post":copy_pnl(sett,temi,pr,rng),
            "cta_prodotto":pr["prodotto"],"cta_url":pr["url"],"hashtag":htag,
            "nome_file_webp":f"SICURIX_TALES_{code.replace('.','')}_{'_'.join(str(i) for i in idxs)}.webp","drive_folder":DRIVE,"stato":"DA_GENERARE_IMG"}
def sig(code,idxs): return code+"#"+",".join(map(str,sorted(idxs)))
def run(n,seed=None):
    rng=random.Random(seed if seed is not None else datetime.datetime.now().timestamp())
    done=load_state(); rows=[]; tries=0; mx=n*80
    while len(rows)<n and tries<mx:
        tries+=1; code=rng.choice(CODES); k=len(ATOMS[code])
        size=min(k, rng.choice([10,11,12]))
        idxs=rng.sample(range(k),size); s=sig(code,idxs)
        if s in done: continue
        done.add(s); rows.append(build(code,idxs,rng))
    save_state(done)
    cols=["codice_ateco","settore","sezione","area_mix","n_vignette","adempimenti","fonti","cast_personaggi","image_prompt","titolo_clickbait","corpo_post","cta_prodotto","cta_url","hashtag","nome_file_webp","drive_folder","stato"]
    stamp=datetime.date.today().isoformat()
    outp=OUTD/f"SICURIX_GEN_{stamp}.csv"
    exists=outp.exists()
    with open(outp,"a" if exists else "w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols)
        if not exists: w.writeheader()
        w.writerows(rows)
    newf=not MANIFEST.exists()
    with open(MANIFEST,"a",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["data"]+cols)
        if newf: w.writeheader()
        for r in rows: w.writerow({"data":stamp,**r})
    tot=sum(2**len(v)-1 for v in ATOMS.values())
    print(f"Generate {len(rows)} pagine NUOVE -> {outp.name}")
    print(f"Totale prodotte (stato): {len(done):,} / power set {tot:,} | restano {tot-len(done):,}")
if __name__=="__main__":
    run(int(sys.argv[1]) if len(sys.argv)>1 else 1000)
