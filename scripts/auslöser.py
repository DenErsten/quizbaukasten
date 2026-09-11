#!/usr/bin/env python3
"""
Auslöser fuer unscharfe Anforderungen — liest den Strom aus #35 (Teil 1) und
entscheidet, wann ein Hinweis faellig ist.

Vier eng gefasste Muster, sonst nichts:

    1. Mengenwort ohne Zahl   — "schnell", "viele", "zuverlaessig", "bald"
    2. Zusage ohne Termin     — "das machen wir noch", "bis zum naechsten Mal"
    3. Widerspruch zu docs/plan.md, Abschnitt "Was nicht dazugehoert"
    4. Widerspruch zu docs/pilotnutzer.md

WARUM NUR VIER MUSTER
----------------------
Zwanzig Hinweise pro Meeting sind so nutzlos wie keiner. Der Auslöser
bewertet keine Ideen und sagt nie "das halte ich fuer falsch" — er stellt
fest, dass eine Formulierung unscharf ist, und schlaegt die Frage vor, die
sie schaerft. Alles, was mehr Urteil braucht als das, gehoert nicht hierher.

WARUM DEDUPLIKATION
--------------------
Ohne sie wiederholt sich derselbe Hinweis, solange ueber dasselbe Thema
geredet wird — und das ist genau die Art Rauschen, die dazu fuehrt, dass
man das Fenster zuklappt. Ein Hinweis gilt deshalb als "schon gesagt", bis
ein andersartiger Hinweis dazwischenkommt; erst dann darf er erneut fallen.

AUFRUF
------
    python scripts/mithoeren.py --datei sitzung.wav | python "scripts/auslöser.py"
"""

from __future__ import annotations

import json
import re
import sys
from typing import Iterable, Iterator, TypedDict


class Satz(TypedDict):
    zeit: float
    text: str


class Hinweis(TypedDict):
    zeit: float
    text: str
    muster: str
    grund: str
    frage: str


ZAHL = re.compile(r"\d")

MENGENWOERTER: dict[str, re.Pattern[str]] = {
    "schnell": re.compile(r"\bschnell\w*\b", re.IGNORECASE),
    "viele": re.compile(r"\bviele?\b", re.IGNORECASE),
    "zuverlässig": re.compile(r"\bzuverlässig\w*\b", re.IGNORECASE),
    "bald": re.compile(r"\bbald\b", re.IGNORECASE),
}

ZUSAGEN: list[re.Pattern[str]] = [
    re.compile(r"\bdas\s+machen\s+wir\s+noch\b", re.IGNORECASE),
    re.compile(r"\bbis\s+zum\s+n(ä|ae)chsten\s+mal\b", re.IGNORECASE),
    re.compile(r"\bmachen\s+wir\s+sp(ä|ae)ter\b", re.IGNORECASE),
]

WOCHENTAGE_UND_MONATE = (
    r"montags?|dienstags?|mittwochs?|donnerstags?|freitags?|samstags?|sonntags?"
    r"|januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember"
)
TERMIN = re.compile(rf"\d|{WOCHENTAGE_UND_MONATE}", re.IGNORECASE)

# Reihenfolge des Plans: docs/plan.md, Abschnitt "Was nicht dazugehört".
PLAN_AUSSCHLUESSE: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bantworten\b.*\bhandys?\b|\bhandys?\b.*\bantworten\b", re.IGNORECASE),
        "Teams antworten über ihre eigenen Handys (Live-Multiplayer)",
    ),
    (
        re.compile(r"\bbenutzerkont(en|o)\b|\banmeldung\b|\blogin\b", re.IGNORECASE),
        "Benutzerkonten und Anmeldung",
    ),
    (
        re.compile(r"\bfragen-?datenbank\b|\bfragenkatalog\b|\bki-generierte\s+fragen\b", re.IGNORECASE),
        "Fragen-Datenbank, Import fertiger Fragenkataloge, KI-generierte Fragen",
    ),
    (
        re.compile(r"\bbuzzer\b|\bzeitdruck\b", re.IGNORECASE),
        "Buzzer, Zeitdruck, Musik- oder Videofragen",
    ),
    (
        re.compile(r"\bmehrere\s+quizmaster\b", re.IGNORECASE),
        "Mehrere Quizmaster gleichzeitig am selben Quiz",
    ),
]

# Konkrete, bekannte Tatsachen aus docs/pilotnutzer.md — kein Raum fuer neue
# Annahmen ueber Marek, nur ein Abgleich mit dem, was dort schon steht.
PILOTNUTZER_WIDERSPRUECHE: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(internet|wlan|netz|online)\b.*\bquizabend\b"
            r"|\bquizabend\b.*\b(internet|wlan|netz|online)\b"
            r"|\bbraucht\s+(dann\s+)?(internet|wlan|netz)\b",
            re.IGNORECASE,
        ),
        "Ein Quizabend lässt sich nicht wiederholen — Marek fürchtet einen Ausfall mehr als Vorarbeit",
    ),
    (
        re.compile(r"\bfürs?\s+handy\s+bauen\b|\bals\s+handy-?app\b", re.IGNORECASE),
        "Marek baut seine Quizze bisher am Laptop und liest sie vom Laptop ab",
    ),
]


def mengenwort_ohne_zahl(satz: Satz) -> Hinweis | None:
    text = satz["text"]
    if ZAHL.search(text):
        return None
    for wort, muster in MENGENWOERTER.items():
        treffer = muster.search(text)
        if treffer:
            return Hinweis(
                zeit=satz["zeit"],
                text=text,
                muster="mengenwort",
                grund=wort,
                frage=f"{treffer.group().capitalize()} im Vergleich wozu?",
            )
    return None


def zusage_ohne_termin(satz: Satz) -> Hinweis | None:
    text = satz["text"]
    if TERMIN.search(text):
        return None
    for muster in ZUSAGEN:
        treffer = muster.search(text)
        if treffer:
            return Hinweis(
                zeit=satz["zeit"],
                text=text,
                muster="zusage",
                grund=treffer.group().lower(),
                frage="Bis wann genau?",
            )
    return None


def widerspruch_plan(satz: Satz) -> Hinweis | None:
    text = satz["text"]
    for muster, punkt in PLAN_AUSSCHLUESSE:
        if muster.search(text):
            return Hinweis(
                zeit=satz["zeit"],
                text=text,
                muster="plan",
                grund=punkt,
                frage=f'Das steht in docs/plan.md unter "Was nicht dazugehört": {punkt}. '
                f"Bewusste Planänderung?",
            )
    return None


def widerspruch_pilotnutzer(satz: Satz) -> Hinweis | None:
    text = satz["text"]
    for muster, tatsache in PILOTNUTZER_WIDERSPRUECHE:
        if muster.search(text):
            return Hinweis(
                zeit=satz["zeit"],
                text=text,
                muster="pilotnutzer",
                grund=tatsache,
                frage=f"Das widerspricht docs/pilotnutzer.md: {tatsache}. Ist das Absicht?",
            )
    return None


ERKENNER = (mengenwort_ohne_zahl, zusage_ohne_termin, widerspruch_plan, widerspruch_pilotnutzer)


def ausloeser(strom: Iterable[Satz]) -> Iterator[Hinweis]:
    """
    Macht aus dem Mitschrift-Strom einen Strom von Hinweisen.

    Ein Hinweis mit demselben Muster und Grund wie der zuletzt gemeldete wird
    unterdrückt — sonst haemmert der Auslöser mit derselben Frage, solange
    ueber dasselbe Thema geredet wird. Kommt zwischendurch ein andersartiger
    Hinweis, darf das alte Thema danach wieder melden.
    """
    zuletzt: tuple[str, str] | None = None
    for satz in strom:
        for erkennen in ERKENNER:
            hinweis = erkennen(satz)
            if hinweis is None:
                continue
            schluessel = (hinweis["muster"], hinweis["grund"])
            if schluessel != zuletzt:
                zuletzt = schluessel
                yield hinweis
            break


def main() -> int:
    zeilen = (json.loads(zeile) for zeile in sys.stdin if zeile.strip())
    for hinweis in ausloeser(zeilen):
        print(json.dumps(hinweis, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
