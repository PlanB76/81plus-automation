"""ftp_db.py · scarica e ricarica 81plus.db da Hostinger via FTP con tolleranza d'errore totale.
I contatti e i log restano sul DB dell'host, niente risiede permanentemente su GitHub.

Miglioramenti industriali:
- Multipli tentativi con backoff esponenziale (default 5 tentativi, timeout 120s)
- PASV mode esplicito e blocksize 64KB per trasferimenti veloci
- Risoluzione intelligente di path (root '/', 'public_html/', '..', ecc.)
- Scarta file < 100KB (come stub da 0 byte) e verifica integrità SQLite (PRAGMA quick_check)
- Download e Upload ATOMICI (.tmp -> rename)
- Protezione PUT: non sovrascrive MAI l'host se il file locale è vuoto o corrotto
- Fallback trasparente: se l'FTP ha un blip temporaneo ma il DB locale è valido, prosegue
"""
import os, sys, time, ftplib, sqlite3

H = os.getenv("FTP_HOST")
U = os.getenv("FTP_USER")
P = os.getenv("FTP_PASS")
DIR = os.getenv("FTP_DIR", "").strip()
LOCAL = os.getenv("EMAIL81_DB", "81plus.db")
TIMEOUT = int(os.getenv("FTP_TIMEOUT", "120"))
TRIES = int(os.getenv("FTP_TRIES", "5"))
BLOCKSIZE = 65536

# Candidati per la ricerca del DB remoto
CUSTOM_PATH = os.getenv("FTP_DB_PATH", "").strip()
BASE_CANDS = [
    "81plus.db",
    "/81plus.db",
    "public_html/81plus.db",
    "/public_html/81plus.db",
    "../81plus.db",
    "0-81PLUS.NET/81plus.db",
    "/0-81PLUS.NET/81plus.db",
    "domains/81plus.net/public_html/81plus.db",
    "/domains/81plus.net/public_html/81plus.db"
]
if CUSTOM_PATH:
    CANDS = [CUSTOM_PATH] + [c for c in BASE_CANDS if c != CUSTOM_PATH]
else:
    CANDS = BASE_CANDS


def connect_ftp():
    """Connessione resiliente con retry, passive mode e timeout esteso."""
    last_err = None
    delay = 3
    for attempt in range(1, TRIES + 1):
        try:
            f = ftplib.FTP(timeout=TIMEOUT)
            f.connect(H, 21, timeout=TIMEOUT)
            f.login(U, P)
            f.set_pasv(True)
            if DIR:
                try:
                    f.cwd(DIR)
                except Exception as ce:
                    print(f"Nota: f.cwd({DIR}) non riuscito ({ce}), rimango in root.")
            return f
        except Exception as e:
            last_err = e
            print(f"[FTP] Tentativo {attempt}/{TRIES} fallito verso {H}: {e}")
            if attempt < TRIES:
                time.sleep(delay)
                delay = min(delay * 2, 30)
    raise RuntimeError(f"Impossibile connettersi all'host FTP dopo {TRIES} tentativi: {last_err}")


def verifica_integrita_sqlite(percorso):
    """Ritorna True se il file è un DB SQLite valido e non corrotto."""
    if not os.path.exists(percorso):
        return False
    if os.path.getsize(percorso) < 100000:
        return False
    try:
        con = sqlite3.connect(percorso, timeout=10)
        res = con.execute("PRAGMA quick_check").fetchone()
        con.close()
        return res is not None and res[0] == "ok"
    except Exception as e:
        print(f"Controllo integrità SQLite fallito per {percorso}: {e}")
        return False


def get():
    """Scarica il database dall'host remoto."""
    print(f"=== [FTP GET] Download {LOCAL} dall'host ===")
    tmp_local = LOCAL + ".download.tmp"
    if os.path.exists(tmp_local):
        try:
            os.remove(tmp_local)
        except Exception:
            pass

    f = connect_ftp()
    success = False
    chosen_path = None
    last_err = None

    try:
        cur_dir = ""
        try:
            cur_dir = f.pwd()
        except Exception:
            pass
        print(f"[FTP] Connesso con successo. Directory remota attuale: '{cur_dir}'")

        for path in CANDS:
            try:
                # Controlla dimensione remota prima di scaricare
                try:
                    rem_size = f.size(path)
                except Exception:
                    rem_size = None

                if rem_size is not None and rem_size < 100000:
                    print(f"  [SKIP] '{path}' esiste ma è troppo piccolo ({rem_size} byte)")
                    continue

                print(f"  [TENTATIVO] Scarico '{path}' (size attesa: {rem_size})...")
                with open(tmp_local, "wb") as fp:
                    f.retrbinary(f"RETR {path}", fp.write, blocksize=BLOCKSIZE)

                # Verifica integrità
                if verifica_integrita_sqlite(tmp_local):
                    downloaded_size = os.path.getsize(tmp_local)
                    if os.path.exists(LOCAL):
                        try:
                            os.remove(LOCAL)
                        except Exception:
                            pass
                    os.replace(tmp_local, LOCAL)
                    chosen_path = path
                    success = True
                    print(f"  [OK] DB integro scaricato da '{path}' -> {LOCAL} ({downloaded_size:,} byte)")
                    try:
                        with open(".dbpath", "w", encoding="utf-8") as dp:
                            dp.write(path)
                    except Exception:
                        pass
                    break
                else:
                    print(f"  [FAIL] '{path}' scaricato ma non ha superato PRAGMA quick_check.")
                    if os.path.exists(tmp_local):
                        os.remove(tmp_local)

            except Exception as e:
                last_err = e
                # Se la socket è morta, ricolleghiamo
                try:
                    f.voidcmd("NOOP")
                except Exception:
                    try:
                        f.quit()
                    except Exception:
                        pass
                    try:
                        f = connect_ftp()
                    except Exception:
                        pass

    finally:
        try:
            f.quit()
        except Exception:
            pass

    if success:
        return

    # Se non trovato su FTP ma abbiamo già un DB locale integro (es. fallback o precedente)
    if verifica_integrita_sqlite(LOCAL):
        print(f"[WARN] DB remoto non scaricato via FTP ({last_err}), ma {LOCAL} locale è integro. Procedo con DB locale!")
        return

    raise SystemExit(f"ERRORE CRITICO: DB non trovato via FTP (provati: {CANDS}) · Ultimo errore: {last_err}")


def put():
    """Ricarica il database aggiornato sull'host."""
    print(f"=== [FTP PUT] Sincronizzazione {LOCAL} verso l'host ===")
    if not os.path.exists(LOCAL):
        print(f"[WARN] {LOCAL} non esiste in locale. PUT annullato per salvaguardia.")
        return

    local_size = os.path.getsize(LOCAL)
    if local_size < 100000:
        print(f"[BLOCCATO] {LOCAL} è sospettosamente piccolo ({local_size} byte). PUT annullato per evitare sovrascritture distruttive.")
        return

    if not verifica_integrita_sqlite(LOCAL):
        print(f"[BLOCCATO] {LOCAL} non è un database SQLite integro. PUT annullato.")
        return

    target_path = None
    if os.path.exists(".dbpath"):
        try:
            target_path = open(".dbpath", encoding="utf-8").read().strip()
        except Exception:
            pass
    if not target_path:
        target_path = CANDS[0]

    # Eseguiamo upload su file temporaneo remoto e poi rename atomico
    f = connect_ftp()
    try:
        tmp_remote = target_path + ".tmp_upload"
        print(f"[FTP] Carico {LOCAL} ({local_size:,} byte) su '{tmp_remote}'...")
        with open(LOCAL, "rb") as fp:
            f.storbinary(f"STOR {tmp_remote}", fp, blocksize=BLOCKSIZE)

        # Rename atomico su host
        try:
            f.delete(target_path)
        except Exception:
            pass
        f.rename(tmp_remote, target_path)
        print(f"[OK] DB ricaricato e sostituito atomicamente su host: '{target_path}'")

        # Se il target era nella root ma esiste anche public_html, sincronizziamo una copia anche lì
        if "/" not in target_path or target_path == "81plus.db":
            try:
                pub_copy = "public_html/81plus.db"
                with open(LOCAL, "rb") as fp:
                    f.storbinary(f"STOR {pub_copy}", fp, blocksize=BLOCKSIZE)
                print(f"[OK] Copia speculare caricata anche in '{pub_copy}'")
            except Exception as e:
                print(f"Nota copia public_html: {e}")

    except Exception as e:
        print(f"[ERRORE PUT] Fallimento caricamento DB su host: {e}")
        raise
    finally:
        try:
            f.quit()
        except Exception:
            pass


if __name__ == "__main__":
    action = (sys.argv[1:] or ["get"])[0].lower()
    if action == "put":
        put()
    else:
        get()
