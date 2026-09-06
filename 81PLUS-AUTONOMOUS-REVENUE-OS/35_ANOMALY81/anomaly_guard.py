"""
81PLUS-AUTONOMOUS-REVENUE-OS
35_ANOMALY81/anomaly_guard.py — Guardia Automatica di Sicurezza & Kill-Switch
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def check_system_anomalies():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM global_suppression_list WHERE motivo = 'HARD_BOUNCE'")
    bounces = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ghl_user360")
    total = c.fetchone()[0]
    conn.close()

    bounce_rate = (bounces / total * 100) if total else 0.0
    anomalies = []

    if bounce_rate > 1.5:
        anomalies.append({"severity": "CRITICAL", "message": f"Hard bounce anomalo: {bounce_rate:.2f}% > 1.5%", "action": "KILL_SWITCH_EMAIL"})
    
    status = "HEALTHY" if not anomalies else "ALERT"
    return {"system_status": status, "anomalies_detected": anomalies, "bounce_rate": bounce_rate}

if __name__ == '__main__':
    res = check_system_anomalies()
    print(f"[*] Anomaly Guard status: {res['system_status']} (Hard bounce rate: {res['bounce_rate']:.2f}%)")
