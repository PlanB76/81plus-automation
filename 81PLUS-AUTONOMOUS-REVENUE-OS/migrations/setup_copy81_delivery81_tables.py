"""
81PLUS-AUTONOMOUS-REVENUE-OS
migrations/setup_copy81_delivery81_tables.py — Setup Tabelle COPY81 & DELIVERY81
"""
import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

def setup_tables():
    conn = get_connection()
    cur = conn.cursor()
    
    print("📦 Creazione tabelle COPY81 e DELIVERY81 nel database centrale...")
    
    # 1. Communication Profiles (Communication Twin)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS communication_profiles (
        contact_id INTEGER PRIMARY KEY,
        current_episode INTEGER DEFAULT 1,
        awareness_temp TEXT DEFAULT 'W20',
        dominant_need TEXT,
        dominant_objection TEXT,
        last_angle_seen TEXT,
        winning_angle TEXT,
        total_emails_sent INTEGER DEFAULT 0,
        total_opens INTEGER DEFAULT 0,
        total_clicks_platform INTEGER DEFAULT 0,
        is_registered INTEGER DEFAULT 0,
        is_buyer INTEGER DEFAULT 0,
        last_reaction TEXT, -- NO_OPEN, OPEN_NO_CLICK, CLICK_NO_REG, REGISTERED, BOUGHT, UNSUBSCRIBED
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_id) REFERENCES compliance_digital_twin(contact_id)
    );
    """)
    
    # 2. Narrative Episodes (I 12 Episodi Canonici)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS narrative_episodes (
        episode_num INTEGER PRIMARY KEY,
        titolo TEXT NOT NULL,
        obiettivo_cognitivo TEXT NOT NULL,
        hook_pattern_break TEXT NOT NULL,
        corpo_problema TEXT NOT NULL,
        beneficio_chiave TEXT NOT NULL,
        prova_trasparenza TEXT NOT NULL,
        cta_testo TEXT DEFAULT 'VAI SULLA PIATTAFORMA',
        cta_url TEXT DEFAULT 'https://81plus.net'
    );
    """)
    
    # 3. Objection Taxonomy (Le 10 Obiezioni Comuni e le Soluzioni)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS objection_taxonomy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codice_obiezione TEXT UNIQUE NOT NULL,
        descrizione_obiezione TEXT NOT NULL,
        angolo_risolutivo TEXT NOT NULL,
        risposta_antino TEXT NOT NULL,
        max_tentativi INTEGER DEFAULT 2
    );
    """)
    
    # 4. Training Delivery Catalog (Doppio Canale: FAD PID 2377 vs AULA ANFOS)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS training_delivery_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codice_corso TEXT UNIQUE NOT NULL,
        nome_corso TEXT NOT NULL,
        macro_settore TEXT NOT NULL, -- EDILIZIA, FOOD_HACCP, GENERALE_PMI, TRASVERSALE
        delivery_mode TEXT NOT NULL, -- ONLINE_FAD, AULA_PRESENZA, BLENDED, DOCUMENTALE
        provider_platform TEXT NOT NULL, -- FAD_PID_2377, ANFOS_CENTRI, 81PLUS_INTERNAL
        costo_base_attestato REAL NOT NULL, -- es. 10.0 - 30.0 euro per ANFOS
        prezzo_vendita_consigliato REAL NOT NULL, -- es. 150.0 - 300.0 euro
        margine_stimato_pct REAL NOT NULL,
        durata_ore INTEGER NOT NULL,
        validita_anni INTEGER NOT NULL,
        descrizione TEXT
    );
    """)
    
    # Popolamento cataloghi base
    # Episodi
    episodes = [
        (1, "Il problema che non sapevi di avere", "Pattern Break & Consapevolezza", 
         "Hai presente quel corso che 'facciamo la settimana prossima'? La settimana prossima ha un talento particolare: riesce a non arrivare mai.",
         "Capire chi deve fare cosa non dovrebbe richiedere una mezza giornata di ricerche.",
         "Con 81+ trovi corsi e documenti in un unico percorso semplice.", "A norma di legge D.Lgs. 81/08."),
        (2, "La caccia al tesoro dei documenti", "Riconoscimento del dolore",
         "Un corso qui. Un attestato là. Un PDF disperso dal 2023. Cercarli in 5 posti diversi non è una competenza richiesta dal Testo Unico.",
         "Centralizza corsi, scadenze e attestati in un solo cassetto digitale.",
         "Risparmia fino all'80% del tempo perso in ricerche burocratiche.", "Attestati validi a livello nazionale."),
        (3, "Perché abbiamo costruito la piattaforma", "Presentazione Soluzione",
         "La sicurezza sul lavoro è già abbastanza complicata. Noi abbiamo evitato di complicarti anche il modo di gestirla.",
         "Corsi online immediati e sessioni pratiche in aula gestiti senza intermediari lenti.",
         "Entri, trovi il tuo codice ATECO e hai tutto in regola in pochi passaggi.", "Ente Paritetico Nazionale Accreditato."),
        (4, "Cosa trovi davvero dentro", "Chiarezza Catalogo (Online + Aula)",
         "Non devi diventare esperto di normative. C'è solo ciò che serve alla tua impresa.",
         "Dalla formazione generale online all'addestramento pratico su carrelli ed estintori.",
         "Un catalogo completo con prezzi trasparenti e zero abbonamenti vincolanti.", "Conformità garantita al 100%."),
        (5, "Come funziona in 60 secondi", "Abbattimento frizione d'ingresso",
         "Nessun manuale da 80 pagine per capire da dove partire.",
         "1. Entri. 2. Scegli corso o documento. 3. Completi online o prenoti l'aula. 4. Scarichi l'attestato.",
         "Attivazione istantanea senza attese telefoniche.", "Tracciamento SCORM certificato."),
        (6, "Ma io non so cosa mi serve!", "Guida per ATECO",
         "Comprare corsi a caso sarebbe un metodo originale, ma poco efficace.",
         "Inserisci il tuo settore e il Safety Check ti mostra solo i tuoi obblighi minimi indispensabili.",
         "Zero corsi inutili, solo la reale conformità richiesta agli ispettori.", "Matrice ATECO costantemente aggiornata."),
        (7, "Non ho tempo per queste cose", "Flessibilità 24/7",
         "È aperta quando hai tempo tu. Sì, anche quando ti ricordi della sicurezza alle 22:47 della domenica sera.",
         "Fai i corsi online quando vuoi, spezzandoli in lezioni da 15 minuti su smartphone o PC.",
         "Salva i progressi al secondo, senza dover ricominciare da capo.", "Disponibilità garantita 24 ore su 24, 7 giorni su 7."),
        (8, "Quanto costa davvero?", "Trasparenza economica",
         "Nessun asterisco creativo, nessun costo nascosto a sorpresa.",
         "Tariffe chiare, fattura elettronica immediata e deducibile al 100% come costo sicurezza aziendale.",
         "Paghi solo quello che usi, con sconti dedicati su pacchetti per più lavoratori.", "Prezzi equi e trasparenti."),
        (9, "Gli errori che costano cari (senza terrorismo)", "Autorevolezza",
         "Non parliamo di multe apocalittiche. Parliamo di non farsi bloccare un cantiere o un'ispezione per un attestato scaduto.",
         "Verifica preventiva degli attestati e della patente a crediti per lavorare in serenità.",
         "La tranquillità di sapere che tutti i tuoi collaboratori sono abilitati a norma.", "Verificato contro il D.Lgs. 81/08."),
        (10, "Il tuo settore specifico (Edilizia / Food / PMI)", "Rilevanza verticale",
         "Cantiere edile o ristorante? La sicurezza non è una taglia unica.",
         "POS cantieri in 90 secondi per le imprese edili, manuali e registri HACCP per i ristoratori.",
         "Documenti conformi compilati con precisione millimetrica.", "Allineato alle linee guida ASL e ITL."),
        (11, "Cosa succede dopo (Lo Scadenzario Perpetuo)", "Fidelizzazione",
         "Fatto il corso, non ti lasciamo solo con l'ansia di ricordarti quando scade.",
         "Calcoliamo la data di rinnovo e ti avvisiamo noi con 3 mesi di anticipo prima della scadenza.",
         "Zero dimenticanze, zero rinnovi dell'ultimo secondo.", "Notifiche di cortesia su misura."),
        (12, "La decisione più semplice", "Chiusura serena",
         "Continuare a rimandare o toglierti il pensiero in 10 minuti?",
         "Il link è sempre lo stesso: entra e chiudiamo la pratica prima della fine della settimana.",
         "Meno burocrazia, più tempo per la tua impresa.", "Unisciti alle migliaia di aziende già in regola.")
    ]
    
    for ep in episodes:
        cur.execute("""
            INSERT OR REPLACE INTO narrative_episodes 
            (episode_num, titolo, obiettivo_cognitivo, hook_pattern_break, corpo_problema, beneficio_chiave, prova_trasparenza)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ep)
        
    # Obiezioni
    objections = [
        ("NO_TEMPO", "Non ho tempo per seguire i corsi", "SEMPLICITA_TEMPO", "Piattaforma fruibile 24/7 in micro-moduli da 15 minuti su qualsiasi dispositivo.", 2),
        ("NO_SCELTA", "Non so quale corso mi serve", "GUIDA_ATECO", "Safety Check automatico per codice ATECO in 90 secondi.", 2),
        ("NO_FUNZIONA", "Non so come funziona la piattaforma", "GUIDA_RAPIDA", "Guida visiva in 4 step '81+ Senza Manuale'.", 2),
        ("COSTO_DUBBIO", "Quanto mi costa davvero?", "TRASPARENZA_PREZZI", "Nessun abbonamento, prezzi chiari, fattura elettronica deducibile 100%.", 2),
        ("PROCRASTINA", "Lo faccio più avanti", "TIMING_PREVENTIVO", "Prevenire sanzioni e blocchi di cantiere prima dell'ispezione.", 2),
        ("GIA_FATTO", "Ho già fatto tutti i corsi", "SCADENZIARIO_PERPETUO", "Verifica gratuita delle date di scadenza per non perdere i crediti acquisiti.", 1),
        ("COMMERCIALISTA", "Ci pensa già il mio commercialista", "COMPLEMENTARITA", "Il commercialista gestisce i cedolini, 81+ fornisce attestati e POS a norma.", 2),
        ("DIFFIDENZA", "Gli attestati sono validi per legge?", "AUTOREVOLEZZA_LEGALE", "Attestati con codice univoco rilasciati da Ente Paritetico Nazionale.", 2),
        ("NO_REGISTRA", "Non voglio registrarmi", "BENEFICIO_ACCOUNT", "L'account gratuito funge da cassetto digitale sicuro per conservare gli attestati.", 2),
        ("AULA_VS_ONLINE", "Questo corso devo farlo online o in aula?", "ROUTING_IBRIDO", "Teoria online 24/7, prova pratica in aula sui centri ANFOS territoriali.", 2)
    ]
    for ob in objections:
        cur.execute("""
            INSERT OR REPLACE INTO objection_taxonomy 
            (codice_obiezione, descrizione_obiezione, angolo_risolutivo, risposta_antino, max_tentativi)
            VALUES (?, ?, ?, ?, ?)
        """, ob)
        
    # Catalogo Prodotti (Dual Delivery)
    catalog = [
        ("FAD_GEN_4H", "Formazione Generale Lavoratori (4h)", "TRASVERSALE", "ONLINE_FAD", "FAD_PID_2377", 12.0, 45.0, 73.3, 4, 5, "Corso base per tutti i lavoratori"),
        ("FAD_SPEC_BASSO_4H", "Formazione Specifica Rischio Basso (4h)", "GENERALE_PMI", "ONLINE_FAD", "FAD_PID_2377", 15.0, 55.0, 72.7, 4, 5, "Per uffici, commercio e servizi"),
        ("FAD_AGGIORN_LAV_6H", "Aggiornamento Lavoratori Quinquennale (6h)", "TRASVERSALE", "ONLINE_FAD", "FAD_PID_2377", 18.0, 65.0, 72.3, 6, 5, "Rinnovo obbligatorio ogni 5 anni"),
        ("FAD_RSPP_DATORE_16H", "RSPP Datore di Lavoro Rischio Basso (16h)", "GENERALE_PMI", "ONLINE_FAD", "FAD_PID_2377", 45.0, 190.0, 76.3, 16, 5, "Abilitazione per titolari d'azienda"),
        ("FAD_HACCP_RESP_12H", "Responsabile HACCP / Alimentaristi (12h)", "FOOD_HACCP", "ONLINE_FAD", "FAD_PID_2377", 25.0, 95.0, 73.7, 12, 3, "Per titolari di ristoranti, bar e alimentari"),
        ("AULA_ANTINCENDIO_L2", "Addetto Antincendio Livello 2 (8h - Teoria + Prove)", "TRASVERSALE", "BLENDED", "ANFOS_CENTRI", 25.0, 220.0, 88.6, 8, 3, "Corso con prova pratica estintori"),
        ("AULA_PRIMOSOCCORSO_GRUPPO_B", "Primo Soccorso Aziendale Gruppo B-C (12h)", "TRASVERSALE", "AULA_PRESENZA", "ANFOS_CENTRI", 28.0, 240.0, 88.3, 12, 3, "Corso con prove pratiche manovre BLS"),
        ("AULA_MULETTO_CARRELLI_12H", "Abilitazione Carrelli Elevatori Semoventi (12h)", "EDILIZIA", "BLENDED", "ANFOS_CENTRI", 30.0, 260.0, 88.5, 12, 5, "Patentino muletto con addestramento pratico"),
        ("AULA_PLE_CON_STABILIZZATORI", "Abilitazione Piattaforme PLE (10h)", "EDILIZIA", "BLENDED", "ANFOS_CENTRI", 30.0, 250.0, 88.0, 10, 5, "Patentino cestello aereo con prova pratica"),
        ("DOC_POS_CANTIERI_AUTO", "Generatore Piano Operativo di Sicurezza (POS)", "EDILIZIA", "DOCUMENTALE", "81PLUS_INTERNAL", 0.0, 180.0, 100.0, 0, 1, "POS cantiere guidato in 90 secondi"),
        ("DOC_HACCP_REGISTRI_AUTO", "Manuale e Registri Sanificazione HACCP", "FOOD_HACCP", "DOCUMENTALE", "81PLUS_INTERNAL", 0.0, 140.0, 100.0, 0, 1, "Registri temperature e sanificazione")
    ]
    for cat in catalog:
        cur.execute("""
            INSERT OR REPLACE INTO training_delivery_catalog
            (codice_corso, nome_corso, macro_settore, delivery_mode, provider_platform, costo_base_attestato, prezzo_vendita_consigliato, margine_stimato_pct, durata_ore, validita_anni, descrizione)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cat)
        
    conn.commit()
    conn.close()
    print("✅ Tabelle COPY81 e DELIVERY81 configurate e popolate con successo!")

if __name__ == '__main__':
    setup_tables()
