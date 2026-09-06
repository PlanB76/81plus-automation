"""
81PLUS-AUTONOMOUS-REVENUE-OS
15_RENEW81/renewal_monitor.py — Scadenzario Perpetuo T-90 .. T-7 & Trigger Rinnovi
"""
import os, sys, sqlite3
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def get_expiring_soon(days_ahead=60):
    conn = get_connection()
    c = conn.cursor()
    limit_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    c.execute('SELECT * FROM network_documenti_emessi WHERE data_scadenza IS NOT NULL AND data_scadenza <= ?', (limit_date,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

if __name__ == '__main__':
    exp = get_expiring_soon(60)
    print(f'[*] Attestati con scadenza entro 60gg: {len(exp)}')
