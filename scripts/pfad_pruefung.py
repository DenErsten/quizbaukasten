#!/usr/bin/env python3
"""
Prüft, ob ein Pull Request geschützte Pfade anfasst — und wenn ja, ob ein
Mensch ihn freigegeben hat.

Das ist der Wächter über den Selbstumbau. Die KI entscheidet über Code; sie
entscheidet nicht über die Regeln, nach denen sie über Code entscheidet.

Aufruf in der Action:

    gh pr diff "$NR" --name-only > geaendert.txt
    gh pr view "$NR" --json reviews,files > pr.json
    python3 scripts/pfad_pruefung.py --geaendert geaendert.txt --pr pr.json

Rückgabewerte:
    0  frei zum Mergen
    1  geschützte Pfade betroffen, keine menschliche Freigabe
    2  Aufrufproblem (fehlende Datei, kaputtes JSON)

Lokal testen ohne GitHub:

    python3 scripts/pfad_pruefung.py --dateien CLAUDE.md src/app.ts
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from fnmatch import fnmatch
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
MUSTERDATEI = WURZEL / ".github" / "geschuetzte-pfade.txt"
MENSCHENDATEI = WURZEL / "scripts" / "menschen.txt"


def zeilen(pfad: Path) -> list[str]:
    if not pfad.exists():
        print(f"::error::Datei fehlt: {pfad}", file=sys.stderr)
        sys.exit(2)
    ergebnis = []
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#", 1)[0].strip()
        if zeile:
            ergebnis.append(zeile)
    return ergebnis


def passt(datei: str, muster: str) -> bool:
    """Glob-Vergleich wie in .gitignore: ** greift über Verzeichnisgrenzen."""
    if fnmatch(datei, muster):
        return True
    if muster.endswith("/**") and datei.startswith(muster[:-2]):
        return True
    # Ein Muster ohne Pfadtrenner soll auch tief im Baum greifen,
    # damit z. B. package.json in einem Unterprojekt erfasst wird.
    if "/" not in muster and fnmatch(os.path.basename(datei), muster):
        return True
    return False


def treffer(dateien: list[str], muster: list[str]) -> list[tuple[str, str]]:
    gefunden = []
    for d in dateien:
        for m in muster:
            if passt(d, m):
                gefunden.append((d, m))
                break
    return gefunden


def nur_neue_zeilen(pr: dict, datei: str) -> bool:
    """
    True, wenn an dieser Datei ausschließlich hinzugefügt wurde.

    Neue Tests darf der Agent frei schreiben — das ist erwünscht. Nur das
    Ändern oder Löschen bestehender Tests braucht einen Menschen, weil genau
    dort das Netz gelockert wird, in das der Agent selbst fällt.
    """
    for f in pr.get("files", []):
        if f.get("path") == datei:
            return f.get("deletions", 0) == 0 and f.get("additions", 0) > 0
    return False


def menschliche_freigaben(pr: dict, menschen: list[str]) -> list[str]:
    """Letzter Review-Stand je Person; nur APPROVED von echten Nutzerkonten."""
    stand: dict[str, str] = {}
    for r in pr.get("reviews", []):
        autor = (r.get("author") or {}).get("login")
        if not autor:
            continue
        zustand = r.get("state", "")
        if zustand in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            stand[autor] = zustand
    return [a for a, z in stand.items() if z == "APPROVED" and a in menschen]


def main() -> int:
    zerleger = argparse.ArgumentParser()
    zerleger.add_argument("--geaendert", help="Datei mit geänderten Pfaden, einer pro Zeile")
    zerleger.add_argument("--pr", help="JSON aus: gh pr view --json reviews,files")
    zerleger.add_argument("--dateien", nargs="*", default=[], help="Pfade direkt (zum Testen)")
    a = zerleger.parse_args()

    muster = zeilen(MUSTERDATEI)
    menschen = zeilen(MENSCHENDATEI)

    if a.geaendert:
        dateien = [z.strip() for z in Path(a.geaendert).read_text(encoding="utf-8").splitlines() if z.strip()]
    else:
        dateien = list(a.dateien)

    pr: dict = {}
    if a.pr:
        try:
            pr = json.loads(Path(a.pr).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as fehler:
            print(f"::error::PR-JSON nicht lesbar: {fehler}", file=sys.stderr)
            return 2

    gefunden = treffer(dateien, muster)

    # Reine Ergänzungen an Testdateien durchlassen.
    durchgelassen = []
    if pr.get("files"):
        rest = []
        for datei, m in gefunden:
            if m.startswith(("tests/", "test/", "**/*_test", "**/*.test", "**/*.spec")) \
                    and nur_neue_zeilen(pr, datei):
                durchgelassen.append(datei)
            else:
                rest.append((datei, m))
        gefunden = rest

    print(f"Geänderte Dateien: {len(dateien)}")
    for d in durchgelassen:
        print(f"  durchgelassen (nur ergänzt): {d}")

    if not gefunden:
        print("Keine geschützten Pfade betroffen. Die KI darf hier allein entscheiden.")
        return 0

    print()
    print("Geschützte Pfade betroffen:")
    for datei, m in gefunden:
        print(f"  {datei}   (Muster: {m})")

    freigaben = menschliche_freigaben(pr, menschen)
    print()
    if freigaben:
        print(f"Menschliche Freigabe liegt vor: {', '.join(freigaben)}")
        print("Merge frei.")
        return 0

    print("Keine menschliche Freigabe. Merge blockiert.")
    print(f"Zählende Freigeber: {', '.join(menschen) or '(niemand eingetragen!)'}")
    print()
    print("Das ist kein Fehler im Ablauf, sondern der Ablauf: Dieser PR ändert")
    print("die Regeln, nach denen die KI entscheidet. Das entscheidet ein Mensch.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
