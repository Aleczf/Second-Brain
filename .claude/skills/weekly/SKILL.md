---
name: weekly
description: Review settimanale del vault. Usala quando l'utente scrive "review settimanale" (o "weekly"). Smista l'inbox proponendo una destinazione per ogni nota (con conferma), segnala i progetti fermi da più di 14 giorni e i TODO scaduti, scrive journal/weekly/YYYY-Www.md.
---

# weekly — review settimanale

## Passi
1. `OGGI=$(TZ=Europe/Rome date +%F)`, `SETT=$(TZ=Europe/Rome date +%G-W%V)`.

2. **Smistamento inbox** (tutte le note in `inbox/` tranne `_index.md`).
   Per ognuna proponi **una** destinazione:
   | Contenuto | Destinazione |
   |---|---|
   | task di un progetto | riga `- [ ] …` in "Prossimo passo" di `projects/<slug>/stato.md`; nota eliminata |
   | appunto/idea di un progetto | `projects/<slug>/<slug-nota>.md` (`type: resource`) |
   | decisione | ADR con la skill `decision` |
   | concetto riutilizzabile | `resources/<slug>.md` |
   | cliente / persona / area | integrazione nella nota esistente; nota eliminata |
   | superata o inutile | eliminazione |
   Mostra una tabella numerata `# · nota · proposta · motivo` e **chiedi conferma**
   ("ok" per tutte, oppure correzioni per numero). Non spostare nulla prima della conferma.
   Dopo la conferma: sposta con `git mv` (o `mv` se non tracciata), aggiorna frontmatter
   (`type`, `tags`, `related`, `updated`), il nome file (senza timestamp) e i link che puntavano
   al vecchio percorso (`grep -rl "inbox/<nome>" --include=*.md .`).

3. **Progetti fermi**: per ogni `projects/*/stato.md` con `status: active`, ultima attività =
   la più recente tra `updated` e `git log -1 --format=%cs -- projects/<slug>/`.
   Oltre 14 giorni → segnala `progetto · giorni · prossimo passo`, e chiedi se metterlo in `paused`.

4. **TODO scaduti**: task aperti con scadenza passata, esclusi `templates/` e `private/`:
   `grep -rnE -- '- \[ \] .*📅 [0-9]{4}-[0-9]{2}-[0-9]{2}' --include=*.md --exclude-dir=templates --exclude-dir=private .`
   e tieni quelli con data < OGGI. Elenca `task · scadenza · nota`.
   Segnala a parte gli `stato.md` con "In una riga" ancora `TODO:`.

5. **Scrivi `journal/weekly/SETT.md`** dal template `templates/weekly.md` (title `Weekly SETT`):
   inbox smistata (cosa è andato dove), progetti fermi, TODO scaduti, link alle daily della settimana,
   "Com'è andata" e "Focus prossima settimana" solo da ciò che risulta dal vault o dice l'utente
   (altrimenti `TODO:`).

6. `python3 scripts/validate.py --fix-index` (verde) → `python3 scripts/build_index.py` →
   `git add -A && git commit -m "weekly: SETT"` (controlla che `private/` resti fuori).

## Risposta
Riepilogo breve: note smistate, progetti fermi, TODO scaduti, file della review, hash del commit.
