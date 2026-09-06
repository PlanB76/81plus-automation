"""
81+ ANFOS AUTONOMOUS NIGHTLY VALIDATION ENGINE
Centro di Formazione Territoriale Convenzionato ANFOS: RO/3
Docente Formatore Accreditato: DOTT. ARCH. DIEGO LIACI PENZO

Missione:
Eseguire una volta al giorno, di notte in totale autonomia (Zero Mani),
la richiesta di esattamente 5 nuove validazioni corso sul portale ANFOS
(https://centri.anfos.it/centri-anfos3/centro/#validazioni) fino al completamento
totale del catalogo corsi (290 corsi attivabili).

Normative di riferimento:
- D.Lgs. 9 aprile 2008 n. 81 e s.m.i.
- Nuovo Accordo Stato-Regioni Formazione Sicurezza 2025 (rep. 59)
- D.M. 2 settembre 2021 (Antincendio)
- D.M. 388/2003 (Primo Soccorso)
- CEI 11-27 (PES/PAV)
- D.P.R. 177/2011 (Spazi Confinati)
"""

import os
import sys
import json
import sqlite3
import re
import time
import logging
from datetime import datetime, timedelta
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ANFOS-BOT] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ANFOS_BOT")

# Constants & Credentials
ANFOS_BASE_URL = "https://centri.anfos.it/centri-anfos3/centro/"
ANFOS_USER = os.getenv("ANFOS_USER", "labomobile.lm@gmail.com")
ANFOS_PASSWORD = os.getenv("ANFOS_PASSWORD", "h29031976T.")
CENTRO_CODICE = "RO/3"
DOCENTE_ACCREDITATO = "DOTT. ARCH. DIEGO LIACI PENZO"
MAX_DAILY_VALIDATIONS = 5

# Local Database Resolution
CANDIDATE_DBS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "emailflux81", "81plus.db"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "emailflux81", "81plus.db"),
    r"c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\emailflux81\81plus.db",
    r"c:\81PLUS_GLOBAL_MASTER\81plus.net\0-81PLUS.NET\81plus.db"
]
DB_PATH = next((p for p in CANDIDATE_DBS if os.path.exists(p)), CANDIDATE_DBS[2])

def init_db(conn: sqlite3.Connection):
    """Ensure table anfos_validation_log exists."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anfos_validation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            corso_id TEXT NOT NULL,
            titolo_corso TEXT NOT NULL,
            gruppo TEXT,
            durata_ore INTEGER,
            data_presunta TEXT,
            docente TEXT,
            esito TEXT NOT NULL,
            response_payload TEXT
        );
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_anfos_date ON anfos_validation_log(timestamp);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_anfos_corso ON anfos_validation_log(corso_id);
    """)
    conn.commit()

def count_today_validations(conn: sqlite3.Connection) -> int:
    """Return count of successful validations submitted today (YYYY-MM-DD)."""
    today_prefix = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM anfos_validation_log 
        WHERE timestamp LIKE ? AND esito = 'SUCCESS'
    """, (f"{today_prefix}%",))
    count = cursor.fetchone()[0]
    return count

def extract_duration_from_title(title: str, group: str) -> int:
    """Extract hours from title using regex, with sensible fallback based on course group."""
    # Pattern: '16 ore', '16ore', '8 h', '40 ore'
    match = re.search(r'(\d+)\s*(?:ore|ora|h\b)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Fallback heuristic based on group or name
    t_lower = title.lower()
    if "rischio alto" in t_lower:
        return 16
    if "rischio medio" in t_lower:
        return 8
    if "rischio basso" in t_lower or "generale" in t_lower:
        return 4
    if "preposto" in t_lower:
        return 12 if "aggiornamento" not in t_lower else 6
    if "dirigente" in t_lower:
        return 16 if "aggiornamento" not in t_lower else 6
    if "primo soccorso" in t_lower:
        return 16 if "aggiornamento" not in t_lower else 6
    if "antincendio 3" in t_lower or "livello 3" in t_lower:
        return 16 if "aggiornamento" not in t_lower else 8
    if "antincendio 2" in t_lower or "livello 2" in t_lower:
        return 8 if "aggiornamento" not in t_lower else 5
    if "antincendio 1" in t_lower or "livello 1" in t_lower:
        return 4 if "aggiornamento" not in t_lower else 2
    if "carrelli" in t_lower or "muletto" in t_lower:
        return 12 if "aggiornamento" not in t_lower else 4
    if "ple" in t_lower:
        return 10 if "aggiornamento" not in t_lower else 4
    if "gru" in t_lower:
        return 12 if "aggiornamento" not in t_lower else 4
    if "aggiornamento" in t_lower:
        return 6
    return 8

def build_compliance_metadata(corso_id: str, title: str, group: str, duration: int) -> tuple[str, str]:
    """
    Generate authoritative legal references and professional didactic syllabus
    fully compliant with D.Lgs. 81/08 and Accordo Stato-Regioni 2025.
    """
    t_lower = title.lower()
    g_lower = group.lower() if group else ""
    
    # 1. Attrezzature di lavoro (Art. 73, comma 5)
    if "attrezzatur" in g_lower or any(k in t_lower for k in ["carrell", "ple", "gru", "escavator", "trattor", "terne", "sollevator", "pompa"]):
        rif = (
            "D.Lgs. 81/2008 e s.m.i., Artt. 37, 71 comma 7, 73 commi 4 e 5; "
            "Accordo Stato-Regioni sulla formazione per le attrezzature di lavoro; "
            "Nuovo Accordo Quadro Stato-Regioni 2025."
        )
        prog = (
            f"PROGRAMMA DIDATTICO UFFICIALE ({duration} ORE)\n"
            "MODULO 1 - GIURIDICO NORMATIVO (Durata conforme alla tipologia):\n"
            "- Cenni di normativa generale in materia di igiene e sicurezza sul lavoro (D.Lgs. 81/08)\n"
            "- Responsabilità dell'operatore, datore di lavoro, noleggiatore e utilizzatore\n"
            "MODULO 2 - TECNICO ED ELEMENTI MECCANICI:\n"
            "- Categorie e tipologie dell'attrezzatura, componenti strutturali e organi di comando\n"
            "- Dispositivi di sicurezza, stabilità statica e dinamica, diagrammi di carico\n"
            "- DPI specifici, rischi da ribaltamento, interferenze e linee elettriche\n"
            "MODULO 3 - PRATICO ED OPERATIVO:\n"
            "- Ispezione visiva e controlli pre-utilizzo (freni, livelli, sistemi di sicurezza)\n"
            "- Manovre di messa a punto, traslazione, posizionamento e movimentazione sicura\n"
            "- Manovre di emergenza, arresto in sicurezza e messa a riposo dell'attrezzatura\n"
            "- Verifica finale di apprendimento con prova pratica individuale."
        )
        return rif, prog

    # 2. Corsi Antincendio (D.M. 02/09/2021)
    if "antincendio" in g_lower or "antincendio" in t_lower or "incendio" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Art. 37 comma 9 e Art. 46; "
            "D.M. 2 settembre 2021 (Criteri per la gestione dei luoghi di lavoro in esercizio ed in emergenza e formazione addetti);"
        )
        prog = (
            f"PROGRAMMA CORSO ADDETTI ANTINCENDIO ({duration} ORE)\n"
            "PARTE TEORICA:\n"
            "- L'incendio e la prevenzione incendi: triangolo del fuoco, cause e misure preventive\n"
            "- Protezione antincendio attiva e passiva: compartimentazioni, vie d'esodo, estintori, idranti, impianti\n"
            "- Procedure da adottare in caso di incendio, gestione dell'evacuazione e chiamate di soccorso\n"
            "PARTE PRATICA:\n"
            "- Presa visione e chiarimenti sulle attrezzature di protezione individuale (DPI antincendio)\n"
            "- Esercitazioni pratiche sull'uso degli estintori portatili (CO2 e idrici/polvere) su focolare reale\n"
            "- Esercitazioni su naspi e idranti, verifica finale di idoneità."
        )
        return rif, prog

    # 3. Primo Soccorso (D.M. 388/2003)
    if "primo soccorso" in g_lower or "primo soccorso" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Art. 37 comma 9 e Art. 45; "
            "Decreto Ministeriale 15 luglio 2003 n. 388 (Regolamento pronto soccorso aziendale);"
        )
        prog = (
            f"PROGRAMMA ADDETTI AL PRIMO SOCCORSO AZIENDALE ({duration} ORE)\n"
            "MODULO A - ALLERTA E RICONOSCIMENTO DELL'EMERGENZA:\n"
            "- Allertamento del sistema di soccorso (NUE 112), raccolta informazioni, diagnosi primaria\n"
            "- Riconoscimento dei rischi ambientali e sicurezza del soccorritore\n"
            "MODULO B - INTERVENTI DI PRIMO SOCCORSO:\n"
            "- Traumi, emorragie, shock, intossicazioni, ustioni e patologie legate al calore/freddo\n"
            "MODULO C - PARTE PRATICA:\n"
            "- Posizione laterale di sicurezza (PLS), respirazione artificiale e massaggio cardiaco (BLS)\n"
            "- Tecniche di disostruzione delle vie aeree e simulazioni pratiche di soccorso."
        )
        return rif, prog

    # 4. RSPP / ASPP (Art. 32 o 34)
    if "rspp" in g_lower or "aspp" in g_lower or "rspp" in t_lower or "aspp" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Art. 32 e Art. 34; "
            "Accordo Stato-Regioni del 7 luglio 2016 e Nuovo Accordo Stato-Regioni 2025."
        )
        prog = (
            f"PROGRAMMA FORMATIVO RSPP / ASPP ({duration} ORE)\n"
            "- Quadro normativo europeo e nazionale sulla sicurezza del lavoro\n"
            "- Il sistema aziendale della prevenzione, ruoli, deleghe e responsabilità giuridiche\n"
            "- Valutazione di tutti i rischi (DVR), stress lavoro-correlato, sostanze pericolose, macchine\n"
            "- Organizzazione del servizio di prevenzione, piano di emergenza, DPI e sorveglianza sanitaria\n"
            "- Comunicazione, consultazione e coinvolgimento degli attori della sicurezza (RLS, Preposti, Lavoratori)\n"
            "- Test finale di verifica delle competenze acquisite."
        )
        return rif, prog

    # 5. Preposti e Dirigenti (Artt. 19, 37)
    if "prepost" in t_lower or "dirigent" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Art. 19 e Art. 37 comma 7; "
            "Legge 215/2021; Accordo Stato-Regioni 2025."
        )
        prog = (
            f"PROGRAMMA FORMAZIONE PREPOSTI E DIRIGENTI ({duration} ORE)\n"
            "- Ruolo e funzioni del Preposto/Dirigente secondo il D.Lgs. 81/08 aggiornato\n"
            "- Obbligo di vigilanza e intervento tempestivo in caso di comportamenti insicuri\n"
            "- Relazioni tra i vari soggetti interni ed esterni del sistema di prevenzione\n"
            "- Individuazione e gestione dei fattori di rischio specifici dell'area di lavoro\n"
            "- Tecniche di comunicazione assertiva, motivazione e gestione della sicurezza sul campo\n"
            "- Verifica finale di apprendimento."
        )
        return rif, prog

    # 6. RLS (Art. 37 commi 10-11)
    if "rls" in t_lower or "rappresentante dei lavoratori" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Art. 37 commi 10 e 11; "
            "Nuovo Accordo Stato-Regioni 2025; CCNL di settore."
        )
        prog = (
            f"PROGRAMMA FORMAZIONE / AGGIORNAMENTO RLS ({duration} ORE)\n"
            "- Principi giuridici comunitari e nazionali della prevenzione\n"
            "- Il ruolo del Rappresentante dei Lavoratori per la Sicurezza (RLS): diritti e attribuzioni\n"
            "- Metodologie di valutazione e gestione dei rischi aziendali\n"
            "- Nozioni di igiene del lavoro, tossicologia e malattie professionali\n"
            "- Tecniche di contrattazione, consultazione e riunione periodica (Art. 35)\n"
            "- Test finale di verifica."
        )
        return rif, prog

    # 7. DPI / Lavori in Quota / Spazi Confinati
    if "dpi" in t_lower or "quota" in t_lower or "confinat" in t_lower or "funi" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Artt. 77 comma 4 e 5, 107, 111, 115, 116; "
            "D.P.R. 177/2011 (ambienti sospetti di inquinamento o confinati); "
            "Regolamento UE 2016/425; Accordo Stato-Regioni 2025."
        )
        prog = (
            f"PROGRAMMA SPECIALISTICO TEORICO-PRATICO ({duration} ORE)\n"
            "- Cenni normativi sui lavori speciali e DPI di III categoria (salvavita)\n"
            "- Valutazione dei rischi di caduta dall'alto e atmosfere pericolose/confinate\n"
            "- Caratteristiche tecniche, verifica periodica, stoccaggio e indosso corretto dei DPI\n"
            "- Sistemi di posizionamento, trattenuta e arresto caduta (UNI EN 361, 355, 354, 795)\n"
            "- Addestramento pratico con simulazione di recupero ed evacuazione operatore\n"
            "- Prova pratica finale."
        )
        return rif, prog

    # 8. PES / PAV / PEI (Rischio Elettrico)
    if "pes" in t_lower or "pav" in t_lower or "pei" in t_lower or "elettric" in t_lower:
        rif = (
            "D.Lgs. 81/2008 Artt. 80, 82, 83; "
            "Norma CEI 11-27 (Lavori su impianti elettrici) ed. V; Accordo Stato-Regioni 2025."
        )
        prog = (
            f"PROGRAMMA FORMAZIONE PES-PAV-PEI ({duration} ORE)\n"
            "- Quadro legislativo e normativo generale: D.Lgs. 81/08 e Norma CEI 11-27\n"
            "- Effetti della corrente sul corpo umano (elettrocuzione, arco elettrico, ustioni)\n"
            "- Definizioni di PES (Persona Esperta), PAV (Persona Avvertita) e PEI (Idonea ai lavori sotto tensione)\n"
            "- Procedure per lavori a contatto, a distanza, in prossimità e fuori tensione in BT e MT\n"
            "- Scelta e utilizzo dei DPI e attrezzi isolati (CEI EN 60900)\n"
            "- Valutazione finale teorico-pratica."
        )
        return rif, prog

    # 9. Formazione Lavoratori Generale e Specifica (Default)
    rif = (
        "D.Lgs. 9 aprile 2008 n. 81 e s.m.i., Art. 37; "
        "Nuovo Accordo Stato-Regioni del 17 aprile 2025 (rep. 59)."
    )
    prog = (
        f"PROGRAMMA FORMATIVO LAVORATORI CONFORME AL D.LGS. 81/08 ({duration} ORE)\n"
        "MODULO TEORICO ED APPLICATIVO:\n"
        "- Concetti di rischio, danno, prevenzione, protezione e organizzazione aziendale\n"
        "- Diritti, doveri e sanzioni per tutti i soggetti del sistema prevenzionistico aziendale\n"
        "- Rischi infortunistici specifici del settore e della mansione (meccanici, elettrici, cadute)\n"
        "- Rischi igienico-ambientali (agenti chimici, fisici, biologici, ergonomia, VDT, movimentazione carichi)\n"
        "- Misure di prevenzione, uso corretto dei DPI e procedure aziendali di emergenza\n"
        "- Test finale di verifica dell'apprendimento."
    )
    return rif, prog

def calculate_next_course_date() -> str:
    """Calculate a plausible future course date approx 30-40 days out on a Tuesday or Thursday."""
    target = datetime.now() + timedelta(days=32)
    # Ensure it's Tuesday (1) or Thursday (3) for typical professional training days
    while target.weekday() not in (1, 3):
        target += timedelta(days=1)
    return target.strftime("%Y-%m-%d")

class AnfosSession:
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        })

    def login(self) -> bool:
        url = ANFOS_BASE_URL + "api2/login"
        payload = {"user": self.user, "pwd": self.password}
        try:
            resp = self.session.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                logger.info(f"Login riuscito con successo su ANFOS per Centro {CENTRO_CODICE} ({self.user})")
                return True
            else:
                logger.error(f"Login ANFOS fallito con status HTTP {resp.status_code}: {resp.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Eccezione durante login ANFOS: {e}")
            return False

    def get_attivabili(self) -> list[dict]:
        url = ANFOS_BASE_URL + "api2/centriconvenzionati/validazioni/attivabili"
        try:
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Recuperati {len(data)} corsi attivabili ancora da validare.")
                return data
            else:
                logger.error(f"Errore recupero corsi attivabili: HTTP {resp.status_code}")
                return []
        except Exception as e:
            logger.error(f"Eccezione recupero attivabili: {e}")
            return []

    def get_existing_validazioni(self) -> list[dict]:
        url = ANFOS_BASE_URL + "api2/centriconvenzionati/validazioni"
        try:
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            logger.error(f"Eccezione recupero validazioni: {e}")
            return []

    def request_validazione(self, corso_id: str, title: str, group: str, duration: int, presunta_date: str) -> tuple[bool, str]:
        """
        Submit a new validation request via POST api2/centriconvenzionati/validazioni.
        Matches exact payload schema required by Backbone Model App.Models.Validazione.
        """
        url = ANFOS_BASE_URL + "api2/centriconvenzionati/validazioni"
        rif, prog = build_compliance_metadata(corso_id, title, group, duration)
        
        payload = {
            "corso_id": str(corso_id),
            "riferimenti_normativi": rif,
            "programma_formativo": prog,
            "durata": str(duration),
            "data_presunta_corso": presunta_date
        }

        try:
            resp = self.session.post(url, json=payload, timeout=25)
            # Both 200 and 201 are valid success responses for Backbone models
            if resp.status_code in (200, 201):
                logger.info(f"[VALIDAZIONE OK] Corso ID {corso_id} - '{title}' ({duration}h) inviato con successo!")
                return True, resp.text
            else:
                logger.warning(f"[VALIDAZIONE WARN] Corso ID {corso_id} respinto/errore HTTP {resp.status_code}: {resp.text[:250]}")
                return False, resp.text
        except Exception as e:
            logger.error(f"[VALIDAZIONE ERR] Eccezione sottomissione corso ID {corso_id}: {e}")
            return False, str(e)


def run_anfos_nightly_job(limit_override: int = None) -> dict:
    """
    Main autonomous entry point:
    Logs into ANFOS, checks daily quota, selects unvalidated courses,
    submits requests up to quota limit (default 5), and persists audit trail.
    """
    start_time = datetime.now()
    logger.info("================================================================================")
    logger.info(f"AVVIO JOB NOTTURNO ANFOS - Centro {CENTRO_CODICE} | Docente: {DOCENTE_ACCREDITATO}")
    logger.info("================================================================================")

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    already_done_today = count_today_validations(conn)
    logger.info(f"Validazioni già sottomesse oggi ({start_time.strftime('%Y-%m-%d')}): {already_done_today}")

    target_limit = limit_override if limit_override is not None else MAX_DAILY_VALIDATIONS
    quota_available = max(0, target_limit - already_done_today)

    if quota_available <= 0:
        logger.info(f"Quota giornaliera di {target_limit} validazioni già completata per oggi. Il bot va a riposo fino a domani notte.")
        conn.close()
        return {"status": "QUOTA_REACHED", "submitted_today": already_done_today, "remaining_quota": 0}

    logger.info(f"Quota rimanente da richiedere per questa notte: {quota_available}")

    client = AnfosSession(ANFOS_USER, ANFOS_PASSWORD)
    if not client.login():
        logger.error("Interruzione: impossibile autenticarsi su ANFOS.")
        conn.close()
        return {"status": "LOGIN_ERROR", "error": "Autenticazione fallita"}

    attivabili = client.get_attivabili()
    if not attivabili:
        logger.warning("Nessun corso attivabile trovato o catalogo già completato al 100%!")
        conn.close()
        return {"status": "CATALOG_COMPLETED", "submitted_today": already_done_today}

    # Sort courses logically to prioritize foundational and high-demand courses:
    # 1. Attrezzature (Carrelli, PLE, Gru)
    # 2. Antincendio & Primo Soccorso
    # 3. Lavoratori & Preposti
    # 4. RSPP & RLS
    # 5. DPI & Restanti
    priority_order = [
        "Corsi Attrezzature",
        "Corsi Antincendio",
        "Corsi Primo soccorso",
        "Corsi Preposti e Dirigenti",
        "Corsi Formazione lavoratore",
        "Aggiornamenti Attrezzature",
        "Corsi Dispositivi Protezione Individuali",
        "Corsi RSPP esterno",
        "Corsi RSPP datore di lavoro",
        "Corsi PES-PAV",
        "Corsi Coordinatore per la sicurezza",
        "Corsi RLS",
        "Moduli di approfondimento lavoratore"
    ]
    
    def sort_key(c):
        grp = c.get("gruppo", "")
        try:
            p_idx = priority_order.index(grp)
        except ValueError:
            p_idx = 99
        return (p_idx, int(c.get("id", 999999)))

    sorted_attivabili = sorted(attivabili, key=sort_key)

    submitted_this_run = 0
    next_date = calculate_next_course_date()

    for corso in sorted_attivabili:
        if submitted_this_run >= quota_available:
            break

        cid = str(corso.get("id"))
        title = corso.get("corso", "").strip()
        group = corso.get("gruppo", "")
        duration = extract_duration_from_title(title, group)

        logger.info(f"[{submitted_this_run + 1}/{quota_available}] Elaborazione richiesta per Corso ID {cid}: '{title}' ({duration}h, Gruppo: '{group}')...")
        
        success, resp_text = client.request_validazione(cid, title, group, duration, next_date)
        
        esito_db = "SUCCESS" if success else "FAILED"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO anfos_validation_log 
            (timestamp, corso_id, titolo_corso, gruppo, durata_ore, data_presunta, docente, esito, response_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, cid, title, group, duration, next_date, DOCENTE_ACCREDITATO, esito_db, resp_text))
        conn.commit()

        if success:
            submitted_this_run += 1
            # Graceful pause between requests to respect server
            time.sleep(4)
        else:
            # If server reported already requested or limit reached
            if "già richiesta" in resp_text.lower() or "limite" in resp_text.lower():
                logger.warning(f"Avviso dalla piattaforma ANFOS: {resp_text[:150]}")
            time.sleep(2)

    total_today = already_done_today + submitted_this_run
    logger.info("================================================================================")
    logger.info(f"JOB NOTTURNO CONCLUSO: {submitted_this_run} nuove validazioni inviate stanotte.")
    logger.info(f"Totale validazioni convalidate/inviate oggi: {total_today}/{target_limit}.")
    logger.info(f"Corsi ancora da attivare nel catalogo ANFOS: {len(attivabili) - submitted_this_run}.")
    logger.info("================================================================================")

    conn.close()
    return {
        "status": "OK",
        "submitted_this_run": submitted_this_run,
        "total_today": total_today,
        "remaining_in_catalog": len(attivabili) - submitted_this_run
    }

if __name__ == "__main__":
    # If run directly with an argument (e.g. `python anfos_validation_bot.py 5`)
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    res = run_anfos_nightly_job(limit_override=limit)
    print(json.dumps(res, indent=2))
