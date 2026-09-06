"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/srv_governance/human_queue.py — HUMAN81: Exception Queue & WhatsApp Escalation
"""
import os, sys, sqlite3, urllib.parse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

WHATSAPP_ADMIN = "+393388771737"

def enqueue_exception(tipo_eccezione, email, dettagli, valore_eur=0.0):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS human_exception_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT NOT NULL,
            email TEXT,
            dettagli TEXT,
            valore_eur REAL DEFAULT 0.0,
            stato TEXT DEFAULT 'OPEN'
        )
    """)
    c.execute("INSERT INTO human_exception_queue (tipo, email, dettagli, valore_eur) VALUES (?, ?, ?, ?)",
              (tipo_eccezione, email, dettagli, valore_eur))
    conn.commit()
    item_id = c.lastrowid
    conn.close()

    text_wa = f"⚠️ [HUMAN81 ECCEZIONE #{item_id}] Tipo: {tipo_eccezione} | Email: {email} | Valore: € {valore_eur:,.2f} | Dettaglio: {dettagli}"
    link_wa = f"https://wa.me/{WHATSAPP_ADMIN.replace('+', '')}?text={urllib.parse.quote(text_wa)}"

    return {
        "queue_id": item_id,
        "tipo": tipo_eccezione,
        "status": "QUEUED_FOR_HUMAN_REVIEW",
        "whatsapp_routing_url": link_wa
    }

if __name__ == '__main__':
    q = enqueue_exception("PREVENTIVO_ALTO_VALORE", "direzione@costruzionigrandi.it", "Richiesta fascicolo 14 cantieri + POS cumulativo", 2450.00)
    print("[+] Exception Enqueued:", q["queue_id"], "-> Status:", q["status"])
