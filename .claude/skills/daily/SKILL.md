---
name: daily
description: Chiusura di giornata. Usala quando l'utente scrive "fine giornata" (o "chiudi la giornata", "daily"). Riassume cosa è cambiato nel vault oggi via git, aggiorna gli stato.md toccati, scrive journal/daily/YYYY-MM-DD.md, lancia validate e build_index e fa il commit.
---

# daily — fine giornata

## Passi
1. `OGGI=$(TZ=Europe/Rome date +%F)`.
2. **Cosa è cambiato oggi** (`private/` è fuori da Git e resta fuori dal riepilogo):
   - commit di oggi: `git log --since="$OGGI 00:00" --name-status --format='%h %s'`
   - non committato: `git status --porcelain` e `git diff HEAD` (i file nuovi leggili direttamente).
   Ignora i file generati (`llms.txt`, blocchi `index` e `projects` di HOME e degli `_index`).
   Nessuna modifica → rispondi "Nessuna modifica oggi, niente da chiudere." e fermati.
3. **Raggruppa** per progetto (`projects/<slug>/`), area, cliente, persona, inbox, risorse.
4. **Aggiorna gli `stato.md`** dei progetti toccati, solo sulla base di quello che mostrano le modifiche:
   - task completati → spuntali (`- [x]`) in "Prossimo passo";
   - nuove decisioni già in `decisioni/` ma non in "Decisioni recenti" → aggiungile;
   - "Stato attuale" / "In una riga": aggiornale solo se le modifiche lo rendono evidente;
     nel dubbio chiedi una riga all'utente invece di inventare;
   - `updated: OGGI`.
5. **Scrivi `journal/daily/OGGI.md`** dal template `templates/daily.md` (se esiste già, integrala):
   - `## Cosa è cambiato`: 3-8 punti concreti, con wikilink a percorso completo alle note toccate;
   - `## Progetti toccati`: un punto per progetto;
   - `## Decisioni prese`: ADR create oggi (o "Nessuna");
   - `## Da fare domani`: task aperti dai "Prossimo passo" dei progetti toccati + todo catturati oggi,
     come **elenco semplice senza checkbox** con link alla nota sorgente (i task vivono solo lì,
     così la weekly non li conta due volte);
   - `related`: gli `stato.md` dei progetti toccati.
6. `python3 scripts/validate.py --fix-index` → deve essere verde (correggi gli errori, non aggirarli),
   poi `python3 scripts/build_index.py`.
7. **Commit**: `git add -A && git commit -m "daily: OGGI — <sintesi in max 8 parole>"`.
   Controlla prima con `git status` che non ci sia nulla sotto `private/` o `.env`.
   Push solo se l'utente lo ha chiesto o se è la prassi concordata per questo vault.

## Risposta
Massimo 5 righe: progetti toccati, stati aggiornati, file del journal, hash del commit.
