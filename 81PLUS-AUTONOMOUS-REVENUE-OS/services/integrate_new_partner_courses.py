import sys, os, sqlite3
from datetime import datetime

sys.path.insert(0, r'c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\81PLUS-AUTONOMOUS-REVENUE-OS')
from shared.database.db import get_connection

conn = get_connection()
cur = conn.cursor()
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 1. Aggiornamento link ref precisi nella tabella partner
cur.execute("""
    UPDATE partner
    SET url_piattaforma = 'https://www.lezione-online.it/?ref=6232899',
        provvigione_pct = 50.0,
        note = 'Partner Ufficiale Lezione Online. Link ref: https://www.lezione-online.it/?ref=6232899'
    WHERE nome LIKE '%Lezione-Online%';
""")

cur.execute("""
    UPDATE partner
    SET url_piattaforma = 'https://differentacademy.it/?ref=labomobile',
        provvigione_pct = 50.0,
        note = 'Partner Ufficiale Different Academy. Link ref: https://differentacademy.it/?ref=labomobile'
    WHERE nome LIKE '%Different Academy%';
""")
conn.commit()

# 2. Censimento Corsi dei 2 Nuovi Partners nel Catalogo Centrale
# Assicuriamo che la tabella training_delivery_catalog abbia la colonna referral_url
cols = [c['name'] for c in cur.execute("PRAGMA table_info(training_delivery_catalog);").fetchall()]
if 'referral_url' not in cols:
    cur.execute("ALTER TABLE training_delivery_catalog ADD COLUMN referral_url TEXT;")
if 'partner_name' not in cols:
    cur.execute("ALTER TABLE training_delivery_catalog ADD COLUMN partner_name TEXT;")

nuovi_corsi = [
    # LEZIONE-ONLINE.IT (Ref: https://www.lezione-online.it/?ref=6232899)
    {
        "codice": "LEZ_EXCEL_PRO",
        "nome": "Excel Avanzato, Formule e Dashboard per l'Impresa",
        "macro": "INFORMATICA_DIGITALE",
        "delivery": "ONLINE_FAD",
        "provider": "LEZIONE_ONLINE_6232899",
        "partner": "Lezione-Online.it",
        "costo_attestato": 0.0,
        "prezzo": 79.0,
        "margine_pct": 50.0,
        "ore": 12,
        "validita": 99,
        "desc": "Corso pratico di Excel per titolari, amministrazione e uffici.",
        "ref": "https://www.lezione-online.it/?ref=6232899"
    },
    {
        "codice": "LEZ_PAGHE_CONTAB",
        "nome": "Contabilità Aziendale, Buste Paga e Gestione Fiscale PMI",
        "macro": "AMMINISTRAZIONE_LAVORO",
        "delivery": "ONLINE_FAD",
        "provider": "LEZIONE_ONLINE_6232899",
        "partner": "Lezione-Online.it",
        "costo_attestato": 0.0,
        "prezzo": 129.0,
        "margine_pct": 50.0,
        "ore": 20,
        "validita": 99,
        "desc": "Percorso completo di amministrazione aziendale per dipendenti e titolari.",
        "ref": "https://www.lezione-online.it/?ref=6232899"
    },
    {
        "codice": "LEZ_MKT_SOCIAL_PMI",
        "nome": "Marketing e Social Media per Piccole e Medie Imprese",
        "macro": "MARKETING_VENDITE",
        "delivery": "ONLINE_FAD",
        "provider": "LEZIONE_ONLINE_6232899",
        "partner": "Lezione-Online.it",
        "costo_attestato": 0.0,
        "prezzo": 99.0,
        "margine_pct": 50.0,
        "ore": 15,
        "validita": 99,
        "desc": "Acquisizione clienti con Meta Ads, Google e presenza online per aziende locali.",
        "ref": "https://www.lezione-online.it/?ref=6232899"
    },
    {
        "codice": "LEZ_CANVA_GRAFICA",
        "nome": "Grafica per la Comunicazione Aziendale e Social con Canva",
        "macro": "GRAFICA_CREATIVITA",
        "delivery": "ONLINE_FAD",
        "provider": "LEZIONE_ONLINE_6232899",
        "partner": "Lezione-Online.it",
        "costo_attestato": 0.0,
        "prezzo": 59.0,
        "margine_pct": 50.0,
        "ore": 8,
        "validita": 99,
        "desc": "Creazione autonoma di grafiche promozionali, volantini e brochure per l'azienda.",
        "ref": "https://www.lezione-online.it/?ref=6232899"
    },
    {
        "codice": "LEZ_INGLESE_BUSINESS",
        "nome": "Inglese Commerciale e Tecnico per Professionisti e Imprese",
        "macro": "LINGUE_BUSINESS",
        "delivery": "ONLINE_FAD",
        "provider": "LEZIONE_ONLINE_6232899",
        "partner": "Lezione-Online.it",
        "costo_attestato": 0.0,
        "prezzo": 149.0,
        "margine_pct": 50.0,
        "ore": 30,
        "validita": 99,
        "desc": "Comunicazione commerciale, email e trattative in lingua inglese per B2B.",
        "ref": "https://www.lezione-online.it/?ref=6232899"
    },
    {
        "codice": "LEZ_AUTOCAD_2D3D",
        "nome": "AutoCAD 2D e 3D per Studi Tecnici e Carpenteria",
        "macro": "PROFESSIONI_TECNICHE",
        "delivery": "ONLINE_FAD",
        "provider": "LEZIONE_ONLINE_6232899",
        "partner": "Lezione-Online.it",
        "costo_attestato": 0.0,
        "prezzo": 189.0,
        "margine_pct": 50.0,
        "ore": 35,
        "validita": 99,
        "desc": "Progettazione tecnica assistita per geometri, periti, impiantisti edili e meccanici.",
        "ref": "https://www.lezione-online.it/?ref=6232899"
    },
    
    # DIFFERENT ACADEMY (Ref: https://differentacademy.it/?ref=labomobile)
    {
        "codice": "DIF_EXEC_LEADERSHIP",
        "nome": "Executive Master in Leadership e Team Management (Certificato ISO 9001)",
        "macro": "ALTA_FORMAZIONE_MANAGERIALE",
        "delivery": "ONLINE_FAD_MENTORING",
        "provider": "DIFFERENT_ACADEMY_LABOMOBILE",
        "partner": "Different Academy",
        "costo_attestato": 0.0,
        "prezzo": 390.0,
        "margine_pct": 50.0,
        "ore": 45,
        "validita": 99,
        "desc": "Gestione del personale, delega, motivazione e leadership operativa per titolari.",
        "ref": "https://differentacademy.it/?ref=labomobile"
    },
    {
        "codice": "DIF_SOFT_SKILLS_CREAT",
        "nome": "Executive Master in Soft Skills e Sviluppo Creativo Aziendale",
        "macro": "ALTA_FORMAZIONE_MANAGERIALE",
        "delivery": "ONLINE_FAD_MENTORING",
        "provider": "DIFFERENT_ACADEMY_LABOMOBILE",
        "partner": "Different Academy",
        "costo_attestato": 0.0,
        "prezzo": 350.0,
        "margine_pct": 50.0,
        "ore": 40,
        "validita": 99,
        "desc": "Problem solving complesso, negoziazione commerciale e comunicazione efficace.",
        "ref": "https://differentacademy.it/?ref=labomobile"
    },
    {
        "codice": "DIF_HR_AI_APPLIED",
        "nome": "Master Specialistico in Risorse Umane e Intelligenza Artificiale Applicata",
        "macro": "HR_INNOVAZIONE",
        "delivery": "ONLINE_FAD_MENTORING",
        "provider": "DIFFERENT_ACADEMY_LABOMOBILE",
        "partner": "Different Academy",
        "costo_attestato": 0.0,
        "prezzo": 450.0,
        "margine_pct": 50.0,
        "ore": 50,
        "validita": 99,
        "desc": "Automazione recruiting, gestione performance e strumenti AI per la gestione del personale.",
        "ref": "https://differentacademy.it/?ref=labomobile"
    },
    {
        "codice": "DIF_INFINITY_PASS",
        "nome": "Different Infinity — Accesso All-Inclusive Certificazioni ISO 9001",
        "macro": "ACADEMY_SUBSCRIPTION",
        "delivery": "ONLINE_FAD_PASS",
        "provider": "DIFFERENT_ACADEMY_LABOMOBILE",
        "partner": "Different Academy",
        "costo_attestato": 0.0,
        "prezzo": 590.0,
        "margine_pct": 50.0,
        "ore": 120,
        "validita": 99,
        "desc": "Abbonamento annuale illimitato a tutti i master e corsi con sessioni di Skill Coaching.",
        "ref": "https://differentacademy.it/?ref=labomobile"
    }
]

# Inserimento nel catalogo
for c in nuovi_corsi:
    cur.execute("""
        INSERT OR REPLACE INTO training_delivery_catalog (
            codice_corso, nome_corso, macro_settore, delivery_mode, provider_platform,
            costo_base_attestato, prezzo_vendita_consigliato, margine_stimato_pct,
            durata_ore, validita_anni, descrizione, referral_url, partner_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        c["codice"], c["nome"], c["macro"], c["delivery"], c["provider"],
        c["costo_attestato"], c["prezzo"], c["margine_pct"],
        c["ore"], c["validita"], c["desc"], c["ref"], c["partner"]
    ))

conn.commit()

# 3. Creazione / Aggiornamento Flussi Email Dedicati nella Macchina (leadgen_flows & leadgen_flow_steps)
# Aggiungiamo 2 flussi specifici nell'albero 81+:
# 1. FLOW_ACADEMY_LEZIONEONLINE (per upskill pratico, informatica, buste paga, marketing)
# 2. FLOW_ACADEMY_DIFFERENT (per titolari, executive, leadership, ISO 9001)

flussi_nuovi = [
    {
        "code": "FLOW_ACADEMY_LEZIONEONLINE",
        "name": "Academy PMI: Competenze Pratiche & Uffici con Lezione-Online",
        "trigger": "NURTURE_STAGE_ACADEMY_LEZ",
        "segment": "MEMBER81",
        "cluster": "Academy Formazione Continua",
        "notes": "Affiliazione Ufficiale Lezione Online; Provvigione 50%; Ref https://www.lezione-online.it/?ref=6232899"
    },
    {
        "code": "FLOW_ACADEMY_DIFFERENT",
        "name": "Academy Executive: Leadership & Master Manageriali con Different Academy",
        "trigger": "NURTURE_STAGE_ACADEMY_DIF",
        "segment": "CLUB81",
        "cluster": "Alta Formazione & Leadership",
        "notes": "Affiliazione Ufficiale Different Academy; Provvigione 50%; Ref https://differentacademy.it/?ref=labomobile"
    }
]

for fl in flussi_nuovi:
    cur.execute("""
        INSERT OR REPLACE INTO leadgen_flows (
            flow_code, flow_name, trigger_event, target_segment, status, priority, notes, cluster, is_paused
        ) VALUES (?, ?, ?, ?, 'ACTIVE', 150, ?, ?, 0)
    """, (fl["code"], fl["name"], fl["trigger"], fl["segment"], fl["notes"], fl["cluster"]))

# Step Email con link ref effettivi
steps_nuovi = [
    # LEZIONE ONLINE STEP 1, 2, 3
    (
        "FLOW_ACADEMY_LEZIONEONLINE", 1, 0, "EMAIL",
        "[81+ Academy] Oltre la conformità: fai crescere il tuo ufficio con le competenze giuste",
        "Ciao {{first_name}},\n\nMettere a norma la tua azienda con DVR e sicurezza è il primo passo per proteggerti. Ma un'azienda solida cresce se il personale migliora le sue competenze operative ogni giorno: dalla contabilità a Excel avanzato, dal marketing alla gestione interna.\n\nAttraverso la convenzione con Lezione-Online, hai accesso immediato a oltre 800 corsi pratici on-demand con attestato certificato.\n\nScegli il percorso per te o per i tuoi collaboratori.",
        "VAI AL CATALOGO CORSI", "https://www.lezione-online.it/?ref=6232899", "ACADEMY_LEZ_01", 100, 1
    ),
    (
        "FLOW_ACADEMY_LEZIONEONLINE", 2, 72, "EMAIL",
        "Excel, Paghe o Marketing? Ecco i 3 percorsi più scelti dalle PMI italiane",
        "Ciao {{first_name}},\n\nIl tempo è la risorsa più scarsa per chi fa impresa. Per questo i corsi di Lezione-Online sono al 100% pratici, senza teoria inutile, con lezioni brevi e accesso a vita 24/7.\n\nScopri i corsi più richiesti e inizia subito.",
        "SCOPRI I CORSI IN PROMOZIONE", "https://www.lezione-online.it/?ref=6232899", "ACADEMY_LEZ_02", 150, 1
    ),
    (
        "FLOW_ACADEMY_LEZIONEONLINE", 3, 144, "EMAIL",
        "Certifica le competenze del tuo team (Attestato di Merito incluso)",
        "Ciao {{first_name}},\n\nOgni corso completato rilascia un doppio attestato valido per il CV e l'inquadramento aziendale. Approfitta del listino convenzionato 81+.\n\nAttiva ora il tuo accesso riservato.",
        "ACCEDI AI CORSI CONVENZIONATI", "https://www.lezione-online.it/?ref=6232899", "ACADEMY_LEZ_03", 200, 1
    ),

    # DIFFERENT ACADEMY STEP 1, 2, 3
    (
        "FLOW_ACADEMY_DIFFERENT", 1, 0, "EMAIL",
        "[81+ Executive Club] Leadership e Gestione del Team: la differenza tra subire e guidare",
        "Ciao {{first_name}},\n\nGestire un'azienda richiede molto più della tecnica: richiede leadership, capacità di delega, negoziazione e gestione dei collaboratori.\n\nIn partnership con Different Academy, abbiamo riservato per i titolari e dirigenti 81+ l'accesso agli Executive Master con certificazione internazionale ISO 9001 valida in oltre 160 paesi.\n\nScopri il programma Executive Leadership.",
        "SCOPRI IL MASTER EXECUTIVE", "https://differentacademy.it/?ref=labomobile", "ACADEMY_DIF_01", 250, 1
    ),
    (
        "FLOW_ACADEMY_DIFFERENT", 2, 72, "EMAIL",
        "Executive Coaching e Certificazione ISO 9001: accelera i risultati aziendali",
        "Ciao {{first_name}},\n\nI Master di Different Academy includono sessioni con Skill Coach dedicati per applicare subito il metodo alla tua realtà aziendale.\n\nDai Risorse Umane e AI Applicata fino al programma Different Infinity con accesso completo a tutti i percorsi.\n\nRichiedi informazioni sul percorso convenzionato.",
        "RICHIEDI L'ACCESSO EXECUTIVE", "https://differentacademy.it/?ref=labomobile", "ACADEMY_DIF_02", 300, 1
    ),
    (
        "FLOW_ACADEMY_DIFFERENT", 3, 144, "EMAIL",
        "Posti riservati per l'Executive Club 81+: fissa la tua sessione di orientamento",
        "Ciao {{first_name}},\n\nLe classi executive sono a numero chiuso per garantire la massima interazione con i mentor del settore.\n\nFissa la tua call orientativa con lo Skill Coach e riserva la tua iscrizione con i benefit 81+.",
        "ISCRIVITI AL MASTER CONVENZIONATO", "https://differentacademy.it/?ref=labomobile", "ACADEMY_DIF_03", 500, 1
    )
]

for s in steps_nuovi:
    cur.execute("""
        INSERT OR REPLACE INTO leadgen_flow_steps (
            flow_code, step_number, delay_hours, channel, subject,
            body_text, cta_label, cta_url, mission_code, pvplus_reward, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, s)

conn.commit()

print("Censimento e integrazione completata:")
print(f"• Corsi totali nel catalogo training_delivery_catalog: {cur.execute('SELECT count(*) FROM training_delivery_catalog;').fetchone()[0]}")
print(f"• Flussi totali attivi in leadgen_flows: {cur.execute('SELECT count(*) FROM leadgen_flows;').fetchone()[0]}")
print(f"• Step email totali in leadgen_flow_steps: {cur.execute('SELECT count(*) FROM leadgen_flow_steps;').fetchone()[0]}")
conn.close()
