# -*- coding: utf-8 -*-
"""
TG LIBRI 81+ · posta a rotazione 1 libro di Mirco Pregnolato sul canale Telegram
con caption DIVERTENTE (ironica, stile "sicurezza/HACCP/privacy senza noia")
generata con AI (GROQ) + link Amazon (anteprima = copertina automatica).
Ruota sui libri in libri.json, traccia l'indice in state_libri.json.
Nessuno scraping Amazon: la copertina la mostra Telegram dal link.
Secret usati: SICURIX_TG_TOKEN, SICURIX_TG_CHANNEL, GROQ_API_KEY (opzionale).
"""
import os, json, urllib.request, urllib.parse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LIB  = json.load(open(os.path.join(HERE, "libri.json"), encoding="utf-8"))["libri"]
STATE_P = os.path.join(HERE, "state_libri.json")

def load_state():
    try: return json.load(open(STATE_P, encoding="utf-8"))
    except Exception: return {"idx": 0}
def save_state(s): json.dump(s, open(STATE_P,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
def log(m): print("[tg-libri] " + m)

CTA = "Lo trovi su Amazon \U0001F447\nMettiti in regola e semplifica tutto su 81plus.net"

def groq_caption(b):
    key = os.environ.get("GROQ_API_KEY","").strip()
    fallback = ("\U0001F4DA " + b["t"] + "\n\n"
                "Categoria: " + b.get("cat","") + "\n"
                "Guide pratiche di Mirco Pregnolato: la sicurezza, l'HACCP e la burocrazia "
                "spiegate in modo semplice e senza stress.\n\n" + CTA +
                "\n\n#81plus #libri #sicurezzasullavoro #HACCP #Amazon")
    if not key: return fallback
    sys = ("Sei il copywriter di 81+/Sicurissimo. Tono SIMPATICO, ironico ma intelligente: "
           "rendi sicurezza sul lavoro, HACCP e privacy leggeri e divertenti, mai noiosi. "
           "Italiano, frasi brevi, 1-2 emoji ben piazzate, zero inventiva su norme o prezzi. "
           "Scrivi una caption Telegram per promuovere un LIBRO: gancio ironico nella prima riga, "
           "2-3 righe di beneficio concreto per chi lavora/ha un'azienda, poi invito a leggerlo. "
           "NON inventare il contenuto del libro oltre al titolo/categoria. "
           "Chiudi con la CTA (verbatim): '" + CTA + "' e 4-5 hashtag. Rispondi SOLO col testo della caption.")
    usr = "Libro: " + b["t"] + " | Categoria: " + b.get("cat","")
    body = json.dumps({"model":"llama-3.3-70b-versatile",
        "messages":[{"role":"system","content":sys},{"role":"user","content":usr}],
        "temperature":0.85}).encode("utf-8")
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            txt = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
        if CTA.split("\n")[0] not in txt: txt += "\n\n" + CTA
        return txt[:900]
    except Exception as e:
        log("caption AI ko: %s" % e); return fallback

def tg_post(text, link):
    tok = os.environ.get("SICURIX_TG_TOKEN","").strip()
    ch  = os.environ.get("SICURIX_TG_CHANNEL","").strip()
    if not tok or not ch:
        log("SALTO: mancano SICURIX_TG_TOKEN / SICURIX_TG_CHANNEL."); return False
    full = text + "\n\n" + link
    body = urllib.parse.urlencode({"chat_id":ch,"text":full,"disable_web_page_preview":"false"}).encode("utf-8")
    try:
        urllib.request.urlopen(urllib.request.Request(
            "https://api.telegram.org/bot%s/sendMessage" % tok, data=body), timeout=20)
        log("postato su " + ch); return True
    except Exception as e:
        log("tg ko: %s" % e); return False

def main():
    if not LIB: log("nessun libro in libri.json"); return
    st = load_state()
    i = st.get("idx", 0) % len(LIB)
    b = LIB[i]
    log("libro #%d: %s" % (i, b["t"]))
    cap = groq_caption(b)
    if tg_post(cap, b["u"]):
        st["idx"] = (i + 1) % len(LIB)
        save_state(st)
    log("Giro libri completato " + datetime.datetime.utcnow().isoformat() + "Z")

if __name__ == "__main__":
    main()
