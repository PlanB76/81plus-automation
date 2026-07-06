# -*- coding: utf-8 -*-
"""TALES OF SICURIX · ATECO — genera 50 pagine/giorno (progressive) per le 1.290 sottocategorie ATECO 2025.
Per ogni pagina: 28 campi scheda + prompt immagine/video/fumetto + caption + hashtag + nome file + cartella Drive + stato.
Personaggi dal canone SICURIX_CHARACTERS.json (anti-ripetizione per tipo attività). Indice con stato, blocchi da 50, JSON/CSV/report.
Le IMMAGINI le genera ChatGPT e le salva in WebP sul Drive; qui si produce il BRIEF completo per ogni pagina."""
import json,csv,os,sys,re,datetime,pathlib
HERE=pathlib.Path(os.environ.get("SICU_DIR") or pathlib.Path(__file__).resolve().parent)
ATECO=os.environ.get("ATECO_JSON","/sessions/friendly-festive-wright/mnt/81PLUS_GLOBAL_MASTER/81plus.net/ATECO81+/ateco81_master.json")
DRIVE=os.environ.get("ATECO_DRIVE","https://drive.google.com/drive/folders/1WjeOyVESSZwPXf0QhsLsGrmoUcqObaBc")
OUT=HERE/"SICURIX_TALES_ATECO"; OUT.mkdir(exist_ok=True)
IDX=OUT/"SICURIX_TALES_ATECO_INDEX.csv"
SITE="81plus.net"; PERDAY=int(os.environ.get("ATECO_PERDAY","50"))
def sl(s): return re.sub(r"[^a-z0-9]+","_",str(s).lower()).strip("_")[:40]
# canone personaggi
# pool per area (dal canone)
POOL={
 "Sicurezza":{"eroi":["Scudix","Prepostix","Formix","Checkix"],"cattivi":["Riskix","Cadutix","Schiaccix","Voltix","Fumix","Polverix","Nondpix","Segnalex","Sottovalutix","Frettix","Improvvisix","Caosix","Macchinix" if False else "Segnalex"]},
 "HACCP":{"eroi":["Chefix","Hygienix","Traccix","Blinkix","Checkix"],"cattivi":["Sporckix","Crossix","Temporix","Scadutix","Mescolix","Dosagix","Acquaix"]},
 "Privacy":{"eroi":["Privacix","Cifrix","Consensix","Documix","Luxpectorix"],"cattivi":["Leakix","Phishix","Spyix","Hackix","Permissionix","Cancelix"]},
 "Documenti":{"eroi":["Documix","Checkix","Prepostix"],"cattivi":["Caosix","Oblivix","Archivix" if False else "Oblivix","Multix"]}}
SEZ_NAME={"A":"Agricoltura","B":"Estrazione","C":"Manifattura","D":"Energia","E":"Acqua/Rifiuti","F":"Costruzioni","G":"Commercio","H":"Trasporti","I":"Alloggio/Ristorazione","J":"Informazione/ICT","K":"Finanza","L":"Immobiliare","M":"Attività professionali","N":"Servizi alle imprese","O":"PA","P":"Istruzione","Q":"Sanità","R":"Arte/Sport","S":"Altri servizi","T":"Famiglie","U":"Organizzazioni extra"}
def load_ateco():
    d=json.load(open(ATECO,encoding="utf-8")); rng=d["divRanges"]
    def sez(code):
        try: dv=int(code.split(".")[0])
        except: return "S"
        for s,(a,b) in rng.items():
            if a<=dv<=b: return s
        return "S"
    subs=[]
    for x in d["sottocategorie"]:
        c=x["codice"]; subs.append({"codice":c,"titolo":x["titolo"],"sezione":sez(c),
          "divisione":c.split(".")[0],"gruppo":c[:4],"classe":c[:5],"categoria":c[:7]})
    return subs
def area_of(sez,titolo):
    t=titolo.lower()
    if sez=="I" or any(k in t for k in ["aliment","ristorant","bar","catering","mensa","gelat","panific","carne","pesce","latt","bevande","pasticc","cucina","macell"]): return "HACCP"
    if sez in ("J","K","M","P") or any(k in t for k in ["informatic","software","dati","consulenza","assicur","banc","credito","telecomunic","internet","marketing","pubblicit","istruzione","formazione","scuola"]): return "Privacy"
    if sez in ("O","Q","N","L"): return "Misto"
    return "Sicurezza"  # A,B,C,D,E,F,G,H,R,S...
def cast(area,i):
    a=area if area in POOL else "Sicurezza"
    P=POOL[a]; er=P["eroi"]; ca=[c for c in P["cattivi"] if c]
    heroes=[er[i%len(er)],er[(i+2)%len(er)]]
    vill=[ca[i%len(ca)],ca[(i+1)%len(ca)]]
    if area=="Misto": vill.append(POOL["Privacy"]["cattivi"][i%6])
    return list(dict.fromkeys(heroes)),list(dict.fromkeys(vill))
def scheda(n,x,i):
    area=area_of(x["sezione"],x["titolo"]); heroes,vill=cast(area,i)
    amb=x["titolo"][:70]; titolo=f"{x['titolo'][:44]} — Pericolo vs Metodo81+"
    fname=f"SICURIX_TALES_{n:04d}_{x['codice'].replace('.','')}_{sl(x['titolo'])}_{area.upper()}_v1.png"
    block=f"{((n-1)//50)*50+1:04d}-{((n-1)//50)*50+50:04d}"
    img=(f"Crea una pagina fumetto verticale 'SICURIX TALES — {x['titolo'][:50]}'. Stile ufficiale original toy-brick comic adventure, personaggi modulari giocattolo, fumetto europeo umoristico 81+, ambientazione coerente con: {amb}. "
         f"Mostra: ambiente reale dell'attività, 2-4 pericoli realistici, i cattivi {', '.join(vill)}, gli eroi {', '.join(heroes)}, SICURIX che guida, checklist Metodo81+, risultato ordinato, CTA {SITE}. "
         f"Layout 8-12 vignette, titolo alto, sezione PERICOLO in rosso, SOLUZIONE Metodo81+ in verde, finale 'Prima vedi. Poi sistemi.'. "
         f"NEGATIVE: no LEGO logo, no Asterix/Obelix, no caschi alati, no personaggi protetti, no horror/gore, no 'zero multe/rischio zero/promesse assolute'.")
    vid=(f"Clip verticale 9:16 8-10s, SICURIX TALES toy-brick. Ambientazione: {amb}. Scena: 1) problema 2) entra {vill[0]} 3) rischio chiaro non ansiogeno 4) arriva SICURIX 5) interviene {heroes[0]} 6) Metodo81+ 7) risultato ordinato 8) CTA {SITE}. Overlay: 'Pericolo?' 'Prima vedi.' 'Poi sistemi.' 'Metodo81+' '{SITE}'. NO horror, NO claim assoluti.")
    fumetto=(f"4 vignette: 1) {amb}: {vill[0]} crea il pericolo. 2) conseguenza operativa (no terrore). 3) SICURIX+{heroes[0]}: 'Prima vedi. Poi sistemi' + checklist Metodo81+. 4) risultato sicuro, CTA {SITE}.")
    caption=(f"🟧 {x['titolo'][:60]} — i rischi che chi lavora in questo settore conosce bene. In questa pagina SICURIX TALES: pericolo, {vill[0]}, e la soluzione col Metodo81+. 👉 {SITE}. Contenuto informativo.")
    hashtag=f"#SicurixTales #{area} #SicurezzaSulLavoro #81plus #Sicurissimo81 #Metodo81 #ATECO"
    checklist=["Rischi valutati e documentati","Formazione/DPI adeguati","Procedure e scadenze aggiornate","Responsabilità chiare"]
    return {"pagina":f"{n:04d}","codice_ateco":x["codice"],"descrizione_ateco":x["titolo"],"sezione":f"{x['sezione']} {SEZ_NAME.get(x['sezione'],'')}","divisione":x["divisione"],"gruppo":x["gruppo"],"classe":x["classe"],"categoria":x["categoria"],"sottocategoria":x["codice"],
      "titolo_fumetto":titolo,"area":area,"ambientazione":amb,"cattivi":vill,"eroi":heroes,
      "rischi":[f"Rischio {area} prevalente per: {amb}"],"soluzioni_metodo81":["Fotografia/Audit 81+","Corso/checklist collegata","Aggiornamento periodico"],
      "vignette":[f"V{k+1}" for k in range(10)],"prompt_immagine":img,"prompt_video":vid,"prompt_fumetto_4":fumetto,"caption":caption,"hashtag":hashtag,
      "checklist":checklist,"cta":f"Vai su {SITE}","nome_file":fname,"cartella_drive":f"{DRIVE} /{block}/","stato":"DA_GENERARE"}
def main():
    subs=load_ateco(); done=set()
    if IDX.exists():
        for r in csv.DictReader(open(IDX,encoding="utf-8")):
            if r.get("stato") in ("FATTO","BRIEF_PRONTO"): done.add(r["codice_ateco"])
    todo=[(i+1,x) for i,x in enumerate(subs) if x["codice"] not in done]
    if not todo:
        print("TUTTE le 1290 pagine hanno il brief. Genero indice finale."); return
    batch=todo[:PERDAY]; first=batch[0][0]; last=batch[-1][0]
    block=f"{((first-1)//50)*50+1:04d}-{((last-1)//50)*50+50:04d}"
    bdir=OUT/block; bdir.mkdir(exist_ok=True)
    pages=[scheda(n,x,n) for n,x in batch]
    json.dump(pages,open(bdir/"pages.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    with open(bdir/"tabella_50.csv","w",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh); w.writerow(["pagina","codice","descrizione","area","cattivi","eroi","titolo","nome_file"])
        for p in pages: w.writerow([p["pagina"],p["codice_ateco"],p["descrizione_ateco"],p["area"],"|".join(p["cattivi"]),"|".join(p["eroi"]),p["titolo_fumetto"],p["nome_file"]])
    with open(bdir/"schede.md","w",encoding="utf-8") as fh:
        for p in pages:
            fh.write(f"## Pag {p['pagina']} · {p['codice_ateco']} — {p['descrizione_ateco']}\n- Area:{p['area']} · Cattivi:{', '.join(p['cattivi'])} · Eroi:{', '.join(p['eroi'])}\n- File:{p['nome_file']}\n- PROMPT IMMAGINE: {p['prompt_immagine']}\n- PROMPT VIDEO: {p['prompt_video']}\n- Caption: {p['caption']}\n- {p['hashtag']}\n\n")
    # indice cumulativo
    newidx=not IDX.exists()
    with open(IDX,"a",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh)
        if newidx: w.writerow(["pagina","codice_ateco","descrizione","area","block","nome_file","stato"])
        for p in pages: w.writerow([p["pagina"],p["codice_ateco"],p["descrizione_ateco"],p["area"],block,p["nome_file"],"BRIEF_PRONTO"])
    # report
    from collections import Counter
    ac=Counter(p["area"] for p in pages); ec=Counter(h for p in pages for h in p["eroi"]); vc=Counter(v for p in pages for v in p["cattivi"])
    tot_done=len(done)+len(pages)
    open(bdir/"report.md","w",encoding="utf-8").write(
      f"# REPORT blocco {block}\n- Pagine oggi: {len(pages)} ({first:04d}-{last:04d})\n- Totale brief pronti: {tot_done}/1290 · rimanenti: {1290-tot_done}\n- Aree: {dict(ac)}\n- Eroi usati: {dict(ec)}\n- Cattivi usati: {dict(vc)}\n- Prossime 50: da pagina {last+1:04d}\n")
    print(f"BLOCCO {block}: {len(pages)} brief · totale {tot_done}/1290 · aree {dict(ac)}")
if __name__=="__main__": main()
