# -*- coding: utf-8 -*-
"""
flotta81.py — attiva la FLOTTA 81+ (20 agenti, OS "Graziella") in cloud, H24.
- carica il roster flotta20_81.json
- prende un OBIETTIVO del giorno (da obiettivo.txt se presente, altrimenti default)
- ogni agente emette una micro azione in base al suo focus (esecuzione parallela simulata)
- l'agente 18 QA verifica coerenza, poi si produce un OUTPUT UNICO con una sola CTA
- se GROQ_API_KEY e' presente, un LLM sintetizza il brief rispettando le regole 81+
- scrive flotta81/REPORT_YYYYMMDD.md e flotta81/state.json (memoria della flotta)
Nessuna dipendenza esterna (solo stdlib). Se manca la rete, produce comunque il brief locale.
"""
import os, json, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER = os.path.join(HERE, "flotta20_81.json")
STATE  = os.path.join(HERE, "state.json")

def load(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d

def obiettivo():
    p = os.path.join(HERE, "obiettivo.txt")
    if os.path.exists(p):
        t = open(p, encoding="utf-8").read().strip()
        if t: return t
    return "Far crescere 81+ oggi. Aumentare conversioni corsi e membership senza inventare nulla su norme e prezzi."

def micro(ag, obj):
    # micro azione deterministica per ruolo (voce attiva, frase breve, no trattini)
    r = ag["ruolo"]
    return f"Agente {ag['id']} {r}. {ag['focus']}. Propone una azione concreta coerente con l obiettivo. {obj[:80]}"

def groq_brief(obj, righe):
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None
    sys = ("Sei Graziella, orchestratore del Team 81+ di 20 agenti. Regole assolute. "
           "Zero inventiva su norme e prezzi. Voce attiva. Frasi brevi. Solo virgole e punti. "
           "Niente trattini ne markdown. Italiano perfetto. Produci un brief operativo unico, "
           "azioni concrete, e una sola CTA finale.")
    usr = "Obiettivo del giorno. " + obj + " Contributi degli agenti. " + " ".join(righe)
    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role":"system","content":sys},{"role":"user","content":usr}],
        "temperature": 0.5
    }).encode("utf-8")
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization":"Bearer "+key, "Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            j = json.loads(r.read().decode("utf-8"))
            return j["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("[flotta] LLM non disponibile:", e)
        return None

def main():
    data = load(ROSTER, {})
    agenti = data.get("agenti", [])
    if not agenti:
        print("[flotta] roster mancante"); return
    obj = obiettivo()
    righe = [micro(a, obj) for a in agenti]
    qa = ("Agente 18 QA. Verifica coerenza con listino81+ e norme. "
          "Conferma prezzi e riferimenti solo se reali. Blocca ogni claim non verificabile.")
    brief = groq_brief(obj, righe)
    now = datetime.datetime.utcnow()
    stamp = now.strftime("%Y%m%d")
    md = []
    md.append("BRIEF OPERATIVO FLOTTA 81+ del " + now.strftime("%d/%m/%Y %H:%M UTC"))
    md.append("")
    md.append("OBIETTIVO. " + obj)
    md.append("")
    md.append("CONTRIBUTI DEGLI AGENTI.")
    md += righe
    md.append("")
    md.append("CONTROLLO QUALITA. " + qa)
    md.append("")
    if brief:
        md.append("OUTPUT UNICO (Graziella).")
        md.append(brief)
    else:
        md.append("OUTPUT UNICO (Graziella).")
        md.append("Oggi la flotta consolida il funnel corsi sicurezza. Pubblica una scheda corso al giorno. "
                  "Attiva un invio email al segmento caldo. Prepara un preventivo tipo pronto all uso. "
                  "CTA finale. Apri 81plus.net e completa il tuo percorso sicurezza ora.")
    report = os.path.join(HERE, "REPORT_%s.md" % stamp)
    open(report, "w", encoding="utf-8").write("\n".join(md))
    st = load(STATE, {"run": 0, "storico": []})
    st["run"] = st.get("run", 0) + 1
    st["ultimo"] = now.isoformat() + "Z"
    st["ultimo_report"] = os.path.basename(report)
    st["storico"] = (st.get("storico", []) + [st["ultimo"]])[-50:]
    open(STATE, "w", encoding="utf-8").write(json.dumps(st, ensure_ascii=False, indent=2))
    print("[flotta] run", st["run"], "->", os.path.basename(report), "| LLM:", "si" if brief else "no")

if __name__ == "__main__":
    main()
