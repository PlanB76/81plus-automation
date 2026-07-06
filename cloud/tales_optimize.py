# -*- coding: utf-8 -*-
"""TALES OPTIMIZE — sync vignette dalla cartella Google Drive + compressione WebP web-light + manifest.
H24: gira su GitHub Actions. Scarica la cartella Drive pubblica (gdown), comprime a ~<=250KB/img (1080px WebP),
salva in tales_web/ e ricostruisce tales_manifest.json con URL raw.githubusercontent (CDN gratis, veloce)."""
import os,sys,json,re,glob,tempfile
from PIL import Image
FOLDERS=[f.strip() for f in os.environ.get("TALES_DRIVE_FOLDERS","1hICKXdl9JTZBL1pemG19oE_661z-EH_k,1WjeOyVESSZwPXf0QhsLsGrmoUcqObaBc").split(",") if f.strip()]
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
DST=os.path.join(REPO,"tales_web"); os.makedirs(DST,exist_ok=True)
OWNER=os.environ.get("GH_OWNER","PlanB76"); NAME=os.environ.get("GH_REPO","81plus-automation"); BR=os.environ.get("GH_BRANCH","main")
def slug(f): return re.sub(r"[^a-z0-9]+","-",os.path.splitext(os.path.basename(f))[0].lower()).strip("-")[:50]
def theme(f):
    fl=f.lower()
    if "haccp" in fl or any(k in fl for k in ["cucina","aliment","igien","food"]): return "HACCP"
    if "privacy" in fl or any(k in fl for k in ["gdpr","dati","cyber"]): return "Privacy"
    return "Sicurezza"
# 1) scarica da Drive (se pubblica); altrimenti usa i sorgenti gia' presenti
src=tempfile.mkdtemp()
try:
    import gdown
    for i,fid in enumerate(FOLDERS):
        try: gdown.download_folder(id=fid,output=os.path.join(src,f"f{i}"),quiet=True,use_cookies=False); print("Drive ok:",fid)
        except Exception as e2: print("folder skip",fid,e2)
except Exception as e:
    print("gdown skip (",e,") -> uso tales_src/ locale se presente")
    src=os.path.join(REPO,"tales_src")
imgs=[f for f in glob.glob(os.path.join(src,"**","*"),recursive=True) if f.lower().endswith((".png",".jpg",".jpeg",".webp"))]
if not imgs: print("Nessuna nuova immagine: mantengo tales_web esistente"); sys.exit(0)
man=[]; tin=tout=0
for p in sorted(imgs):
    tin+=os.path.getsize(p); im=Image.open(p).convert("RGB"); w,h=im.size; mx=1080
    if max(w,h)>mx: r=mx/max(w,h); im=im.resize((int(w*r),int(h*r)))
    out=os.path.join(DST,slug(p)+".webp"); q=80; im.save(out,"WEBP",quality=q,method=6)
    while os.path.getsize(out)>256000 and q>45: q-=8; im.save(out,"WEBP",quality=q,method=6)
    tout+=os.path.getsize(out)
    man.append({"file":os.path.basename(out),"theme":theme(p),"drive_url":f"https://raw.githubusercontent.com/{OWNER}/{NAME}/{BR}/tales_web/{slug(p)}.webp"})
json.dump(man,open(os.path.join(HERE,"data","tales_manifest.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"OK {len(man)} vignette · {tin/1048576:.1f}MB -> {tout/1024:.0f}KB")
