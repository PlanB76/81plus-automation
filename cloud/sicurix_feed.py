# -*- coding: utf-8 -*-
"""SICURIX FEED - scrive sicurix_feed.json (ultime N card) per il ticker scorrevole su index.html.
Legge il manifest cumulativo (SICURIX_GEN_MANIFEST.csv); ogni card = {titolo, cta_url, settore, img}.
img = URL raw GitHub delle WEBP (dopo il push) con fallback al master visual.
USO: python sicurix_feed.py [N]"""
import os,sys,csv,json,glob,pathlib
HERE=pathlib.Path(__file__).resolve().parent; OUTD=HERE/"out"
MANIFEST=OUTD/"SICURIX_GEN_MANIFEST.csv"
# base URL raw github (dopo push). Personalizzabile via env.
RAW=os.environ.get("SICURIX_RAW_BASE","https://raw.githubusercontent.com/PlanB76/81plus-automation/main/cloud/out/img")
FALLBACK_IMG=os.environ.get("SICURIX_FALLBACK_IMG","https://81plus.net/SICURIX81+/0_MASTER_VISUAL_SICURIX.png")
def main():
    n=int(sys.argv[1]) if len(sys.argv)>1 else 24
    if not MANIFEST.exists(): print("Manca il manifest."); return
    rows=list(csv.DictReader(open(MANIFEST,encoding="utf-8")))[-n:]
    cards=[]
    for r in rows:
        img=f"{RAW}/{r['nome_file_webp']}" if r.get("stato")=="IMG_OK" else FALLBACK_IMG
        cards.append({"titolo":r["titolo_clickbait"],"settore":r["settore"],"cta_url":r["cta_url"],"cta":r["cta_prodotto"],"img":img})
    feed={"generato":rows[-1]["data"] if rows else "","cards":cards}
    # scrive nel repo e (se esiste) nella cartella sito
    out1=OUTD/"sicurix_feed.json"; json.dump(feed,open(out1,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    site=HERE.parent.parent/"0-81PLUS.NET"/"sicurix_feed.json"
    try:
        if site.parent.exists(): json.dump(feed,open(site,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    except Exception as e: print("site write warn",e)
    print(f"Feed scritto: {len(cards)} card -> {out1}")
if __name__=="__main__": main()
