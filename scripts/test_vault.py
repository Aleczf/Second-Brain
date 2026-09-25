#!/usr/bin/env python3
"""Test di validate.py e build_index.py su una copia temporanea del vault.

Uso: python3 scripts/test_vault.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import vault as v  # noqa: E402
import validate  # noqa: E402

FM = """---
title: "{title}"
summary: "Nota di test."
type: {type}
status: active
tags: [test]
related: []
updated: 2026-09-25
---
"""


class VaultTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", "private", "__pycache__"))
        (self.tmp / "private").mkdir()
        (self.tmp / "private" / "contratto-segreto.md").write_text("riservato\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, rel: str, body: str = "", type_: str = "resource", title: str = "Test") -> Path:
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(FM.format(title=title, type=type_) + body, encoding="utf-8")
        return p

    def errors(self) -> list[str]:
        return validate.validate(self.tmp)[0]

    def assertError(self, fragment: str):
        errs = self.errors()
        self.assertTrue(any(fragment in e for e in errs), f"atteso '{fragment}' in {errs}")

    def fix(self):
        validate.fix_indexes(self.tmp, "2026-09-25")

    # --- casi validi -----------------------------------------------------------
    def test_vault_reale_valido(self):
        self.assertEqual(self.errors(), [])

    def test_nota_nuova_diventa_valida_dopo_fix_index(self):
        self.write("resources/prompt-engineering.md")
        self.assertError("orfana")
        self.fix()
        self.assertEqual(self.errors(), [])
        self.assertIn("[[resources/prompt-engineering|Test]]", (self.tmp / "resources/_index.md").read_text())

    def test_adr_nell_index_del_progetto_dalla_piu_recente(self):
        self.write("projects/sofia/decisioni/2026-01-10-vecchia.md", type_="decision", title="Vecchia")
        self.write("projects/sofia/decisioni/2026-03-01-nuova.md", type_="decision", title="Nuova")
        self.fix()
        self.assertEqual(self.errors(), [])
        idx = (self.tmp / "projects/sofia/_index.md").read_text()
        self.assertIn("**decisioni/**", idx)
        self.assertLess(idx.index("Nuova"), idx.index("Vecchia"))

    def test_fix_index_idempotente(self):
        self.write("resources/a.md")
        self.fix()
        before = {p: p.read_text() for p in self.tmp.rglob("_index.md")}
        self.fix()
        self.assertEqual(before, {p: p.read_text() for p in self.tmp.rglob("_index.md")})

    def test_fix_index_svuota_indice_senza_note(self):
        p = self.write("inbox/2026-09-25-1200-idea.md", type_="inbox")
        self.fix()
        p.unlink()
        self.assertError("wikilink rotto")
        self.fix()
        self.assertEqual(self.errors(), [])
        self.assertIn("_Nessuna nota._", (self.tmp / "inbox/_index.md").read_text())

    def test_frontmatter_a_blocchi_stile_obsidian(self):
        p = self.tmp / "resources/blocchi.md"
        p.write_text('---\ntitle: Blocchi\nsummary: "x"\ntype: resource\nstatus: active\n'
                     'tags:\n  - a\n  - b\nrelated:\n  - "[[HOME]]"\nupdated: 2026-09-25\n---\n')
        self.fix()
        self.assertEqual(self.errors(), [])

    def test_link_nel_codice_ignorati(self):
        self.write("resources/codice.md", "```\n[[non-esiste]]\n```\n`[[neanche]]`\n<!-- [[commento]] -->\n")
        self.fix()
        self.assertEqual(self.errors(), [])

    # --- errori ----------------------------------------------------------------
    def test_frontmatter_mancante(self):
        (self.tmp / "resources/nuda.md").write_text("# niente frontmatter\n")
        self.assertError("frontmatter mancante")

    def test_campo_mancante_e_valori_non_ammessi(self):
        p = self.write("resources/x.md")
        p.write_text(p.read_text().replace("status: active\n", "").replace("type: resource", "type: boh")
                     .replace("updated: 2026-09-25", "updated: 25/09/2026"))
        errs = " ".join(self.errors())
        for frag in ("campi mancanti: status", "type 'boh'", "updated '25/09/2026'"):
            self.assertIn(frag, errs)

    def test_link_rotto(self):
        self.write("resources/x.md", "[[resources/non-esiste]]")
        self.assertError("wikilink rotto: [[resources/non-esiste]]")

    def test_related_rotto(self):
        p = self.write("resources/x.md")
        p.write_text(p.read_text().replace("related: []", 'related: ["[[people/nessuno]]"]'))
        self.assertError("wikilink rotto: [[people/nessuno]]")

    def test_link_ambiguo(self):
        self.write("resources/x.md", "[[stato]]")
        self.assertError("ambiguo")

    def test_link_verso_private(self):
        self.write("resources/a.md", "[[private/contratto-segreto]]")
        self.write("resources/b.md", "[[contratto-segreto]]")  # risolto per nome
        self.write("resources/c.md", "[x](../private/contratto-segreto.md)")
        errs = [e for e in self.errors() if "private/" in e]
        self.assertEqual(len(errs), 3, errs)

    def test_orfana_in_progetto(self):
        self.write("projects/sofia/note-varie.md")
        self.assertError("non linkata da projects/sofia/_index.md")

    # --- build_index -----------------------------------------------------------
    def test_build_index_home_e_llms(self):
        stato = self.tmp / "projects/sofia/stato.md"
        stato.write_text(stato.read_text().replace(
            "TODO: stato attuale in una frase (compare in HOME.md).", "In pilota | 3 clienti"))
        run = lambda *a: subprocess.run([sys.executable, str(HERE / "build_index.py"), "--root", str(self.tmp), *a],
                                        capture_output=True, text=True)
        self.assertEqual(run("--check").returncode, 1)
        self.assertEqual(run().returncode, 0)
        self.assertEqual(run("--check").returncode, 0)
        home = (self.tmp / "HOME.md").read_text()
        self.assertIn("| [[projects/sofia/stato\\|Sofia]] | active | In pilota \\| 3 clienti |", home)
        llms = (self.tmp / "llms.txt").read_text()
        self.assertIn("- projects/sofia/stato.md: ", llms)
        self.assertNotIn("private", llms.split("\n", 5)[-1])
        self.assertEqual(self.errors(), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
