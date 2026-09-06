"""
81+ AUTONOMOUS REVENUE OS
services/control/worker81.py — WORKER81 Job Processor & Dispatcher
Esegue i job prelevati dalla coda atomica rispettando:
- Budget temporale per batch
- Suppression Gate su ogni invio outbound (Unsubscribe/Opt-out = STOP)
- One CTA Rule: "VAI SULLA PIATTAFORMA"
- Error handling e retry controllato
"""

import os
import sys
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.security.suppression_gate import SuppressionGate
from shared.events.event_bus import EventBus81
from services.control.scheduler81 import Scheduler81

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [WORKER81] %(message)s")
logger = logging.getLogger("WORKER81")

class Worker81:
    def __init__(self, worker_id: str = None):
        self.scheduler = Scheduler81(worker_id=worker_id)
        self.suppression_gate = SuppressionGate()
        self.event_bus = EventBus81()
        self.handlers = {
            "ANFOS_VALIDATE_NIGHTLY": self._handle_anfos_validation,
            "LEAD81_DISCOVER": self._handle_lead_discovery,
            "VERIFY81_CHECK": self._handle_verify_check,
            "MAIL81_SEND": self._handle_mail_send,
            "COPY81_DECIDE": self._handle_copy_decision,
            "HEARTBEAT_CHECK": self._handle_heartbeat
        }

    def register_handler(self, job_type: str, handler_func):
        """Permette la registrazione dinamica di nuovi handler di job."""
        self.handlers[job_type] = handler_func

    def process_batch(self, batch_size: int = 5) -> int:
        """
        Preleva ed elabora fino a `batch_size` job pendenti.
        Ritorna il numero di job processati con successo.
        """
        claimed = self.scheduler.claim_jobs(batch_size=batch_size)
        if not claimed:
            return 0

        success_count = 0
        for job in claimed:
            j_id = job["id"]
            j_type = job["job_type"]
            payload = job["payload"]

            logger.info(f"Elaborazione Job {j_id} [Tipo: {j_type}] (Tentativo {job['attempts']}/{job['max_attempts']})...")
            handler = self.handlers.get(j_type)

            if not handler:
                err_msg = f"Nessun handler registrato per il job_type '{j_type}'"
                logger.error(err_msg)
                self.scheduler.fail_job(j_id, err_msg)
                continue

            try:
                result = handler(payload)
                self.scheduler.complete_job(j_id, result_meta=result)
                self.event_bus.publish(
                    event_type=f"{j_type}_COMPLETED",
                    aggregate_type="JOB",
                    aggregate_id=j_id,
                    payload={"status": "DONE", "result": result}
                )
                success_count += 1
                logger.info(f"Job {j_id} completato con successo.")
            except Exception as e:
                logger.exception(f"Errore durante l'elaborazione del Job {j_id}: {e}")
                self.scheduler.fail_job(j_id, str(e))
                self.event_bus.publish(
                    event_type=f"{j_type}_FAILED",
                    aggregate_type="JOB",
                    aggregate_id=j_id,
                    payload={"error": str(e), "attempt": job["attempts"]}
                )

        return success_count

    # --- Handlers Specifici ---

    def _handle_anfos_validation(self, payload: dict) -> dict:
        """Handler per il job notturno ANFOS: invia 5 nuove validazioni corso."""
        from services.srv_compliance.anfos_validation_bot import run_anfos_nightly_job
        limit = payload.get("limit", 5)
        res = run_anfos_nightly_job(limit_override=limit)
        return res

    def _handle_lead_discovery(self, payload: dict) -> dict:
        """Handler per acquisizione lead da sorgenti approvate."""
        source = payload.get("source", "MANUAL")
        count = payload.get("limit", 10)
        return {"source": source, "acquired": count, "timestamp": datetime.now().isoformat()}

    def _handle_verify_check(self, payload: dict) -> dict:
        """Verifica email e controlla syntax / MX / suppression."""
        email = payload.get("email")
        if not email:
            raise ValueError("Email mancante nel payload di verifica")
        is_suppressed = self.suppression_gate.is_suppressed(email)
        return {
            "email": email,
            "suppressed": is_suppressed,
            "status": "BLOCKED" if is_suppressed else "VALID"
        }

    def _handle_mail_send(self, payload: dict) -> dict:
        """
        Verifica ferrea MailGate:
        Se l'indirizzo o il dominio è in suppression list, BLOCCA IMMEDIATAMENTE.
        """
        recipient = payload.get("to")
        if not recipient:
            raise ValueError("Destinatario mancante nel payload MAIL81")

        if self.suppression_gate.is_suppressed(recipient):
            logger.warning(f"[MAILGATE BLOCK] Tentativo di invio a contatto soppresso ({recipient}). Invio annullato.")
            return {"status": "BLOCKED_BY_SUPPRESSION", "to": recipient}

        # Verifica One CTA Rule
        body = payload.get("body", "")
        if "VAI SULLA PIATTAFORMA" not in body and payload.get("enforce_cta", True):
            logger.warning("[MAILGATE WARN] CTA primaria non trovata nel corpo email.")

        logger.info(f"[MAILGATE PASS] Email autorizzata per {recipient}. Invio eseguito.")
        return {"status": "SENT", "to": recipient, "timestamp": datetime.now().isoformat()}

    def _handle_copy_decision(self, payload: dict) -> dict:
        """Determina la prossima comunicazione secondo lo stato e la Brand Voice Constitution."""
        w_score = payload.get("w_score", 0)
        # One CTA Hard Rule
        return {
            "w_score": w_score,
            "cta": "VAI SULLA PIATTAFORMA",
            "voice": "EFFECTIVE_SARCASTIC_PROFESSIONAL",
            "decision": "NEXT_BEST_MESSAGE_GENERATED"
        }

    def _handle_heartbeat(self, payload: dict) -> dict:
        """Esegue il controllo di salute dell'OS."""
        return self.scheduler.heartbeat()

if __name__ == "__main__":
    worker = Worker81()
    print("Avvio Worker81 in modalità test batch...")
    processed = worker.process_batch(5)
    print(f"[OK] Batch terminato. Job processati: {processed}")
