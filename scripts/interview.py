#!/usr/bin/env python3
"""
Das gefuehrte Erstgespraech (#114).

DER UNTERSCHIED ZUM ZWISCHENRUF
-------------------------------
`ausloeser.py` reagiert auf Reizwoerter mitten im Satz: Wer "einige" sagt,
wird unterbrochen. Das Interview ist an zwei andere Dinge gebunden — an
Sprechpausen und an den Leitfaden. Es schweigt, solange gesprochen wird, und
entscheidet erst, wenn ein Gedanke zu Ende ist.

DIE GRENZEN SIND DER PUNKT
--------------------------
Hoechstens eine Rueckfrage je Frage, hoechstens so viele Fragen wie im
Leitfaden stehen, dann ist Schluss — auch wenn noch etwas zu fragen waere.
Ein Erstgespraech, das alles klaert, klaert nichts: Es schreibt Vermutungen
auf, die niemand pruefen konnte, weil noch nichts gebaut ist (docs/plan.md,
Abschnitt "Die Runde").

LOKAL, NICHT IN DER WOLKE
-------------------------
Ob eine Antwort traegt, entscheidet der Rechner. docs/plan.md laesst Text nur
auf Klick hinaus; ein Interview, das jede Pause auswertet, waere ein
Dauerstrom. Die Pruefungen sind entsprechend einfach — und sie stehen als
Name im Leitfaden, nicht hier: Wer dort einen Punkt ergaenzt, ergaenzt das
Interview mit.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable

PAUSE = 3.0

WEITER = "weiter"
NACHFRAGEN = "nachfragen"
OFFEN = "offen"
ENDE = "ende"

ZAHL = re.compile(r"\d")
ZAHLWOERTER = {
    "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn",
    "elf", "zwölf", "zwanzig", "dreißig", "fünfzig", "hundert", "tausend",
    "einmal", "zweimal", "dreimal", "täglich", "wöchentlich", "monatlich",
    "jährlich", "stündlich", "pro", "prozent", "minuten", "sekunden", "stunden",
}
PRUEFBAR = {
    "wenn", "sobald", "dann", "erscheint", "sieht", "sehen", "kann", "steht",
    "zeigt", "zeigen", "bekommt", "auftaucht", "klappt", "funktioniert",
    "gespeichert", "sichtbar", "fertig",
}
ABGRENZUNG = {
    "nicht", "kein", "keine", "keinen", "ohne", "außer", "später", "erstmal",
    "weglassen", "verzichten", "raus", "braucht", "unwichtig", "egal",
}
FEHLERFALL = {
    "wenn", "falls", "ausfällt", "schiefgeht", "fehler", "abstürzt", "kaputt",
    "offline", "verliert", "verloren", "abbricht", "hängt", "leer", "nichts",
}
FUELLWOERTER = {
    "also", "halt", "eben", "ja", "ne", "äh", "ähm", "und", "oder", "aber",
    "der", "die", "das", "ein", "eine", "einen", "ist", "sind", "wir", "ich",
    "es", "man", "so", "dass", "zu", "in", "auf", "mit", "für", "von",
}


def _woerter(text: str) -> list[str]:
    return re.findall(r"[a-zäöüß]+", text.lower())


def _inhaltswoerter(text: str) -> list[str]:
    return [w for w in _woerter(text) if w not in FUELLWOERTER]


def _traegt(text: str, marker: set[str], mindestens: int = 3) -> bool:
    """Ein Marker aus der Liste und genug Substanz drumherum."""
    woerter = set(_woerter(text))
    return bool(woerter & marker) and len(_inhaltswoerter(text)) >= mindestens


def prueft_inhalt(text: str) -> bool:
    """Genug gesagt, um daraus einen Kontextsatz zu machen."""
    return len(_inhaltswoerter(text)) >= 6


def prueft_pruefbar(text: str) -> bool:
    """Etwas, das man nachsehen kann — eine Bedingung, kein Wunsch."""
    return _traegt(text, PRUEFBAR, mindestens=4)


def prueft_abgrenzung(text: str) -> bool:
    """Eine Verneinung. Ohne sie ist keine Grenze gezogen worden."""
    return _traegt(text, ABGRENZUNG, mindestens=2)


def prueft_zahl(text: str) -> bool:
    """Eine Zahl. 'Einige' ist keine."""
    return bool(ZAHL.search(text)) or bool(set(_woerter(text)) & ZAHLWOERTER)


def prueft_fehlerfall(text: str) -> bool:
    return _traegt(text, FEHLERFALL, mindestens=2)


PRUEFUNGEN: dict[str, Callable[[str], bool]] = {
    "inhalt": prueft_inhalt,
    "pruefbar": prueft_pruefbar,
    "abgrenzung": prueft_abgrenzung,
    "zahl": prueft_zahl,
    "fehlerfall": prueft_fehlerfall,
}


class UnbekanntePruefung(ValueError):
    """
    Ein Leitfadenpunkt nennt eine Pruefung, die es nicht gibt.

    Ein eigener Fehler statt eines stillen "dann eben immer weiter": Ein
    Punkt, der nie nachfragt, sieht im Gespraech genauso aus wie einer, auf
    den immer gut geantwortet wird.
    """


class Interview:
    """
    Fuehrt durch die Punkte des Leitfadens.

    Der Aufrufer meldet zwei Dinge: was gehoert wurde (`gehoert`) und dass
    Zeit vergeht (`takt`). Alles andere passiert hier — ohne Uhr, ohne
    Threads, ohne Whisper, damit die Tests es Schritt fuer Schritt
    durchspielen koennen.
    """

    def __init__(
        self,
        punkte: Iterable[dict],
        pause: float = PAUSE,
        pruefungen: dict[str, Callable[[str], bool]] | None = None,
    ) -> None:
        self._punkte = [dict(p) for p in punkte]
        self._pause = pause
        self._pruefungen = dict(pruefungen or PRUEFUNGEN)
        for punkt in self._punkte:
            name = punkt.get("pruefung", "")
            if name not in self._pruefungen:
                raise UnbekanntePruefung(
                    f"Punkt {punkt.get('titel')!r} nennt die Prüfung {name!r}, "
                    f"die es nicht gibt. Bekannt: {', '.join(sorted(self._pruefungen))}"
                )
        self._nr = 0
        self._gesagt: list[str] = []
        self._zuletzt: float | None = None
        self._nachgefragt = False
        self._ergebnisse: list[dict] = []

    # -- was hereinkommt ---------------------------------------------------

    def gehoert(self, zeit: float, text: str) -> None:
        """Ein Stueck erkannter Text. Setzt die Stilleuhr zurueck."""
        text = (text or "").strip()
        if not text:
            return
        self._gesagt.append(text)
        self._zuletzt = zeit

    def takt(self, zeit: float) -> dict | None:
        """
        Zeit vergeht. Liefert ein Ereignis — oder None, wenn nichts ansteht.

        None ist der Normalfall: solange gesprochen wird, passiert nichts.
        Genau das ist der Unterschied zum Zwischenruf.
        """
        if self.fertig:
            return None
        if self._zuletzt is None:
            # Es wurde noch nichts zu dieser Frage gesagt. Stille am Anfang
            # ist Nachdenken, nicht eine leere Antwort.
            return None
        if zeit - self._zuletzt < self._pause:
            return None
        return self._entscheiden()

    # -- was herauskommt ---------------------------------------------------

    def _entscheiden(self) -> dict:
        punkt = self._punkte[self._nr]
        gesagt = " ".join(self._gesagt).strip()
        pruefung = self._pruefungen[punkt["pruefung"]]

        if pruefung(gesagt):
            return self._ablegen(punkt, gesagt, offen=False, art=WEITER)
        if not self._nachgefragt:
            self._nachgefragt = True
            # Die Uhr laeuft neu: Nach einer Rueckfrage darf man ueberlegen.
            self._zuletzt = None
            return {
                "art": NACHFRAGEN,
                "titel": punkt["titel"],
                "rueckfrage": punkt.get("rueckfrage", ""),
            }
        return self._ablegen(punkt, gesagt, offen=True, art=OFFEN)

    def _ablegen(self, punkt: dict, gesagt: str, offen: bool, art: str) -> dict:
        self._ergebnisse.append({
            "titel": punkt["titel"],
            "frage": punkt["frage"],
            "antwort": gesagt,
            "offen": offen,
        })
        self._nr += 1
        self._gesagt = []
        self._zuletzt = None
        self._nachgefragt = False
        if self.fertig:
            return {"art": ENDE, "titel": punkt["titel"], "offen": offen, "vorher": art}
        return {"art": art, "titel": punkt["titel"], "naechste": self._punkte[self._nr]["frage"]}

    # -- Zustand -----------------------------------------------------------

    @property
    def fertig(self) -> bool:
        return self._nr >= len(self._punkte)

    def stand(self) -> dict:
        """
        Was die Oberflaeche zeigt.

        `offen` wird ausdruecklich mitgefuehrt: Eine Frage, auf die keine
        tragfaehige Antwort kam, ist ein Ergebnis und kein Versaeumnis —
        sie ist die Liste fuer das naechste Gespraech.
        """
        return {
            "fertig": self.fertig,
            "nummer": self._nr + 1 if not self.fertig else len(self._punkte),
            "von": len(self._punkte),
            "frage": "" if self.fertig else self._punkte[self._nr]["frage"],
            "titel": "" if self.fertig else self._punkte[self._nr]["titel"],
            "nachgefragt": self._nachgefragt,
            "rueckfrage": (
                self._punkte[self._nr].get("rueckfrage", "")
                if self._nachgefragt and not self.fertig else ""
            ),
            "beantwortet": list(self._ergebnisse),
            "offene": [e["titel"] for e in self._ergebnisse if e["offen"]],
        }
