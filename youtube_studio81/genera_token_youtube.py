# -*- coding: utf-8 -*-
"""
GENERA TOKEN YOUTUBE 81+ (token unico a 3 scope)
Crea un token OAuth che copre: caricare short (youtube.upload),
restyle titoli/descrizioni/thumbnail (youtube.force-ssl) e leggere il Drive
(drive.readonly). Un solo token per canale -> incollalo nel secret GitHub.

USO:
  python genera_token_youtube.py <client_secret.json> <token_out.json>

Esempio (canale @sicurissimo):
  python genera_token_youtube.py client_secret_686001138759-XXXX.json token_sicurissimo.json
Poi apri token_sicurissimo.json, copia TUTTO il contenuto e incollalo nel
secret GitHub  YOUTUBE_TOKEN_JSON.
Per @destinorandagio -> token_destino.json -> secret YOUTUBE_TOKEN_JSON_DESTINO.

NB: fai login con l'account Google che gestisce QUEL canale YouTube.
Dipendenze:  pip install google-auth-oauthlib google-api-python-client
"""
import sys, os, glob

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/drive.readonly",
]

def trova_client():
    # se non passato, cerca un client_secret*.json nella cartella corrente
    cand = sorted(glob.glob("client_secret*.json"))
    return cand[0] if cand else None

def main():
    client = sys.argv[1] if len(sys.argv) > 1 else ""
    if not client:
        client = trova_client()
    out    = sys.argv[2] if len(sys.argv) > 2 else "token_youtube.json"
    if not client or not os.path.exists(client):
        print("ERRORE: passa il file client_secret .json come primo argomento.")
        print("Uso: python genera_token_youtube.py <client_secret.json> <token_out.json>")
        sys.exit(1)
    from google_auth_oauthlib.flow import InstalledAppFlow
    print(">> Si aprira' il browser: accedi con l'account del canale e concedi i permessi.")
    flow = InstalledAppFlow.from_client_secrets_file(client, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    with open(out, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print("\nOK. Token scritto in:", os.path.abspath(out))
    print("Scope inclusi:", creds.scopes)
    print("Ora copia TUTTO il contenuto di", out, "nel secret GitHub corrispondente.")

if __name__ == "__main__":
    main()
