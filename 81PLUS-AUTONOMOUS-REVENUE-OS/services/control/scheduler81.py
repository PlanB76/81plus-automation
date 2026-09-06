"""
81+ AUTONOMOUS REVENUE OS
services/control/scheduler81.py — CRON81 / SCHEDULER81 Motore di Schedulazione Applicativo
Hard Constraints:
- Nessun demone finto. Scheduler persistito atomico su SQLite WAL.
- Lock atomico concurrency safe.
- Idempotency key obbligatoria.
- Retry con exponential backoff.
- Dead-letter queue dopo superamento max_attempts.
- Recovery automatico di job bloccati da worker crashati.
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime, timedelta
import sqlite3
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

logger = logging.getLogger("SCHEDULER81")

class Scheduler81:
    def __init__(self, conn: sqlite3.Connection = None, worker_id: str = None):
        self.conn = conn
        self.worker_id = worker_id or f"worker_{os.getpid()}_{uuid.uuid4().hex[:6]}"

    def _get_conn(self):
        return self.conn if self.conn is not None else get_connection()

    def enqueue(self, job_type: str, payload: dict, priority: int = 10,
                due_at: str = None, idempotency_key: str = None, max_attempts: int = 5) -> str:
        """
        Inserisce un nuovo job nella coda.
        Se idempotency_key esiste già, ritorna l'ID esistente senza duplicare.
        """
        job_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due = due_at or now
        payload_str = json.dumps(payload, ensure_ascii=False)
        idemp = idempotency_key or f"{job_type}_{uuid.uuid4().hex}"

        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO scheduled_jobs 
                (id, job_type, payload_json, priority, status, due_at, attempts, max_attempts, 
                 idempotency_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?, 0, ?, ?, ?, ?)
            """, (job_id, job_type, payload_str, priority, due, max_attempts, idemp, now, now))
            
            if self.conn is None:
                conn.commit()
                conn.close()
            else:
                conn.commit()
            return job_id
        except sqlite3.IntegrityError:
            # Idempotency collision: restituisce il job esistente
            cursor.execute("SELECT id FROM scheduled_jobs WHERE idempotency_key = ?", (idemp,))
            row = cursor.fetchone()
            existing_id = row[0] if row else None
            if self.conn is None:
                conn.close()
            return existing_id

    def claim_jobs(self, batch_size: int = 5, lock_timeout_sec: int = 300) -> list[dict]:
        """
        Acquisisce in modo atomico fino a `batch_size` job che sono scaduti (`due_at <= now`)
        e pronti per l'elaborazione (`PENDING` o `RETRY`).
        Aggiorna immediatamente lo status a `RUNNING` e assegna il lock a `self.worker_id`.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Recupera job pendenti
        cursor.execute("""
            SELECT id, job_type, payload_json, priority, attempts, max_attempts, idempotency_key
            FROM scheduled_jobs
            WHERE (status IN ('PENDING', 'RETRY'))
              AND due_at <= ?
            ORDER BY priority ASC, due_at ASC
            LIMIT ?
        """, (now, batch_size))
        
        candidates = cursor.fetchall()
        claimed = []

        for row in candidates:
            j_id = row["id"]
            # Tentativo atomico di claim con verifica status
            cursor.execute("""
                UPDATE scheduled_jobs
                SET status = 'RUNNING',
                    locked_at = ?,
                    locked_by = ?,
                    attempts = attempts + 1,
                    last_run_at = ?,
                    updated_at = ?
                WHERE id = ? AND status IN ('PENDING', 'RETRY')
            """, (now, self.worker_id, now, now, j_id))

            if cursor.rowcount > 0:
                claimed.append({
                    "id": j_id,
                    "job_type": row["job_type"],
                    "payload": json.loads(row["payload_json"]),
                    "priority": row["priority"],
                    "attempts": row["attempts"] + 1,
                    "max_attempts": row["max_attempts"],
                    "idempotency_key": row["idempotency_key"]
                })

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return claimed

    def complete_job(self, job_id: str, result_meta: dict = None):
        """Marca un job come completato con successo (DONE)."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scheduled_jobs
            SET status = 'DONE',
                locked_at = NULL,
                locked_by = NULL,
                updated_at = ?
            WHERE id = ?
        """, (now, job_id))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

    def fail_job(self, job_id: str, error_message: str):
        """
        Gestisce il fallimento di un job:
        - Se attempts < max_attempts: imposta status='RETRY' con exponential backoff.
        - Se attempts >= max_attempts: sposta in `dead_letter_jobs` e imposta status='DEAD'.
        """
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT attempts, max_attempts, job_type, payload_json, idempotency_key FROM scheduled_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            if self.conn is None:
                conn.close()
            return

        attempts = row["attempts"]
        max_attempts = row["max_attempts"]

        if attempts < max_attempts:
            # Exponential backoff: 30s, 60s, 120s, 240s...
            delay_seconds = 30 * (2 ** (attempts - 1))
            next_due = (now_dt + timedelta(seconds=delay_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE scheduled_jobs
                SET status = 'RETRY',
                    due_at = ?,
                    next_run_at = ?,
                    locked_at = NULL,
                    locked_by = NULL,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
            """, (next_due, next_due, error_message[:500], now_str, job_id))
        else:
            # Dead letter
            cursor.execute("""
                INSERT OR REPLACE INTO dead_letter_jobs 
                (id, job_type, payload_json, failed_at, attempts, fatal_error, idempotency_key)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_id, row["job_type"], row["payload_json"], now_str, attempts, error_message[:500], row["idempotency_key"]))

            cursor.execute("""
                UPDATE scheduled_jobs
                SET status = 'DEAD',
                    locked_at = NULL,
                    locked_by = NULL,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
            """, (f"MAX_ATTEMPTS_EXCEEDED: {error_message[:400]}", now_str, job_id))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

    def recover_stale_jobs(self, timeout_seconds: int = 300) -> int:
        """
        Recupera job rimasti in stato `RUNNING` per oltre `timeout_seconds`
        a causa di worker terminati improvvisamente o crash di processo.
        """
        threshold = (datetime.now() - timedelta(seconds=timeout_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE scheduled_jobs
            SET status = 'RETRY',
                locked_at = NULL,
                locked_by = NULL,
                last_error = 'STALE_LOCK_AUTO_RECOVERED',
                updated_at = ?
            WHERE status = 'RUNNING' AND locked_at < ?
        """, (now, threshold))
        count = cursor.rowcount

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()
        return count

    def heartbeat(self) -> dict:
        """
        Registra il tick in `system_health` e verifica le metriche chiave della coda.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT status, COUNT(*) as c FROM scheduled_jobs GROUP BY status")
        counts = {r["status"]: r["c"] for r in cursor.fetchall()}

        cursor.execute("SELECT MIN(due_at) FROM scheduled_jobs WHERE status IN ('PENDING', 'RETRY')")
        oldest_pending = cursor.fetchone()[0]

        recovered = self.recover_stale_jobs()

        metrics = {
            "counts": counts,
            "oldest_pending": oldest_pending,
            "recovered_zombies": recovered,
            "timestamp": now
        }
        
        # Calcolo health score (0..100)
        dead_count = counts.get("DEAD", 0)
        running_count = counts.get("RUNNING", 0)
        health_score = 100
        if dead_count > 10:
            health_score -= 20
        if dead_count > 50:
            health_score -= 40
        status_label = "RUN" if health_score >= 90 else ("DEGRADED" if health_score >= 70 else "STOP")

        cursor.execute("""
            INSERT INTO system_health (timestamp, component, status, health_score, metrics_json, last_tick)
            VALUES (?, 'SCHEDULER81', ?, ?, ?, ?)
        """, (now, status_label, health_score, json.dumps(metrics), now))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

        return {
            "status": status_label,
            "health_score": health_score,
            "metrics": metrics
        }

if __name__ == "__main__":
    sched = Scheduler81()
    print("Testing Scheduler81:")
    jid = sched.enqueue("TEST_JOB", {"test": True}, idempotency_key="m0_init_check")
    print(f"Enqueued job: {jid}")
    claimed = sched.claim_jobs(5)
    print(f"Claimed jobs: {len(claimed)}")
    if claimed:
        for j in claimed:
            print(f" - Executing job {j['id']} ({j['job_type']})")
            sched.complete_job(j["id"])
            print(f" - Completed job {j['id']}")
    hb = sched.heartbeat()
    print("Heartbeat:", json.dumps(hb, indent=2))
