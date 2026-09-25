---
name: resume
description: Briefing per riprendere un progetto. Usala quando l'utente scrive "riprendi <progetto>" (o "dove eravamo con <progetto>", "briefing <progetto>"). Legge stato.md, le ultime 3 decisioni e le note recenti e restituisce al massimo 8 righe con il prossimo passo.
---

# resume — riprendi un progetto in 30 secondi

Sola lettura: **non modificare nessun file.**

## Passi
1. **Trova il progetto**: confronta il nome dato con le cartelle `projects/*/` e i `title` dei loro
   `_index.md` (ignora maiuscole, accenti, spazi/trattini; accetta abbreviazioni univoche, es.
   "fatture" → `controllo-costi-fatture-passive`). Se ambiguo o assente, elenca i candidati e chiedi
   quale: è l'unica domanda ammessa.
2. **Leggi** `projects/<slug>/stato.md` per intero.
3. **Decisioni**: `ls projects/<slug>/decisioni/*.md | sort -r | head -3` e leggi le tre ADR
   (per quelle in `status: archived` basta sapere che sono superate).
4. **Note recenti** (escluse `stato.md`, `_index.md` e le ADR già lette), max 3:
   - modifiche non committate: `git status --porcelain -- projects/<slug>/`
   - ultimi 14 giorni: `git log --since="14 days ago" --name-only --format= -- projects/<slug>/ | sort -u`
   Leggi il `summary`; apri il corpo solo se serve a capire il prossimo passo.
5. Se `related` punta a clienti o persone, leggi solo il loro `summary`. Mai aprire `private/`.

## Briefing (massimo 8 righe, in italiano)
```
**<Progetto>** — <status> · aggiornato <updated> (<N> giorni fa)
Obiettivo: …
Stato: …
Decisioni recenti: <data> <titolo>; …   (oppure "nessuna")
Novità: <note recenti in una riga>        (ometti se non ce ne sono)
Blocchi: …                                (ometti se nessuno)
**Prossimo passo:** <il primo task aperto in "Prossimo passo", o il più urgente>
```
- Usa solo quello che c'è nel vault. Non inventare, non riempire i buchi.
- Se `stato.md` è ancora quasi tutto `TODO:`, dillo in una riga e il prossimo passo diventa
  "compilare stato.md (obiettivo, stato, prossimo passo)".
- Se l'ultimo aggiornamento è di più di 14 giorni fa, segnalalo nella prima riga.
