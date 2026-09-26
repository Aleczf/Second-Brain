#!/usr/bin/env python3
"""Genera gli indici derivati del vault.

- `llms.txt`: una riga per nota (percorso + summary), raggruppate per cartella.
- `HOME.md`: la tabella tra <!-- projects:start --> e <!-- projects:end -->, letta da
  projects/*/stato.md (status, `## In una riga`, updated).

Uso:
  python3 scripts/build_index.py           # scrive i file
  python3 scripts/build_index.py --check   # exit 1 se i file non sono aggiornati
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault as v  # noqa: E402

STATUS_ORDER = {"active": 0, "paused": 1, "done": 2, "archived": 3}
SECTION_TITLES = {
    "": "Radice",
    "inbox": "Inbox",
    "projects": "Progetti",
    "areas": "Aree",
    "clients": "Clienti",
    "people": "Persone",
    "resources": "Risorse",
    "journal": "Journal",
    "scripts": "Script",
}


def build_llms(notes: list[v.Note]) -> str:
    groups: dict[str, list[v.Note]] = {}
    for n in notes:
        top = n.path.parts[0] if len(n.path.parts) > 1 else ""
        groups.setdefault(top, []).append(n)
    order = list(SECTION_TITLES) + sorted(set(groups) - set(SECTION_TITLES))
    out = [
        "# Second Brain",
        "",
        "> Vault Obsidian di un freelance (AI automation, sviluppo, consulenza per PMI italiane).",
        "> Una riga per nota: percorso e summary. Parti da HOME.md, poi projects/<slug>/stato.md.",
        "> Il contenuto di private/ è escluso.",
    ]
    for top in order:
        if top not in groups:
            continue
        out += ["", f"## {SECTION_TITLES.get(top, top)}", ""]
        for n in sorted(groups[top], key=lambda n: n.path.as_posix()):
            summary = " ".join(str(n.get("summary") or "").split()) or "TODO: summary"
            out.append(f"- {n.path.as_posix()}: {summary}")
    return "\n".join(out) + "\n"


def cell(s: str) -> str:
    return s.replace("|", "\\|").strip()


def project_rows(notes: list[v.Note]) -> str:
    rows = []
    for n in notes:
        p = n.path.parts
        if len(p) != 3 or p[0] != "projects" or p[2] != "stato.md":
            continue
        name = re.sub(r"\s+—\s+stato$", "", str(n.get("title") or p[1]))
        line = v.first_line(v.section(n.body, "In una riga"))
        if not line or line.startswith("TODO"):
            line = "TODO"
        status = str(n.get("status") or "?")
        updated = str(n.get("updated") or "")
        rows.append((STATUS_ORDER.get(status, 9), _neg(updated), name.lower(),
                     f"| [[{n.key}\\|{cell(name)}]] | {status} | {cell(line)} | {updated} |"))
    header = "| Progetto | Status | In una riga | Aggiornato |\n|---|---|---|---|"
    body = "\n".join(r[-1] for r in sorted(rows)) or "| _nessun progetto_ | | | |"
    return f"{header}\n{body}"


def _neg(date: str) -> str:
    """Chiave per ordinare le date dalla più recente (stringhe della stessa lunghezza)."""
    return "".join(str(9 - int(c)) if c.isdigit() else c for c in date)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="non scrive: exit 1 se llms.txt o HOME.md vanno rigenerati")
    ap.add_argument("--root", type=Path, default=v.ROOT, help="radice del vault")
    args = ap.parse_args()
    root = args.root.resolve()
    notes = v.load_notes(root)

    targets: dict[Path, str] = {root / "llms.txt": build_llms(notes)}
    home = root / v.HOME
    if home.exists():
        old = home.read_text(encoding="utf-8")
        new = v.replace_block(old, v.PROJECTS_START, v.PROJECTS_END, project_rows(notes))
        if new != old:
            new = v.set_updated(new, dt.date.today().isoformat())
        targets[home] = new

    stale = []
    for path, content in targets.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        stale.append(path.relative_to(root))
        if not args.check:
            path.write_text(content, encoding="utf-8")

    if args.check:
        for p in stale:
            print(f"da rigenerare: {p}")
        return 1 if stale else 0
    for p in stale:
        print(f"aggiornato {p}")
    if not stale:
        print("✓ indici già aggiornati")
    return 0


if __name__ == "__main__":
    sys.exit(main())
