"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/srv_autopilot/autopilot_controller.py — AUTOPILOT81 & BOTTLENECK81 Constraint Engine
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.database.db import get_connection

def evaluate_bottleneck():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ghl_user360")
    leads = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM compliance_digital_twin WHERE temp_ladder IN ('W80', 'W100')")
    buyers = c.fetchone()[0]
    conn.close()

    # Catena dei colli di bottiglia
    # Se abbiamo già 9.000+ lead ma pochi W80, il bottleneck non è raccogliere lead ma attivare la conversione!
    if leads > 5000 and (buyers / leads) < 0.05:
        bottleneck = "ENGAGEMENT_TO_CONVERSION"
        direttiva = "Focalizzare 80% della capacità su Nudge Corsi Incompleti e Asseverazioni POS/HACCP (Non raccogliere lead freddi a caso)."
    else:
        bottleneck = "LEAD_DISCOVERY"
        direttiva = "Aumentare volume discovery H24 su ATECO Edilizia/Food con moltiplicatore ICP 3.2x."

    return {
        "active_bottleneck": bottleneck,
        "direttiva_operativa_oggi": direttiva,
        "total_leads": leads,
        "total_buyers": buyers
    }

if __name__ == '__main__':
    b = evaluate_bottleneck()
    print("=" * 65)
    print(f"[*] BOTTLENECK81: {b['active_bottleneck']}")
    print(f"[*] AUTOPILOT81 Direttiva: {b['direttiva_operativa_oggi']}")
    print("=" * 65)
