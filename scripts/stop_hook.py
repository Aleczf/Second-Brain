#!/usr/bin/env python3
"""Hook `Stop` di Claude Code: valida il vault a fine risposta.

- Nessuna nota .md modificata (git status) → esce 0 senza fare nulla.
- Vault valido → exit 0.
- Errori → li stampa su stderr ed esce 2: Claude li riceve e li corregge.
- Se lo stop è già stato bloccato una volta (`stop_hook_active`), non blocca di nuovo:
  segnala gli errori all'utente ed esce 0, così niente cicli infiniti.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if not any(line.rstrip().endswith(".md") for line in status.stdout.splitlines()):
        return 0

    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), "-q"],
                         cwd=ROOT, capture_output=True, text=True)
    if res.returncode == 0:
        return 0

    if payload.get("stop_hook_active"):
        print(json.dumps({"systemMessage": "validate.py ancora rosso dopo un tentativo di correzione:\n"
                                           + res.stdout.strip()}))
        return 0
    print("Il vault non è valido: correggi questi errori prima di chiudere "
          "(di solito basta `python3 scripts/build_index.py && python3 scripts/validate.py --fix-index`).\n"
          + res.stdout.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
