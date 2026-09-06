"""
81PLUS-AUTONOMOUS-REVENUE-OS
17_PROFIT81/profit_predictor.py — Reverse Funnel & Previsioni Cash Flow Cohort
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def get_latest_forecast():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM compliance_profit_forecasts ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}

if __name__ == '__main__':
    f = get_latest_forecast()
    print(f"[*] Ultimo forecast ARR: € {f.get('ricavi_attesi_365d_arr', 0):,.2f} | MRR: € {f.get('mrr_stimato', 0):,.2f}")
