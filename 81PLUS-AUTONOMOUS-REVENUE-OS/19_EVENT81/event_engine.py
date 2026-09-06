"""
81PLUS-AUTONOMOUS-REVENUE-OS
19_EVENT81/event_engine.py — Event-Driven Architecture & Trigger Dispatcher
"""
import os, sys, json, sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

SUPPORTED_EVENTS = [
    "NEW_COMPANY",
    "NEW_HIRE",
    "COURSE_EXPIRING",
    "LAW_CHANGED",
    "DOCUMENT_EXPIRING",
    "EMAIL_CLICKED",
    "QUOTE_REQUESTED",
    "CART_ABANDONED",
    "CUSTOMER_INACTIVE"
]

def emit_event(event_type, company_id, payload=None):
    if event_type not in SUPPORTED_EVENTS:
        raise ValueError(f"Evento non supportato: {event_type}")
    payload = payload or {}
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS event_stream (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            company_id TEXT,
            payload_json TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    c.execute("INSERT INTO event_stream (event_type, company_id, payload_json) VALUES (?, ?, ?)",
              (event_type, str(company_id), json.dumps(payload)))
    conn.commit()
    conn.close()
    return {"status": "QUEUED", "event": event_type, "company_id": company_id}

if __name__ == '__main__':
    res = emit_event("COURSE_EXPIRING", "COMPANY-2377", {"scadenza_giorni": 30, "corso": "RSPP Datore"})
    print("[+] Event Engine test:", res)
