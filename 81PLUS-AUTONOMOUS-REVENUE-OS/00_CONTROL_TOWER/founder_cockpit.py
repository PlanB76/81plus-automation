"""
81PLUS-AUTONOMOUS-REVENUE-OS
00_CONTROL_TOWER/founder_cockpit.py — Cockpit Esecutivo Founder 81+

Missione:
100% Automazione del Business 81+
Principio operativo del Founder:
1. VEDO (Monitoraggio H24 della macchina, dei lead e delle vendite)
2. CONTROLLO & SE DEL CASO FERMO (Emergency Kill-Switch globale e per singolo flusso)
3. A FINE MESE FACCIO LE FATTURE E CONTO I SOLDI (Export SDI per commercialista & calcolo utile netto)
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta

# Assicura codifica console corretta
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.database.db import get_connection

def ensure_cockpit_tables():
    """Crea o aggiorna le tabelle per la governance del cockpit founder."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tabella Stato Globale e Kill-Switch
    c.execute("""
        CREATE TABLE IF NOT EXISTS founder_system_governance (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            emergency_halt INTEGER DEFAULT 0,
            halt_reason TEXT,
            halted_at DATETIME,
            autonomous_mode TEXT DEFAULT 'ACTIVE_FULL_AUTO',
            monthly_revenue_target REAL DEFAULT 83333.0,
            last_founder_check DATETIME,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    c.execute("""
        INSERT OR IGNORE INTO founder_system_governance (id, emergency_halt, autonomous_mode)
        VALUES (1, 0, 'ACTIVE_FULL_AUTO');
    """)
    
    # 2. Tabella Ordini e Incassi per Fatturazione
    c.execute("""
        CREATE TABLE IF NOT EXISTS founder_billing_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            contact_id INT,
            rag_soc TEXT,
            piva_cf TEXT,
            indirizzo TEXT,
            pec_sdi TEXT,
            oggetto_servizio TEXT,
            importo_lordo REAL,
            imponibile REAL,
            iva_22 REAL,
            gateway_fee REAL,
            costo_partner REAL,
            utile_netto REAL,
            stato_pagamento TEXT DEFAULT 'PAID',
            data_pagamento DATETIME DEFAULT CURRENT_TIMESTAMP,
            fattura_generata INTEGER DEFAULT 0,
            fattura_numero TEXT,
            note TEXT
        );
    """)
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# 1. VEDO (Status & Visione della Macchina)
# ---------------------------------------------------------
def get_cockpit_status():
    """Restituisce il quadro completo e sintetico del business 81+."""
    ensure_cockpit_tables()
    conn = get_connection()
    c = conn.cursor()
    
    # Stato Kill-Switch
    gov = c.execute("SELECT emergency_halt, halt_reason, autonomous_mode, monthly_revenue_target FROM founder_system_governance WHERE id = 1;").fetchone()
    is_halted = bool(gov['emergency_halt'])
    halt_reason = gov['halt_reason'] or "Nessun blocco attivo"
    auto_mode = gov['autonomous_mode']
    target_mo = gov['monthly_revenue_target']
    
    # Volumi Digital Twins & Lead
    c.execute("SELECT COUNT(*) FROM compliance_digital_twin;")
    twins_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM privacy_compliance_gate WHERE status_permesso = 'CAN_CONTACT';")
    can_contact_count = c.fetchone()[0]
    
    # 81 Flussi e Step
    c.execute("SELECT COUNT(*), SUM(is_paused) FROM leadgen_flows;")
    row_f = c.fetchone()
    total_flows = row_f[0] or 0
    paused_flows = row_f[1] or 0
    
    c.execute("SELECT COUNT(*) FROM leadgen_flow_steps;")
    total_steps = c.fetchone()[0]
    
    # Categorie Ingegneristiche attive
    c.execute("SELECT cluster, COUNT(*), SUM(is_paused) FROM leadgen_flows WHERE cluster IS NOT NULL GROUP BY cluster ORDER BY COUNT(*) DESC;")
    categories = [{'cluster': r[0], 'flows': r[1], 'paused': r[2] or 0} for r in c.fetchall()]
    
    # Incassi del mese in corso
    now = datetime.now()
    first_of_month = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
    
    c.execute("""
        SELECT COUNT(*), COALESCE(SUM(importo_lordo), 0), COALESCE(SUM(utile_netto), 0)
        FROM founder_billing_ledger
        WHERE stato_pagamento = 'PAID' AND data_pagamento >= ?;
    """, (first_of_month,))
    billing_row = c.fetchone()
    orders_month = billing_row[0]
    gross_month = billing_row[1]
    net_month = billing_row[2]
    
    conn.close()
    
    return {
        'status': 'BLOCCO_EMERGENZA' if is_halted else 'OPERATIVO_100_AUTO',
        'is_halted': is_halted,
        'halt_reason': halt_reason,
        'autonomous_mode': auto_mode,
        'monthly_revenue_target': target_mo,
        'digital_twins': twins_count,
        'can_contact_leads': can_contact_count,
        'total_flows': total_flows,
        'paused_flows': paused_flows,
        'total_steps_email': total_steps,
        'categories': categories,
        'current_month_stats': {
            'orders_count': orders_month,
            'gross_revenue': gross_month,
            'net_profit': net_month,
            'target_progress_pct': round((gross_month / target_mo * 100) if target_mo else 0, 1)
        }
    }

# ---------------------------------------------------------
# 2. CONTROLLO & FERMO (Kill-Switch)
# ---------------------------------------------------------
def set_emergency_halt(halt=True, reason="Richiesta manuale Founder"):
    """Attiva o disattiva il Kill-Switch di emergenza per l'intera macchina."""
    ensure_cockpit_tables()
    conn = get_connection()
    c = conn.cursor()
    
    val = 1 if halt else 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if halt else None
    c.execute("""
        UPDATE founder_system_governance
        SET emergency_halt = ?, halt_reason = ?, halted_at = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1;
    """, (val, reason if halt else None, now_str))
    
    conn.commit()
    conn.close()
    state = "🔴 MACCHINA FERMATA CON SUCCESSO (KILL-SWITCH ATTIVO)" if halt else "🟢 MACCHINA RIATTIVATA (100% AUTOMATICA IN CORSO)"
    return {'halted': halt, 'message': state, 'reason': reason}

def toggle_flow_pause(flow_code, pause=True):
    """Mette in pausa o riattiva un singolo flusso o categoria."""
    conn = get_connection()
    c = conn.cursor()
    val = 1 if pause else 0
    c.execute("UPDATE leadgen_flows SET is_paused = ? WHERE flow_code = ?;", (val, flow_code))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return {'flow_code': flow_code, 'paused': pause, 'updated': affected}

# ---------------------------------------------------------
# 3. FINE MESE: FATTURO E CONTO I SOLDI
# ---------------------------------------------------------
def record_sale(order_id, rag_soc, piva_cf, indirizzo, pec_sdi, oggetto, lordo, partner_cost=0.0):
    """Registra una vendita automatica avvenuta sulla piattaforma 81+."""
    ensure_cockpit_tables()
    conn = get_connection()
    c = conn.cursor()
    
    imponibile = round(lordo / 1.22, 2)
    iva_22 = round(lordo - imponibile, 2)
    gateway_fee = round(lordo * 0.015 + 0.25, 2) # Stripe standard
    utile_netto = round(imponibile - gateway_fee - partner_cost, 2)
    
    c.execute("""
        INSERT OR REPLACE INTO founder_billing_ledger (
            order_id, rag_soc, piva_cf, indirizzo, pec_sdi,
            oggetto_servizio, importo_lordo, imponibile, iva_22,
            gateway_fee, costo_partner, utile_netto, stato_pagamento
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PAID');
    """, (order_id, rag_soc, piva_cf, indirizzo, pec_sdi, oggetto, lordo, imponibile, iva_22, gateway_fee, partner_cost, utile_netto))
    
    conn.commit()
    conn.close()
    return {'order_id': order_id, 'lordo': lordo, 'netto': utile_netto}

def generate_end_of_month_report(year=None, month=None):
    """Genera il riepilogo per il commercialista e il conto netto dei soldi del mese."""
    ensure_cockpit_tables()
    conn = get_connection()
    c = conn.cursor()
    
    now = datetime.now()
    y = year or now.year
    m = month or now.month
    
    start_date = f"{y:04d}-{m:02d}-01"
    if m == 12:
        end_date = f"{y+1:04d}-01-01"
    else:
        end_date = f"{y:04d}-{m+1:02d}-01"
        
    c.execute("""
        SELECT order_id, rag_soc, piva_cf, pec_sdi, oggetto_servizio,
               importo_lordo, imponibile, iva_22, gateway_fee, costo_partner, utile_netto, data_pagamento
        FROM founder_billing_ledger
        WHERE stato_pagamento = 'PAID' AND data_pagamento >= ? AND data_pagamento < ?
        ORDER BY data_pagamento ASC;
    """, (start_date, end_date))
    
    rows = c.fetchall()
    
    tot_lordo = sum(r['importo_lordo'] for r in rows)
    tot_imponibile = sum(r['imponibile'] for r in rows)
    tot_iva = sum(r['iva_22'] for r in rows)
    tot_fees = sum(r['gateway_fee'] for r in rows)
    tot_partner = sum(r['costo_partner'] for r in rows)
    tot_utile_netto = sum(r['utile_netto'] for r in rows)
    
    conn.close()
    
    return {
        'periodo': f"{y:04d}-{m:02d}",
        'totale_ordini': len(rows),
        'totale_lordo_incassato': round(tot_lordo, 2),
        'totale_imponibile_fatture': round(tot_imponibile, 2),
        'totale_iva_debito_22': round(tot_iva, 2),
        'totale_commissioni_gateway': round(tot_fees, 2),
        'totale_costi_certificazioni': round(tot_partner, 2),
        'CONTO_SOLDI_UTILE_NETTO': round(tot_utile_netto, 2),
        'ordini_dettaglio': [dict(r) for r in rows]
    }

if __name__ == "__main__":
    st = get_cockpit_status()
    print("=" * 70)
    print("🏢 81+ BUSINESS AUTONOMOUS REVENUE OS — COCKPIT FOUNDER")
    print("=" * 70)
    print(f"Stato Macchina:     {st['status']}")
    print(f"Modalità:           {st['autonomous_mode']}")
    print(f"Kill-Switch:        {'🔴 ATTIVO (FERMA)' if st['is_halted'] else '🟢 DISATTIVATO (IN CORSO)'}")
    print("-" * 70)
    print(f"Lead Profilati:     {st['digital_twins']} Digital Twins")
    print(f"Lead Contattabili:  {st['can_contact_leads']} (Gate Privacy Verificato)")
    print(f"Flussi Email:       {st['total_flows']} Attivi (Pausa: {st['paused_flows']})")
    print(f"Email Copy Pronte:  {st['total_steps_email']} Step Sequenziali")
    print("-" * 70)
    print("CATEGORIE FUNZIONALI:")
    for cat in st['categories']:
        print(f"  • {cat['cluster']:<42} : {cat['flows']:2d} flussi ({cat['flows']*3:2d} email)")
    print("-" * 70)
    m_stat = st['current_month_stats']
    print(f"Mese Corrente:      Ordini: {m_stat['orders_count']} | Lordo: € {m_stat['gross_revenue']:.2f} | Utile Netto: € {m_stat['net_profit']:.2f}")
    print("=" * 70)
