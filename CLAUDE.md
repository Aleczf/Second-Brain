---
title: "CLAUDE — istruzioni del vault"
summary: "Regole operative per Claude Code e per me: scopo, cartelle, convenzioni, flusso di lettura, comandi. Leggila a inizio sessione."
type: index
status: active
tags: [meta]
related: ["[[HOME]]"]
updated: 2026-09-25
---
# Second brain — istruzioni

Vault Obsidian personale e professionale di un freelance (AI automation, sviluppo, consulenza per PMI italiane).
Serve a: (1) riprendere il contesto di un progetto in 30 secondi, (2) tracciare decisioni e motivazioni,
(3) catturare idee e task senza attrito.

## Cartelle
| Cartella | Contenuto |
|---|---|
| `inbox/` | cattura rapida, da smistare nella review settimanale |
| `projects/<slug>/` | `_index.md`, `stato.md`, `decisioni/` (ADR), note libere |
| `areas/` | responsabilità continue; una nota per area, cartella solo oltre 3 note collegate |
| `clients/` | una nota per cliente |
| `people/` | una nota per persona |
| `resources/` | concetti, appunti tecnici, riferimenti riutilizzabili |
| `journal/daily/`, `journal/weekly/` | `YYYY-MM-DD.md`, `YYYY-Www.md` |
| `templates/` | template Obsidian (plugin core Templates); esclusi dalla validazione |
| `scripts/` | `validate.py`, `build_index.py` (Python, solo standard library) |
| `private/` | materiale sensibile dei clienti — **escluso da Git** |

## Flusso di lettura
1. `HOME.md` → quali progetti esistono e il loro stato in una riga.
2. `projects/<slug>/stato.md` → obiettivo, prossimo passo, blocchi.
3. `projects/<slug>/decisioni/` → le ADR più recenti (i nomi iniziano per data).
4. Solo se serve: altre note del progetto, cliente, persone collegate (`related`).
Per cercare senza aprire file: `llms.txt` (percorso + summary di ogni nota).

## Convenzioni
- **Nomi file**: kebab-case, senza accenti. ADR: `decisioni/YYYY-MM-DD-slug.md`. Inbox: `YYYY-MM-DD-HHMM-slug.md`.
- **Lingua**: note in italiano; citazioni e fonti in lingua originale.
- **Link**: wikilink con percorso completo dalla root, senza `.md`: `[[projects/sofia/stato|Sofia]]`.
  Nelle tabelle il pipe va escapato: `[[projects/sofia/stato\|Sofia]]`.
- **Frontmatter** obbligatorio in ogni nota (tranne `templates/`):
  ```yaml
  ---
  title: "..."
  summary: "1-2 frasi: cosa contiene e quando leggerla"
  type: project|decision|client|person|resource|area|journal|inbox|index
  status: active|paused|done|archived
  tags: []
  related: ["[[percorso/nota]]"]
  updated: YYYY-MM-DD
  ---
  ```
  Campi extra ammessi: `repo` (in `stato.md`), `date` e `project` (nelle ADR).
- **`updated`**: aggiornalo a ogni modifica sostanziale della nota.
- **Indici**: ogni nota è linkata dall'`_index.md` più vicino risalendo le cartelle
  (le ADR stanno nell'`_index` del progetto). Il contenuto tra `<!-- index:start -->` e
  `<!-- index:end -->` è generato: non modificarlo a mano.
- **HOME**: la tabella tra `<!-- projects:start -->` e `<!-- projects:end -->` è generata da
  `build_index.py` leggendo `status`, `updated` e la sezione `## In una riga` di ogni `stato.md`.
- **Placeholder vs task**: `TODO:` = contenuto mancante da scrivere.
  Task = `- [ ] testo` con scadenza facoltativa `📅 YYYY-MM-DD`.
- **Status ADR**: `active` = in vigore, `archived` = superata (indicare quale ADR la sostituisce).

## Regole
- **MAI copiare contenuto di `private/` in altre note**, né linkarlo da note versionate.
  Al massimo scrivi "dettagli in private/" senza link e senza riportarne il contenuto.
- Non inventare fatti su progetti, clienti o persone: se un dato manca, lascia `TODO:` o chiedi.
- Una nota nuova va sempre aggiunta al suo `_index` (o rigenera con `--fix-index`).
- Prima di ogni commit: `validate.py` deve essere verde.
- Decisioni architetturali sul vault: esponi opzioni con pro e contro prima di procedere.

## Comandi
Script (dalla root del vault):
- `python3 scripts/validate.py` — frontmatter, link rotti, orfane, link verso `private/`.
- `python3 scripts/validate.py --fix-index` — rigenera gli `_index` dai `summary`.
- `python3 scripts/build_index.py` — rigenera `llms.txt` e la tabella progetti di `HOME.md` (`--check`: solo verifica).
- `python3 scripts/test_vault.py` — test degli script (dopo ogni modifica a `scripts/`).
Sequenza standard dopo aver scritto note: `validate.py --fix-index` → `build_index.py` → commit.

Skill (`.claude/skills/`):
- `capture` — "annota …", "idea: …", "todo: …" → nota in `inbox/`, senza domande.
- `resume` — "riprendi <progetto>" → briefing di massimo 8 righe con il prossimo passo.
- `decision` — "decisione: …" → ADR guidata nel progetto giusto + aggiornamento di `stato.md`.
- `daily` — "fine giornata" → riepilogo da git diff, aggiorna gli stati, journal, validate, commit.
- `weekly` — "review settimanale" → smistamento inbox, progetti fermi da più di 14 giorni, TODO scaduti.
