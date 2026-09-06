"""
81+ AUTONOMOUS REVENUE OS
shared/events/event_bus.py — EVENT81 Event Bus Persistito
Ogni evento significativo attraversa questo bus e viene archiviato in `events81`
con garanzia di audit e tracciabilità completa.
"""

import os
import sys
import json
import uuid
from datetime import datetime
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

class EventBus81:
    def __init__(self, conn: sqlite3.Connection = None):
        self.conn = conn

    def _get_conn(self):
        return self.conn if self.conn is not None else get_connection()

    def publish(self, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> str:
        """Pubblica e persiste un evento nel bus."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        payload_str = json.dumps(payload, ensure_ascii=False)

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events81 (event_id, event_type, aggregate_type, aggregate_id, payload_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, event_type, aggregate_type, aggregate_id, payload_str, timestamp))

        # Registra in audit_logs per conformità
        cursor.execute("""
            INSERT INTO audit_logs (timestamp, actor, action, target_type, target_id, details_json)
            VALUES (?, 'EVENT_BUS', ?, ?, ?, ?)
        """, (timestamp, event_type, aggregate_type, aggregate_id, payload_str))

        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()
        return event_id

    def fetch_unprocessed(self, limit: int = 50) -> list[dict]:
        """Recupera eventi non ancora processati."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, event_type, aggregate_type, aggregate_id, payload_json, timestamp
            FROM events81
            WHERE processed_at IS NULL
            ORDER BY timestamp ASC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        events = []
        for r in rows:
            events.append({
                "event_id": r["event_id"],
                "event_type": r["event_type"],
                "aggregate_type": r["aggregate_type"],
                "aggregate_id": r["aggregate_id"],
                "payload": json.loads(r["payload_json"]),
                "timestamp": r["timestamp"]
            })
        if self.conn is None:
            conn.close()
        return events

    def mark_processed(self, event_id: str):
        """Marca un evento come elaborato."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE events81 SET processed_at = ? WHERE event_id = ?", (now, event_id))
        if self.conn is None:
            conn.commit()
            conn.close()
        else:
            conn.commit()

if __name__ == "__main__":
    bus = EventBus81()
    eid = bus.publish("TEST_EVENT", "SYSTEM", "M0_CHECK", {"status": "ACTIVE", "version": "1.0"})
    print(f"[OK] Published event: {eid}")
    unprocessed = bus.fetch_unprocessed(10)
    print(f"[OK] Unprocessed count: {len(unprocessed)}")
    bus.mark_processed(eid)
    print(f"[OK] Event {eid} marked processed.")
