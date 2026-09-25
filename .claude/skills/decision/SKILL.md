---
name: decision
description: Registra una decisione come ADR. Usala quando l'utente scrive "decisione: …" (o "ho deciso di …", "registra decisione"). Guida a compilare contesto, opzioni, decisione, motivazione e conseguenze nella cartella decisioni/ del progetto giusto e aggiorna stato.md.
---

# decision — ADR guidata

## Passi
1. **Progetto**: deducilo dal testo (nome o slug in `projects/*/`). Se non è chiaro, chiedilo
   (elenca i progetti attivi). Una decisione non legata a un progetto va in un'area: chiedi conferma.
2. **Raccogli i campi dell'ADR** (template: `templates/decision.md`):
   Contesto · Opzioni considerate (almeno 2, con pro e contro) · Decisione · Motivazione · Conseguenze.
   - Pre-compila ciò che l'utente ha già detto e ciò che risulta da `stato.md` e dalle ADR precedenti.
   - Chiedi **in un solo messaggio** solo i campi mancanti, con una bozza da confermare o correggere.
   - Se l'utente dice "salta"/"non so", lascia `TODO:` in quel campo. Non inventare opzioni o motivi.
3. **Verifica le ADR esistenti** in `projects/<slug>/decisioni/`: se la nuova ne supera una,
   chiedi conferma; poi nella vecchia metti `status: archived`, aggiorna `updated` e aggiungi in cima
   al corpo `> Superata da [[projects/<slug>/decisioni/<nuova>]]`.
4. **Scrivi** `projects/<slug>/decisioni/YYYY-MM-DD-slug.md` (data locale:
   `TZ=Europe/Rome date +%F`; slug di 3-6 parole kebab-case). Frontmatter:
   `title` (la decisione in breve), `summary` (cosa + perché in 1-2 frasi), `type: decision`,
   `status: active`, `tags: [decisione]`, `related: ["[[projects/<slug>/stato]]", …]`,
   `date`, `project: "<slug>"`, `updated`.
5. **Aggiorna `projects/<slug>/stato.md`**:
   - in `## Decisioni recenti` inserisci in cima
     `- YYYY-MM-DD [[projects/<slug>/decisioni/<file>|<title>]] — <decisione in una riga>`;
     togli `_Nessuna decisione registrata._`; tieni al massimo 5 voci (le più vecchie restano
     raggiungibili dall'`_index` del progetto);
   - se le conseguenze cambiano "Prossimo passo" o "Blocchi", proponi la modifica e applicala se confermata;
   - `updated` = oggi.
6. `python3 scripts/validate.py --fix-index -q && python3 scripts/build_index.py`. Correggi gli errori.
   Non fare commit (lo fa `daily`), salvo richiesta esplicita.

## Risposta
Due righe: percorso dell'ADR creata e cosa è cambiato in `stato.md`.
