import sys, os, sqlite3
from datetime import datetime

sys.path.insert(0, r'c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\81PLUS-AUTONOMOUS-REVENUE-OS')
from shared.database.db import get_connection

conn = get_connection()
cur = conn.cursor()

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Assicuriamo colonne estese nella tabella partner se servono
cols = [c['name'] for c in cur.execute("PRAGMA table_info(partner);").fetchall()]
for col, ctype in [('url_piattaforma', 'TEXT'), ('termini_pagamento', 'TEXT'), ('accreditamento', 'TEXT')]:
    if col not in cols:
        try:
            cur.execute(f"ALTER TABLE partner ADD COLUMN {col} {ctype};")
            print(f"Aggiunta colonna {col} a partner")
        except:
            pass

partners_seed = [
    {
        "nome": "Lezione-Online.it",
        "categoria": "E-LEARNING_FAD_DIRETTA",
        "tipo_accordo": "AFFILIAZIONE_UFFICIALE_FOUNDER",
        "provvigione_pct": 55.0, # Fino al 55-60% con sconti/margini riservati
        "attivo": 1,
        "solo_vip": 0,
        "contatto": "support@lezione-online.it",
        "url_piattaforma": "https://lezione-online.it",
        "termini_pagamento": "Bonifico Mensile / 30-60 gg",
        "accreditamento": "Ente di Formazione Accreditato FAD / Sicurezza / HACCP",
        "note": "Partner Ufficiale affiliato del Founder. Margini elevati e catalogo completo corsi e-learning."
    },
    {
        "nome": "Different Academy",
        "categoria": "ACADEMY_PREMIUM_BUSINESS",
        "tipo_accordo": "AFFILIAZIONE_UFFICIALE_FOUNDER",
        "provvigione_pct": 50.0, # 50% su corsi specialistici, digital e leadership
        "attivo": 1,
        "solo_vip": 0,
        "contatto": "info@differentacademy.it",
        "url_piattaforma": "https://differentacademy.it",
        "termini_pagamento": "Bonifico Mensile DFFM",
        "accreditamento": "Alta Formazione Professionale & Manageriale",
        "note": "Partner Ufficiale affiliato del Founder. Corsi premium, ticket medio più alto (€190-€450)."
    },
    {
        "nome": "ANFOS (Piattaforma E-Learning 2377)",
        "categoria": "SICUREZZA_HACCP_FAD",
        "tipo_accordo": "CENTRO_TERRITORIALE_CONVENZIONATO",
        "provvigione_pct": 48.0, # 48% corsi, 50% documenti
        "attivo": 1,
        "solo_vip": 0,
        "contatto": "convenzioni@anfos.it",
        "url_piattaforma": "https://www.anfos.it",
        "termini_pagamento": "60 giorni DFFM",
        "accreditamento": "Ente Paritetico Nazionale D.Lgs. 81/08",
        "note": "Piattaforma primaria di erogazione e validazione attestati. Costi fissi zero, 50% docs e 48% corsi."
    },
    {
        "nome": "TuttoHACCP / Formazione Italia Hub",
        "categoria": "HACCP_ALIMENTARE",
        "tipo_accordo": "AFFILIATE_NETWORK",
        "provvigione_pct": 55.0, # Modello wholesale con white-label
        "attivo": 1,
        "solo_vip": 0,
        "contatto": "affiliazioni@tuttohaccp.com",
        "url_piattaforma": "https://www.tuttohaccp.com",
        "termini_pagamento": "30 giorni DFFM",
        "accreditamento": "Formazione Alimentaristi & Piani di Autocontrollo",
        "note": "Alternativa ad alto margine per sole certificazioni alimentari (55% netto su manuali e corsi)."
    },
    {
        "nome": "Hideea / Impresa8108 Network",
        "categoria": "RETE_CENTRI_FORMAZIONE",
        "tipo_accordo": "WHOLESALE_RESELLER",
        "provvigione_pct": 60.0, # Acquistando pacchetti monte-ore FAD wholesale
        "attivo": 1,
        "solo_vip": 0,
        "contatto": "partner@impresa8108.it",
        "url_piattaforma": "https://www.impresa8108.it",
        "termini_pagamento": "Anticipato su pacchetti o 30 gg",
        "accreditamento": "Soggetto Formatore O.P.N.",
        "note": "Modello a gettoni/monte ore FAD: margine fino al 60% sul prezzo di listino per i corsi lavoratori."
    }
]

for idx, p in enumerate(partners_seed, start=1):
    cur.execute("""
        INSERT OR REPLACE INTO partner (
            id, nome, categoria, tipo_accordo, provvigione_pct, attivo, solo_vip,
            contatto, url_piattaforma, termini_pagamento, accreditamento, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        idx, p["nome"], p["categoria"], p["tipo_accordo"], p["provvigione_pct"], p["attivo"], p["solo_vip"],
        p["contatto"], p["url_piattaforma"], p["termini_pagamento"], p["accreditamento"], p["note"], now_str
    ))

conn.commit()
print("Inseriti e aggiornati i Partner nel Database:")
for r in cur.execute("SELECT id, nome, tipo_accordo, provvigione_pct, termini_pagamento FROM partner;").fetchall():
    print(f"  • [{r['id']}] {r['nome']:<30} | {r['provvigione_pct']}% | {r['tipo_accordo']:<28} | {r['termini_pagamento']}")
