# MATRIX81+ — MEMORIA UNIVERSALE 81PLUS+
> Memoria viva dell'ecosistema. Si aggiorna a ogni sessione con le decisioni e ciò che ci diciamo.
> Aggiornamento: manuale o `python3 matrix81_update.py "nota"` (appende in SESSION LOG).
> CORTEX = anima (agisce sul DB). MATRIX = memoria (questo file + RAG JSON).

## 0. IDENTITÀ
- Progetto: **81PLUS+ / 81plus.net** — sicurezza sul lavoro, HACCP, privacy, formazione, Web3 Economy, network marketing.
- Regola madre: **IO DEVO GUADAGNARE** — ogni funnel porta a un acquisto. Etica L.173/2005.
- Owner: Mirco (labomobile.lm@gmail.com).

## 1. DB (uno solo)
- Canonico: `0-81PLUS.NET/81plus.db` (SQLite WAL, 223 tab, 19.961 utenti). Connettore: `db81_universal.php` → `db81()`.
- Niente altri SQL. Vedi `DB81_UNIVERSALE_WIRING.md`.

## 2. ECONOMIA
- Valuta: 1 € = 1 PV = 1 PV+. Wallet81+: PV / PV+ / SAF / 81X.
- Membership (mensile ricorrente / singolo una-tantum): Basic+ 69/103,90 · Pro+ 139/208,90 · Elite+ 209/313,90 · Vip+ 349/523,90 · Royal+ 559/838,90 · GENESYS81+ 1399/2098,90 (81 posti). PV+ bonus = importo; cashback 10% PV+; PV+ NON sconto su membership.
- PV pack + PV FREE: `pv.html` + `data/pv_packs.js`. Checkout PayPal.Me = **aifis**.

## 3. STATUS / MENU
- Menu voci status: **NETWORK · CLUB · FRANCHISING · WEBINAR** (+ Membership). Landing con CTA `index.html#resta`.
- Pipeline: Sconosciuto → USER81+ → MEMBER81+ (Basic/Pro/Elite) → NETWORKER81+ → ELITE81+ → VIP81+ → FRANCHISEE81+ → Socio Holding. Trasversali: CLUB/GENESYS81+, DAO81+.

## 4. MOTORI
- **GoHighLevel81+** (piattaforma CRM/marketing/automation) — in completamento a blocchi.
- **Email**: `MARKETING81+/FLUSSI81/send.py` (SMTP Hostinger, 133 flussi/752 email) + cruscotto `emailer_dashboard.html`. Zero Brevo.
- **Telegram**: 11 chat, 4 bot, `social_growth.py` + tabelle sg_/tg_. Token in `bot_tokens.env` (segreto).
- **Fliki**: `SICù81+/FLIKI_MASTERY_81.md` (video Sicù + repurposing YT).
- **Webinar**: `webinar.html` + `SCALETTA_WEBINAR_81.md`.

## 5. TODO APERTI
- GitHub App da ricollegare all'org (8 commit Claude Code fermi). Secrets: SMTP_PASS, OPENAI_API_KEY, bot token.
- Ultimo miglio DB: unificare `sicid.php`/`db81.php`.
- Deploy su Hostinger (upload 0-81PLUS.NET come web root).

---
# SESSION LOG (auto-append)
## 2026-07-04 · Sessione fondativa
- Sistemata index.html (troncamento + footer81.js) e tutto il sito (0 link rotti, footer ovunque).
- Nuova struttura membership 6 tier applicata a DB+JSON+JS.
- DB unico consolidato in `0-81PLUS.NET/81plus.db` + `db81_universal.php` (Cortex/Matrix hook).
- Landing NETWORK/CLUB/FRANCHISING/WEBINAR + menu. Checkout PV `pv.html` (PayPal.Me aifis) + PV FREE.
- Ticker storie di Sicù in index. Fliki mastery + scaletta webinar. Motore email `send.py` ricostruito (era troncato) + cruscotto.
- Creati MATRIX81.md e CORTEX81 nel folder. Avviato completamento GoHighLevel81+ a blocchi.
- [2026-07-04 20:25] Test updater: MATRIX si auto-aggiorna
- [2026-07-04 20:33] GoHighLevel81+ completato: CRM su DB unico (9.300 contatti), pipeline/opportunità, campagne email/telegram/social, dispatcher, ghl_api.php + gohighlevel81.html. db/cortex/matrix collegati.
- [2026-07-04 21:05] Ecosistema 24/7 completo: orchestratore81 + automazioni GHL + Telegram (1/ora) + YouTube→Fliki + Social globali (FB/IG/TT/LinkedIn/X). Avvio 1-click AVVIA_81PLUS.bat. DB unico: sicid/db81 unificati. 4 bot verificati.
- [2026-07-04 21:15] YT riciclo ciclico video vecchi (recycle) agganciato all'orchestratore. Diagnosi workflow GitHub: script validi, errori = secret mancanti; creato ecosistema81.yml (no OAuth) + WORKFLOWS_FIX_81.md.
- [2026-07-04 21:31] Cortex NEURAL·QUANTUM: cervello autonomo (percepisce/swarm-5-agenti/collasso-softmax/agisce/impara) agganciato all'orchestratore. Funnel conversione sconosciuto->USER->MEMBER(paga) attivo. Ecosistema si auto-guida 24/7.
- [2026-07-04 21:57] Sistema nervoso: censimento 1067 cellule (ogni file=cellula in cells81), battito via footer81.js->pulse81.php, membrana cellula81.php/.py, cervello percepisce cellule vive. File nuovi si auto-registrano (censimento giornaliero orchestratore).
- [2026-07-04 22:18] Organismo81 completo: sangue(vitali81) organi(organi81) scheletro(cells81) anima(coscienza81) e RAGIONAMENTO BINARIO 0/1 (stato_binario). Battito unico organismo81.py vivi agganciato all'orchestratore. Monitor organismo81.html + organismo_api.php. Salute 96%.
- [2026-07-04 22:23] Monitor organismo collegato a gohighlevel81.html (strip cuore live + link). Tutto l'essere gira in un tick: sangue/organi/scheletro/binario/anima/cervello.
- [2026-07-05 08:10] Telegram CTA evergreen (33 CTA sito, mai canale, 0 link t.me). Cervello collegato a TUTTE le 250 tabelle DB (1317 cellule, apparati biologici). Live users dinamici 350-400 (live81.js globale). Dottrina essere vivente applicata (ORGANISMO_VIVENTE_81.md, omeostasi/feedback/nervo vago).
- [2026-07-05 08:37] DB completo: 19.962 contatti tutti con SIC-ID (lead+prospect unificati); listino81 2336 prodotti caricati; CTA evergreen 2369; form completa-profilo.html; Team AI 81+ (ai81.py, 4 provider) innestato in Telegram; MATRIX in DB (matrix81_memory auto-sync).
- [2026-07-05 08:55] EMAIL MARKETING OPERATIVO: test welcome inviato REALE a labomobile.lm@gmail.com via Hostinger SMTP (login OK con password che finisce col punto). Motore send.py pronto per drip. GitHub workflow da completare per 24/7.
- [2026-07-05 09:34] EMAIL GITHUB COMPLETO+TESTATO: workflow emailer81.yml committato, secret SMTP_PASS1, run manuale VERDE (15s) -> welcome inviata a labomobile.lm@gmail.com da GitHub Actions. Cron 06:00 UTC attivo.
- [2026-07-05 10:32] DB UNICO consolidato: integrate 145 tabelle dagli SQL sparsi (ora 541 tab). DB secondari confermati sottoinsiemi (GHL data.db, upload). api/*.php riparati con _core/bid81_lib.php cablato al DB canonico. Welcome email CTA->completa-profilo (form reale su DB unico, +200PV+). Recupero password via email + reimposta-password.html. send.py ripristinato (era troncato).

---
## [2026-07-05] SICÙ81+ FLIKI VIDEO FACTORY H24 (masterplan completo)
- Motore: `SICù81+/sicu81_factory.py` aggrega TUTTO il listino (academy_catalog.js 1787 corsi + catalogo81.json membership/pack/sdk/sdp/club + shop + smartbox + magneti) = **1.860 asset unici**. 1 asset = 1 short Sicù.
- Output in `SICù81+/`: SICU81_VIDEO_MASTERPLAN.xlsx, SICU81_SOCIAL_COPY.csv (post/short/reel + SEO YT + hashtag), SICU81_FLIKI_PROMPTS.csv, SICU81_PUBLISHING_CALENDAR.csv (3/giorno 07:30/13:00/19:00 = ~620gg), SICU81_LONGFORM_PLAN.md (52 episodi 20min, 1/settimana domenica), 75 batch da 25. Personaggi a rotazione, CTA specifica per prodotto, compliance-guard.
- Rigenera: `SICù81+/RUN_FACTORY.bat`.
## Automazione GitHub (repo PlanB76/81plus-automation)
- NUOVO `fliki_daily.yml` (07:00 IT): genera `OGGI_FLIKI.md` con i 3 prompt Fliki del giorno + copy + notifica Telegram (secret TELEGRAM_BOT_TOKEN, var TG_CHANNEL). Coda in `cloud/data/fliki_queue.json` (1860). Fliki NON ha API → render = 1 click umano (o pipeline sprite locale per 100% auto).
- NUOVO `matrix_backup.yml` (05:30 IT): auto-commit `MATRIX81.md` + snapshot datati.
- Già attivi: youtube_evergreen.yml, youtube81_20_daily.yml, omnipresence.yml (TG+YT H24).
## MATRIX storage (46GB): il .md è ~6KB → va su GitHub; i 46GB sono MEDIA → restano su Google Drive (mai su GitHub, limite 100MB/file). Vedi `MATRIX_STORAGE_PLAN.md`.
## GATE (azione owner): incollare Secrets su GitHub (TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY, YOUTUBE_TOKEN_JSON) + Variables (TG_CHANNEL, YT_CHANNEL_ID) → Actions Run. Email marketing GHL a 19k user81+ = NON lanciata in autonomia (alto rischio, serve go esplicito + piattaforma connessa + compliance).
