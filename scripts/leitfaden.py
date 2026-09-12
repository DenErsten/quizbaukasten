#!/usr/bin/env python3
"""
Liest den Gesprächsleitfaden aus `docs/leitfaden.md`.

Warum ein Parser und keine Liste im Code: Der Leitfaden wird gelesen, bevor er
benutzt wird — von einem Menschen, im Gespräch. Läge er zusätzlich als Liste im
JavaScript, gäbe es zwei Leitfäden, und der gedruckte wäre irgendwann der
falsche. Dasselbe Argument wie bei der Scope-Liste in `ausloeser.py`, die aus
`docs/plan.md` kommt statt aus einer Konstante.

Aufruf zum Prüfen:

    python3 scripts/leitfaden.py
"""

from __future__ import annotations

import json
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
LEITFADENDATEI = WURZEL / "docs" / "leitfaden.md"

ABSCHNITT = "die fünf fragen"
FELDER = {
    "frage:": "frage",
    "füllt:": "fuellt",
    "achtung:": "achtung",
    # Steuern das gefuehrte Gespraech (#114): woran der Rechner erkennt, dass
    # eine Antwort traegt, und der eine Satz, der kommt, wenn sie es nicht tut.
    "prüfung:": "pruefung",
    "rückfrage:": "rueckfrage",
}


def punkte(text: str) -> list[dict]:
    """
    Die Punkte aus dem Abschnitt „Die fünf Fragen".

    Ein Punkt beginnt mit `### `, seine Felder stehen als `Frage:`, `Füllt:`
    und `Achtung:` darunter. Mehrzeilige Felder werden zusammengezogen —
    im Markdown darf umgebrochen werden, in der Anzeige steht ein Satz.
    """
    ergebnis: list[dict] = []
    im_abschnitt = False
    feld: str | None = None

    for zeile in text.splitlines():
        blank = zeile.strip()

        if blank.startswith("## "):
            im_abschnitt = ABSCHNITT in blank[3:].strip().lower()
            feld = None
            continue
        if not im_abschnitt:
            continue

        if blank.startswith("### "):
            ergebnis.append({
                "titel": blank[4:].strip(),
                "frage": "", "fuellt": "", "achtung": "",
                "pruefung": "", "rueckfrage": "",
            })
            feld = None
            continue
        if not ergebnis:
            continue

        schluessel = next((k for k in FELDER if blank.lower().startswith(k)), None)
        if schluessel:
            feld = FELDER[schluessel]
            ergebnis[-1][feld] = blank[len(schluessel):].strip()
            continue

        # Leerzeile beendet das Feld; Folgezeilen gehoeren noch dazu.
        if not blank:
            feld = None
        elif feld:
            ergebnis[-1][feld] = f"{ergebnis[-1][feld]} {blank}".strip()

    # Ein Punkt ohne Frage waere in der Anzeige eine leere Zeile, die niemand
    # stellen kann. Lieber gar nicht zeigen als stumm halb zeigen.
    return [p for p in ergebnis if p["frage"]]


def lesen(pfad: Path = LEITFADENDATEI) -> list[dict]:
    """Fehlt die Datei, ist das ein Fehler und kein leerer Leitfaden."""
    if not pfad.exists():
        raise FileNotFoundError(f"Leitfaden fehlt: {pfad}")
    gefunden = punkte(pfad.read_text(encoding="utf-8"))
    if not gefunden:
        raise ValueError(f"Kein Punkt in {pfad} gefunden — Abschnitt „Die fünf Fragen“ leer?")
    return gefunden


if __name__ == "__main__":
    print(json.dumps(lesen(), ensure_ascii=False, indent=2))
