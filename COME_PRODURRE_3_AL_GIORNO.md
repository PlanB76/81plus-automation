# ▶️ SICÙ81+ — Come produrre 3 short al giorno (H24)

## Ogni giorno, in automatico (GitHub)
1. Il workflow **`fliki_daily.yml`** (07:00 IT) genera **`OGGI_FLIKI.md`** con i 3 prompt del giorno + titoli, descrizioni SEO, hashtag e copy per TG/IG/TikTok.
2. Se hai messo i Secret, ti arriva la notifica su **Telegram** con i 3 titoli.

## Cosa fai tu (10 min)
1. Apri `OGGI_FLIKI.md`.
2. Per ognuno dei 3: **copia il PROMPT FLIKI** → incolla in Fliki (formato 9:16, sottotitoli ON, voce IT) → **Render** → scarica il .mp4.
3. Carica su YouTube Short/TikTok/IG con **titolo + descrizione + hashtag** già pronti nello stesso file.

## Perché non 100% automatico su Fliki
Fliki **non espone un'API pubblica** per generare video in batch: nessun tool esterno (né GitHub) può cliccare "Render" al posto tuo. Quindi l'automazione consegna i prompt pronti; il render è 1 click tuo.
**Alternativa 100% auto:** rendere gli short con la pipeline sprite locale (già usata per gli .mp4 SICÙ) → in quel caso pubblica anche il video da solo. Dillo e la attivo.

## Video lungo 20 min (1/settimana)
Vedi `SICù81+/SICU81_LONGFORM_PLAN.md`: 52 episodi, ognuno con prompt Fliki a capitoli. Domenica.
