---
name: capture
description: Cattura rapida nel vault. Usala quando l'utente scrive "annota …", "idea: …", "todo: …" (o "nota: …", "ricordami …"). Crea subito una nota in inbox/ con timestamp, senza fare domande.
---

# capture — cattura rapida in inbox/

Obiettivo: zero attrito. **Non fare domande**, non chiedere conferme, non smistare: lo farà `weekly`.

## Passi
1. Ora locale: `TZ=Europe/Rome date '+%Y-%m-%d %H%M'` → `DATA`, `HHMM`.
2. Tipo dal trigger: `idea:` → `idea`; `todo:`/`ricordami` → `todo`; `annota`/`nota:` → `nota`.
3. Slug: 3-6 parole chiave del testo, kebab-case, senza accenti né articoli.
   File: `inbox/DATA-HHMM-slug.md` (se esiste già, aggiungi `-2`).
4. Scrivi la nota:
   ```markdown
   ---
   title: "<frase breve, max 60 caratteri>"
   summary: "<tipo> catturata il DATA: <sintesi in una frase>. Da smistare."
   type: inbox
   status: active
   tags: [<tipo>]
   related: []
   updated: DATA
   ---
   # <title>

   <testo dell'utente, fedele, senza abbellirlo né aggiungere fatti>
   ```
   - `todo`: il corpo è `- [ ] <testo>`. Se l'utente indica una scadenza ("venerdì", "entro il 3"),
     convertila in data assoluta: `- [ ] <testo> 📅 YYYY-MM-DD`.
   - Se il testo nomina esplicitamente un progetto, un cliente o una persona che esiste nel vault
     (cerca in `projects/*/`, `clients/`, `people/`), aggiungilo a `related` con percorso completo,
     es. `"[[projects/sofia/stato]]"`, e il tag slug del progetto. Nessuna corrispondenza certa → `related: []`.
   - Password, token, IBAN o dati riservati di clienti: **non** scriverli nella nota; salva il resto e
     avvisa in una riga che vanno messi in `private/`.
5. `python3 scripts/build_index.py && python3 scripts/validate.py --fix-index -q` (aggiunge la nota a `inbox/_index.md` e a `llms.txt`).
   Se fallisce per colpa della nuova nota, correggila.
6. Non fare commit (lo fa `daily`).

## Risposta
Una sola riga: `Annotato → inbox/<file>` (+ eventuale avviso su dati sensibili).
