"""
81PLUS-AUTONOMOUS-REVENUE-OS
20_ICP81/market_prioritizer.py — Market Prioritizer & Self-Directed Acquisition Loop
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Punteggi ICP calcolati per macro-settore
ICP_MATRIX = {
    "EDILIZIA_CANTIERI": {
        "ateco_prefixes": ["41", "42", "43"],
        "ticket_medio": 320.0,
        "frequenza_rinnovi_anno": 1.4,
        "urgenza_sanzioni": 0.95, # Patente a crediti D.L. 159/2025
        "margine_operativo": 0.82,
        "multiplier": 3.2,
        "direttiva_discovery": "PRIORITA_MASSIMA_ACQUISIZIONE"
    },
    "RISTORAZIONE_FOOD": {
        "ateco_prefixes": ["55", "56"],
        "ticket_medio": 240.0,
        "frequenza_rinnovi_anno": 1.2,
        "urgenza_sanzioni": 0.85, # ASL / Controlli HACCP
        "margine_operativo": 0.78,
        "multiplier": 2.4,
        "direttiva_discovery": "ALTA_PRIORITA"
    },
    "INDUSTRIA_MANIFATTURA": {
        "ateco_prefixes": ["10", "25", "28"],
        "ticket_medio": 450.0,
        "frequenza_rinnovi_anno": 1.0,
        "urgenza_sanzioni": 0.80,
        "margine_operativo": 0.75,
        "multiplier": 2.1,
        "direttiva_discovery": "MEDIA_PRIORITA"
    },
    "STUDI_SERVIZI": {
        "ateco_prefixes": ["62", "69", "70"],
        "ticket_medio": 120.0,
        "frequenza_rinnovi_anno": 0.8,
        "urgenza_sanzioni": 0.40,
        "margine_operativo": 0.88,
        "multiplier": 1.0,
        "direttiva_discovery": "MANTENIMENTO"
    }
}

def get_best_acquisition_target():
    """Comunica a LEAD81 dove cercare per massimizzare il ROI."""
    sorted_targets = sorted(ICP_MATRIX.items(), key=lambda x: x[1]['multiplier'], reverse=True)
    return sorted_targets[0]

if __name__ == '__main__':
    best = get_best_acquisition_target()
    print(f"[*] Best ICP Target: {best[0]} (Moltiplicatore: {best[1]['multiplier']}x) -> Direttiva: {best[1]['direttiva_discovery']}")
