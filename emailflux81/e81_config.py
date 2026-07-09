"""e81_config.py · configurazione EMAIL81+ (SMTP Hostinger). Segreti SOLO da env.
DB = UNICO universale 81plus.db (0-81PLUS.NET). NESSUN DB separato."""
import os
_here=os.path.dirname(os.path.abspath(__file__))
# DB universale: sta nella cartella genitore (0-81PLUS.NET/81plus.db)
_default_db=os.path.abspath(os.path.join(_here,"..","81plus.db"))
DB          = os.getenv("EMAIL81_DB", _default_db)   # override solo per test
SMTP_HOST   = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER   = os.getenv("SMTP_USER", "")
SMTP_PASS   = os.getenv("SMTP_PASS", "")
MAIL_FROM   = os.getenv("MAIL_FROM", "81+ · SICURISSIMO <welcome@81plus.net>")
REPLY_TO    = os.getenv("REPLY_TO", "info@81plus.net")
BASE_URL    = os.getenv("BASE_URL", "https://81plus.net")
DRY_RUN     = os.getenv("DRY_RUN", "1") == "1"
DAILY_CAP   = int(os.getenv("DAILY_CAP", "120"))   # warm-up dominio nuovo: parti basso e sali
BATCH       = int(os.getenv("BATCH", "40"))
THROTTLE    = float(os.getenv("THROTTLE_SEC", "8"))
PROVIDER    = os.getenv("PROVIDER", "hostinger")
