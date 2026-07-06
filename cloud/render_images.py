# -*- coding: utf-8 -*-
"""SICURIX RENDER IMAGES - pagine fumetto WEBP via OpenAI gpt-image-1 nello stile degli originali.
Usa reference (cloud/data/ref/*.jpg) via /v1/images/edits per coerenza stile/personaggi; fallback /v1/images/generations.
API KEY solo da env OPENAI_API_KEY. Default N=100/giorno. Output WEBP<=250KB in cloud/out/img/.
Drive: https://drive.google.com/drive/folders/1WjeOyVESSZwPXf0QhsLsGrmoUcqObaBc"""
import os,sys,csv,json,base64,io,glob,uuid,pathlib,urllib.request
HERE=pathlib.Path(__file__).resolve().parent
OUTD=HERE/"out"; IMG=OUTD/"img"; IMG.mkdir(parents=True,exist_ok=True)
REFDIR=HERE/"data"/"ref"
DRIVE_FOLDER_ID="1WjeOyVESSZwPXf0QhsLsGrmoUcqObaBc"
API_KEY=os.environ.get("OPENAI_API_KEY")
MODEL=os.environ.get("OPENAI_IMAGE_MODEL","gpt-image-1")
SIZE=os.environ.get("OPENAI_IMAGE_SIZE","1024x1536")
QUALITY=os.environ.get("OPENAI_IMAGE_QUALITY","high")
TARGET_KB=int(os.environ.get("WEBP_TARGET_KB","250"))
def latest_csv():
    fs=sorted(x for x in glob.glob(str(OUTD/"SICURIX_GEN_*.csv")) if "MANIFEST" not in x)
    return fs[-1] if fs else None
def refs():
    return sorted(glob.glob(str(REFDIR/"*.jpg")))+sorted(glob.glob(str(REFDIR/"*.png")))
def _multipart(fields,files):
    b=b""; bnd="----sicurix"+uuid.uuid4().hex
    for k,v in fields.items():
        b+=("--"+bnd+"\r\nContent-Disposition: form-data; name=\""+k+"\"\r\n\r\n"+str(v)+"\r\n").encode()
    for k,path in files:
        data=open(path,"rb").read(); fn=pathlib.Path(path).name
        ct="image/jpeg" if fn.lower().endswith(("jpg","jpeg")) else "image/png"
        b+=("--"+bnd+"\r\nContent-Disposition: form-data; name=\""+k+"\"; filename=\""+fn+"\"\r\nContent-Type: "+ct+"\r\n\r\n").encode()
        b+=data+b"\r\n"
    b+=("--"+bnd+"--\r\n").encode()
    return b,bnd
def gen_with_refs(prompt,ref_paths):
    fields={"model":MODEL,"prompt":prompt[:32000],"size":SIZE,"quality":QUALITY,"n":"1"}
    files=[("image[]",p) for p in ref_paths[:4]]
    body,bnd=_multipart(fields,files)
    req=urllib.request.Request("https://api.openai.com/v1/images/edits",data=body,method="POST",
        headers={"Authorization":"Bearer "+API_KEY,"Content-Type":"multipart/form-data; boundary="+bnd})
    with urllib.request.urlopen(req,timeout=300) as r: d=json.loads(r.read().decode())
    return base64.b64decode(d["data"][0]["b64_json"])
def gen_plain(prompt):
    body=json.dumps({"model":MODEL,"prompt":prompt[:32000],"size":SIZE,"quality":QUALITY,"n":1}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/images/generations",data=body,method="POST",
        headers={"Authorization":"Bearer "+API_KEY,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=300) as r: d=json.loads(r.read().decode())
    it=d["data"][0]
    if it.get("b64_json"): return base64.b64decode(it["b64_json"])
    with urllib.request.urlopen(it["url"],timeout=120) as r2: return r2.read()
def make_image(prompt):
    if not API_KEY: raise SystemExit("OPENAI_API_KEY assente: mettila come secret/env. Non e' hardcodata di proposito.")
    rp=refs()
    if rp:
        try: return gen_with_refs(prompt,rp)
        except Exception as e: print("   (edits fallito, uso generations):",e)
    return gen_plain(prompt)
def to_webp(png,path):
    from PIL import Image
    im=Image.open(io.BytesIO(png)).convert("RGB")
    w=1080; h=int(im.height*w/im.width); im=im.resize((w,h)); q=92
    while q>=40:
        im.save(path,"WEBP",quality=q,method=6)
        if path.stat().st_size<=TARGET_KB*1024: break
        q-=8
    return path.stat().st_size
def main():
    n=int(sys.argv[1]) if len(sys.argv)>1 else 100
    csvp=sys.argv[2] if len(sys.argv)>2 else latest_csv()
    if not csvp: raise SystemExit("Nessuno sheet in cloud/out/. Lancia prima sicurix_gen_daily.py")
    rows=list(csv.DictReader(open(csvp,encoding="utf-8"))); cols=list(rows[0].keys()) if rows else []
    todo=[r for r in rows if r.get("stato")=="DA_GENERARE_IMG"][:n]
    print("Render",len(todo),"immagini da",pathlib.Path(csvp).name,"(",MODEL,SIZE,"quality",QUALITY,len(refs()),"reference )")
    ok=0
    for i,r in enumerate(todo,1):
        name=r.get("nome_file_webp") or ("sicurix_%d.webp"%i); out=IMG/name
        if out.exists(): r["stato"]="IMG_OK"; ok+=1; continue
        try:
            png=make_image(r["image_prompt"]); kb=to_webp(png,out)//1024
            r["stato"]="IMG_OK"; ok+=1; print("  [%d/%d] %s (%dKB)"%(i,len(todo),name,kb))
        except Exception as e:
            r["stato"]="IMG_ERR"; print("  [%d/%d] ERRORE %s: %s"%(i,len(todo),name,e))
    with open(csvp,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("FATTO: %d/%d immagini in %s"%(ok,len(todo),IMG))
    print("Upload su Drive (passo separato, serve auth Google): cartella",DRIVE_FOLDER_ID)
if __name__=="__main__": main()
