"""
81PLUS-AUTONOMOUS-REVENUE-OS
04_COMPANY81/digital_twin.py — Digital Twin dell'Impresa (Identita, ATECO, Gap, Scadenze)
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def get_digital_twin_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM compliance_digital_twin WHERE email = ?', (email.lower(),))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

if __name__ == '__main__':
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM compliance_digital_twin')
    tot = c.fetchone()[0]
    conn.close()
    print(f'[*] Totale Company Digital Twin attivi: {tot}')
