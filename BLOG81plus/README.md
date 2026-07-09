# BLOG81+ / PACK81+ — Macchina contenuti & offerte automatiche

Sistema unico che vive dentro `0-81PLUS.NET` (così l'upload prende tutto):

- **PACK81+**: crea offerte a 3 tier (**SCUDO / CORAZZA / FORTEZZA**) pescando dal **listino ufficiale**
  (`data/catalog_data.js`, 1760 voci reali). Prezzi tagliati, % sconto, posti, FOMO, decoy sul tier centrale,
  bonus PV+, link **PayPal.me/aifis**. Genera **landing** (AIDA/EPPPA/REPPPA + PNL/neuro), **blocco per la index**
  (countdown), **pagina "scaduta"** con waitlist. Pack **oneshot** e **ricorrenti**.
- **Ciclo 90 giorni**: i pack si creano una volta e lo scheduler li **riapre e ri-promuove ogni 3 mesi**
  (nuova deadline, posti azzerati, social+email). Scala valori sempre piena.
- **BLOG81+**: **1 articolo al giorno** su temi 81+ (Sicurezza Lavoro, HACCP, Privacy, Gare Appalto, Crescita,
  Formazione, Economia, SICURIX). Notizie **reali via RSS** (INAIL, ANSA lavoro, Google News per tema),
  scritte con LLM (copy/PNL/neuro, funnel TOFU-MOFU-BOFU) e **CTA obbligo-paura vs soluzione 81+**,
  con link a Listino81+, PACK81+, YouTube @sicurissimo, Telegram, social.

## Cosa produce (dentro 0-81PLUS.NET)
- `blog81.html` — indice blog (a menu: voce **BLOG**) con hero, blocco promo, griglia articoli
- `blog/<data>-<slug>.html` — pagine articolo
- `promo/<slug>.html` + `promo/<slug>-scaduta.html` — landing e pagina scaduta
- `promo/index.html` — vetrina offerte (voce menu **OFFERTE**)
- `promo/_promo_block.html` — blocco iniettato nella `index.html` sul marker `<!--PACK81_PROMO-->`
- `BLOG81plus/data/*_registry.json` — stato campagne e articoli

## Uso locale
```
cd BLOG81plus
python engine\scheduler.py            # genera tutto (senza pubblicare)
python engine\scheduler.py --send     # genera E pubblica su Telegram/canali
```
Windows: doppio clic `AVVIA_BLOG81.bat` (poi fondibile in `AVVIA_81_GLOBALE.bat`).

## Automazione GitHub
Workflow `.github/workflows/blog81.yml` — cron giornaliero 06:00 UTC. Secrets in repo → Settings → Secrets:
- `ANTHROPIC_API_KEY` **o** `OPENAI_API_KEY` (per articoli scritti dall'AI; senza chiave usa template)
- `TG_BOT_TOKEN`, `TG_CHANNEL` (Telegram — già attivi)
- opzionali: `FB_TOKEN`, `IG_TOKEN`, `EMAIL_PROVIDER_KEY`, `EMAIL_LIST_ID`
GitHub Pages: Settings → Pages → branch `main` (le pagine sono già alla root del sito).

## Config unica
`BLOG81plus/config/blog81_config.json` — tier e sconti, ciclo 90gg, temi, feed RSS per tema,
mapping tema→categorie listino, link canali, provider LLM, marker index.

## Note
- Legge SEMPRE il listino reale in `data/catalog_data.js` (fallback seed se assente).
- Marker già inserito nella `index.html`: `<!--PACK81_PROMO-->…<!--/PACK81_PROMO-->`.
- Voci menu **BLOG** e **OFFERTE** già aggiunte all'array `MI[]` della index.
