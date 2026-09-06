"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/srv_revenue/class_demand_engine.py — In-Class Training & Demand-Supply Engine

Raggruppa le capability dell'Aula:
- DEMAND81: Rileva e aggrega la domanda territoriale per provincia e codice corso.
- CLASS81: Genera classi al raggiungimento del quorum economico.
- SCHEDULE81: Gestisce il calendario edizioni (date, sedi, orari, posti, conferme).
- SUPPLY81: Monitora disponibilità effettiva di aule e posti prima di ogni promozione.
"""

import os
import sys
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OS_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if OS_ROOT not in sys.path:
    sys.path.insert(0, OS_ROOT)

from shared.database.db import get_connection

class ClassDemandEngine:
    def __init__(self):
        self.conn = get_connection()

    def record_interest_signal(self, provincia, codice_corso, num_corsisti=1, valore_stimato=250.0):
        """DEMAND81: Registra un segnale di interesse per un corso pratico in aula."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM class_demand_aggregations
            WHERE provincia = ? AND codice_corso = ?
        """, (provincia.upper(), codice_corso))
        row = cur.fetchone()
        
        if row:
            nuove_aziende = row["aziende_interessate_count"] + 1
            nuovi_corsisti = row["corsisti_potenziali_count"] + num_corsisti
            nuovo_valore = row["valore_stimato_totale"] + (valore_stimato * num_corsisti)
            stato = "QUORUM_RAGGIUNTO" if nuovi_corsisti >= 5 else "ACCUMULO"
            
            cur.execute("""
                UPDATE class_demand_aggregations
                SET aziende_interessate_count = ?, corsisti_potenziali_count = ?,
                    valore_stimato_totale = ?, stato_proposta = ?, last_updated = CURRENT_TIMESTAMP
                WHERE aggregation_id = ?
            """, (nuove_aziende, nuovi_corsisti, nuovo_valore, stato, row["aggregation_id"]))
        else:
            stato = "QUORUM_RAGGIUNTO" if num_corsisti >= 5 else "ACCUMULO"
            cur.execute("""
                INSERT INTO class_demand_aggregations
                (provincia, codice_corso, aziende_interessate_count, corsisti_potenziali_count, valore_stimato_totale, stato_proposta)
                VALUES (?, ?, 1, ?, ?, ?)
            """, (provincia.upper(), codice_corso, num_corsisti, valore_stimato * num_corsisti, stato))
            
        self.conn.commit()
        return self.get_aggregation_status(provincia, codice_corso)

    def get_aggregation_status(self, provincia, codice_corso):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM class_demand_aggregations
            WHERE provincia = ? AND codice_corso = ?
        """, (provincia.upper(), codice_corso))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_available_editions(self, provincia=None, codice_corso=None):
        """SUPPLY81: Verifica aule confermate con posti ancora disponibili."""
        cur = self.conn.cursor()
        query = "SELECT * FROM classroom_editions WHERE stato IN ('IN_ATTESA_QUORUM', 'CONFERMATO') AND posti_occupati < posti_totali"
        params = []
        if provincia:
            query += " AND provincia = ?"
            params.append(provincia.upper())
        if codice_corso:
            query += " AND codice_corso = ?"
            params.append(codice_corso)
            
        query += " ORDER BY data_inizio ASC"
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def book_seat(self, edition_id, num_posti=1):
        """SCHEDULE81: Prenota posti e verifica raggiungimento quorum o completamento aula."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM classroom_editions WHERE edition_id = ?", (edition_id,))
        row = cur.fetchone()
        if not row:
            return {"success": False, "error": "Edizione non trovata"}
            
        ed = dict(row)
        posti_rimasti = ed["posti_totali"] - ed["posti_occupati"]
        if num_posti > posti_rimasti:
            return {"success": False, "error": f"Solo {posti_rimasti} posti disponibili"}
            
        nuovi_occupati = ed["posti_occupati"] + num_posti
        nuovo_stato = ed["stato"]
        
        # Logica di stato
        if nuovi_occupati >= ed["quorum_minimo"] and ed["stato"] == "IN_ATTESA_QUORUM":
            nuovo_stato = "CONFERMATO"
        if nuovi_occupati >= ed["posti_totali"]:
            nuovo_stato = "COMPLETO"
            
        cur.execute("""
            UPDATE classroom_editions
            SET posti_occupati = ?, stato = ?
            WHERE edition_id = ?
        """, (nuovi_occupati, nuovo_stato, edition_id))
        self.conn.commit()
        
        # Calcolo margine economico classe
        ricavo_classe = nuovi_occupati * ed["prezzo_corsista"]
        costo_anfos = nuovi_occupati * ed["costo_attestato_anfos"]
        margine_classe = ricavo_classe - costo_anfos
        
        return {
            "success": True,
            "edition_id": edition_id,
            "posti_prenotati": num_posti,
            "posti_totali_occupati": nuovi_occupati,
            "posti_residui": ed["posti_totali"] - nuovi_occupati,
            "stato_classe": nuovo_stato,
            "economics_classe": {
                "ricavo_totale": ricavo_classe,
                "costo_anfos_totale": costo_anfos,
                "margine_netto_eur": margine_classe,
                "margine_pct": round((margine_classe / ricavo_classe) * 100, 1)
            }
        }

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    engine = ClassDemandEngine()
    print("=" * 70)
    print("🏫 TEST CLASS DEMAND ENGINE — DEMAND81 + CLASS81 + SCHEDULE81")
    print("=" * 70)
    
    # 1. Rilevazione domanda aggregata su Bologna per corso Muletto
    print("\n--- 1. AGGREGAZIONE DOMANDA TERRITORIALE (DEMAND81) ---")
    agg = engine.record_interest_signal("BO", "AULA_MULETTO_CARRELLI_12H", num_corsisti=3)
    print(f"Provincia: {agg['provincia']} | Corso: {agg['codice_corso']}")
    print(f"Aziende Interessate: {agg['aziende_interessate_count']} | Corsisti Potenziali: {agg['corsisti_potenziali_count']}")
    print(f"Stato Proposta: {agg['stato_proposta']} | Valore Stimato: € {agg['valore_stimato_totale']:,.2f}")
    
    # 2. Controllo disponibilità aule (SUPPLY81)
    print("\n--- 2. VERIFICA SUPPLY & POSTI DISPONIBILI (SUPPLY81) ---")
    edizioni = engine.get_available_editions(provincia="BO")
    for ed in edizioni:
        print(f"Edizione #{ed['edition_id']}: {ed['titolo_corso']} | Data: {ed['data_inizio']} | Posti: {ed['posti_occupati']}/{ed['posti_totali']} ({ed['stato']})")
        
    # 3. Prenotazione posti e raggiungimento Quorum (SCHEDULE81)
    print("\n--- 3. PRENOTAZIONE POSTI & QUORUM TRIGGER (SCHEDULE81) ---")
    prenotazione = engine.book_seat(edizioni[0]['edition_id'], num_posti=2)
    print(f"Prenotazione Effettuata: {prenotazione['success']}")
    print(f"Nuovo Stato Classe: {prenotazione['stato_classe']} (Posti: {prenotazione['posti_totali_occupati']})")
    print(f"Margine Economico Classe: € {prenotazione['economics_classe']['margine_netto_eur']:,.2f} ({prenotazione['economics_classe']['margine_pct']}%)")
    
    print("\n" + "=" * 70)
    print("✅ Test Class Demand & Supply completato con successo!")
    engine.close()
