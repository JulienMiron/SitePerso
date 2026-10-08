#!/usr/bin/env python3
"""Met à jour les liens de index.html à partir des fichiers présents dans le dépôt.

Chaque lien à mettre à jour automatiquement porte un attribut data-glob :

    <a data-glob="Documents/Guide enseignant/*.pdf" href="...">

Chaque document a son dossier (Documents/<nom>/) où l'on garde toutes les
versions. Le script cherche les fichiers qui correspondent au motif et
remplace le href par le plus récent (date du dernier commit Git, puis date de
modification, puis nom). Si un seul fichier correspond, c'est lui. Si aucun ne
correspond, le lien existant est laissé tel quel et un avertissement est
affiché.

Usage : python3 scripts/maj_liens.py            (modifie index.html)
        python3 scripts/maj_liens.py --dry-run  (affiche seulement les changements)
"""
import fnmatch
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parent.parent / "apps" / "PartageDMS"
INDEX = ROOT / "index.html"
LIEN = re.compile(r'(<a data-glob=")([^"]+)(" href=")([^"]*)(")')


def nfc(s):
    return unicodedata.normalize("NFC", s)


def date_git(fichier):
    r = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", str(fichier.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True,
    )
    # fichier pas encore commité : on utilise sa date de modification
    return int(r.stdout.strip() or fichier.stat().st_mtime)


def meilleur(motif):
    candidats = [
        f for f in ROOT.rglob("*")
        if f.is_file()
        and not any(p.startswith(".") for p in f.relative_to(ROOT).parts)
        and fnmatch.fnmatchcase(nfc(f.relative_to(ROOT).as_posix()), nfc(motif))
    ]
    if not candidats:
        return None
    return max(candidats, key=lambda f: (date_git(f), f.stat().st_mtime, nfc(f.name)))


def main():
    dry = "--dry-run" in sys.argv
    html = INDEX.read_text(encoding="utf-8")
    changements = []

    def remplacer(m):
        motif, ancien = m.group(2), m.group(4)
        f = meilleur(motif)
        if f is None:
            print(f"AVERTISSEMENT : aucun fichier ne correspond à « {motif} » (lien conservé : {unquote(ancien)})")
            return m.group(0)
        rel = nfc(f.relative_to(ROOT).as_posix())
        nouveau = quote(rel, safe="/")
        if nfc(unquote(ancien)) != rel:
            changements.append((unquote(ancien), rel))
        return m.group(1) + motif + m.group(3) + nouveau + m.group(5)

    nouveau_html = LIEN.sub(remplacer, html)
    for ancien, nouveau in changements:
        print(f"{ancien}  ->  {nouveau}")
    if not changements:
        print("Aucun changement.")
    elif not dry:
        INDEX.write_text(nouveau_html, encoding="utf-8")


if __name__ == "__main__":
    main()
