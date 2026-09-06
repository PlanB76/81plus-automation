"""
81+ AUTONOMOUS REVENUE OS — ENGINE M7: LEAD FACTORY H24 & SOURCE REGISTRY
Capability: LEAD81, SOURCE81, SOURCEHUNTER81, SOURCEROI81, RATE81, VERIFY81.
Hard Rule: Policy dubbia = QUARANTINE. Solo fonti APPROVED possono alimentare la macchina.
"""

import sqlite3
import uuid
import json
import time
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection
from shared.security.suppression_gate import SuppressionGate
from shared.events.event_bus import emit_event

class SourcePolicyQuarantineError(PermissionError):
    """Sollevata se una sorgente non è esplicitamente APPROVED per l'acquisizione marketing."""
    pass

class LeadFactoryH24Engine:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn or get_connection()
        self.suppression_gate = SuppressionGate(self.conn)
        self._ensure_seed_sources()

    def _ensure_seed_sources(self):
        """Inizializza le fonti note con stato legale stringente."""
        cursor = self.conn.cursor()
        sources = [
            ("SRC_OPEN_DATA_VENETO", "Open Data Imprese Regione Veneto", "OPEN_DATA_GOV", "CC-BY 4.0 Pubblico Riutilizzabile", "APPROVED", 120, 10000),
            ("SRC_PUB_SEED_7K", "Archivio Proprietario Seed Imprese 81+", "PUBLIC_DATASET", "Dati legittimamente acquisiti", "APPROVED", 300, 10000),
            ("SRC_CAMERA_COMM_UNVERIFIED", "Scraping Portale Camere di Commercio", "DIRECTORY", "Termini non verificati / limitati", "QUARANTINE", 10, 100),
            ("SRC_ALBO_PROFESSIONALE_RESTRICTED", "Albo Consulenti e Ordini", "DIRECTORY", "Vietato scraping e riuso commerciale", "FORBIDDEN", 0, 0)
        ]
        now_str = datetime.now().isoformat()
        for s_id, name, s_type, lic, st, r_lim, quota in sources:
            cursor.execute("""
                INSERT OR IGNORE INTO source_registry (
                    id, name, source_type, license_terms, policy_status,
                    rate_limit_per_min, daily_quota, source_roi_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1.2, ?)
            """, (s_id, name, s_type, lic, st, r_lim, quota, now_str))

            cursor.execute("""
                INSERT OR IGNORE INTO source_economics (
                    source_id, total_cost_eur, total_leads_acquired, total_buyers_generated,
                    total_revenue_generated, cac_eur, roi_ratio, updated_at
                ) VALUES (?, 0.0, 0, 0, 0.0, 0.0, 1.0, ?)
            """, (s_id, now_str))
        self.conn.commit()

    def run_source_policy_check(self, source_id: str) -> dict:
        """Verifica lo stato legale della sorgente. Blocca tutto se != APPROVED."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, policy_status, daily_quota FROM source_registry WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Sorgente {source_id} sconosciuta.")

        s_id, name, status, quota = row
        if status != "APPROVED":
            emit_event("SOURCE_QUARANTINE_BLOCKED", {
                "source_id": s_id, "name": name, "policy_status": status,
                "reason": "Policy non approvata: accesso bloccato da guardrail legale."
            }, self.conn)
            raise SourcePolicyQuarantineError(
                f"ACCESSO BLOCCATO: La sorgente '{name}' ({s_id}) ha stato '{status}'. "
                f"Solo sorgenti con licenza 'APPROVED' possono alimentare la Lead Factory."
            )

        return {"source_id": s_id, "name": name, "status": status, "daily_quota": quota}

    def execute_acquisition_batch(self, source_id: str, raw_leads: list) -> dict:
        """
        Esegue l'acquisizione di un batch da una sorgente approvata:
        POLICY CHECK → NORMALIZE → DEDUPE → ATECO → CONTACT GATE → PERSIST → ENQUEUE
        """
        # 1. Source Policy Gate
        self.run_source_policy_check(source_id)

        cursor = self.conn.cursor()
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()
        now_str = datetime.now().isoformat()

        # Cache clean names ed email esistenti per deduplica O(1)
        cursor.execute("SELECT clean_name, id FROM company_twins")
        comp_by_clean = {r[0]: r[1] for r in cursor.fetchall() if r[0]}

        cursor.execute("SELECT email FROM company_contacts")
        seen_emails = {r[0].lower() for r in cursor.fetchall() if r[0]}

        valid_records = 0
        deduped_new_companies = 0
        quarantined_records = 0

        for lead in raw_leads:
            email = (lead.get("email") or "").strip().lower()
            raw_comp_name = (lead.get("company_name") or "").strip()
            city = lead.get("city", "ROVIGO")
            province = lead.get("province", "RO")

            if not email or "@" not in email or "." not in email:
                quarantined_records += 1
                continue

            if email in seen_emails:
                continue
            seen_emails.add(email)

            valid_records += 1

            # Normalizzazione nome
            clean_comp = raw_comp_name.upper().replace("S.R.L.", "").replace("S.N.C.", "").strip() or "IMPRESA"

            if clean_comp in comp_by_clean:
                company_id = comp_by_clean[clean_comp]
            else:
                company_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"
                comp_by_clean[clean_comp] = company_id
                domain = email.split("@")[1] if "@" in email else "azienda.it"
                ateco = lead.get("ateco", "43.21.01")
                risk = lead.get("risk", "ALTO")

                cursor.execute("""
                    INSERT OR IGNORE INTO company_twins (
                        id, business_name, clean_name, domain, ateco_code,
                        ateco_description, risk_level, employee_count, city, province, region,
                        data_confidence, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'Attività qualificata', ?, 6, ?, ?, 'VENETO', 0.90, ?, ?)
                """, (company_id, raw_comp_name, clean_comp, domain, ateco, risk, city, province, now_str, now_str))

                cursor.execute("""
                    INSERT OR IGNORE INTO communication_twins (
                        company_id, w_score, dominant_need, dominant_objection, last_action, updated_at
                    ) VALUES (?, 0, 'SICUREZZA_BASE', NULL, 'ACQUIRED_H24', ?)
                """, (company_id, now_str))

                deduped_new_companies += 1

            # Contactability gate
            is_sup = self.suppression_gate.is_suppressed(email)
            contact_status = "SUPPRESSED" if is_sup else "CONTACTABLE"

            contact_id = f"CNT-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute("""
                INSERT OR IGNORE INTO company_contacts (
                    id, company_id, full_name, email, role, contactability_status,
                    provenance, created_at
                ) VALUES (?, ?, ?, ?, 'TITOLARE', ?, ?, ?)
            """, (contact_id, company_id, lead.get("contact_name", "Referente"), email, contact_status, source_id, now_str))

            # Enqueue nel job queue per lavorazione successiva
            job_id = f"JOB-NURTURE-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute("""
                INSERT INTO scheduled_jobs (
                    id, job_type, payload_json, priority, status, due_at,
                    idempotency_key, created_at, updated_at
                ) VALUES (?, 'LEAD_NURTURE_DISPATCH', ?, 2, 'PENDING', ?, ?, ?, ?)
            """, (job_id, json.dumps({"company_id": company_id, "email": email}), now_str, f"IDEM-{email}", now_str, now_str))

        duration = round(time.time() - start_time, 3)

        # Registrazione run
        cursor.execute("""
            INSERT INTO source_acquisition_runs (
                id, source_id, records_fetched, records_valid, records_deduped,
                records_quarantined, status, duration_sec, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'COMPLETED', ?, ?)
        """, (run_id, source_id, len(raw_leads), valid_records, deduped_new_companies,
              quarantined_records, duration, now_str))

        # Aggiornamento source registry & economics
        cursor.execute("""
            UPDATE source_registry
            SET last_run_at = ?, records_collected_total = records_collected_total + ?
            WHERE id = ?
        """, (now_str, valid_records, source_id))

        cursor.execute("""
            UPDATE source_economics
            SET total_leads_acquired = total_leads_acquired + ?, updated_at = ?
            WHERE source_id = ?
        """, (valid_records, now_str, source_id))

        self.conn.commit()

        emit_event("ACQUISITION_RUN_COMPLETED", {
            "run_id": run_id, "source_id": source_id, "valid_leads": valid_records,
            "new_companies": deduped_new_companies
        }, self.conn)

        return {
            "run_id": run_id,
            "source_id": source_id,
            "records_fetched": len(raw_leads),
            "records_valid": valid_records,
            "new_companies": deduped_new_companies,
            "quarantined": quarantined_records,
            "duration_sec": duration,
            "status": "COMPLETED"
        }

if __name__ == "__main__":
    factory = LeadFactoryH24Engine()
    print("[OK] LeadFactoryH24Engine inizializzata con successo.")
