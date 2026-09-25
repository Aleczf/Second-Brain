"""Funzioni condivise da validate.py e build_index.py (solo standard library).

Il frontmatter è un sottoinsieme di YAML: scalari (anche tra virgolette),
liste inline `[a, "b"]` e liste a blocchi `- item`, come le scrive Obsidian.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Cartelle non considerate note del vault.
EXCLUDED_DIRS = {".git", ".obsidian", ".trash", ".claude", "templates", "private", "node_modules"}
PRIVATE_DIR = "private"
INDEX_NAME = "_index.md"
HOME = "HOME.md"
ROOT_NOTES = {"HOME.md", "CLAUDE.md"}  # note radice, non richiedono un _index

REQUIRED = ["title", "summary", "type", "status", "tags", "related", "updated"]
TYPES = {"project", "decision", "client", "person", "resource", "area", "journal", "inbox", "index"}
STATUSES = {"active", "paused", "done", "archived"}

INDEX_START, INDEX_END = "<!-- index:start -->", "<!-- index:end -->"
PROJECTS_START, PROJECTS_END = "<!-- projects:start -->", "<!-- projects:end -->"

FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
WIKILINK_RE = re.compile(r"(!?)\[\[([^\]\n]+?)\]\]")
MDLINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[^\n]*$", re.S | re.M)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


class FrontmatterError(ValueError):
    pass


def _scalar(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def _inline_list(raw: str) -> list[str]:
    inner = raw.strip()[1:-1]
    items, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
    if quote:
        raise FrontmatterError(f"virgolette non chiuse in lista: {raw}")
    items.append(buf)
    return [_scalar(i) for i in items if i.strip()]


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Restituisce (frontmatter, corpo). frontmatter è None se assente."""
    m = FM_RE.match(text)
    if not m:
        return None, text
    data: dict = {}
    current_list: str | None = None
    for n, line in enumerate(m.group(1).splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if current_list and re.match(r"^\s*-\s", line):
            data[current_list].append(_scalar(line.split("-", 1)[1]))
            continue
        km = re.match(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$", line)
        if not km:
            raise FrontmatterError(f"riga {n} non valida: {line!r}")
        key, raw = km.group(1), (km.group(2) or "").strip()
        if key in data:
            raise FrontmatterError(f"chiave duplicata: {key}")
        current_list = None
        if raw == "":
            data[key] = []  # lista a blocchi (o valore vuoto)
            current_list = key
        elif raw.startswith("["):
            if not raw.endswith("]"):
                raise FrontmatterError(f"lista inline non chiusa: {key}")
            data[key] = _inline_list(raw)
        else:
            data[key] = _scalar(raw)
    return data, text[m.end():]


def strip_code(body: str) -> str:
    """Rimuove blocchi di codice, codice inline e commenti HTML (link lì dentro non contano)."""
    body = FENCE_RE.sub("", body)
    body = COMMENT_RE.sub("", body)
    return INLINE_CODE_RE.sub("", body)


def split_link(raw: str) -> str:
    """`path#heading|alias` → `path` (gestisce il pipe escapato nelle tabelle)."""
    target = raw.replace("\\|", "|").split("|", 1)[0]
    target = target.split("#", 1)[0].split("^", 1)[0]
    return target.strip().rstrip("\\")


def wikilinks(text: str) -> list[tuple[bool, str]]:
    """Lista di (embed, target) dai wikilink del testo, codice escluso."""
    return [(bool(m.group(1)), split_link(m.group(2))) for m in WIKILINK_RE.finditer(strip_code(text))]


def mdlinks(text: str) -> list[str]:
    return [m.group(1) for m in MDLINK_RE.finditer(strip_code(text))]


@dataclass
class Note:
    path: Path  # relativo alla root
    fm: dict | None
    body: str
    text: str
    fm_error: str | None = None
    links: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.path.with_suffix("").as_posix()

    @property
    def is_index(self) -> bool:
        return self.path.name == INDEX_NAME

    def get(self, k, default=""):
        return (self.fm or {}).get(k, default)


def is_excluded(rel: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in rel.parts[:-1])


def load_notes(root: Path = ROOT) -> list[Note]:
    notes = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if is_excluded(rel):
            continue
        text = p.read_text(encoding="utf-8")
        try:
            fm, body = parse_frontmatter(text)
            err = None
        except FrontmatterError as e:
            fm, body, err = None, text, str(e)
        notes.append(Note(rel, fm, body, text, err))
    return notes


class Resolver:
    """Risolve i target dei wikilink come Obsidian: percorso completo, poi nome file univoco."""

    def __init__(self, root: Path = ROOT):
        self.by_path: dict[str, Path] = {}
        self.by_name: dict[str, list[Path]] = {}
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(root)
            if rel.parts[0] in {".git", ".obsidian", ".trash"}:
                continue
            keys = {rel.as_posix().lower()}
            if p.suffix == ".md":
                keys.add(rel.with_suffix("").as_posix().lower())
            for k in keys:
                self.by_path[k] = rel
            for k in {p.name.lower(), p.stem.lower() if p.suffix == ".md" else p.name.lower()}:
                self.by_name.setdefault(k, []).append(rel)

    def resolve(self, target: str) -> tuple[Path | None, str]:
        """Restituisce (percorso, esito) con esito in {'path', 'name', 'ambiguous', 'missing'}."""
        t = target.strip().lstrip("/").lower()
        if t in self.by_path:
            return self.by_path[t], "path"
        if "/" not in t:
            hits = self.by_name.get(t, [])
            if len(hits) == 1:
                return hits[0], "name"
            if len(hits) > 1:
                return None, "ambiguous"
        return None, "missing"


def is_private(rel: Path | str) -> bool:
    s = rel.as_posix() if isinstance(rel, Path) else rel
    return s.lstrip("./").lower().split("/", 1)[0] == PRIVATE_DIR


def parent_index(note: Note, existing: set[str]) -> str:
    """Nota (senza .md) che deve linkare `note`: l'_index più vicino risalendo, altrimenti HOME."""
    folder = note.path.parent
    if note.is_index:
        folder = folder.parent
        if note.path.parent == Path("."):
            return "HOME"
    while True:
        cand = (folder / INDEX_NAME).as_posix().lstrip("./")
        if cand in existing:
            return cand[:-3]
        if folder == Path("."):
            return "HOME"
        folder = folder.parent


def replace_block(text: str, start: str, end: str, content: str) -> str:
    """Sostituisce il contenuto tra i marker; se mancano, li aggiunge in fondo."""
    block = f"{start}\n{content}\n{end}"
    if start in text and end in text:
        pre, rest = text.split(start, 1)
        _, post = rest.split(end, 1)
        return pre + block + post
    return text.rstrip() + "\n\n" + block + "\n"


def set_updated(text: str, date: str) -> str:
    return re.sub(r"(?m)^updated:.*$", f"updated: {date}", text, count=1)


def section(body: str, heading: str) -> str:
    """Testo sotto `## heading` fino al prossimo heading di livello <= 2."""
    m = re.search(rf"(?m)^##\s+{re.escape(heading)}\s*$", body)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"(?m)^#{1,2}\s", rest)
    return rest[: nxt.start()] if nxt else rest


def first_line(text: str) -> str:
    for line in COMMENT_RE.sub("", text).splitlines():
        line = line.strip()
        if line:
            return line
    return ""
