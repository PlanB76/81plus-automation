"""
81PLUS-AUTONOMOUS-REVENUE-OS
21_VALUE81/ltv_engine.py — Customer Lifetime Value Prediction (12, 24, 36 Mesi)
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database.db import get_connection

def calculate_company_ltv(num_dipendenti=5, classe_rischio='ALTO', ateco_macro='EDILIZIA_CANTIERI'):
    # Valore formazione base per lavoratore: € 85
    # Valore aggiornamento annuo medio: € 40/lavoratore
    # Documento/POS annuo: € 250
    # Presidio asseverato: € 150/anno
    base_anno_1 = (num_dipendenti * 85) + 250 + 150
    anno_2 = (num_dipendenti * 40) + 150
    anno_3 = (num_dipendenti * 45) + 200 # Ciclo quinquennale rinnovi pesanti

    ltv_12m = base_anno_1
    ltv_24m = ltv_12m + anno_2
    ltv_36m = ltv_24m + anno_3

    return {
        "ltv_12m": round(ltv_12m, 2),
        "ltv_24m": round(ltv_24m, 2),
        "ltv_36m": round(ltv_36m, 2),
        "expected_profit_per_company": round(ltv_12m * 0.78, 2)
    }

if __name__ == '__main__':
    val = calculate_company_ltv(num_dipendenti=6, classe_rischio='ALTO')
    print(f"[*] Stima LTV Impresa Edile (6 dipendenti): 12m: € {val['ltv_12m']} | 24m: € {val['ltv_24m']} | 36m: € {val['ltv_36m']}")
