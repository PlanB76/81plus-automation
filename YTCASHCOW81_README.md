# 🐄 YTCASHCOW81+ — Automazione GLOBALE canali YouTube (H24 7/7)
Motore multi-canale che tiene VIVO ogni canale YT e lo spinge verso la monetizzazione, in autonomia su GitHub Actions.

## Cosa fa ogni giorno (per OGNI canale in `cloud/channels.json`)
1. **RICICLO EVERGREEN** (2–3 video vecchi/giorno, rotazione ciclica su tutto il catalogo, agli orari migliori 14:30/18:30):
   - Titolo → **clickbait** magnetico · Descrizione → **super-SEO ipnotica** (hook + CHECK gratuito + 2 CTA a **prodotti reali** dal LISTINO81+ coerenti col tema + iscrizione canale) · **hashtag** · **thumbnail** brandizzata 81+.
   - Via YouTube Data API (`videos.update` + `thumbnails.set`).
2. **SOCIAL81+**: pubblica lo **short-del-giorno** (dal piano editoriale 365 ciclico) su **Telegram** (auto, canale pubblico + privato) e genera il **pacchetto post** per **YT/FB/IG/TikTok/LinkedIn** (`SOCIAL81_OGGI.md`), con CTA al canale @sicurissimo + prodotto su 81plus.net + check gratuito.

## Verità utile (niente fumo)
- YouTube **non ri-programma** un video già pubblico: il "riciclo" = refresh titolo/descrizione/hashtag/thumbnail su rotazione → l'algoritmo lo ri-valuta (è ciò che rende "virale" un vecchio video). Per i video NUOVI si usa `publishAt`.
- **Telegram** si pubblica da solo (bot). **FB/IG/TikTok/LinkedIn**: copy pronta in `SOCIAL81_OGGI.md`; per l'auto-post serve un connettore (Postiz/Buffer o le API ufficiali) — si aggancia poi.
- La **creazione dei video** (cartoni Sicù) resta separata: vedi `SICù81+/SICU81_ROTAZIONE_AI_VIDEO.md` (rotazione Veo+Kling+Vidu+Hailuo+Pika+Fliki+CapCut).

## Multi-canale (globale)
Aggiungi canali in `cloud/channels.json` (handle, channel_id, best_times, recycle_per_day, tg_public, tg_private). Il motore li cicla tutti.

## Accensione (owner)
- Secrets GitHub: `YOUTUBE_TOKEN_JSON` (OAuth write), `YOUTUBE_API_KEY`, `TELEGRAM_BOT_TOKEN`.
- `SYNC_GITHUB.bat` per push. Actions → **YTCASHCOW81+ Global** → Run.
- Senza `YOUTUBE_TOKEN_JSON` gira in **DRY-RUN** (scrive `YTCASHCOW_REPORT.md` con cosa cambierebbe, senza toccare il canale).

## File
`cloud/ytcashcow81.py` (motore) · `cloud/ytseo81.py` (SEO virale) · `cloud/social81_pack.py` (multi-social) · `cloud/channels.json` · `cloud/data/product_links.json` (2144 prodotti) · `cloud/data/editorial_365.json` (1095 short ciclici) · `.github/workflows/ytcashcow81.yml`
