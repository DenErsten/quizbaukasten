#!/usr/bin/env python3
"""
Live-Mitschrift: nimmt vom Mikrofon auf, schneidet in Stücke von wenigen
Sekunden, erkennt jedes Stück lokal und schreibt das Ergebnis zeilenweise
nach stdout als JSON — Zeitmarke und Text. Ein Strom, kein Dokument.

Teil 1 von #34, siehe #35. `scripts/transkribieren.sh` arbeitet stapelweise;
für einen Zwischenruf ist das zu spät.

Nichts verlässt den Rechner: dieselbe lokale Whisper-Erkennung wie in
transkribieren.sh.

Schreibt keine Audiodatei, solange --mitschneiden nicht ausdrücklich gesetzt
ist. Eine Aufnahme, die niemand angefordert hat, ist der Unterschied zwischen
Mithören und Abhören — siehe die Einwilligung in #34.

INSTALLATION
------------
    pip install sounddevice numpy soundfile
    # Apple Silicon:
    pip install mlx-whisper
    # sonst:
    pip install faster-whisper

AUFRUF
------
    python scripts/mithoeren.py                              # Mikrofon, bis Strg-C
    python scripts/mithoeren.py --mitschneiden                # zusätzlich Audiodatei sichern
    python scripts/mithoeren.py --datei aufnahmen/probe.wav   # aus Datei statt Mikrofon
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import wave
from collections.abc import Callable, Iterator
from pathlib import Path

SAMPLERATE = 16000
STUECK_SEKUNDEN = 5.0


def wav_stuecke(pfad: str, stueck_sekunden: float = STUECK_SEKUNDEN) -> Iterator[tuple[float, io.BytesIO]]:
    """Liest eine WAV-Datei und liefert (Startzeit, Stück) paarweise.

    Jedes Stück ist eine eigenständige WAV-Datei im Speicher — dafür wird
    nichts auf die Festplatte geschrieben.
    """
    with wave.open(pfad, "rb") as quelle:
        kanaele = quelle.getnchannels()
        breite = quelle.getsampwidth()
        rate = quelle.getframerate()
        rahmen_pro_stueck = max(1, int(rate * stueck_sekunden))

        zeit = 0.0
        while True:
            rahmen = quelle.readframes(rahmen_pro_stueck)
            if not rahmen:
                return
            stueck = io.BytesIO()
            with wave.open(stueck, "wb") as ziel:
                ziel.setnchannels(kanaele)
                ziel.setsampwidth(breite)
                ziel.setframerate(rate)
                ziel.writeframes(rahmen)
            stueck.seek(0)
            yield zeit, stueck
            zeit += len(rahmen) / breite / kanaele / rate


def mikrofon_stuecke(stueck_sekunden: float = STUECK_SEKUNDEN) -> Iterator[tuple[float, io.BytesIO]]:
    """Nimmt vom Mikrofon auf, bis das Programm beendet wird. Liefert Stücke wie wav_stuecke."""
    import sounddevice as sd

    rahmen_pro_stueck = int(SAMPLERATE * stueck_sekunden)
    zeit = 0.0
    while True:
        aufnahme = sd.rec(rahmen_pro_stueck, samplerate=SAMPLERATE, channels=1, dtype="int16")
        sd.wait()
        stueck = io.BytesIO()
        with wave.open(stueck, "wb") as ziel:
            ziel.setnchannels(1)
            ziel.setsampwidth(2)
            ziel.setframerate(SAMPLERATE)
            ziel.writeframes(aufnahme.tobytes())
        stueck.seek(0)
        yield zeit, stueck
        zeit += stueck_sekunden


def erkenner_laden() -> Callable[[io.BytesIO], str]:
    """Lädt das Spracherkennungsmodell einmal. Gibt eine Funktion Stück -> Text zurück."""
    try:
        import mlx_whisper

        def erkennen(stueck: io.BytesIO) -> str:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                f.write(stueck.read())
                f.flush()
                ergebnis = mlx_whisper.transcribe(
                    f.name, path_or_hf_repo="mlx-community/whisper-large-v3-mlx", language="de"
                )
            return ergebnis.get("text", "").strip()

        return erkennen
    except ImportError:
        pass

    try:
        from faster_whisper import WhisperModel

        modell = WhisperModel("large-v3", device="auto", compute_type="int8")

        def erkennen(stueck: io.BytesIO) -> str:
            segmente, _ = modell.transcribe(stueck, language="de", vad_filter=True)
            return " ".join(s.text.strip() for s in segmente).strip()

        return erkennen
    except ImportError:
        pass

    sys.exit("Kein Spracherkenner gefunden. pip install mlx-whisper oder faster-whisper")


def strom(
    stuecke: Iterator[tuple[float, io.BytesIO]],
    erkennen: Callable[[io.BytesIO], str],
) -> Iterator[dict]:
    """Erkennt jedes Stück. Ein Stück ohne erkennbare Sprache erzeugt keine Zeile."""
    for zeit, stueck in stuecke:
        text = erkennen(stueck).strip()
        if not text:
            continue
        yield {"zeit": round(zeit, 2), "text": text}


def mit_mitschnitt(
    stuecke: Iterator[tuple[float, io.BytesIO]], ziel: Path
) -> Iterator[tuple[float, io.BytesIO]]:
    """Reicht jedes Stück durch, hängt es dabei an eine Mitschnitt-Datei an."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    schreiber: wave.Wave_write | None = None
    try:
        for zeit, stueck in stuecke:
            rohdaten = stueck.getvalue()
            with wave.open(io.BytesIO(rohdaten), "rb") as quelle:
                if schreiber is None:
                    schreiber = wave.open(str(ziel), "wb")
                    schreiber.setnchannels(quelle.getnchannels())
                    schreiber.setsampwidth(quelle.getsampwidth())
                    schreiber.setframerate(quelle.getframerate())
                schreiber.writeframes(quelle.readframes(quelle.getnframes()))
            stueck.seek(0)
            yield zeit, stueck
    finally:
        if schreiber is not None:
            schreiber.close()


def main(argv: list[str] | None = None) -> None:
    zerleger = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    zerleger.add_argument("--datei", help="WAV-Datei statt Mikrofon lesen (zum Testen)")
    zerleger.add_argument("--stueck-sekunden", type=float, default=STUECK_SEKUNDEN, help="Länge eines Stücks")
    zerleger.add_argument(
        "--mitschneiden", action="store_true", help="Aufnahme zusätzlich als WAV-Datei sichern"
    )
    zerleger.add_argument("--mitschnitt-ziel", default=None, help="Pfad für die Mitschnitt-Datei")
    argumente = zerleger.parse_args(argv)

    stuecke = (
        wav_stuecke(argumente.datei, argumente.stueck_sekunden)
        if argumente.datei
        else mikrofon_stuecke(argumente.stueck_sekunden)
    )

    if argumente.mitschneiden:
        ziel = Path(argumente.mitschnitt_ziel or f"aufnahmen/mithoeren-{int(time.time())}.wav")
        stuecke = mit_mitschnitt(stuecke, ziel)

    erkennen = erkenner_laden()
    for zeile in strom(stuecke, erkennen):
        print(json.dumps(zeile, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
