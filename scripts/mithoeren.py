#!/usr/bin/env python3
"""
Laufende Mitschrift — Mikrofon in Stuecken, lokal erkannt.

Gibt zeilenweise JSON auf stdout aus, waehrend gesprochen wird:

    {"zeit": 12.0, "text": "das muss schnell gehen"}

Wer diesen Strom liest, entscheidet Teil 2 (#36). Dieses Skript urteilt
nicht, es hoert nur.

WARUM NICHT transkribieren.sh
-----------------------------
Das Skript dort arbeitet stapelweise: Datei rein, ffmpeg, Whisper,
Transkript raus. Fuer einen Zwischenruf waehrend des Gespraechs ist das zu
spaet — man braucht alle paar Sekunden ein Stueck, nicht am Ende alles.

WARUM KEINE AUFNAHME
--------------------
Ohne --mitschneiden entsteht keine Audiodatei. Der Unterschied zwischen
Mithoeren und Abhoeren ist, ob hinterher etwas da ist; deshalb ist das
Schweigen die Voreinstellung und das Aufzeichnen die Ausnahme, die man
hinschreiben muss.

WARUM DIE ERKENNUNG AUSTAUSCHBAR IST
------------------------------------
`strom` bekommt die Erkennung als Argument. Das ist kein Selbstzweck: Ohne
sie liesse sich hier nichts pruefen, ohne Whisper und ein Mikrofon in der
CI zu haben. Ein Test, den kein Lauf startet, ist eine Behauptung.

AUFRUF
------
    python scripts/mithoeren.py                      # Mikrofon
    python scripts/mithoeren.py --datei probe.wav    # aus einer Datei
    python scripts/mithoeren.py --mitschneiden aufnahmen/sitzung.wav
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import wave
from pathlib import Path
from typing import Callable, Iterable, Iterator

# 16 kHz mono — das Format, das alle Whisper-Varianten am liebsten moegen,
# und dasselbe, auf das transkribieren.sh normalisiert.
ABTASTRATE = 16_000
BREITE = 2  # Bytes je Abtastwert (16 bit)

Stueck = tuple[float, bytes]
Erkennung = Callable[[bytes], str]


def stuecke_aus_datei(pfad: Path, sekunden: float = 5.0) -> Iterator[Stueck]:
    """Zerlegt eine WAV-Datei in Stuecke. Fuer Tests und zum Nachstellen."""
    with wave.open(str(pfad), "rb") as datei:
        rate = datei.getframerate()
        je_stueck = int(rate * sekunden)
        gelesen = 0
        while True:
            daten = datei.readframes(je_stueck)
            if not daten:
                return
            yield gelesen / rate, daten
            gelesen += len(daten) // (datei.getsampwidth() * datei.getnchannels())


def stuecke_vom_mikrofon(sekunden: float = 5.0) -> Iterator[Stueck]:
    """Nimmt vom Standard-Eingang auf. Import spaet, damit Tests ohne Geraet laufen."""
    import sounddevice  # noqa: PLC0415

    je_stueck = int(ABTASTRATE * sekunden)
    verstrichen = 0.0
    with sounddevice.RawInputStream(
        samplerate=ABTASTRATE, channels=1, dtype="int16", blocksize=je_stueck
    ) as strom_ein:
        while True:
            daten, uebergelaufen = strom_ein.read(je_stueck)
            if uebergelaufen:
                # Nicht abbrechen: Ein verlorenes Stueck ist aergerlich, ein
                # abgebrochenes Mithoeren mitten im Gespraech ist schlimmer.
                print("Warnung: Audio-Stueck verloren", file=sys.stderr)
            yield verstrichen, bytes(daten)
            verstrichen += sekunden


# Ab wie vielen wartenden Stuecken der Rueckstand gemeldet wird. Drei
# Stuecke sind bei fuenf Sekunden Laenge eine Viertelminute Verzug — ab da
# hinken die Hinweise dem Gespraech spuerbar hinterher.
RUECKSTAND_AB = 3

# Ausdruecklich, nicht die Voreinstellung der Bibliothek. mlx_whisper nimmt
# ohne Angabe "whisper-tiny" — das kleinste verfuegbare Modell. Eine Minute
# Deutsch ergab damit genau eine Zeile Kauderwelsch: "Dieses Themen wie die
# anderen spielen, koennen besten KI-Geschuechermel." (#84)
#
# "small" ist der uebliche Kompromiss: deutlich besser als tiny, auf Apple
# Silicon noch schnell genug fuer Stuecke von fuenf Sekunden. Wer wechseln
# will, aendert diese eine Zeile — und genau deshalb steht sie hier und
# nicht im Aufruf.
MODELL = "mlx-community/whisper-small-mlx"
MODELL_FASTER = "small"


class Puffer:
    """
    Liest ununterbrochen, waehrend die Erkennung arbeitet.

    Ohne das verdraengt die Erkennung den Ton: `stuecke_vom_mikrofon` liest
    ein Stueck, `strom` gibt es an Whisper und wartet — und solange niemand
    liest, laeuft der Puffer des Audiogeraets ueber. Bei der ersten echten
    Aufnahme am 2026-09-12 stand deshalb zweimal "Audio-Stueck verloren" im
    Log (#80). Whisper braucht fuer fuenf Sekunden Ton oft laenger als fuenf
    Sekunden; der Verlust war die Regel, nicht die Ausnahme.

    Hinkt die Erkennung nach, waechst die Warteschlange — aber nichts geht
    verloren. Ein Gespraech laesst sich nicht wiederholen.
    """

    _ENDE = object()

    def __init__(self, stuecke: Iterable[Stueck]) -> None:
        self._quelle = stuecke
        self._schlange: queue.Queue = queue.Queue()
        self._leser = threading.Thread(target=self._lesen, daemon=True)
        self._gestartet = False

    def _lesen(self) -> None:
        try:
            for stueck in self._quelle:
                self._schlange.put(stueck)
        finally:
            self._schlange.put(self._ENDE)

    @property
    def rueckstand(self) -> int:
        """Wie viele Stuecke warten. Waechst, wenn die Erkennung nachhinkt."""
        return self._schlange.qsize()

    def __iter__(self) -> Iterator[Stueck]:
        if not self._gestartet:
            self._leser.start()
            self._gestartet = True
        while True:
            stueck = self._schlange.get()
            if stueck is self._ENDE:
                return
            yield stueck


def erkennung_whisper(
    modell: str = MODELL, modell_faster: str = MODELL_FASTER
) -> Erkennung:
    """
    Lokale Erkennung. Import spaet — die CI hat kein Whisper.

    Zwei Modellnamen, weil die beiden Bibliotheken verschiedene Formate
    erwarten: mlx_whisper ein MLX-Repo, faster_whisper eine Groessenangabe
    oder ein CT2-Repo. Ein Name fuer beide waere in einem der Zweige falsch.

    Beide sind uebergebbar. Vorher nahm der faster-whisper-Zweig die
    Konstante, egal was uebergeben wurde — ein Parameter, der nichts tut,
    ist schlimmer als keiner (review an PR #85).

    Das Modell wird nicht von Hand zwischengespeichert: mlx_whisper haelt es
    in ModelHolder und laedt nur nach, wenn sich der Pfad aendert. Ich hatte
    in #84 behauptet, es werde je Stueck neu geladen — das stimmt nicht.
    """
    try:
        import mlx_whisper  # noqa: PLC0415

        def erkennen(daten: bytes) -> str:
            import numpy  # noqa: PLC0415

            tonspur = numpy.frombuffer(daten, dtype=numpy.int16).astype(numpy.float32)
            tonspur /= 32768.0
            ergebnis = mlx_whisper.transcribe(
                tonspur, language="de", path_or_hf_repo=modell
            )
            return str(ergebnis.get("text", ""))

        return erkennen
    except ImportError:
        pass

    from faster_whisper import WhisperModel  # noqa: PLC0415

    geladen = WhisperModel(modell_faster, device="cpu", compute_type="int8")

    def erkennen(daten: bytes) -> str:
        import numpy  # noqa: PLC0415

        tonspur = numpy.frombuffer(daten, dtype=numpy.int16).astype(numpy.float32)
        tonspur /= 32768.0
        abschnitte, _ = geladen.transcribe(tonspur, language="de")
        return " ".join(a.text for a in abschnitte)

    return erkennen


def strom(
    stuecke: Iterable[Stueck],
    erkennen: Erkennung,
    mitschnitt: Path | None = None,
    transkript: Path | None = None,
) -> Iterator[dict]:
    """
    Macht aus Audio-Stuecken einen Strom erkannter Saetze.

    Stille erzeugt keine Zeile — auch keine leere. Wer den Strom liest, soll
    zaehlen koennen, was gesagt wurde, ohne Leerzeilen auszusortieren.

    Ist `transkript` gesetzt, wird jeder erkannte Satz zusaetzlich dort
    abgelegt. Ohne das verschwindet alles, was kein Hinweis wird — und
    niemand kann unterscheiden, ob nichts gesagt wurde oder nichts gehoert
    (#81). Das Werkzeug heisst Protokoll-Werkzeug; es braucht ein Protokoll.

    Ein Transkript, das sich nicht schreiben laesst, bricht die Aufnahme
    NICHT ab. Ein Gespraech laesst sich nicht wiederholen — eine Datei
    schon.
    """
    mitschreiber = None
    mitschrift = None
    try:
        if transkript is not None:
            try:
                transkript.parent.mkdir(parents=True, exist_ok=True)
                mitschrift = transkript.open("a", encoding="utf-8")
            except OSError as fehler:
                print(f"Transkript nicht schreibbar, laeuft ohne: {fehler}",
                      file=sys.stderr)

        if mitschnitt is not None:
            mitschnitt.parent.mkdir(parents=True, exist_ok=True)
            mitschreiber = wave.open(str(mitschnitt), "wb")
            mitschreiber.setnchannels(1)
            mitschreiber.setsampwidth(BREITE)
            mitschreiber.setframerate(ABTASTRATE)

        gemeldeter_rueckstand = 0
        for zeit, daten in stuecke:
            # Der Rueckstand gehoert in den Strom, nicht nur auf stderr: Wer
            # die Hinweise liest, soll erfahren, dass sie hinterherhinken.
            rueckstand = getattr(stuecke, "rueckstand", 0)
            if rueckstand >= RUECKSTAND_AB and rueckstand > gemeldeter_rueckstand:
                gemeldeter_rueckstand = rueckstand
                yield {"zeit": round(zeit, 2), "art": "rueckstand", "stuecke": rueckstand}
            elif rueckstand < RUECKSTAND_AB:
                gemeldeter_rueckstand = 0

            if mitschreiber is not None:
                mitschreiber.writeframes(daten)
            text = (erkennen(daten) or "").strip()
            if not text:
                continue

            zeile = {"zeit": round(zeit, 2), "text": text}
            if mitschrift is not None:
                try:
                    mitschrift.write(json.dumps(zeile, ensure_ascii=False) + "\n")
                    mitschrift.flush()  # fortlaufend, nicht am Ende auf einmal
                except OSError as fehler:
                    print(f"Transkript nicht schreibbar, laeuft ohne: {fehler}",
                          file=sys.stderr)
                    mitschrift = None
            yield zeile
    finally:
        if mitschreiber is not None:
            mitschreiber.close()
        if mitschrift is not None:
            mitschrift.close()


def main() -> int:
    zerleger = argparse.ArgumentParser(description="Laufende Mitschrift, lokal.")
    zerleger.add_argument("--datei", type=Path, help="WAV statt Mikrofon")
    zerleger.add_argument("--sekunden", type=float, default=5.0, help="Laenge je Stueck")
    zerleger.add_argument(
        "--transkript",
        type=Path,
        default=None,
        metavar="JSONL",
        help="Erkannten Text zusaetzlich hierhin schreiben (kein Ton).",
    )
    zerleger.add_argument(
        "--mitschneiden",
        type=Path,
        default=None,
        metavar="WAV",
        help="Audio zusaetzlich aufzeichnen. Ohne diese Angabe entsteht keine Datei.",
    )
    argumente = zerleger.parse_args()

    roh = (
        stuecke_aus_datei(argumente.datei, argumente.sekunden)
        if argumente.datei
        else stuecke_vom_mikrofon(argumente.sekunden)
    )
    stuecke = Puffer(roh)

    for zeile in strom(
        stuecke, erkennung_whisper(), argumente.mitschneiden, argumente.transkript
    ):
        print(json.dumps(zeile, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
