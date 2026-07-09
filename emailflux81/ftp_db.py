"""ftp_db.py · scarica/ricarica 81plus.db dall'host via FTP (i contatti NON vanno su GitHub).
Env: FTP_HOST, FTP_USER, FTP_PASS, FTP_DIR (opz), FTP_DB_PATH (opz). Prova piu' percorsi candidati."""
import os, sys, ftplib
H=os.getenv("FTP_HOST"); U=os.getenv("FTP_USER"); P=os.getenv("FTP_PASS")
DIR=os.getenv("FTP_DIR",""); LOCAL=os.getenv("EMAIL81_DB","81plus.db")
CANDS=[c for c in [os.getenv("FTP_DB_PATH"), "81plus.db", "0-81PLUS.NET/81plus.db",
        "public_html/81plus.db", "public_html/0-81PLUS.NET/81plus.db",
        "domains/81plus.net/public_html/0-81PLUS.NET/81plus.db"] if c]
def conn():
    f=ftplib.FTP(H,timeout=40); f.login(U,P)
    if DIR:
        try: f.cwd(DIR)
        except Exception: pass
    return f
def get():
    f=conn(); last=None
    for path in CANDS:
        try:
            with open(LOCAL,"wb") as fp: f.retrbinary("RETR "+path, fp.write)
            f.quit(); print("DB scaricato:",path,"->",LOCAL,os.path.getsize(LOCAL),"byte")
            open(".dbpath","w").write(path); return
        except Exception as e: last=e
    f.quit(); raise SystemExit("DB non trovato via FTP (provati: %s) · %s"%(CANDS,last))
def put():
    path=open(".dbpath").read().strip() if os.path.exists(".dbpath") else CANDS[0]
    f=conn()
    with open(LOCAL,"rb") as fp: f.storbinary("STOR "+path, fp)
    f.quit(); print("DB ricaricato su host:",path)
if __name__=="__main__":
    (get if (sys.argv[1:] or ["get"])[0]=="get" else put)()
