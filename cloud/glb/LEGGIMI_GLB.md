# SICURIX GLB Factory — personaggi 3D generati da soli, H24, gratis

Genera i GLB texturati dei personaggi SICURIX (stile manga del nuovo master) **senza browser e senza GPU tua**:
GitHub Actions chiama lo Space **SF3D (Stable Fast 3D)** via API, la GPU è quella gratuita di Hugging Face,
il workflow salva i GLB nel repo. Va a lotti ogni 3 ore finché non li ha fatti tutti.

## Cosa fa
- Input: `cloud/glb/crops/*.png` (ritagli FRONT dei personaggi, già pronti).
- Motore: `cloud/glb/make_glb.py` → SF3D → GLB.
- Output: `cloud/glb/out/<NOME>.glb` + stato anti-ripetizione `glb_state.json`.
- Workflow: `.github/workflows/sicurix_glb.yml` (cron ogni 3 ore + avvio manuale).

## L'UNICA cosa che devi fare tu (una volta)
1. Crea un **token Hugging Face gratuito**: huggingface.co → Settings → Access Tokens → *New token* (ruolo **read**).
2. Su GitHub, nel repo dell'automazione: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `HF_TOKEN`  ·  Secret: il token `hf_...`
3. Fai partire: scheda **Actions → "SICURIX GLB Factory" → Run workflow** (oppure aspetta il cron).

Da lì genera i GLB da solo, un lotto per volta, e li committa in `cloud/glb/out/`.

## Portare i GLB nel gioco
Quando ci sono nuovi GLB in `cloud/glb/out/`, lancia `IMPORTA_GLB.bat` (nella cartella del gioco):
copia gli `*.glb` in `sicurix-game/assets/models/`. Il gioco li **usa in automatico** (auto-load): nessun codice da toccare.
I nomi già corretti per il gioco: SICURIX, CHECKIX, CHEFIX, HYGIENIX, TRACCIX, SCUDIX, AIDIX, DOCUMIX.
Gli altri sono nominati `S02_R1`, `S03_R2`… (Sheet/Riga): utili per Tales/marketing; per usarli in gioco basta rinominarli col nome del personaggio.

## Note oneste
- SF3D è veloce e gratis, ma la **quota GPU di Hugging Face è giornaliera**: per questo si va a lotti (6 per run, ~ogni 3 ore). In pochi giorni li fa tutti, da solo.
- Se un modello esce male, cancella il suo nome da `glb_state.json` e rigenera.
- Stile = master originale "SICURIX UNIVERSE" (manga tattico nero/bianco/arancione). Nessun riferimento LEGO.
