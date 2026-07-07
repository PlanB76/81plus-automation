# -*- coding: utf-8 -*-
"""SICURIX GLB FACTORY (cloud, H24) — genera GLB texturati dai ritagli dei personaggi
chiamando lo Space SF3D (Stable Fast 3D) via gradio_client. NIENTE browser, NIENTE GPU sul runner:
la GPU e' quella gratuita di Hugging Face. A lotti per rispettare la quota giornaliera.

USO:   HF_TOKEN=hf_xxx python make_glb.py [N]        (default N=6 per run)
       python make_glb.py --api                      (stampa la firma API dello Space)

Input : cloud/glb/crops/*.png   (ritagli FRONT dei personaggi, sfondo trasparente)
Output: cloud/glb/out/<NOME>.glb + stato anti-ripetizione cloud/glb/glb_state.json
Space : stabilityai/stable-fast-3d  (gratis; serve HF_TOKEN per la quota ZeroGPU)
"""
import os, sys, json, glob, shutil, pathlib, time

HERE = pathlib.Path(__file__).resolve().parent
CROPS = HERE/"crops"; OUT = HERE/"out"; OUT.mkdir(parents=True, exist_ok=True)
STATE = HERE/"glb_state.json"
SPACE = os.environ.get("SF3D_SPACE", "stabilityai/stable-fast-3d")
TOKEN = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN") or "").strip() or None
N = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1].isdigit()) else int(os.environ.get("GLB_N", "6"))

def load_state():
    if STATE.exists():
        try: return set(json.load(open(STATE, encoding="utf-8")))
        except: return set()
    return set()
def save_state(s): json.dump(sorted(s), open(STATE, "w", encoding="utf-8"))

def make_client():
    from gradio_client import Client
    import inspect; _kw={k:TOKEN for k in ("hf_token","token") if TOKEN and k in inspect.signature(Client).parameters}; return Client(SPACE, **_kw)

def find_endpoint(client):
    """Trova l'endpoint giusto: input immagine, output model3d/.glb."""
    try:
        info = client.view_api(return_format="dict")
    except Exception as e:
        print("view_api non disponibile:", e); return "/run"
    named = (info or {}).get("named_endpoints", {}) or {}
    best = None
    for name, ep in named.items():
        outs = ep.get("returns", []) or []
        ins = ep.get("parameters", []) or []
        has_img = any((p.get("python_type", {}) or {}).get("type", "").lower() in ("filepath", "str") or "image" in (p.get("label", "") or "").lower() for p in ins)
        has_model = any("model" in (o.get("component", "") or "").lower() or ".glb" in json.dumps(o).lower() or "model3d" in json.dumps(o).lower() for o in outs)
        if has_model and has_img:
            best = name; break
    return best or "/run"

def to_glb(result):
    """Il risultato puo' essere un path, una tupla o un dict: estrai il .glb."""
    def pick(x):
        if isinstance(x, str) and x.lower().endswith((".glb", ".gltf")): return x
        if isinstance(x, dict):
            for v in x.values():
                r = pick(v)
                if r: return r
        if isinstance(x, (list, tuple)):
            for v in x:
                r = pick(v)
                if r: return r
        if isinstance(x, str) and os.path.exists(x): return x
        return None
    return pick(result)

def call(client, ep, img):
    from gradio_client import handle_file
    # parametri SF3D: image, foreground_ratio, remesh_option, vertex_count, texture_size
    trials = [
        dict(kwargs=dict(image=handle_file(img), foreground_ratio=0.85, remesh_option="None", vertex_count=-1, texture_size=1024)),
        dict(args=(handle_file(img), 0.85, "None", -1, 1024)),
        dict(args=(handle_file(img), 0.85, "None", 1024)),
        dict(args=(handle_file(img),)),
    ]
    last = None
    for t in trials:
        try:
            if "kwargs" in t: return client.predict(api_name=ep, **t["kwargs"])
            return client.predict(*t["args"], api_name=ep)
        except Exception as e:
            last = e
    raise last

def main():
    if "--api" in sys.argv:
        c = make_client()
        print(json.dumps(c.view_api(return_format="dict"), indent=2)[:6000]); return
    crops = sorted(glob.glob(str(CROPS/"*.png")))
    if not crops:
        print("Nessun ritaglio in", CROPS); return
    done = load_state()
    todo = [p for p in crops if pathlib.Path(p).stem not in done][:N]
    print(f"GLB factory: {len(todo)} da fare (su {len(crops)} totali, {len(done)} gia' fatti). Space={SPACE}")
    if not TOKEN:
        print("ATTENZIONE: HF_TOKEN assente. Aggiungilo come secret per usare la quota ZeroGPU.")
    client = make_client(); ep = find_endpoint(client); print("endpoint:", ep)
    ok = 0
    for i, img in enumerate(todo, 1):
        name = pathlib.Path(img).stem
        try:
            res = call(client, ep, img); glb = to_glb(res)
            if not glb or not os.path.exists(glb): raise RuntimeError("nessun .glb nel risultato: %r" % (res,))
            dst = OUT/(name+".glb"); shutil.copy(glb, dst)
            done.add(name); ok += 1; print(f"  [{i}/{len(todo)}] {name}.glb ({os.path.getsize(dst)//1024} KB)")
            save_state(done)
        except Exception as e:
            print(f"  [{i}/{len(todo)}] ERRORE {name}: {e}")
            time.sleep(3)
    save_state(done)
    print(f"FATTO: {ok}/{len(todo)} GLB in {OUT}. Restano {len(crops)-len(done)}.")

if __name__ == "__main__":
    main()
