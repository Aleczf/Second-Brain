#!/usr/bin/env python3
"""Valida il vault.

Errori (exit 1): frontmatter mancante o incompleto, wikilink rotti o ambigui,
note orfane (non linkate dal loro _index), link da note versionate verso private/.
Avvisi (exit 0): link per solo nome file invece che per percorso, nomi file non kebab-case.

Uso:
  python3 scripts/validate.py               # valida
  python3 scripts/validate.py --fix-index   # rigenera gli _index dai summary, poi valida
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault as v  # noqa: E402

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NAME_RE = re.compile(r"^(_index|HOME|CLAUDE|README|\d{4}-W\d{2}|[a-z0-9]+(-[a-z0-9]+)*)$")
DATED_RE = re.compile(r"^\d{4}-")


def check_frontmatter(n: v.Note, errors: list[str]) -> None:
    if n.fm_error:
        errors.append(f"{n.path}: frontmatter non valido ({n.fm_error})")
        return
    if n.fm is None:
        errors.append(f"{n.path}: frontmatter mancante")
        return
    missing = [k for k in v.REQUIRED if k not in n.fm]
    if missing:
        errors.append(f"{n.path}: campi mancanti: {', '.join(missing)}")
    for k in ("title", "summary", "type", "status", "updated"):
        if k in n.fm and (not isinstance(n.fm[k], str) or not n.fm[k].strip()):
            errors.append(f"{n.path}: '{k}' vuoto")
    for k in ("tags", "related"):
        if k in n.fm and not isinstance(n.fm[k], list):
            errors.append(f"{n.path}: '{k}' deve essere una lista")
    t, s, u = n.get("type"), n.get("status"), n.get("updated")
    if t and t not in v.TYPES:
        errors.append(f"{n.path}: type '{t}' non ammesso ({'|'.join(sorted(v.TYPES))})")
    if s and s not in v.STATUSES:
        errors.append(f"{n.path}: status '{s}' non ammesso ({'|'.join(sorted(v.STATUSES))})")
    if isinstance(u, str) and u:
        try:
            if not DATE_RE.match(u):
                raise ValueError
            dt.date.fromisoformat(u)
        except ValueError:
            errors.append(f"{n.path}: updated '{u}' non è una data YYYY-MM-DD")
    for r in n.get("related", []) if isinstance(n.get("related"), list) else []:
        if not re.fullmatch(r"\[\[[^\]]+\]\]", r.strip()):
            errors.append(f"{n.path}: related contiene '{r}', atteso un wikilink \"[[percorso]]\"")


def check_links(n: v.Note, res: v.Resolver, errors: list[str], warnings: list[str]) -> set[str]:
    """Controlla i link della nota; restituisce le chiavi delle note linkate."""
    targets: list[str] = []
    related = n.get("related", [])
    for r in related if isinstance(related, list) else []:
        targets += [t for _, t in v.wikilinks(r)]
    targets += [t for _, t in v.wikilinks(n.body)]
    linked: set[str] = set()
    for t in targets:
        if not t:
            continue  # [[#heading]]: link interno alla nota
        if v.is_private(t):
            errors.append(f"{n.path}: link verso private/ vietato ([[{t}]])")
            continue
        path, how = res.resolve(t)
        if path is None:
            what = "ambiguo, usa il percorso completo" if how == "ambiguous" else "rotto"
            errors.append(f"{n.path}: wikilink {what}: [[{t}]]")
            continue
        if v.is_private(path):
            errors.append(f"{n.path}: link verso private/ vietato ([[{t}]] → {path})")
            continue
        if how == "name":
            warnings.append(f"{n.path}: [[{t}]] risolto per nome, meglio [[{path.with_suffix('').as_posix()}]]")
        linked.add(path.with_suffix("").as_posix() if path.suffix == ".md" else path.as_posix())
    for url in v.mdlinks(n.body):
        if "://" in url or url.startswith("mailto:"):
            continue
        target = (n.path.parent / url.split("#", 1)[0]).as_posix()
        if v.is_private(url) or v.is_private(Path(target.lstrip("./"))) or "private/" in url:
            errors.append(f"{n.path}: link markdown verso private/ vietato ({url})")
    return linked


def check_names(n: v.Note, warnings: list[str]) -> None:
    for part in [*n.path.parts[:-1], n.path.stem]:
        if not NAME_RE.match(part):
            warnings.append(f"{n.path}: '{part}' non è kebab-case")
            break


def children_of(notes: list[v.Note]) -> dict[str, list[v.Note]]:
    existing = {n.path.as_posix() for n in notes if n.is_index}
    kids: dict[str, list[v.Note]] = defaultdict(list)
    for n in notes:
        if n.path.as_posix() in v.ROOT_NOTES:
            continue
        kids[v.parent_index(n, existing)].append(n)
    return kids


def validate(root: Path) -> tuple[list[str], list[str]]:
    notes = v.load_notes(root)
    res = v.Resolver(root)
    errors: list[str] = []
    warnings: list[str] = []
    outlinks: dict[str, set[str]] = {}
    for n in notes:
        check_frontmatter(n, errors)
        check_names(n, warnings)
        outlinks[n.key] = check_links(n, res, errors, warnings)
    for parent, kids in children_of(notes).items():
        have = outlinks.get(parent, set())
        for k in kids:
            if k.key not in have:
                errors.append(f"{k.path}: orfana, non linkata da {parent}.md")
    return errors, warnings


def ordered_groups(kids: list[v.Note], base: Path) -> list[tuple[str, list[v.Note]]]:
    """Prima i sotto-indici, poi le note della cartella, poi una sezione per sottocartella.
    In ogni gruppo: note senza data in ordine alfabetico, poi quelle datate dalla più recente."""
    groups: dict[tuple[int, str], list[v.Note]] = defaultdict(list)
    for k in kids:
        sub = "" if k.is_index else k.path.parent.relative_to(base).as_posix()
        groups[(0 if k.is_index else 1, "" if sub == "." else sub)].append(k)
    out = []
    for (_, sub), items in sorted(groups.items()):
        undated = sorted((k for k in items if not DATED_RE.match(k.path.stem)), key=lambda k: k.key)
        dated = sorted((k for k in items if DATED_RE.match(k.path.stem)), key=lambda k: k.key, reverse=True)
        out.append((sub, undated + dated))
    return out


def entry(n: v.Note) -> str:
    title = re.sub(r"[\[\]|]", "", n.get("title") or n.path.stem)
    summary = " ".join(str(n.get("summary") or "TODO: summary").split())
    return f"- [[{n.key}|{title}]] — {summary}"


def fix_indexes(root: Path, today: str) -> list[Path]:
    notes = v.load_notes(root)
    children = children_of(notes)
    changed = []
    # Tutti gli _index, anche quelli rimasti senza note (es. inbox appena svuotata).
    # HOME è escluso: le sue sezioni sono scritte a mano e da build_index.py.
    for parent in sorted(n.key for n in notes if n.is_index):
        kids = children.get(parent, [])
        base = Path(parent).parent
        lines: list[str] = []
        for sub, items in ordered_groups(kids, base):
            if sub:
                lines += ["", f"**{sub}/**"]
            lines += [entry(k) for k in items]
        content = "\n".join(lines).strip() or "_Nessuna nota._"
        path = root / f"{parent}.md"
        old = path.read_text(encoding="utf-8")
        new = v.replace_block(old, v.INDEX_START, v.INDEX_END, content)
        if new != old:
            path.write_text(v.set_updated(new, today), encoding="utf-8")
            changed.append(path.relative_to(root))
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix-index", action="store_true", help="rigenera gli _index dai summary")
    ap.add_argument("--root", type=Path, default=v.ROOT, help="radice del vault (default: cartella padre di scripts/)")
    ap.add_argument("-q", "--quiet", action="store_true", help="non mostrare gli avvisi")
    args = ap.parse_args()
    root = args.root.resolve()

    if args.fix_index:
        for p in fix_indexes(root, dt.date.today().isoformat()):
            print(f"aggiornato {p}")

    errors, warnings = validate(root)
    if warnings and not args.quiet:
        print(f"{len(warnings)} avvisi:")
        for w in warnings:
            print(f"  ! {w}")
    if errors:
        print(f"{len(errors)} errori:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"✓ vault valido ({len(v.load_notes(root))} note)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
