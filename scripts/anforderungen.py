#!/usr/bin/env python3
"""
Leitet aus einem Transkript Anforderungs-Entwürfe ab.

Was hier NICHT passiert: Issues anlegen. Der Schritt endet bei Entwürfen.
Angelegt wird erst, wenn ein Mensch auf einen Entwurf klickt — sonst wäre
Gate G2 nur noch Zierde (#102).

WARUM TEXT DEN RECHNER VERLÄSST
-------------------------------
Bis zum 2026-09-12 verbot `docs/plan.md` pauschal jede Verarbeitung in der
Cloud. Firat hat in #102 Option B gewählt und den Plan geändert: Ton bleibt
hier, Text geht auf Klick heraus. Der Aufruf steht deshalb an genau einer
Stelle — `_aufruf_standard` —, damit man nachlesen kann, was wohin geht.

WARUM DER LEITFADEN DIE VORLAGE IST
-----------------------------------
Die fünf Fragen aus `docs/leitfaden.md` bestimmen, wonach im Gespräch gefragt
wird. Dieselben fünf bestimmen hier, wonach gesucht wird. Zwei getrennte
Listen liefen auseinander, und dann würde nach etwas anderem gesucht als
gefragt wurde.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Callable, Iterable

MODELL = "claude-sonnet-5"
GROESSEN = ("S", "M", "L")

# Ein Gespräch von einer Stunde ergibt mehr Text, als ein Aufruf braucht.
# Die Grenze schneidet vorne ab, nicht hinten: Das Ende eines Gesprächs
# enthält häufiger Beschlüsse als der Anfang.
HOECHSTZEICHEN = 60_000


def gespraech(zeilen: Iterable[dict]) -> str:
    """Das Transkript als lesbarer Text mit Zeitmarken."""
    saetze = []
    for zeile in zeilen:
        text = str(zeile.get("text", "")).strip()
        if not text:
            continue
        sekunden = float(zeile.get("zeit", 0) or 0)
        saetze.append(f"[{int(sekunden // 60):02d}:{int(sekunden % 60):02d}] {text}")
    ganzes = "\n".join(saetze)
    if len(ganzes) > HOECHSTZEICHEN:
        ganzes = "… (Anfang gekürzt) …\n" + ganzes[-HOECHSTZEICHEN:]
    return ganzes


def eingabe(text: str, punkte: list[dict]) -> str:
    """Die Anweisung samt Gespräch."""
    fragen = "\n".join(f"{n}. {p['titel']}: {p['frage']} — füllt: {p['fuellt']}"
                       for n, p in enumerate(punkte, 1))
    return f"""Du liest das Transkript eines Gesprächs über Software und leitest daraus
Anforderungs-Entwürfe ab. Das Transkript stammt aus automatischer Spracherkennung
und enthält Hörfehler; verbessere offensichtliche Verhörer stillschweigend, aber
erfinde nichts.

Der Gesprächsleitfaden, nach dem gefragt wurde:

{fragen}

Regeln:
- Nur was gesagt wurde. Keine Anforderung, die im Text keine Grundlage hat.
- Wurde ein prüfbares "fertig, wenn ..." genannt, schreib es in `fertig_wenn`.
  Wurde keins genannt, lass `fertig_wenn` LEER und schreib in `offene_frage`,
  was man nachfragen muss. Erfinde niemals ein Kriterium.
- `zitat` ist wörtlich aus dem Transkript, ein Satz, unverändert.
- `zeit` ist die Zeitmarke dieses Zitats in Sekunden.
- `groesse` ist S, M oder L nach Aufwand.
- Kein Smalltalk, keine Wiederholung, keine Anforderung aus einem Nebensatz,
  der offensichtlich etwas anderes meinte.

Antworte mit NICHTS ausser einem JSON-Array. Jedes Element:

{{"titel": "...", "kontext": "...", "fertig_wenn": "...", "offene_frage": "...",
  "groesse": "S", "zeit": 0, "zitat": "..."}}

Findest du keine einzige Anforderung, antworte mit [].

Transkript:

{text}
"""


def _aufruf_standard(anweisung: str, modell: str = MODELL) -> str:
    """
    Der eine Ort, an dem Text den Rechner verlässt.

    Ohne Werkzeuge: Der Aufruf soll lesen und antworten, nicht handeln. Käme
    er an `Bash` oder `Write`, wäre aus einem Ableitungsschritt ein zweiter
    Agent geworden, den niemand beauftragt hat.
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
        timeout=300,
    )
    if ergebnis.returncode != 0:
        raise RuntimeError(ergebnis.stderr.strip() or "claude ist fehlgeschlagen")
    try:
        huelle = json.loads(ergebnis.stdout)
    except json.JSONDecodeError as fehler:
        raise RuntimeError(f"Antwort von claude war kein JSON: {fehler}") from fehler
    if huelle.get("is_error"):
        raise RuntimeError(str(huelle.get("result") or "claude meldet einen Fehler"))
    return str(huelle.get("result", ""))


def entwuerfe_aus_text(roh: str) -> list[dict]:
    """
    Das JSON aus der Antwort holen — auch wenn ein Codeblock drumherum steht.

    Erklärtext vor dem Array ist kein Grund, alles wegzuwerfen; ein Array, das
    gar nicht da ist, schon. Stilles Leerliefern wäre hier besonders teuer:
    Das Gespräch ist vorbei und lässt sich nicht wiederholen.
    """
    text = roh.strip()
    if not text:
        raise ValueError("Leere Antwort")

    ohne_zaun = re.sub(r"^```[a-z]*\n|\n```$", "", text, flags=re.MULTILINE).strip()
    anfang, ende = ohne_zaun.find("["), ohne_zaun.rfind("]")
    if anfang == -1 or ende <= anfang:
        raise ValueError(f"Kein JSON-Array in der Antwort: {text[:200]}")

    geladen = json.loads(ohne_zaun[anfang:ende + 1])
    if not isinstance(geladen, list):
        raise ValueError("Antwort war kein Array")
    return [_aufraeumen(e) for e in geladen if isinstance(e, dict) and str(e.get("titel", "")).strip()]


def _aufraeumen(entwurf: dict) -> dict:
    """
    Jedes Feld bekommt einen Wert, auch wenn es fehlt.

    Ein fehlendes Feld sähe in der Anzeige aus wie ein leeres — und leer heisst
    hier etwas anderes als fehlend: dass im Gespräch nichts dazu gesagt wurde.
    """
    groesse = str(entwurf.get("groesse", "")).strip().upper()
    try:
        zeit = round(float(entwurf.get("zeit", 0) or 0), 1)
    except (TypeError, ValueError):
        zeit = 0.0
    return {
        "titel": str(entwurf.get("titel", "")).strip(),
        "kontext": str(entwurf.get("kontext", "")).strip(),
        "fertig_wenn": str(entwurf.get("fertig_wenn", "")).strip(),
        "offene_frage": str(entwurf.get("offene_frage", "")).strip(),
        "groesse": groesse if groesse in GROESSEN else "M",
        "zeit": zeit,
        "zitat": str(entwurf.get("zitat", "")).strip(),
    }


def ableiten(
    zeilen: Iterable[dict],
    punkte: list[dict],
    aufrufen: Callable[[str], str] = _aufruf_standard,
) -> list[dict]:
    """
    Transkript zu Entwürfen. `aufrufen` ist einsetzbar, damit die Tests ohne
    Netz, ohne Abo und ohne Kosten laufen.
    """
    text = gespraech(zeilen)
    if not text.strip():
        raise ValueError("Das Transkript ist leer — es gibt nichts abzuleiten.")
    return entwuerfe_aus_text(aufrufen(eingabe(text, punkte)))


def als_issue(entwurf: dict) -> tuple[str, str]:
    """
    Entwurf zu Titel und Text eines Issues.

    Fehlt das Abnahmekriterium, wird es NICHT erfunden — dann steht die offene
    Frage im Issue. CLAUDE.md: "Wenn du es nicht formulieren kannst, weisst du
    zu wenig."
    """
    zeit = int(entwurf.get("zeit", 0) or 0)
    marke = f"{zeit // 60:02d}:{zeit % 60:02d}"
    teile = [entwurf.get("kontext", "").strip() or "(kein Kontext im Gespräch genannt)", ""]

    if entwurf.get("fertig_wenn"):
        teile += ["**fertig, wenn**", "", entwurf["fertig_wenn"], ""]
    else:
        teile += [
            "**fertig, wenn** — im Gespräch nicht genannt.",
            "",
            "Offene Frage: " + (entwurf.get("offene_frage") or
                                "Woran ist zu erkennen, dass das fertig ist?"),
            "",
        ]

    if entwurf.get("zitat"):
        teile += [f"> {entwurf['zitat']}", "", f"Aus dem Gespräch bei {marke}.", ""]

    teile += [
        f"groesse:{entwurf.get('groesse', 'M')}",
        "",
        "---",
        "Abgeleitet aus einem Transkript und von einem Menschen übernommen. "
        "Der Wortlaut oben stammt aus automatischer Spracherkennung.",
    ]
    return entwurf.get("titel", "Ohne Titel"), "\n".join(teile)
