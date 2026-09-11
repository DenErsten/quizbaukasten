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
import sys
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


def erkennung_whisper() -> Erkennung:
    """Lokale Erkennung. Import spaet — die CI hat kein Whisper."""
    try:
        import mlx_whisper  # noqa: PLC0415

        def erkennen(daten: bytes) -> str:
            import numpy  # noqa: PLC0415

            tonspur = numpy.frombuffer(daten, dtype=numpy.int16).astype(numpy.float32)
            tonspur /= 32768.0
            ergebnis = mlx_whisper.transcribe(tonspur, language="de")
            return str(ergebnis.get("text", ""))

        return erkennen
    except ImportError:
        pass

    from faster_whisper import WhisperModel  # noqa: PLC0415

    modell = WhisperModel("small", device="cpu", compute_type="int8")

    def erkennen(daten: bytes) -> str:
        import numpy  # noqa: PLC0415

        tonspur = numpy.frombuffer(daten, dtype=numpy.int16).astype(numpy.float32)
        tonspur /= 32768.0
        abschnitte, _ = modell.transcribe(tonspur, language="de")
        return " ".join(a.text for a in abschnitte)

    return erkennen


def strom(
    stuecke: Iterable[Stueck],
    erkennen: Erkennung,
    mitschnitt: Path | None = None,
) -> Iterator[dict]:
    """
    Macht aus Audio-Stuecken einen Strom erkannter Saetze.

    Stille erzeugt keine Zeile — auch keine leere. Wer den Strom liest, soll
    zaehlen koennen, was gesagt wurde, ohne Leerzeilen auszusortieren.
    """
    mitschreiber = None
    try:
        if mitschnitt is not None:
            mitschnitt.parent.mkdir(parents=True, exist_ok=True)
            mitschreiber = wave.open(str(mitschnitt), "wb")
            mitschreiber.setnchannels(1)
            mitschreiber.setsampwidth(BREITE)
            mitschreiber.setframerate(ABTASTRATE)

        for zeit, daten in stuecke:
            if mitschreiber is not None:
                mitschreiber.writeframes(daten)
            text = (erkennen(daten) or "").strip()
            if not text:
                continue
            yield {"zeit": round(zeit, 2), "text": text}
    finally:
        if mitschreiber is not None:
            mitschreiber.close()


def main() -> int:
    zerleger = argparse.ArgumentParser(description="Laufende Mitschrift, lokal.")
    zerleger.add_argument("--datei", type=Path, help="WAV statt Mikrofon")
    zerleger.add_argument("--sekunden", type=float, default=5.0, help="Laenge je Stueck")
    zerleger.add_argument(
        "--mitschneiden",
        type=Path,
        default=None,
        metavar="WAV",
        help="Audio zusaetzlich aufzeichnen. Ohne diese Angabe entsteht keine Datei.",
    )
    argumente = zerleger.parse_args()

    stuecke = (
        stuecke_aus_datei(argumente.datei, argumente.sekunden)
        if argumente.datei
        else stuecke_vom_mikrofon(argumente.sekunden)
    )

    for zeile in strom(stuecke, erkennung_whisper(), argumente.mitschneiden):
        print(json.dumps(zeile, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
