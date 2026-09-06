"""
81+ AUTONOMOUS REVENUE OS
shared/security/suppression_gate.py — Suppression Gate Universale
Hard Rule: Opt-out, Unsubscribe o DO_NOT_CONTACT = STOP ASSOLUTO.
Nessun messaggio può oltrepassare questo gate se l'identificatore è soppresso.
"""

import sqlite3
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

class SuppressionGate:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn

    def _get_conn(self):
        return self.conn if self.conn is not None else get_connection()

    def is_suppressed(self, identifier: str) -> bool:
        """
        Verifica se un identificatore (email, dominio, piva, telefono) è soppresso.
        Controlla la tabella primaria `suppressions` e le tabelle legacy di opt-out.
        """
        if not identifier:
            return True # Sicurezza per default: identificatore nullo = bloccato
        
        ident = identifier.strip().lower()
        domain = ident.split("@")[-1] if "@" in ident else None

        conn = self._get_conn()
        cursor = conn.cursor()

        # 1. Tabella primaria suppressions
        cursor.execute("SELECT id, reason FROM suppressions WHERE identifier = ?", (ident,))
        row = cursor.fetchone()
        if row:
            return True

        if domain:
            cursor.execute("SELECT id, reason FROM suppressions WHERE identifier = ?", (domain,))
            if cursor.fetchone():
                return True

        # 2. Controllo tabelle legacy se presenti
        legacy_checks = [
            ("leadgen81_unsubscribes", "email"),
            ("scout81_optout", "email"),
            ("lead_exclusions_81", "email")
        ]
        for tbl, col in legacy_checks:
            try:
                cursor.execute(f"SELECT 1 FROM {tbl} WHERE LOWER({col}) = ? LIMIT 1", (ident,))
                if cursor.fetchone():
                    return True
            except sqlite3.OperationalError:
                pass # Tabella non presente o colonna diversa

        return False

    def add_suppression(self, identifier: str, id_type: str, reason: str, source: str = "SYSTEM") -> bool:
        """Aggiunge una soppressione permanente e irrevocabile."""
        if not identifier:
            return False
        ident = identifier.strip().lower()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO suppressions (identifier, type, reason, created_at, source)
            VALUES (?, ?, ?, ?, ?)
        """, (ident, id_type.upper(), reason.upper(), now, source))
        
        # Registra in audit log
        cursor.execute("""
            INSERT INTO audit_logs (timestamp, actor, action, target_type, target_id, details_json)
            VALUES (?, 'SUPPRESSION_GATE', 'ADD_SUPPRESSION', ?, ?, ?)
        """, (now, id_type.upper(), ident, f'{{"reason": "{reason}", "source": "{source}"}}'))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()
        return True

if __name__ == "__main__":
    gate = SuppressionGate()
    print("Test Suppression Gate:")
    gate.add_suppression("test_blocked@example.com", "EMAIL", "UNSUBSCRIBE", "TEST")
    print("Is test_blocked@example.com suppressed?", gate.is_suppressed("test_blocked@example.com"))
    print("Is valid_lead@example.com suppressed?", gate.is_suppressed("valid_lead@example.com"))
