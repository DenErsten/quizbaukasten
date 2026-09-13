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
import sys
from pathlib import Path
from typing import Callable, Iterable

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.mithoeren import STUECK_SEKUNDEN  # noqa: E402

# WARUM DIESE ZAHL AUS mithoeren.py KOMMT
# ---------------------------------------
# Am 2026-09-12 stand hier 3.0, waehrend die Erkennung in Stuecken von 5.0
# Sekunden arbeitet. Zwischen zwei Stuecken liegen also immer rund fuenf
# Sekunden ohne neue Zeile — das Interview ging nach JEDEM Stueck weiter,
# unabhaengig davon, ob jemand sprach. Im ersten echten Gespraech galten
# drei von fuenf Fragen als unbeantwortet, und eine Antwort wurde mitten im
# Satz der naechsten Frage zugeschlagen (#127).
#
# Eine Pause, die kuerzer ist als ein Stueck, misst nicht das Gespraech,
# sondern den Takt der Maschine. Deshalb leitet sie sich ab, statt danebenzu-
# stehen, und ein Test haelt die Beziehung fest.
# Wie viele Stuecke am Stueck ohne ein Wort, bis ein Gedanke als fertig gilt.
# Das ist das ehrlichere Mass: Es zaehlt, was die Erkennung gemeldet hat,
# statt zu raten, warum nichts kam.
STILLE_STUECKE = 2

# Die Uhr ist der Notnagel und muss deshalb SPAETER zuschlagen als der
# Stueck-Zaehler. Beim ersten Versuch stand sie auf STUECK_SEKUNDEN + 3 = 8
# Sekunden, waehrend zwei stille Stuecke zehn Sekunden dauern — die Uhr kam
# also immer zuerst, und der Zaehler war im Betrieb tot. Der Pruefer in
# abnahme hat genau das gefunden. Ein zweiter Weg, den nie jemand geht, ist
# kein zweiter Weg, sondern toter Code mit einem Test daneben.
PAUSE = STILLE_STUECKE * STUECK_SEKUNDEN + 3.0

WEITER = "weiter"
ANTWORT = "antwort"

# Wie oft das Werkzeug je Punkt auf eine Frage des Menschen antwortet, bevor
# es auf der Leitfrage besteht. Ohne Grenze liesse sich das Gespraech
# beliebig vom Thema wegfuehren.
ANTWORTEN_JE_PUNKT = 2
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
    # Dazugekommen am 2026-09-13 (#130): Woerter, die in Whisper-Rauschen
    # haeufig auftauchen und nie den Inhalt tragen. "Ist nicht sein sein"
    # hat damit ein Inhaltswort statt dreien — "ohne Anmeldung" behaelt
    # seine zwei und bleibt eine gueltige Antwort.
    "sein", "seine", "seinen", "mal", "schon", "noch", "gerade", "irgendwie",
    "eigentlich", "dann", "da", "wie", "was", "nun",
}


# ABSAGEN
# -------
# Am 2026-09-13 gingen drei von fuenf Antworten als beantwortet durch, die
# woertlich "weiss ich nicht" lauteten. Die Pruefungen suchen Stichwoerter,
# und "fertig", "nicht", "wenn" stecken in einer Absage genauso wie in einer
# Antwort: "Ich weiss nicht warum das fertig sein sollte" enthaelt "fertig"
# und genug Inhaltswoerter — bestanden.
#
# Gestern hat das Werkzeug mitten im Satz unterbrochen, heute nickt es. Das
# zweite ist schlimmer: Ein Zwischenruf zur falschen Zeit faellt auf, ein
# zustimmendes Nicken nicht. Am Ende steht ein Rahmen, der vollstaendig
# aussieht und leer ist — und der Ableitungsschritt baut darauf auf (#130).
ABSAGE = re.compile(
    r"\b(wei(ß|ss)\s+(ich\s+)?(gerade\s+|noch\s+|jetzt\s+)?nicht"
    r"|(ich\s+)?wei(ß|ss)\s+es\s+nicht"
    r"|keine\s+ahnung"
    r"|kann\s+ich\s+(dir\s+)?(gerade\s+|jetzt\s+)?nicht\s+sagen"
    r"|gute\s+frage"
    r"|bin\s+(ich\s+)?mir\s+nicht\s+sicher"
    r"|m(ü|ue)sste\s+ich\s+(mal\s+)?(erst\s+)?(ü|ue)berlegen"
    r"|(da\s+)?f(ä|ae)llt\s+mir\s+(gerade\s+)?nichts\s+ein"
    r"|keine\s+idee)\b",
    re.IGNORECASE,
)

# Fuellsel, das allein keinen Satz ausmacht.
NUR_LAUT = re.compile(r"^[\s.,…!?-]*((ä|a)h+m?|hm+|also|naja|tja|ja|nee?|ne)[\s.,…!?-]*$", re.IGNORECASE)


def _saetze(text: str) -> list[str]:
    """Grob nach Satzzeichen geteilt, samt dem Zeichen, das den Satz beendet."""
    teile = re.split(r"([.!?…]+)", text or "")
    saetze = []
    for i in range(0, len(teile), 2):
        satz = teile[i].strip()
        zeichen = teile[i + 1] if i + 1 < len(teile) else ""
        if satz and not NUR_LAUT.match(satz):
            saetze.append((satz, "?" in zeichen))
    return saetze


def ohne_absagen(text: str) -> str:
    """
    Was uebrig bleibt, wenn man Absagen und Rueckfragen streicht.

    Nicht "ist das eine Absage?", sondern "was steht da ausser der Absage?".
    Der Unterschied zaehlt bei gemischten Antworten: "Ich nutze das taeglich.
    Ich weiss es nicht." enthaelt eine Antwort — "taeglich" — und die soll
    zaehlen. Wer den ganzen Text verwirft, sobald irgendwo Unsicherheit
    steht, macht den umgekehrten Fehler.

    Eine Rueckfrage an das Werkzeug faellt ebenfalls weg. Am 2026-09-13 stand
    "Gibt's eine Fehlermeldung?" als Antwort auf den Fehlerfall (#130).
    """
    behalten = [satz for satz, ist_frage in _saetze(text)
                if not ist_frage and not ABSAGE.search(satz)]
    return " ".join(behalten)


def ist_absage(text: str) -> bool:
    """Nach Abzug von Absagen und Rueckfragen bleibt nichts uebrig."""
    return not ohne_absagen(text).strip()


def _woerter(text: str) -> list[str]:
    return re.findall(r"[a-zäöüß]+", text.lower())


def _ohne_wiederholung(woerter: list[str]) -> list[str]:
    """
    Unmittelbare Wortwiederholungen zaehlen einmal.

    Whisper wiederholt sich, wenn es unsicher ist: "sein sein", und am
    2026-09-12 "Audi Audi Audi Audi Audi". Solche Stellen sind kein Inhalt,
    sondern ein Zeichen dafuer, dass die Erkennung geraten hat. Sie durften
    bisher die Substanzpruefung bestehen (#130).
    """
    ergebnis: list[str] = []
    for wort in woerter:
        if not ergebnis or ergebnis[-1] != wort:
            ergebnis.append(wort)
    return ergebnis


def _inhaltswoerter(text: str) -> list[str]:
    return _ohne_wiederholung([w for w in _woerter(text) if w not in FUELLWOERTER])


def _traegt(text: str, marker: set[str], mindestens: int = 3) -> bool:
    """Ein Marker aus der Liste und genug Substanz drumherum — im Rest."""
    rest = ohne_absagen(text)
    woerter = set(_woerter(rest))
    return bool(woerter & marker) and len(_inhaltswoerter(rest)) >= mindestens


def prueft_inhalt(text: str) -> bool:
    """Genug gesagt, um daraus einen Kontextsatz zu machen."""
    return len(_inhaltswoerter(ohne_absagen(text))) >= 6


def prueft_pruefbar(text: str) -> bool:
    """Etwas, das man nachsehen kann — eine Bedingung, kein Wunsch."""
    return _traegt(text, PRUEFBAR, mindestens=4)


def prueft_abgrenzung(text: str) -> bool:
    """
    Eine Verneinung und etwas, das verneint wird.

    "Ist nicht sein sein" bestand die Pruefung am 2026-09-13, weil "nicht"
    darin steht (#130). Die Schwelle hochzudrehen war der falsche Weg — sie
    haette auch "ohne Anmeldung" verworfen, zwei Woerter und eine richtige
    Antwort. Stattdessen zaehlt "sein" nicht mehr als Inhalt: Es traegt in
    "Ist nicht sein sein" nichts bei, waehrend "Anmeldung" es tut.
    """
    return _traegt(text, ABGRENZUNG, mindestens=2)


def prueft_zahl(text: str) -> bool:
    """Eine Zahl. 'Einige' ist keine, 'weiss ich nicht' erst recht nicht."""
    rest = ohne_absagen(text)
    return bool(ZAHL.search(rest)) or bool(set(_woerter(rest)) & ZAHLWOERTER)


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
        stille_stuecke: int = STILLE_STUECKE,
        fuehrung: Callable[..., dict] | None = None,
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
        self._stille_stuecke = stille_stuecke
        # Ohne Fuehrung laeuft alles wie bisher: lokale Pruefungen, kein Wort
        # verlaesst den Rechner. Sie wird nur gesetzt, wenn jemand das
        # gefuehrte Gespraech ausdruecklich gestartet hat (#125).
        self._fuehrung = fuehrung
        self._rueckfrage_text = ""
        self._antworten = 0
        self._fuehrung_fehler: str | None = None
        self._nr = 0
        self._gesagt: list[str] = []
        self._zuletzt: float | None = None
        self._stille = 0
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
        self._stille = 0

    def stille(self, zeit: float = 0.0) -> None:
        """
        Ein Stueck, in dem nichts gesagt wurde.

        Das ist die verlaessliche Nachricht, und die Uhr ist nur der Notnagel:
        Sie sagt "die Erkennung hat gearbeitet und nichts gehoert" — nicht
        "es kam nichts an", was auch heissen koennte, dass sie haengt.
        """
        self._stille += 1

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
        # Gemeldete Stille zaehlt zuerst: Sie ist eine Aussage der Erkennung.
        if self._stille >= self._stille_stuecke:
            return self._entscheiden()
        # Die Uhr ist der Notnagel fuer den Fall, dass GAR NICHTS mehr kommt:
        # keine Worte und keine Stille-Meldungen. Dann haengt die Erkennung,
        # und irgendwann muss das Gespraech trotzdem weitergehen. Ihre
        # Schwelle liegt hinter dem Stueck-Zaehler, sonst kaeme sie im
        # Normalbetrieb zuerst und der Zaehler waere Zierde (#127).
        if zeit - self._zuletzt < self._pause:
            return None
        return self._entscheiden()

    # -- was herauskommt ---------------------------------------------------

    def _entscheiden(self) -> dict:
        punkt = self._punkte[self._nr]
        gesagt = " ".join(self._gesagt).strip()

        if self._fuehrung is not None:
            ereignis = self._gefuehrt(punkt, gesagt)
            if ereignis is not None:
                return ereignis
            # Faellt die Fuehrung aus, entscheidet die lokale Pruefung weiter.
            # Ein Gespraech laesst sich nicht wiederholen — es darf nicht am
            # Netz haengen.

        pruefung = self._pruefungen[punkt["pruefung"]]

        if pruefung(gesagt):
            return self._ablegen(punkt, gesagt, offen=False, art=WEITER)
        if not self._nachgefragt:
            return self._nachfragen(punkt, punkt.get("rueckfrage", ""))
        return self._ablegen(punkt, gesagt, offen=True, art=OFFEN)

    # -- der gefuehrte Weg --------------------------------------------------

    def _gefuehrt(self, punkt: dict, gesagt: str) -> dict | None:
        """
        Einen Zug von der Gespraechsfuehrung holen.

        Gibt None zurueck, wenn sie nicht antwortet — dann entscheidet die
        lokale Pruefung. Der Fehler wird gemerkt und im Stand gezeigt: Eine
        Fuehrung, die still ausfaellt, saehe aus wie eine, die schlecht
        fragt (#99).
        """
        try:
            zug = self._fuehrung(punkt, gesagt, list(self._ergebnisse))
            self._fuehrung_fehler = None
        except Exception as fehler:  # noqa: BLE001
            self._fuehrung_fehler = str(fehler)
            return None

        art = zug.get("zug")
        if art == "traegt":
            return self._ablegen(punkt, gesagt, offen=False, art=WEITER)

        if art == "antworten" and self._antworten < ANTWORTEN_JE_PUNKT:
            # Eine Frage an das Werkzeug zaehlt nicht als Rueckfrage: Sie
            # bringt den Punkt nicht weiter, sie raeumt ein Hindernis weg.
            # Am 2026-09-12 und 2026-09-13 hat Firat zweimal gefragt und
            # zweimal keine Antwort bekommen (#131).
            self._antworten += 1
            self._gesagt = []
            self._zuletzt = None
            self._stille = 0
            self._rueckfrage_text = zug.get("satz", "")
            return {"art": ANTWORT, "titel": punkt["titel"],
                    "satz": zug.get("satz", "")}

        if not self._nachgefragt:
            return self._nachfragen(punkt, zug.get("satz", "") or punkt.get("rueckfrage", ""))
        return self._ablegen(punkt, gesagt, offen=True, art=OFFEN)

    def _nachfragen(self, punkt: dict, satz: str) -> dict:
        self._nachgefragt = True
        self._rueckfrage_text = satz
        # Die Uhr laeuft neu: Nach einer Rueckfrage darf man ueberlegen.
        self._zuletzt = None
        self._stille = 0
        return {"art": NACHFRAGEN, "titel": punkt["titel"], "rueckfrage": satz}

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
        self._stille = 0
        self._nachgefragt = False
        self._rueckfrage_text = ""
        self._antworten = 0
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
            "rueckfrage": self._rueckfrage_text if not self.fertig else "",
            # Eine Fuehrung, die ausgefallen ist, wird genannt. Sonst sieht
            # sie aus wie eine, die schlecht fragt.
            "fuehrung_fehler": self._fuehrung_fehler,
            "gefuehrt": self._fuehrung is not None,
            "beantwortet": list(self._ergebnisse),
            "offene": [e["titel"] for e in self._ergebnisse if e["offen"]],
        }
