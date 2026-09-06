"""
81PLUS-AUTONOMOUS-REVENUE-OS
37_LEARN81/learning_loop.py — Continuous Learning Loop & Policy Calibration
PREDICTION -> ACTION -> RESULT -> DELTA -> LEARN -> NEW POLICY
"""
import os, sys, json, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def record_feedback(action_id, prediction_val, actual_val, metric="conversion_rate"):
    delta = actual_val - prediction_val
    learning_rate = 0.05
    adjusted_policy = prediction_val + (learning_rate * delta)

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS learning_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            action_id TEXT,
            metric TEXT,
            predicted REAL,
            actual REAL,
            delta REAL,
            updated_policy REAL
        )
    """)
    c.execute("INSERT INTO learning_policies (action_id, metric, predicted, actual, delta, updated_policy) VALUES (?, ?, ?, ?, ?, ?)",
              (action_id, metric, prediction_val, actual_val, delta, adjusted_policy))
    conn.commit()
    conn.close()
    return {"action_id": action_id, "delta": round(delta, 4), "updated_policy": round(adjusted_policy, 4)}

if __name__ == '__main__':
    res = record_feedback("CAMPAIGN_EDILIZIA_POS", 0.045, 0.052, "ctr")
    print("[+] Learning Loop calibrazione policy:", res)
