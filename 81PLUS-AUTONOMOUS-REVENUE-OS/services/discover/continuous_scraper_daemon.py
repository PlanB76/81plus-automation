"""
81PLUS-AUTONOMOUS-REVENUE-OS
services/discover/continuous_scraper_daemon.py — Scraper H24 Continuo & Legale

Modalità di Esecuzione:
- 100% Locale su macchina Windows (ZERO minuti GitHub Actions consumati).
- Gira H24 con cicli cadenzati ogni 30-45 minuti.
- Estrae aziende su registri pubblici e directory per rotazione Province x Settori ATECO.
- Rispetta rate limit con intervalli etici (2-3 sec) per non essere bloccato.
- Inserisce i nuovi lead direttamente nel database SQLite locale 81plus.db.
"""

import sys, os, time, json, uuid, logging
from datetime import datetime

# Assicura encoding console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.discover.public_dataset_scraper import PublicDatasetNightlyScraper, NIGHTLY_SECTORS, NIGHTLY_CITIES
from shared.database.db import get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [H24-SCRAPER] %(message)s")
logger = logging.getLogger("H24_SCRAPER")

SLEEP_BETWEEN_BATCHES_SEC = 1800  # 30 minuti di pausa tra un ciclo e il successivo

def run_h24_daemon():
    logger.info("=" * 80)
    logger.info("🚀 81+ AUTONOMOUS REVENUE OS — AVVIO SCRAPER CONTINUO H24 (ZERO GITHUB MINUTI)")
    logger.info(f"⏰ Modalità: Demone Locale H24 · Pausa tra cicli: {SLEEP_BETWEEN_BATCHES_SEC // 60} minuti")
    logger.info("=" * 80)

    scraper = PublicDatasetNightlyScraper()
    cycle = 1

    while True:
        try:
            logger.info(f"\n--- AVVIO CICLO SCRAPING #{cycle} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
            
            # Esegue un batch calibrato da 15 aziende
            res = scraper.run_nightly_batch(target_quota=15)
            logger.info(f"Esito Ciclo #{cycle}: {res.get('new_companies', 0)} aziende salvate, {res.get('new_contacts', 0)} contatti.")
            
            cycle += 1
            logger.info(f"Pausa di {SLEEP_BETWEEN_BATCHES_SEC // 60} minuti prima del prossimo ciclo...")
            time.sleep(SLEEP_BETWEEN_BATCHES_SEC)

        except KeyboardInterrupt:
            logger.info("Interruzione manuale del demone H24.")
            break
        except Exception as e:
            logger.error(f"Errore durante il ciclo #{cycle}: {e}")
            time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        scraper = PublicDatasetNightlyScraper()
        res = scraper.run_nightly_batch(target_quota=15)
        print(json.dumps(res, indent=2))
    else:
        run_h24_daemon()
