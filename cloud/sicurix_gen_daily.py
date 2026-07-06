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
    pairs=[]
    for i,(a,c) in enumerate(zip(atoms_sel,cast),1):
        h,v=c.split(">")
        pairs.append(f"{i}) PERICOLO '{a['adempimento']}': il cattivo {v} provoca '{a['rischio']}' con battuta breve e sotto 'Rischio: ...'; accanto SOLUZIONE 81+: l'eroe {h} applica il Metodo81+ con checklist verde.")
    return (
      "Crea una PAGINA A FUMETTI INFOGRAFICA verticale formato A4 (1024x1536), altissima qualita, stile ufficiale 'SICURIX TALES': "
      "personaggi giocattolo a mattoncini 3D renderizzati (minifigure espressive), ambientazione realistica e dettagliata del settore, "
      "TESTI IN ITALIANO GRANDI E PERFETTAMENTE LEGGIBILI (NON storpiare le parole, ortografia corretta). "
      "Palette brand 81+: nero #05050A, bianco panna, arancione #FF6A1A/#E8501A; ROSSO per 'PERICOLO', VERDE/BLU per 'SOLUZIONE 81+'. Logo '81+' su ogni riquadro. "
      f"TEMA: {sett} (ATECO {code}). "
      "STRUTTURA OBBLIGATORIA: "
      "1) HEADER: a sinistra il protagonista SICURIX (eroe con mantello, medaglione arancione '81+', bussola/checklist) che parla in un fumetto "
      f"('Ciao! Sono SICURIX. Oggi in {sett} scopriamo i pericoli e le soluzioni con il Metodo 81+!'); al centro il grande titolo 'SICURIX TALES'; "
      f"sottotitolo '{sett.upper()}: Pericolo vs Soluzione con Metodo 81+'; in alto a destra una legenda con 3 voci (spunta verde 'Sicurezza', triangolo rosso 'Rischio', scudo blu '81+ Soluzione Metodo 81+'); "
      f"sotto una fila di EROI del tema coi nomi: {', '.join(heroes[:6])}. "
      "2) CORPO: vignette NUMERATE a coppie affiancate PERICOLO (sinistra, banda rossa, cattivo NOMINATO) vs SOLUZIONE 81+ (destra, banda blu, eroe con checklist). Contenuti: "
      +" ".join(pairs)+" "
      f"3) BLOCCO in basso 'IL METODO 81+ - SICUREZZA OGNI GIORNO' con checklist verde di {len(atoms_sel)} spunte e gli EROI in fila coi nomi sotto. "
      "4) FOOTER: grande scritta 'Prima vedi. Poi sistemi.'; banner in basso con a sinistra scudo verde 'PROTEGGIAMO. PREVENIAMO. MIGLIORIAMO.' e a destra triangolo rosso 'DISATTENZIONE. RISCHI. COSTI. CAOS.'; al centro logo '81+' e '81plus.net'. "
      f"CATTIVI (coerenti col canone): {', '.join(villains)}. EROI: {', '.join(heroes)}. "
      "IMPORTANTISSIMO: replica ESATTAMENTE lo stile, i personaggi minifigure, i colori e l'impaginazione a griglia delle immagini di riferimento allegate. "
      "Ogni etichetta di testo deve essere MOLTO BREVE (1-3 parole), GRANDE, centrata, in ITALIANO con ORTOGRAFIA PERFETTA, senza parole inventate, lettere doppie errate o testo tagliato. "
      f"TESTI ESATTI da scrivere identici (nient'altro): 'SICURIX TALES', '{sett.upper()}', 'PERICOLO', 'SOLUZIONE 81+', 'Rischio:', 'Metodo 81+', 'Prima vedi. Poi sistemi.', '81plus.net', e i nomi adempimento: '"+"', '".join(a['adempimento'] for a in atoms_sel)+"'. "
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
        size=min(rng.choices([1,2,3,4,5,6],weights=[30,22,18,14,10,6])[0],k)
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
