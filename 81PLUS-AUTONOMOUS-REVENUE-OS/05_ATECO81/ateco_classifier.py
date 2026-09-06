"""
81PLUS-AUTONOMOUS-REVENUE-OS
05_ATECO81/ateco_classifier.py — Tassonomia e Mappatura Rischi per Settore ATECO
"""
SECTOR_MAP = {
    'F': {'settore': 'EDILIZIA_CANTIERI', 'rischio': 'ALTO', 'obblighi': ['POS', 'DVR', 'DPI_III', 'LAVORI_IN_QUOTA', 'PATENTE_CREDITI']},
    'I': {'settore': 'RISTORAZIONE_FOOD', 'rischio': 'MEDIO', 'obblighi': ['MANUALE_HACCP', 'CORSO_ALIMENTARISTA', 'TAMPONI', 'DVR']},
    'C': {'settore': 'INDUSTRIA_MANIFATTURA', 'rischio': 'ALTO', 'obblighi': ['DVR_RUMORE', 'VIBRAZIONI', 'CHIMICO', 'MULETTO']},
    'G': {'settore': 'COMMERCIO', 'rischio': 'MEDIO', 'obblighi': ['DVR', 'PRIMO_SOCCORSO', 'ANTINCENDIO', 'RLS']},
    'M': {'settore': 'STUDI_SERVIZI', 'rischio': 'BASSO', 'obblighi': ['DVR_SEMPLIFICATO', 'VDT', 'PRIVACY_GDPR']}
}

def classify_ateco(code):
    prefix = str(code).strip()[:2]
    if prefix in ['41', '42', '43']:
        return SECTOR_MAP['F']
    elif prefix in ['55', '56']:
        return SECTOR_MAP['I']
    elif prefix in ['10', '11', '12', '25', '28', '29', '30']:
        return SECTOR_MAP['C']
    elif prefix in ['45', '46', '47']:
        return SECTOR_MAP['G']
    else:
        return SECTOR_MAP['M']

if __name__ == '__main__':
    print('[*] Classificazione ATECO 41.20 (Edilizia):', classify_ateco('41.20'))
    print('[*] Classificazione ATECO 56.10 (Ristoranti):', classify_ateco('56.10'))
