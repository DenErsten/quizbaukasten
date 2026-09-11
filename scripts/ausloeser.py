#!/usr/bin/env python3
"""
Auslöser fuer unscharfe Anforderungen — Teil 2 von #34.

Liest den Strom aus mithoeren.py und entscheidet, wann ein Hinweis faellig
ist. Er urteilt nicht ueber Ideen und sagt nie "das halte ich fuer falsch".
Er stellt fest, dass eine Anforderung unscharf ist, und schlaegt die Frage
vor, die sie schaerft.

DER SCHWERSTE TEIL IST DAS SCHWEIGEN
------------------------------------
Zwanzig Hinweise pro Meeting sind so nutzlos wie keiner — nach dem zweiten
Mal klappt man das Fenster zu. Deshalb sind die Muster eng gefasst, und
deshalb gibt es `abstand`: Wer ueber dasselbe Thema redet, loest den
gleichen Hinweis nicht dreimal aus.

WARUM DER SCOPE AUS DER DATEI KOMMT
-----------------------------------
Was nicht zum Produkt gehoert, steht in docs/plan.md und aendert sich. Ein
Muster im Code waere am Tag nach der ersten Planaenderung falsch, ohne dass
es jemand merkt. Also wird die Liste gelesen, nicht eingebaut.

AUFRUF
------
    python scripts/mithoeren.py | python scripts/ausloeser.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator

WURZEL = Path(__file__).resolve().parent.parent

# Woerter, die eine Groesse behaupten, ohne eine zu nennen. Absichtlich kurz:
# Jedes zusaetzliche Wort erzeugt Hinweise, und jeder Hinweis zu viel kostet
# Aufmerksamkeit, die im Gespraech gebraucht wird.
MENGENWOERTER = {
    "schnell": "Schnell im Vergleich wozu?",
    "langsam": "Langsam im Vergleich wozu?",
    "viele": "Wie viele genau?",
    "wenige": "Wie wenige genau?",
    "zuverlässig": "Woran würdest du merken, dass es unzuverlässig ist?",
    "stabil": "Woran würdest du merken, dass es nicht stabil ist?",
    "einfach": "Einfach für wen, und gemessen woran?",
    "bald": "Bis wann genau?",
    "demnächst": "Bis wann genau?",
}

# Zusagen ohne Termin. Hier zaehlt die Formulierung, nicht das Thema.
ZUSAGEN = (
    "machen wir noch",
    "kümmere mich",
    "kuemmere mich",
    "schaue ich mir an",
    "bis zum nächsten mal",
    "bis zum naechsten mal",
    "melde mich",
)

# Eine Zahl im Satz entschaerft ein Mengenwort: "schnell, also unter zwei
# Sekunden" ist keine unscharfe Anforderung mehr.
ZAHL = re.compile(r"\d")

FUELLWOERTER = {
    "das", "die", "der", "den", "dem", "des", "ein", "eine", "einen", "einem",
    "und", "oder", "aber", "dann", "noch", "auch", "mal", "so", "wie", "was",
    "ist", "sind", "wird", "werden", "haben", "hat", "kann", "können", "soll",
    "sollen", "muss", "müssen", "wir", "ich", "du", "es", "sie", "man", "auf",
    "in", "mit", "für", "von", "zu", "über", "ihre", "ihren", "eigenen",
}


def _woerter(satz: str) -> set[str]:
    return {w for w in re.findall(r"[a-zäöüß]+", satz.lower()) if w not in FUELLWOERTER}


def ausserhalb_des_scopes(plan: str) -> list[str]:
    """Die Punkte aus 'Was nicht dazugehört' in docs/plan.md."""
    im_abschnitt = False
    punkte: list[str] = []
    for zeile in plan.splitlines():
        if zeile.startswith("## "):
            im_abschnitt = "nicht dazugehört" in zeile.lower()
            continue
        if im_abschnitt and zeile.strip().startswith("- "):
            punkte.append(zeile.strip()[2:])
    return punkte


def _hinweis(zeit: float, text: str, art: str, grund: str, frage: str) -> dict:
    return {"zeit": round(zeit, 2), "zitat": text, "art": art, "grund": grund, "frage": frage}


def pruefe(zeit: float, text: str, ausserhalb: Iterable[str]) -> dict | None:
    """Ein Satz, hoechstens ein Hinweis. Der erste Treffer gewinnt."""
    klein = text.lower()

    for punkt in ausserhalb:
        gemeinsam = _woerter(punkt) & _woerter(text)
        if len(gemeinsam) >= 2:
            return _hinweis(
                zeit, text, "ausserhalb",
                f"Steht in docs/plan.md unter „Was nicht dazugehört“: {punkt}",
                "Gehört das wirklich dazu, oder ändern wir den Plan?",
            )

    for wort, frage in MENGENWOERTER.items():
        if re.search(rf"\b{wort}\b", klein) and not ZAHL.search(text):
            return _hinweis(zeit, text, "mengenwort", f"Mengenwort ohne Zahl: „{wort}“", frage)

    for wendung in ZUSAGEN:
        if wendung in klein and not ZAHL.search(text):
            return _hinweis(
                zeit, text, "zusage", f"Zusage ohne Termin: „{wendung}“",
                "Bis wann genau?",
            )

    return None


def hinweise(
    zeilen: Iterable[dict],
    ausserhalb: Iterable[str],
    abstand: float = 60.0,
) -> Iterator[dict]:
    """
    Macht aus dem Strom Hinweise — und laesst die meisten davon weg.

    Ein Hinweis derselben Art wird innerhalb von `abstand` Sekunden nur
    einmal ausgegeben. Wer ueber ein Thema redet, sagt "schnell" dreimal;
    dreimal dieselbe Rueckfrage waere Rauschen und nichts sonst.
    """
    ausserhalb = list(ausserhalb)
    zuletzt: dict[str, float] = {}

    for zeile in zeilen:
        zeit = float(zeile.get("zeit", 0.0))
        text = str(zeile.get("text", ""))
        treffer = pruefe(zeit, text, ausserhalb)
        if treffer is None:
            continue
        art = treffer["art"]
        if art in zuletzt and zeit - zuletzt[art] < abstand:
            continue
        zuletzt[art] = zeit
        yield treffer


def main() -> int:
    plan = (WURZEL / "docs" / "plan.md").read_text(encoding="utf-8")
    zeilen = (json.loads(z) for z in sys.stdin if z.strip())
    for hinweis in hinweise(zeilen, ausserhalb_des_scopes(plan)):
        print(json.dumps(hinweis, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
