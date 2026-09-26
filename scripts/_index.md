---
title: "Script"
summary: "Script Python (solo standard library) per validare il vault e generare gli indici."
type: index
status: active
tags: [indice]
related: ["[[HOME]]"]
updated: 2026-09-25
---
# Script

Python 3.9+, solo standard library. Si lanciano dalla root del vault.

| Script | Cosa fa |
|---|---|
| `validate.py` | Errori: frontmatter incompleto, wikilink rotti o ambigui, note orfane, link verso `private/`. Avvisi: link per solo nome, nomi non kebab-case. Exit 1 se ci sono errori. |
| `validate.py --fix-index` | Rigenera il blocco `index:start/end` di ogni `_index.md` da titoli e `summary`, poi valida. |
| `build_index.py` | Rigenera `llms.txt` e la tabella progetti di `HOME.md`. |
| `build_index.py --check` | Non scrive; exit 1 se `llms.txt` o `HOME.md` non sono aggiornati. |
| `test_vault.py` | Test degli script su una copia temporanea del vault. |
| `vault.py` | Modulo condiviso: parser del frontmatter, risoluzione dei link, regole sugli indici. |

<!-- index:start -->
_Nessuna nota._
<!-- index:end -->
