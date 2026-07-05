# 📦 MATRIX81+ — Piano di archiviazione (46GB) e auto-salvataggio GitHub

## Il punto chiave
`MATRIX81.md` (il file di conoscenza del progetto) pesa **~6 KB**, NON 46 GB.
I **46 GB** sono i MEDIA del progetto (video, immagini, .mp4, .db). GitHub NON è adatto a 46 GB:
- limite **100 MB per file**, repo consigliato **< 1–5 GB**, niente cartelle da decine di GB.

## Soluzione adottata (split intelligente)
| Cosa | Dove | Come |
|---|---|---|
| **MATRIX81.md** (testo, ~6 KB) | **GitHub** (`PlanB76/81plus-automation`) | auto-commit giornaliero via workflow `matrix_backup.yml` + snapshot datati in `matrix_snapshots/` |
| Media 46 GB (video/img/db) | **Google Drive** (cartella MEDIA81+) | restano su Drive; il cloud pesca da lì via Drive API/folder ID |
| Sito live | repo `0-81PLUS.NET` | già versionato in git |

## Perché NON mettere i 46GB su GitHub
GitHub bloccherebbe il push (file >100MB), e Git LFS su decine di GB è costoso/lento e non serve:
i media non hanno bisogno di history git, basta un backup su Drive.

## Auto-salvataggio attivo
- Workflow **`matrix_backup.yml`**: ogni giorno alle 05:30 IT commit di `MATRIX81.md` + snapshot `MATRIX81_YYYY-MM-DD.md`.
- In locale: **`SYNC_GITHUB.bat`** fa commit+push manuale quando vuoi.
