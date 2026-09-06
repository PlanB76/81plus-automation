"""
81+ AUTONOMOUS REVENUE OS — ENGINE M5: COPY81 COMMUNICATION & CONVERSION OS
Capability: COPY81, EPPPA81, REPPPA81, OBJECTION81, VOC81, WINNING_LANGUAGE, SARCASM_GOVERNOR.
Regola madre: Una sola CTA Universale = VAI SULLA PIATTAFORMA.
"""

import sqlite3
import uuid
import re
import json
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.security.suppression_gate import SuppressionGate
from shared.events.event_bus import emit_event

UNIVERSAL_CTA_TEXT = "VAI SULLA PIATTAFORMA"
UNIVERSAL_CTA_URL = "https://81plus.net"

class SarcasmViolationError(ValueError):
    """Sollevata quando il copy viola le regole etico-legali di sicurezza del tono."""
    pass

class SarcasmSafetyGovernor:
    """
    Guardrail Etico & Reputazionale:
    Sarcasmo ammesso su: procrastinazione, burocrazia, password, moduli, 'lo facciamo lunedì', confusione.
    VIETATO su: infortuni, morti, disabilità, tragedie, minacce penali inventate, terrorismo.
    """
    FORBIDDEN_PATTERNS = [
        r"(mort[eo]|decess[oi]|tragedi[ae]|uccis[oi])",
        r"(sangue|amputat[oi]|infortun[io]\s+mortal[ei])",
        r"(andate\s+in\s+galera|arresto\s+immediato|multa\s+garantita)",
        r"(sei\s+un\s+incosciente|fai\s+schifo|pezzente)"
    ]

    @classmethod
    def validate(cls, text: str):
        for pat in cls.FORBIDDEN_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                raise SarcasmViolationError(f"Violazione Sarcasm Governor: rilevato pattern proibito '{pat}' nel testo generato.")
        return True

class Copy81Engine:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn or get_connection()
        self.suppression_gate = SuppressionGate(self.conn)
        self._ensure_seed_data()

    def _ensure_seed_data(self):
        """Popola la knowledge base di COPY81: 12 episodi base, obiezioni canoniche e geni."""
        cursor = self.conn.cursor()

        # 1. Popola 12 Episodi Seriali
        cursor.execute("SELECT COUNT(*) FROM copy_narrative_episodes")
        if cursor.fetchone()[0] == 0:
            episodes = [
                (1, "EP01_PROBLEM", "Il problema che non sapevi di avere", "Pattern break & risveglio", "Confusione normativa latente", "W00"),
                (2, "EP02_POSTPONE", "La cosa che tutti rimandano", "Sorriso & riconoscimento procrastinazione", "La settimana prossima non arriva mai", "W00"),
                (3, "EP03_WHY_PLATFORM", "Perché abbiamo costruito la piattaforma", "Sollievo & trasparenza", "Basta caccia al tesoro tra mille siti", "W20"),
                (4, "EP04_INSIDE", "Cosa trovi davvero dentro", "Valore & catalogo unificato", "Corsi online, aula e documenti nello stesso posto", "W20"),
                (5, "EP05_60SEC", "Come funziona in 60 secondi", "Riduzione frizione d'ingresso", "Entri, scegli, completi senza manuali di 80 pagine", "W40"),
                (6, "EP06_DONT_KNOW_NEED", "Ma io non so cosa mi serve", "Guida assistita per ATECO", "Non devi indovinare: ci pensa il test rapido", "W40"),
                (7, "EP07_NO_TIME", "Non ho tempo", "Anti-obiezione tempo", "Costruita per chi ha 15 minuti la sera o tra una riunione e l'altra", "W60"),
                (8, "EP08_PRICING", "Quanto costa?", "Anti-obiezione prezzo & trasparenza", "Zero costi nascosti: paghi solo quello che certifichi", "W60"),
                (9, "EP09_COMMON_MISTAKES", "Gli errori più comuni", "Consapevolezza del rischio concreto", "I 3 errori che fanno tutti con i corsi scaduti", "W60"),
                (10, "EP10_YOUR_ATECO", "Il tuo settore e le tue scadenze", "Iper-personalizzazione settore", "Cosa rischia davvero chi lavora nel tuo codice ATECO", "W80"),
                (11, "EP11_WHAT_HAPPENS_NEXT", "Cosa succede dopo", "Fiducia nel lifecycle & archivio", "Attestati sempre salvati e scadenze ricordate in automatico", "W80"),
                (12, "EP12_DECISION", "La decisione più semplice", "Chiusura & azione definitiva", "Chiudi la pratica sicurezza prima che diventi un'emergenza", "W80")
            ]
            cursor.executemany("""
                INSERT INTO copy_narrative_episodes (episode_num, code, title, cognitive_goal, dominant_angle, w_score_target, cta_text)
                VALUES (?, ?, ?, ?, ?, ?, 'VAI SULLA PIATTAFORMA')
            """, episodes)

        # 2. Popola / Aggiorna Tassonomia Obiezioni
        objections = [
            ("NON_HO_TEMPO", "NO_TEMPO", json.dumps(["non ho tempo", "troppo impegnato", "settimana piena", "chiamami più avanti"]), "SEMPLICITA_TEMPO", 2, "SWITCH_EPISODE_7"),
            ("NON_SO_COSA_SERVE", "NO_SCELTA", json.dumps(["non so cosa fare", "non conosco gli obblighi", "che corsi servono"]), "GUIDA_PERCORSO", 2, "SWITCH_EPISODE_6"),
            ("NON_SO_COME_FUNZIONA", "NO_FUNZIONA", json.dumps(["come funziona", "è complicato", "è difficile"]), "DEMO_QUICKSTART", 2, "SWITCH_EPISODE_5"),
            ("COSTA_TROPPO", "COSTO_DUBBIO", json.dumps(["costa troppo", "prezzo alto", "sconto", "budget"]), "TRASPARENZA_VALORE", 2, "SWITCH_EPISODE_8"),
            ("GIA_FATTO", "GIA_FATTO", json.dumps(["già fatti", "abbiamo già tutto", "corsi a posto", "fatto l'anno scorso"]), "VERIFICA_SCADENZE", 2, "SWITCH_EPISODE_11"),
            ("CI_PENSA_CONSULENTE", "COMMERCIALISTA", json.dumps(["ci pensa il commercialista", "abbiamo il consulente", "segue rsp esterno"]), "COMPLEMENTARITA", 2, "CONSULENTE_SUPPORT"),
            ("NON_MI_FIDO", "DIFFIDENZA", json.dumps(["chi siete", "è valido", "ente accreditato", "truffa"]), "PROVA_ACCREDITAMENTO", 2, "PROVA_ATTESTATI"),
            ("NON_CONTATTARMI", "NON_CONTATTARMI", json.dumps(["non contattarmi", "cancellami", "disiscrivimi", "stop", "privacy", "diffida"]), "SUPPRESSION_IMMEDIATA", 1, "GLOBAL_SUPPRESS")
        ]
        now_str = datetime.now().isoformat()
        for obj_code, legacy_code, kw_json, res_angle, max_att, exit_cond in objections:
            cursor.execute("SELECT id FROM objection_taxonomy WHERE codice_obiezione = ? OR objection_code = ?", (legacy_code, obj_code))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE objection_taxonomy
                    SET objection_code = ?, trigger_keywords_json = ?, resolution_angle = ?, max_attempts = ?, exit_condition = ?
                    WHERE id = ?
                """, (obj_code, kw_json, res_angle, max_att, exit_cond, row[0]))
            else:
                cursor.execute("""
                    INSERT INTO objection_taxonomy (
                        codice_obiezione, descrizione_obiezione, angolo_risolutivo, risposta_antino,
                        objection_code, trigger_keywords_json, resolution_angle, max_attempts, exit_condition, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (legacy_code, obj_code, res_angle, res_angle, obj_code, kw_json, res_angle, max_att, exit_cond, now_str))

        # 3. Popola Regole Negative Language
        cursor.execute("SELECT COUNT(*) FROM negative_language")
        if cursor.fetchone()[0] == 0:
            now_str = datetime.now().isoformat()
            negatives = [
                ("NEG_01", r"mort[eo]|decess[oi]|sangue", "SARCASM_ON_TRAGEDY", "Divieto assoluto di ironia su infortuni o tragedie"),
                ("NEG_02", r"entro\s+24\s+ore\s+altrimenti|scade\s+tra\s+10\s+minuti", "FAKE_URGENCY", "Divieto di falsa urgenza manipolatoria"),
                ("NEG_03", r"ai\s+sensi\s+dell'art\.\s+comma\s+\d+", "BUREAUCRATIC_JARGON", "Evitare legalese astratto in apertura")
            ]
            cursor.executemany("""
                INSERT INTO negative_language (id, pattern_regex, violation_category, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, [(n[0], n[1], n[2], n[3], now_str) for n in negatives])

        self.conn.commit()

    # =========================================================================
    # 1. GENERAZIONE MESSAGGIO SERIALE (FORMULA A 7 STEP & ONE CTA)
    # =========================================================================
    def generate_message(self, company_id: str, episode_num: int = 1) -> dict:
        """
        Genera un messaggio personalizzato secondo la Brand Voice Constitution:
        PATTERN BREAK → SORRISO → RICONOSCIMENTO → PROBLEMA → BENEFICIO → PROVA/CHIAREZZA → CTA
        """
        cursor = self.conn.cursor()

        # Verifica stato azienda & suppressions
        cursor.execute("""
            SELECT ct.business_name, ct.clean_name, ct.ateco_code, ct.risk_level, ct.employee_count,
                   c.email, c.contactability_status,
                   tw.w_score, tw.dominant_objection, tw.last_action
            FROM company_twins ct
            JOIN company_contacts c ON c.company_id = ct.id
            LEFT JOIN communication_twins tw ON tw.company_id = ct.id
            WHERE ct.id = ?
            LIMIT 1
        """, (company_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Company {company_id} non trovata.")

        b_name, c_name, ateco, risk, employees, email, c_status, w_score, dom_obj, last_action = row

        # Guardrail: se soppresso o do not contact -> nessun messaggio
        if self.suppression_gate.is_suppressed(email):
            return {"status": "BLOCKED", "reason": "EMAIL_SUPPRESSED", "email": email}

        # Guardrail: se ha già acquistato o registrato l'account -> stop acquisizione
        if last_action in ("PURCHASED", "REGISTERED"):
            return {"status": "BLOCKED", "reason": "ALREADY_CONVERTED", "action": last_action}

        # Se c'è un'obiezione dominante attiva, fai branch automatico
        if dom_obj == "NON_HO_TEMPO":
            episode_num = 7
        elif dom_obj == "NON_SO_COSA_SERVE":
            episode_num = 6
        elif dom_obj == "COSTA_TROPPO":
            episode_num = 8

        cursor.execute("SELECT code, title, cognitive_goal, dominant_angle FROM copy_narrative_episodes WHERE episode_num = ?", (episode_num,))
        ep_row = cursor.fetchone()
        ep_code, ep_title, ep_goal, ep_angle = ep_row if ep_row else ("EP01", "Sicurezza 81+", "Awareness", "Generale")

        # ---------------------------------------------------------------------
        # Assemblaggio dei 7 Componenti (Brand Voice Constitution)
        # ---------------------------------------------------------------------
        if episode_num == 2 or "POSTPONE" in ep_code:
            subject = f"{c_name}: quel corso che 'facciamo la settimana prossima'"
            pattern_break = "Hai presente quel corso di formazione che 'facciamo sicuramente la settimana prossima'?"
            sorriso = "La settimana prossima ha un talento davvero particolare: riesce a non arrivare mai. Purtroppo abbiamo controllato."
            riconoscimento = f"Con {employees} collaboratori e il lavoro di tutti i giorni, mettersi a spulciare circolari e cataloghi infiniti è l'ultima cosa che hai voglia di fare."
            problema = "Il risultato? Faldoni persi, dubbi sulle scadenze e la sensazione che la sicurezza sia un secondo lavoro non retribuito."
            beneficio = "Abbiamo costruito 81+ esattamente per toglierti questo peso: corsi online veloci, corsi in aula certificati e documenti in un unico posto."
            prova = "Tutto conforme al D.Lgs. 81/08 e al nuovo Accordo Stato-Regioni 2025. Senza asterischi e senza sorprese."
        elif episode_num == 7 or dom_obj == "NON_HO_TEMPO":
            subject = f"{c_name}: non hai tempo da perdere con la sicurezza? Nemmeno noi."
            pattern_break = "Se hai pensato 'non ho mezza giornata da buttare in un corso', abbiamo un'ottima notizia."
            sorriso = "Non abbiamo costruito una piattaforma per regalarti un nuovo hobby o farti passare la serata sui PDF burocratici."
            riconoscimento = f"Chi gestisce un'impresa con codice ATECO {ateco or 'aziendale'} deve produrre, non fare l'archivista."
            problema = "La burocrazia tradizionale ti costringe a telefonate, attese e moduli cartacei infiniti."
            beneficio = "Su 81+ entri, accedi ai tuoi corsi quando hai un buco libero (anche alle 22:30), completi e ricevi l'attestato valido."
            prova = "Oltre 100 aziende nel territorio la usano per azzerare i tempi morti."
        else:
            subject = f"{c_name}: la sicurezza sul lavoro senza manuale di 84 pagine"
            pattern_break = "La sicurezza sul lavoro è già abbastanza complicata per conto suo."
            sorriso = "Noi almeno abbiamo evitato di complicarti anche il modo di metterti in regola."
            riconoscimento = f"Sappiamo bene che in un'azienda come {c_name} il tempo è la risorsa più scarsa."
            problema = "Cercare corsi qui, documenti là e attestati in fondo a vecchie email è una caccia al tesoro inutile."
            beneficio = "Su 81+ trovi corsi e documenti pronti, guidati passo-passo per il tuo settore."
            prova = "Centri accreditati ANFOS e percorsi conformi al 100% all'Accordo Stato-Regioni 2025."

        cta_block = f"\n\n**[{UNIVERSAL_CTA_TEXT}]({UNIVERSAL_CTA_URL})**\n*(Entra in 60 secondi e verifica subito cosa ti serve)*"

        full_body = f"{pattern_break}\n\n{sorriso}\n\n{riconoscimento}\n\n{problema}\n\n{beneficio}\n\n{prova}{cta_block}"

        # Validazione Guardrail Sarcasmo & Rispetto Normativo
        SarcasmSafetyGovernor.validate(full_body)

        # Registrazione esperimento copy
        exp_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now().isoformat()
        genes_used = {
            "subject": subject,
            "pattern_break": pattern_break,
            "sorriso": sorriso,
            "riconoscimento": riconoscimento,
            "problema": problema,
            "beneficio": beneficio,
            "prova": prova,
            "cta": UNIVERSAL_CTA_TEXT
        }

        cursor.execute("""
            INSERT INTO copy_experiments (
                id, company_id, episode_num, variant_code, genes_used_json,
                subject, body, cta_url, sent_at, outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'SENT')
        """, (exp_id, company_id, episode_num, ep_code, json.dumps(genes_used),
              subject, full_body, UNIVERSAL_CTA_URL, now_str))

        # Aggiorna Communication Twin
        cursor.execute("""
            UPDATE communication_twins
            SET messages_sent_count = messages_sent_count + 1,
                last_message_at = ?,
                last_action = 'MESSAGE_SENT',
                updated_at = ?
            WHERE company_id = ?
        """, (now_str, now_str, company_id))

        self.conn.commit()

        emit_event("MESSAGE_SENT", {
            "experiment_id": exp_id, "company_id": company_id, "episode": episode_num,
            "subject": subject, "cta": UNIVERSAL_CTA_TEXT
        }, self.conn)

        return {
            "experiment_id": exp_id,
            "company_id": company_id,
            "episode_num": episode_num,
            "subject": subject,
            "body": full_body,
            "cta_text": UNIVERSAL_CTA_TEXT,
            "cta_url": UNIVERSAL_CTA_URL,
            "status": "READY_TO_SEND"
        }

    # =========================================================================
    # 2. GESTIONE REAZIONI & OBJECTION GRAPH (ANTI-NO GUARDRAILS)
    # =========================================================================
    def handle_inbound_reaction(self, company_id: str, email: str, message_text: str) -> dict:
        """
        Analizza una risposta o reazione inbound.
        Anti-No = risolvere i dubbi legittimi.
        HARD RULE: Se richiede opt-out / cancellazione -> STOP ASSOLUTO + SUPPRESSION GLOBALE.
        """
        cursor = self.conn.cursor()
        text_lower = message_text.lower()

        # 1. Controllo Assoluto Opt-Out / Non contattarmi
        opt_out_triggers = ["non contattarmi", "cancellami", "disiscrivimi", "stop", "privacy", "diffida", "non scrivetemi più"]
        if any(trig in text_lower for trig in opt_out_triggers):
            # Soppressione immediata
            self.suppression_gate.add_suppression(identifier=email, id_type="EMAIL", reason="OPT_OUT_REQUESTED", source="REPLY_ANALYZER")

            cursor.execute("""
                UPDATE company_contacts
                SET contactability_status = 'SUPPRESSED'
                WHERE email = ?
            """, (email,))

            cursor.execute("""
                UPDATE communication_twins
                SET dominant_objection = 'NON_CONTATTARMI',
                    last_action = 'SUPPRESSED',
                    updated_at = ?
                WHERE company_id = ?
            """, (datetime.now().isoformat(), company_id))

            self.conn.commit()

            emit_event("SUPPRESSION_ENFORCED", {
                "company_id": company_id, "email": email, "reason": "OPT_OUT"
            }, self.conn)

            return {
                "action": "SUPPRESSED_IMMEDIATELY",
                "objection_code": "NON_CONTATTARMI",
                "company_id": company_id,
                "can_contact": False
            }

        # 2. Controllo altre obiezioni canoniche (Tempo, Bisogno, Prezzo, etc.)
        cursor.execute("SELECT objection_code, trigger_keywords_json, resolution_angle FROM objection_taxonomy")
        rows = cursor.fetchall()

        detected_code = None
        resolution = None

        for code, kw_json, res_angle in rows:
            if code == "NON_CONTATTARMI":
                continue
            keywords = json.loads(kw_json)
            if any(kw in text_lower for kw in keywords):
                detected_code = code
                resolution = res_angle
                break

        if detected_code:
            now_str = datetime.now().isoformat()
            cursor.execute("""
                UPDATE communication_twins
                SET dominant_objection = ?,
                    last_action = 'OBJECTION_DETECTED',
                    updated_at = ?
                WHERE company_id = ?
            """, (detected_code, now_str, company_id))
            self.conn.commit()

            emit_event("OBJECTION_DETECTED", {
                "company_id": company_id, "objection": detected_code, "resolution": resolution
            }, self.conn)

            return {
                "action": "BRANCH_SWITCHED",
                "objection_code": detected_code,
                "resolution_angle": resolution,
                "can_contact": True
            }

        return {"action": "NO_SPECIFIC_OBJECTION", "can_contact": True}

    # =========================================================================
    # 3. EVOLUZIONE COPY & WINNING LANGUAGE MEMORY
    # =========================================================================
    def record_conversion_outcome(self, experiment_id: str, outcome: str):
        """
        Registra l'esito reale (OPENED, CLICKED, REGISTERED, BOUGHT)
        e alimenta la Winning Language Memory quando un gene produce buyer/registrazioni.
        """
        cursor = self.conn.cursor()
        now_str = datetime.now().isoformat()

        cursor.execute("""
            UPDATE copy_experiments
            SET outcome = ?,
                clicked_at = CASE WHEN ? IN ('CLICKED', 'REGISTERED', 'BOUGHT') THEN ? ELSE clicked_at END,
                registered_at = CASE WHEN ? IN ('REGISTERED', 'BOUGHT') THEN ? ELSE registered_at END,
                ordered_at = CASE WHEN ? = 'BOUGHT' THEN ? ELSE ordered_at END
            WHERE id = ?
        """, (outcome, outcome, now_str, outcome, now_str, outcome, now_str, experiment_id))

        if outcome in ('REGISTERED', 'BOUGHT'):
            # Recupera geni usati
            cursor.execute("""
                SELECT ce.genes_used_json, ct.ateco_code, tw.w_score
                FROM copy_experiments ce
                JOIN company_twins ct ON ct.id = ce.company_id
                LEFT JOIN communication_twins tw ON tw.company_id = ce.company_id
                WHERE ce.id = ?
            """, (experiment_id,))
            row = cursor.fetchone()
            if row:
                genes = json.loads(row[0])
                ateco = row[1] or "GENERALE"
                w_sc = f"W{row[2] or 0}"

                # Registra in winning_language
                win_id = f"WIN-{uuid.uuid4().hex[:8].upper()}"
                cursor.execute("""
                    INSERT INTO winning_language (
                        id, ateco_macro, w_score_range, gene_type, gene_content,
                        conversion_rate, confidence, updated_at
                    ) VALUES (?, ?, ?, 'SUBJECT', ?, 0.08, 0.85, ?)
                """, (win_id, ateco[:2], w_sc, genes["subject"], now_str))

        self.conn.commit()

        emit_event("COPY_OUTCOME_RECORDED", {
            "experiment_id": experiment_id, "outcome": outcome
        }, self.conn)

if __name__ == "__main__":
    engine = Copy81Engine()
    print("[OK] Copy81Engine inizializzato con successo.")
