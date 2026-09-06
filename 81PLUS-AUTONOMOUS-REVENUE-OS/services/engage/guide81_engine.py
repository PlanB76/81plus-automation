"""
81+ AUTONOMOUS REVENUE OS
services/engage/guide81_engine.py — GUIDE81 Platform Guide & Activation Asset
Genera e versiona l'asset centrale permanente:
"81+ — COME FUNZIONA SENZA PERDERE TEMPO / 81+ SENZA MANUALE"
Funge contemporaneamente da:
- Onboarding & manuale rapido per l'utente
- Strumento di conversione anti-obiezione
- Knowledge source strutturata per COPY81 e il router AI
- Garante della One CTA Rule: "VAI SULLA PIATTAFORMA"
"""

import os
import sys
import json
import uuid
from datetime import datetime
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

GUIDE_TITLE = "81+ — COME FUNZIONA SENZA PERDERE TEMPO"
GUIDE_SUBTITLE = "Corsi, documenti e quello che ti serve. Senza trasformare la sicurezza nel tuo nuovo hobby."
CTA_UNIVERSALE = "VAI SULLA PIATTAFORMA"
CTA_URL = "https://81plus.net"

def get_guide_sections() -> list[dict]:
    return [
        {
            "id": "sec_01_cos_e",
            "number": 1,
            "title": "Cos'è 81+ in 20 secondi",
            "content": (
                "81+ è l'ecosistema operativo che ti permette di verificare gli obblighi di sicurezza sul lavoro "
                "della tua azienda, completare i corsi di formazione necessari (sia online che in aula) e ottenere "
                "i documenti di conformità (DVR, POS, HACCP) in un unico posto centralizzato. "
                "Niente burocrazia dispersiva, niente moduli incomprensibili: accedi, verifichi e risolvi."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_02_perche_esiste",
            "number": 2,
            "title": "Perché esiste 81+",
            "content": (
                "La sicurezza sul lavoro è già abbastanza complicata per conto suo: centinaia di pagine del D.Lgs. 81/08, "
                "il nuovo Accordo Stato-Regioni 2025, scadenze che si accumulano e certificati sparsi in cartelle dimenticate. "
                "Noi abbiamo evitato di complicarti anche il modo di gestirla. Abbiamo eliminato la caccia al tesoro tra consulenti, "
                "portali diversi e preventivi fumosi."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_03_cosa_trovi",
            "number": 3,
            "title": "Cosa trovi davvero dentro",
            "content": (
                "Dentro 81+ trovi tutto ciò che la legge richiede alla tua azienda, suddiviso con chiarezza:\n"
                "• Corsi Online in E-Learning (FAD): Fruibili 24 ore su 24, 7 giorni su 7, da PC, tablet o smartphone.\n"
                "• Corsi in Aula e Pratici: Calendario edizioni territoriali per attrezzature, carrelli elevatori, PLE, "
                "antincendio e primo soccorso con formatori accreditati ANFOS (Centro RO/3).\n"
                "• Documenti di Conformità: DVR Standardizzati, Piani Operativi di Sicurezza (POS), manuali e schede HACCP.\n"
                "• Incarichi Professionali: Nomine RSPP esterno, Medico Competente e verifiche tecniche periodiche."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_04_come_entrare",
            "number": 4,
            "title": "Come entrare e registrarsi",
            "content": (
                "Entrare richiede meno di un minuto. Vai sulla piattaforma, inserisci l'email aziendale e imposti una password. "
                "Non ti chiediamo documenti infiniti né dati di fatturazione per guardarti intorno. Il tuo account ti dà accesso "
                "immediato alla dashboard e allo scadenziario."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_05_come_scegliere",
            "number": 5,
            "title": "Come trovare ciò che ti serve",
            "content": (
                "Non devi conoscere a memoria il Testo Unico per trovare il corso giusto. Basta inserire il settore ATECO "
                "della tua attività o il numero di dipendenti: la piattaforma ti mostra esattamente la matrice degli obblighi "
                "pertinenti, distinguendo tra lavoratori, preposti, dirigenti, addetti alle emergenze e RSPP."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_06_corsi_online",
            "number": 6,
            "title": "Come funzionano i corsi online (E-Learning)",
            "content": (
                "I corsi online sono asincroni: inizi subito, metti in pausa quando devi lavorare e riprendi quando hai tempo. "
                "Anche la sera o nel weekend. I moduli video e le dispense sono sempre disponibili. Al termine, svolgi il test di "
                "verifica direttamente online con esito istantaneo e rilascio immediato del certificato a norma di legge."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_07_corsi_aula",
            "number": 7,
            "title": "Come funzionano i corsi in aula e le prove pratiche",
            "content": (
                "Per le attrezzature di lavoro (carrelli elevatori, piattaforme elevabili, gru, macchine movimento terra) "
                "e per i moduli pratici antincendio/primo soccorso che la legge non consente in modalità FAD pura, 81+ ti "
                "propone le edizioni sul tuo territorio convenzionate tramite il Centro di Formazione Territoriale ANFOS (Centro RO/3). "
                "Iscrivi i lavoratori, ricevi la convocazione ufficiale e completi la prova pratica con istruttori abilitati."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_08_documenti",
            "number": 8,
            "title": "Come funzionano i documenti e i servizi",
            "content": (
                "Se ti serve redigere o aggiornare il Documento di Valutazione dei Rischi (DVR), un POS per cantiere edile o "
                "il piano di autocontrollo HACCP, compili un questionario guidato con i dati dell'unità produttiva. "
                "Il documento viene elaborato secondo i modelli standard ministeriali e validato da tecnici abilitati."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_09_costi_trasparenza",
            "number": 9,
            "title": "Cosa si paga e cosa si ottiene (Trasparenza Assoluta)",
            "content": (
                "Zero costi nascosti, zero abbonamenti a trabocchetto. Vedi il prezzo prima di iniziare. "
                "Su molti percorsi formativi puoi seguire la didattica online gratuitamente ed effettuare il pagamento solo "
                "al superamento del test per l'emissione dell'attestato fiscale con codice univoco e QR-Code anticontraffazione. "
                "Sai esattamente quanto spendi prima di confermare."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_10_non_so_cosa_serve",
            "number": 10,
            "title": "Cosa fare se non sai cosa ti serve",
            "content": (
                "Ottimo: comprare corsi a caso sarebbe un metodo innovativo, ma poco consigliabile. "
                "Se hai dubbi su quale corso sia obbligatorio per la tua mansione o se il tuo vecchio attestato sia ancora valido, "
                "la piattaforma include un check guidato in 3 clic: inserisci il settore o carica l'attestato per verificarne la validità."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_11_benefici_concreti",
            "number": 11,
            "title": "Benefici concreti per l'imprenditore",
            "content": (
                "• Tempo risparmiato: niente mattinate perse in aula per materie che puoi seguire online nei ritagli di tempo.\n"
                "• Meno passaggi: un unico account per corsi dei lavoratori, attestati carrellisti, DVR e rinnovi.\n"
                "• Tranquillità nei controlli: attestati rilasciati da Ente Paritetico Nazionale ANFOS con QR-Code verificabile "
                "in tempo reale dagli organi di vigilanza (ASL, ITL, Vigili del Fuoco)."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_12_dopo_primo_utilizzo",
            "number": 12,
            "title": "Cosa succede dopo il primo utilizzo (Lo Scadenziario)",
            "content": (
                "Non ti abbandoniamo dopo il primo attestato. Tutti i corsi e i documenti completati confluiscono nel tuo "
                "Registro Digitale Aziendale. La piattaforma calcola le scadenze legali (es. 5 anni per i lavoratori, 2 anni per "
                "i preposti, 3 anni per il primo soccorso) e ti avvisa per tempo, evitando il rischio di scadenze dimenticate."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_13_faq",
            "number": 13,
            "title": "FAQ vere (Risposte senza giri di parole)",
            "content": (
                "Q: Gli attestati sono validi per legge in tutta Italia?\n"
                "A: Sì, sono emessi in piena conformità all'art. 37 del D.Lgs. 81/08 e ai vigenti Accordi Stato-Regioni tramite Ente Paritetico accreditato.\n\n"
                "Q: Cosa succede se un dipendente non supera il test finale?\n"
                "A: Può ripetere il test gratuitamente senza costi aggiuntivi dopo aver ripassato i moduli formativi.\n\n"
                "Q: Ci pensa già il mio commercialista o consulente paghe?\n"
                "A: Il commercialista si occupa di tasse e contabilità. 81+ si integra perfettamente con i consulenti fornendo loro gli attestati pronti senza perdite di tempo."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_14_quick_start",
            "number": 14,
            "title": "Quick Start in 60 secondi",
            "content": (
                "1. Clicca su 'VAI SULLA PIATTAFORMA'.\n"
                "2. Registra l'account con la tua email.\n"
                "3. Scegli il tuo corso o documento.\n"
                "4. Inizia subito o fissa la data dell'aula."
            ),
            "cta": CTA_UNIVERSALE
        },
        {
            "id": "sec_15_cta_finale",
            "number": 15,
            "title": "La decisione più semplice",
            "content": (
                "Rimandare a lunedì non rende la sicurezza più leggera. Fai il primo passo adesso.\n"
                "Entra, controlla e risolvi in pochi minuti."
            ),
            "cta": CTA_UNIVERSALE
        }
    ]

def generate_guide_markdown(sections: list[dict]) -> str:
    md = [
        f"# {GUIDE_TITLE}",
        f"### *{GUIDE_SUBTITLE}*",
        "\n---\n"
    ]
    for s in sections:
        md.append(f"## {s['number']}. {s['title']}")
        md.append(f"{s['content']}\n")
        md.append(f"👉 **[{s['cta']} →]({CTA_URL})**\n")
        md.append("---\n")
    return "\n".join(md)

def generate_guide_html(sections: list[dict]) -> str:
    html_sections = []
    for s in sections:
        content_html = s['content'].replace('\n', '<br>')
        html_sections.append(f"""
        <div class="guide-card" id="{s['id']}">
            <div class="card-num">{s['number']:02d}</div>
            <h2>{s['title']}</h2>
            <div class="card-body">{content_html}</div>
            <div class="card-action">
                <a href="{CTA_URL}" class="btn-primary" id="cta_{s['id']}">{s['cta']} &rarr;</a>
            </div>
        </div>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{GUIDE_TITLE}</title>
    <meta name="description" content="{GUIDE_SUBTITLE}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #090d16;
            --surface: #111827;
            --surface-elevated: #1f2937;
            --border: #374151;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --accent: #10b981;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            padding: 40px 20px;
        }}
        .container {{ max-width: 880px; margin: 0 auto; }}
        .hero {{ text-align: center; margin-bottom: 60px; }}
        .badge {{
            display: inline-block;
            background: rgba(37, 99, 235, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 6px 16px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            font-size: 1.25rem;
            color: var(--text-muted);
            max-width: 680px;
            margin: 0 auto 30px;
        }}
        .hero-cta a {{
            display: inline-block;
            background: var(--primary);
            color: #ffffff;
            font-weight: 700;
            padding: 16px 36px;
            border-radius: 12px;
            text-decoration: none;
            font-size: 1.15rem;
            transition: all 0.2s ease;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.4);
        }}
        .hero-cta a:hover {{ background: var(--primary-hover); transform: translateY(-2px); }}
        .guide-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 30px;
            position: relative;
            transition: border-color 0.2s;
        }}
        .guide-card:hover {{ border-color: #4b5563; }}
        .card-num {{
            display: inline-block;
            color: #60a5fa;
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 8px;
        }}
        .guide-card h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            margin-bottom: 16px;
            color: #f8fafc;
        }}
        .card-body {{
            color: #cbd5e1;
            font-size: 1.05rem;
            margin-bottom: 24px;
        }}
        .btn-primary {{
            display: inline-flex;
            align-items: center;
            background: #1e293b;
            color: #60a5fa;
            border: 1px solid #3b82f6;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
        }}
        .btn-primary:hover {{
            background: var(--primary);
            color: #ffffff;
        }}
        .footer {{
            text-align: center;
            margin-top: 80px;
            padding-top: 40px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <span class="badge">Guida Ufficiale Ecosistema 81+</span>
            <h1>{GUIDE_TITLE}</h1>
            <p class="subtitle">{GUIDE_SUBTITLE}</p>
            <div class="hero-cta">
                <a href="{CTA_URL}" id="hero_cta_main">{CTA_UNIVERSALE} &rarr;</a>
            </div>
        </div>

        {''.join(html_sections)}

        <div class="footer">
            <p>© 81+ Autonomous Compliance & Revenue OS — Centro di Formazione Territoriale Convenzionato ANFOS RO/3</p>
            <p style="margin-top: 8px;">CTA Primaria Universale: <strong>{CTA_UNIVERSALE}</strong></p>
        </div>
    </div>
</body>
</html>
"""
    return full_html

def build_and_save_guide():
    """Genera, registra su DB e salva su disco gli asset della guida."""
    sections = get_guide_sections()
    markdown_content = generate_guide_markdown(sections)
    html_content = generate_guide_html(sections)

    # 1. Salva su disco docs/
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
    os.makedirs(docs_dir, exist_ok=True)
    
    md_path = os.path.join(docs_dir, "GUIDA_PIATTAFORMA_81PLUS_SENZA_MANUALE.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    html_path = os.path.join(docs_dir, "guida_piattaforma_81plus.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. Salva JSON machine-readable in knowledge/
    kb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge"))
    os.makedirs(kb_dir, exist_ok=True)
    kb_path = os.path.join(kb_dir, "platform_guide.json")
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump({
            "title": GUIDE_TITLE,
            "subtitle": GUIDE_SUBTITLE,
            "one_cta": CTA_UNIVERSALE,
            "target_url": CTA_URL,
            "generated_at": datetime.now().isoformat(),
            "sections": sections
        }, f, indent=2, ensure_ascii=False)

    # 3. Versiona su DB SQLite
    conn = get_connection()
    cursor = conn.cursor()
    version_id = f"guide_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Disattiva vecchie versioni
    cursor.execute("UPDATE platform_guide_versions SET is_active = 0 WHERE is_active = 1")
    cursor.execute("""
        INSERT INTO platform_guide_versions
        (version_id, title, subtitle, content_html, content_markdown, sections_json, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
    """, (version_id, GUIDE_TITLE, GUIDE_SUBTITLE, html_content, markdown_content, json.dumps(sections)))

    conn.commit()
    conn.close()

    print(f"[OK] Guida Piattaforma 81+ compilata:")
    print(f" - Markdown: {md_path}")
    print(f" - HTML Web: {html_path}")
    print(f" - Knowledge JSON: {kb_path}")
    print(f" - DB Version: {version_id} (Active)")
    return version_id

if __name__ == "__main__":
    v = build_and_save_guide()
