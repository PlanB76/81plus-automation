# -*- coding: utf-8 -*-
"""SICURIX VOLUME - ogni 100 pagine fumetto crea un VOLUME PDF pronto per Amazon KDP.
Struttura: COPERTINA FRONTE (wow, numerata, logo TALES OF SICURIX, brand nero/bianco/arancione)
+ INDICE + le 100 vignette formative + STORIA SPECIALE 10 pagine (SICURIX aiutato dai colleghi) + COPERTINA RETRO (perche'/cosa/come/scopo + biografia + FOTO autore).
Cover e storia con gpt-image-1 (riusa render_images). Testo/indice/retro con Pillow.
Output: cloud/out/volumes/SICURIX_VOLUME_NNN.pdf . Biografia in cloud/data/sicurix_bio.txt . Foto autore da SICURIX_AUTHOR_PHOTO.
USO: OPENAI_API_KEY=... python sicurix_volume.py"""
import os,sys,csv,io,glob,textwrap,pathlib,urllib.request
from PIL import Image,ImageDraw,ImageFont
import render_images as RI
HERE=pathlib.Path(__file__).resolve().parent
OUTD=HERE/"out"; IMG=OUTD/"img"; VOLD=OUTD/"volumes"; DATA=HERE/"data"
BIO=DATA/"sicurix_bio.txt"
AUTHOR_PHOTO=os.environ.get("SICURIX_AUTHOR_PHOTO","https://81plus.net/Mirco%20Pregnolato.png")
BLOCK=100; W,H=1024,1536
BLACK=(5,5,10); ORANGE=(255,106,26); WHITE=(245,242,235)
def font(sz):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz)
            except: pass
    return ImageFont.load_default()
def ready_pages():
    mf=OUTD/"SICURIX_GEN_MANIFEST.csv"
    if not mf.exists(): return []
    seen=set(); out=[]
    for r in csv.DictReader(open(mf,encoding="utf-8")):
        f=r.get("nome_file_webp")
        if not f or f in seen: continue
        if (IMG/f).exists(): seen.add(f); out.append(r)
    return out
def text_page(title,lines,sub=""):
    im=Image.new("RGB",(W,H),BLACK); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,150],fill=ORANGE); d.text((60,45),title,font=font(54),fill=BLACK)
    if sub: d.text((60,160),sub,font=font(28),fill=ORANGE)
    y=225
    for ln in lines:
        d.text((60,y),ln,font=font(26),fill=WHITE); y+=44
        if y>H-90: break
    d.text((W-170,H-80),"81+",font=font(52),fill=ORANGE)
    return im
def wrap(txt,width=52):
    out=[]
    for para in txt.split("\n"): out+=(textwrap.wrap(para,width) or [""])
    return out
def back_cover(manifesto,bio):
    im=Image.new("RGB",(W,H),BLACK); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,150],fill=ORANGE); d.text((60,45),"TALES OF SICURIX",font=font(50),fill=BLACK)
    d.text((60,160),"Il perche, il cosa, il come, lo scopo",font=font(26),fill=ORANGE)
    y=220
    for ln in wrap(manifesto,58):
        d.text((60,y),ln,font=font(23),fill=WHITE); y+=36
    y+=20; d.text((60,y),"--- L AUTORE ---",font=font(28),fill=ORANGE); y+=54
    tx=60; ytxt=y
    try:
        req=urllib.request.Request(AUTHOR_PHOTO,headers={"User-Agent":"Mozilla/5.0"})
        raw=urllib.request.urlopen(req,timeout=30).read()
        ph=Image.open(io.BytesIO(raw)).convert("RGB"); pw=300; phh=int(ph.height*pw/ph.width); ph=ph.resize((pw,phh))
        d.rectangle([56,y-4,64+pw,y+phh+4],outline=ORANGE,width=4); im.paste(ph,(60,y)); tx=60+pw+28
    except Exception as e: print("foto autore non caricata:",e)
    for ln in wrap(bio,44):
        d.text((tx,ytxt),ln,font=font(21),fill=WHITE); ytxt+=30
        if ytxt>H-100: break
    d.text((W-170,H-80),"81+",font=font(52),fill=ORANGE)
    return im
def cover_prompt(vol_no,title):
    return ("Crea una COPERTINA di fumetto premium verticale formato libro (1024x1536), stile 'TALES OF SICURIX', grafica SUPER WOW da bestseller Amazon. "
      "SICURIX in primo piano, eroe a mattoncini 3D col mantello e medaglione '81+', posa dinamica, dietro la squadra di eroi. "
      "USO ESCLUSIVO dei brand colors: NERO, BIANCO, ARANCIONE (nessun altro colore). "
      f"In alto grande logo/titolo 'TALES OF SICURIX'. Sottotitolo '{title}'. In basso a destra 'VOLUME {vol_no:03d}'. Logo '81+'. "
      "Composizione epica, luci drammatiche, tipografia italiana grande e leggibile, qualita' da copertina stampata. "
      "NEGATIVE: nessun marchio LEGO, nessun personaggio protetto, nessun colore oltre nero/bianco/arancione.")
STORY=[
 "L'azienda apre: tutto sembra in ordine, i lavoratori iniziano la giornata.",
 "Il cattivo Riskix nasconde i pericoli tra scartoffie e attrezzi lasciati in giro.",
 "Caosix mette in disordine documenti, scadenze e procedure: nessuno ci capisce piu' nulla.",
 "Un lavoratore rischia un infortunio: tensione, il pericolo diventa reale.",
 "Scatta un'emergenza e Improvvisix grida 'si e' sempre fatto cosi': confusione totale.",
 "Arriva SICURIX con la bussola e CHIAMA i colleghi: 'Prima vedi. Poi sistemi. E non da soli!'",
 "Scudix e Formix aiutano SICURIX: DPI indossati, formazione, ruoli chiari (preposto, RLS).",
 "Chefix e Hygienix affiancano la squadra: igiene e HACCP, sanificazione, temperature, tracciabilita'.",
 "Privacix e Cifrix completano il lavoro di squadra: dati protetti, informativa, password sicure.",
 "L'azienda e' sicura e serena: SICURIX e tutta la squadra 81+ salutano. Vai su 81plus.net.",
]
def story_prompt(vol_no,i,beat):
    return (f"Pagina {i} di 10 di una STORIA SPECIALE a fumetti 'TALES OF SICURIX' (Volume {vol_no:03d}), verticale 1024x1536, "
      "QUALITA' EDITORIALE, stile IDENTICO alle immagini di riferimento allegate: minifigure a mattoncini 3D, 10-12 vignette, "
      "brand colors ESCLUSIVI nero/bianco/arancione, testo italiano BREVE e leggibile, logo '81+' in ogni vignetta. "
      "REGOLA: SICURIX non agisce mai da solo, si fa sempre aiutare dai suoi colleghi EROI (lavoro di squadra). "
      f"SCENA DELLA PAGINA: {beat} Continuita' di personaggi, stile e colori con le altre pagine del volume. "
      "NEGATIVE: nessun marchio LEGO, nessun personaggio protetto, niente gore, niente claim assoluti.")
def gen_img(prompt):
    return Image.open(io.BytesIO(RI.make_image(prompt))).convert("RGB").resize((W,H))
def build_volume(vol_no,pages):
    VOLD.mkdir(exist_ok=True)
    pdf=VOLD/f"SICURIX_VOLUME_{vol_no:03d}.pdf"
    if pdf.exists(): print("gia' presente:",pdf.name); return None
    title=f"100 Storie di Sicurezza - Vol.{vol_no:03d}"
    imgs=[]
    try: imgs.append(gen_img(cover_prompt(vol_no,title)))
    except Exception as e:
        print("cover fallback:",e); imgs.append(text_page("TALES OF SICURIX",[f"Volume {vol_no:03d}"],"100 storie di sicurezza"))
    idx=[f"{i+1:3d}. {(p.get('settore') or '')[:24]:24} {(p.get('titolo_clickbait') or '')[:38]}" for i,p in enumerate(pages)]
    for k in range(0,len(idx),25): imgs.append(text_page("INDICE",idx[k:k+25],f"Volume {vol_no:03d}"))
    for p in pages:
        try: imgs.append(Image.open(IMG/p["nome_file_webp"]).convert("RGB").resize((W,H)))
        except Exception as e: print("skip pag",p.get("nome_file_webp"),e)
    for i,beat in enumerate(STORY,1):
        try: imgs.append(gen_img(story_prompt(vol_no,i,beat)))
        except Exception as e: print("storia pag",i,"err:",e)
    manifesto=("PERCHE: la sicurezza raccontata come un'avventura, non come burocrazia.\n"
      "COSA: TALES OF SICURIX trasforma gli adempimenti obbligatori (sicurezza sul lavoro, HACCP, privacy) in storie a fumetti chiare e memorabili.\n"
      "COME: ogni storia mostra prima il PERICOLO e poi il METODO 81+ che lo mette in ordine, passo per passo, con SICURIX e i suoi colleghi.\n"
      "SCOPO: far capire a chiunque, in pochi minuti, cosa serve per lavorare sicuri e in regola. Prima vedi. Poi sistemi. - 81plus.net")
    bio=BIO.read_text(encoding="utf-8") if BIO.exists() else "[Inserisci la tua biografia in cloud/data/sicurix_bio.txt]"
    imgs.append(back_cover(manifesto,bio))
    imgs[0].save(pdf,"PDF",save_all=True,append_images=imgs[1:])
    print("VOLUME creato:",pdf,"| pagine PDF:",len(imgs))
    return pdf
def main():
    pages=ready_pages(); n=len(pages)//BLOCK
    print("Pagine pronte:",len(pages),"| volumi compilabili:",n)
    for b in range(n): build_volume(b+1, pages[b*BLOCK:(b+1)*BLOCK])
    if n==0: print(f"Servono almeno {BLOCK} pagine (ora {len(pages)}). Il volume si crea da solo al traguardo.")
if __name__=="__main__": main()
