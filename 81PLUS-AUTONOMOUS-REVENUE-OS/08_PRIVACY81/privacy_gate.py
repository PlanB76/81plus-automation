"""
81PLUS-AUTONOMOUS-REVENUE-OS
08_PRIVACY81/privacy_gate.py — Privacy Compliance, GDPR & Suppression Gate
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def evaluate_contact(email, nome_azienda='', piva=''):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT status_permesso, note_audit FROM privacy_compliance_gate WHERE email = ?', (email.lower(),))
    row = c.fetchone()
    conn.close()
    if row:
        return {'email': email, 'status': row['status_permesso'], 'reason': row['note_audit']}
    domain = email.split('@')[-1].lower() if '@' in email else ''
    if 'pec' in domain or 'cert' in domain or 'postacert' in domain:
        return {'email': email, 'status': 'DO_NOT_CONTACT', 'reason': 'PEC istituzionale isolata'}
    freemails = {'gmail.com', 'yahoo.com', 'libero.it', 'hotmail.com', 'outlook.com', 'virgilio.it'}
    if domain in freemails:
        return {'email': email, 'status': 'REVIEW_NEEDED', 'reason': 'Consumer/Freemail domain'}
    return {'email': email, 'status': 'CAN_CONTACT', 'reason': 'B2B Corporate domain'}

if __name__ == '__main__':
    print('[*] Privacy Gate test:', evaluate_contact('info@impresaedile.it'))
