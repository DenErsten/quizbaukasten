#!/usr/bin/env python3
"""
Die naechste Frage aus dem Gesagten (#125).

WARUM NICHT LOKAL
-----------------
Am 2026-09-13 sagte Firat "Ich moechte ein Spiel entwickeln." Die naechste
Frage war trotzdem "Woran merkst du, dass es fertig ist?" — eine abstrakte
Frage an jemanden, der gerade vier Woerter gesagt hat. Darauf antwortet man
"weiss nicht", und zwar zu Recht. Vier von fuenf Punkten blieben offen.

Ein tieferer Fragebaum haette dasselbe getan, nur mit mehr Fragen: Er kennt
den Inhalt nicht. "Was fuer ein Spiel?" kann nur jemand fragen, der gehoert
hat, wovon die Rede ist.

WAS DAS KOSTET, UND WAS NICHT
-----------------------------
Waehrend eines gefuehrten Gespraechs geht laufend Text hinaus. Das ist mit
"nur auf Klick" (docs/plan.md) nur vereinbar, wenn der Klick am Anfang steht:
Das gefuehrte Gespraech wird ausdruecklich gestartet, die Oberflaeche sagt
dabei, was hinausgeht, und ohne diesen Klick laeuft die Aufnahme wie bisher
vollstaendig lokal.

Der Ton verlaesst den Rechner in keinem Fall.

DIE GRENZEN BLEIBEN
-------------------
Hoechstens eine Rueckfrage je Punkt, hoechstens so viele Punkte wie im
Leitfaden stehen. Ein Erstgespraech, das alles klaert, klaert nichts.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Callable

MODELL = "claude-sonnet-5"

# Ein Gespraech wartet. Laenger als das ist keine Frage mehr wert.
GEDULD = 45

TRAEGT = "traegt"
NACHFRAGEN = "nachfragen"
ANTWORTEN = "antworten"


def eingabe(punkt: dict, gesagt: str, verlauf: list[dict]) -> str:
    """Die Anweisung fuer einen einzelnen Zug im Gespraech."""
    bisher = "\n".join(
        f"- {e['titel']}: {e['antwort'][:200]}" for e in verlauf if e.get("antwort")
    ) or "(noch nichts)"

    return f"""Du fuehrst ein kurzes Erstgespraech ueber ein Software-Vorhaben. Dein
Gegenueber hat keinen Entwicklerhintergrund. Der Text kommt aus automatischer
Spracherkennung und enthaelt Hoerfehler und abgebrochene Saetze.

Bisher im Gespraech geklaert:
{bisher}

Aktueller Punkt: {punkt['titel']}
Die Leitfrage dazu: {punkt['frage']}
Sie soll fuellen: {punkt.get('fuellt', '')}

Was gerade gesagt wurde:
"{gesagt}"

Entscheide GENAU EINES:

- "{TRAEGT}": Das Gesagte beantwortet die Leitfrage brauchbar. Auch eine
  knappe Antwort reicht, wenn sie die Frage trifft.
- "{NACHFRAGEN}": Es traegt noch nicht. Formuliere EINE kurze Rueckfrage, die
  ein Wort oder einen Gedanken aus dem Gesagten aufgreift. Keine allgemeine
  Frage, keine zweite Frage, kein Vorwurf. Wer "ich moechte ein Spiel
  entwickeln" sagt, bekommt "Was fuer ein Spiel?" und nicht "Koenntest du
  das praezisieren?".
- "{ANTWORTEN}": Das Gegenueber hat DICH etwas gefragt. Beantworte es in
  einem Satz und stelle danach die Leitfrage neu.

Regeln:
- Duze. Ein Satz, hoechstens zwei. Keine Aufzaehlung, keine Hoeflichkeits-
  floskeln, kein "gerne".
- Keine Fachbegriffe: kein Issue, kein Repository, kein Pull Request.
- Erfinde nichts, was nicht gesagt wurde.
- Ist das Gesagte nur Rauschen oder eine Absage ("weiss nicht"), ist das
  "{NACHFRAGEN}" — mit einer leichteren Frage als vorher.

Antworte mit NICHTS ausser diesem JSON:

{{"zug": "{TRAEGT}|{NACHFRAGEN}|{ANTWORTEN}", "satz": "...", "grund": "..."}}

"satz" ist leer bei "{TRAEGT}", sonst das, was vorgelesen wird.
"grund" ist ein kurzer Vermerk fuer das Protokoll, nicht fuer das Gegenueber.
"""


def _aufruf_standard(anweisung: str, modell: str = MODELL) -> str:
    """
    Der eine Ort, an dem waehrend eines Gespraechs Text hinausgeht.

    Ohne Werkzeuge: Der Aufruf soll zuhoeren und fragen, nicht handeln.
    """
    ergebnis = subprocess.run(
        [
            "claude", "-p",
            "--output-format", "json",
            "--model", modell,
            "--disallowedTools", "Bash", "Write", "Edit", "Read", "Glob",
            "Grep", "WebFetch", "WebSearch", "Task", "NotebookEdit",
        ],
        input=anweisung,
        capture_output=True,
        text=True,
        check=False,
        timeout=GEDULD,
    )
    if ergebnis.returncode != 0:
        raise RuntimeError(ergebnis.stderr.strip() or "claude ist fehlgeschlagen")
    huelle = json.loads(ergebnis.stdout)
    if huelle.get("is_error"):
        raise RuntimeError(str(huelle.get("result") or "claude meldet einen Fehler"))
    return str(huelle.get("result", ""))


def zug_aus_text(roh: str) -> dict:
    """
    Das JSON aus der Antwort holen, auch durch einen Codeblock hindurch.

    Ein unlesbarer Zug ist ein Fehler und kein stilles "traegt". Wer hier
    im Zweifel weitergeht, baut genau den Fehler nach, der am 2026-09-13
    vier von fuenf Punkten leer gelassen hat.
    """
    text = (roh or "").strip()
    if not text:
        raise ValueError("Leere Antwort")

    ohne_zaun = re.sub(r"^```[a-z]*\n|\n```$", "", text, flags=re.MULTILINE).strip()
    anfang, ende = ohne_zaun.find("{"), ohne_zaun.rfind("}")
    if anfang == -1 or ende <= anfang:
        raise ValueError(f"Kein JSON in der Antwort: {text[:200]}")

    geladen = json.loads(ohne_zaun[anfang:ende + 1])
    zug = str(geladen.get("zug", "")).strip().lower()
    if zug not in (TRAEGT, NACHFRAGEN, ANTWORTEN):
        raise ValueError(f"Unbekannter Zug: {zug!r}")

    satz = str(geladen.get("satz", "")).strip()
    if zug in (NACHFRAGEN, ANTWORTEN) and not satz:
        raise ValueError(f"Zug {zug!r} ohne Satz — es gibt nichts vorzulesen.")
    return {"zug": zug, "satz": satz, "grund": str(geladen.get("grund", "")).strip()}


def naechster_zug(
    punkt: dict,
    gesagt: str,
    verlauf: list[dict] | None = None,
    aufrufen: Callable[[str], str] = _aufruf_standard,
) -> dict:
    """
    Ein Zug im Gespraech. `aufrufen` ist einsetzbar, damit Tests weder Abo
    noch Netz brauchen.
    """
    if not (gesagt or "").strip():
        raise ValueError("Nichts gesagt — daraus laesst sich keine Frage bilden.")
    return zug_aus_text(aufrufen(eingabe(punkt, gesagt, verlauf or [])))
