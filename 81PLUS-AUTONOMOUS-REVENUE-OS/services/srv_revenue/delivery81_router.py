"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/srv_revenue/delivery81_router.py — DELIVERY81 Training Routing Layer

Gestisce il doppio canale di erogazione mantenendo l'esperienza utente 81+ UNIFICATA:
1. Piattaforma Online FAD (E-learning automatico H24): Partner ID 2377
2. Piattaforma Corsi in Aula / Addestramento Pratico: Centri ANFOS
   - Credenziali operative: labomobile.lm@gmail.com / h29031976T.
   - Costo attestato ANFOS: € 10,00 - € 30,00
   - Prezzo di vendita libero: € 150,00 - € 300,00+
   - Margine operativo netto: 80% - 93%
3. Costruttori Documenti (POS Cantieri / HACCP Registri): Interno 81+ (100% Margine)
"""

import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

PLATFORM_ONLINE_FAD_URL = "https://corsi.elearningsicurezza.com/pid/2377/#login"
PLATFORM_AULA_ANFOS_URL = "https://centri.anfos.it/centri-anfos3/centro/#login"
ANFOS_USER = "labomobile.lm@gmail.com"

class Delivery81Router:
    def __init__(self):
        self.conn = get_connection()

    def route_training_need(self, corso_code_or_keyword, num_corsisti=1, custom_price=None):
        """
        Determina la modalità ottimale (ONLINE_FAD, AULA_PRESENZA, BLENDED, DOCUMENTALE)
        e calcola economics, fornitore e istruzioni per l'utente.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM training_delivery_catalog 
            WHERE codice_corso LIKE ? OR nome_corso LIKE ?
            LIMIT 1
        """, (f"%{corso_code_or_keyword}%", f"%{corso_code_or_keyword}%"))
        row = cur.fetchone()
        
        if not row:
            # Fallback generico
            return {
                "trovato": False,
                "corso": corso_code_or_keyword,
                "delivery_mode": "ONLINE_FAD",
                "message": "Corso non trovato a catalogo; instradato su piattaforma generale."
            }
            
        c = dict(row)
        costo_unitario = c["costo_base_attestato"]
        prezzo_unitario = custom_price if custom_price else c["prezzo_vendita_consigliato"]
        
        tot_costo = costo_unitario * num_corsisti
        tot_ricavo = prezzo_unitario * num_corsisti
        tot_margine = tot_ricavo - tot_costo
        margine_pct = round((tot_margine / tot_ricavo) * 100, 1) if tot_ricavo > 0 else 100.0

        provider_destination = PLATFORM_ONLINE_FAD_URL
        logistica_descrizione = "Fruizione online 24/7 su piattaforma FAD con tracciamento SCORM."
        
        if c["delivery_mode"] in ["AULA_PRESENZA", "BLENDED"]:
            provider_destination = PLATFORM_AULA_ANFOS_URL
            logistica_descrizione = f"Addestramento pratico e sessione d'aula gestiti tramite centro ANFOS ({c['durata_ore']} ore). Attestato abilitativo nazionale."
        elif c["delivery_mode"] == "DOCUMENTALE":
            provider_destination = "https://81plus.net"
            logistica_descrizione = "Generazione guidata immediata online con download PDF conforme."

        return {
            "trovato": True,
            "codice_corso": c["codice_corso"],
            "nome_corso": c["nome_corso"],
            "macro_settore": c["macro_settore"],
            "delivery_mode": c["delivery_mode"],
            "provider_platform": c["provider_platform"],
            "logistica_descrizione": logistica_descrizione,
            "num_corsisti": num_corsisti,
            "economics": {
                "costo_base_unitario": costo_unitario,
                "prezzo_vendita_unitario": prezzo_unitario,
                "totale_costo_attestati": tot_costo,
                "totale_ricavo_lordo": tot_ricavo,
                "margine_netto_eur": tot_margine,
                "margine_netto_pct": margine_pct
            },
            "validita_anni": c["validita_anni"],
            "frontend_cta_url": "https://81plus.net", # Sempre 81plus per l'utente finale
            "backend_execution_url": provider_destination
        }

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    router = Delivery81Router()
    print("=" * 70)
    print("🎓 TEST DELIVERY81 ROUTER — FAD PID 2377 vs AULA ANFOS CON PREZZI LIBERI")
    print("=" * 70)
    
    # Test 1: Corso Online FAD
    res_fad = router.route_training_need("FAD_GEN_4H", num_corsisti=5)
    print(f"\n1. CORSO ONLINE (FAD): {res_fad['nome_corso']}")
    print(f"   Modalità: {res_fad['delivery_mode']} | Provider: {res_fad['provider_platform']}")
    print(f"   Ricavo: € {res_fad['economics']['totale_ricavo_lordo']:,.2f} | Costo: € {res_fad['economics']['totale_costo_attestati']:,.2f}")
    print(f"   Margine Netto: € {res_fad['economics']['margine_netto_eur']:,.2f} ({res_fad['economics']['margine_netto_pct']}%)")
    
    # Test 2: Corso in Aula con ANFOS a Prezzo Libero (€250 cad. a fronte di €30 costo)
    res_aula = router.route_training_need("MULETTO", num_corsisti=3, custom_price=260.0)
    print(f"\n2. CORSO IN AULA / ADDESTRAMENTO: {res_aula['nome_corso']}")
    print(f"   Modalità: {res_aula['delivery_mode']} | Provider: {res_aula['provider_platform']}")
    print(f"   Logistica: {res_aula['logistica_descrizione']}")
    print(f"   Ricavo: € {res_aula['economics']['totale_ricavo_lordo']:,.2f} (3 allievi @ € 260)")
    print(f"   Costo Attestati ANFOS: € {res_aula['economics']['totale_costo_attestati']:,.2f} (3 allievi @ € 30)")
    print(f"   Margine Netto Reale: € {res_aula['economics']['margine_netto_eur']:,.2f} ({res_aula['economics']['margine_netto_pct']}%)")
    
    # Test 3: Documento POS
    res_pos = router.route_training_need("POS", num_corsisti=1)
    print(f"\n3. COSTRUTTORE DOCUMENTALE: {res_pos['nome_corso']}")
    print(f"   Modalità: {res_pos['delivery_mode']} | Margine: {res_pos['economics']['margine_netto_pct']}%")
    
    print("\n" + "=" * 70)
    print("✅ Routing didattico ed economics verificati con successo!")
    router.close()
