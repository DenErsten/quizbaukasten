"""
Tests fuer scripts/mithoeren.py.

Es gibt hier kein Mikrofon und kein Whisper — beides waere in der CI nicht
vorhanden. Geprueft wird deshalb gegen eine erzeugte WAV-Datei und eine
eingesetzte Erkennung. Das ist der Grund, warum `strom` die Erkennung als
Argument nimmt statt sie sich selbst zu holen.

Die WAV-Datei entsteht mit der Standardbibliothek. Eine Binaerdatei im Repo
waere hier ein Fremdkoerper: Niemand koennte nachsehen, was drin ist.
"""

from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from scripts.mithoeren import ABTASTRATE, BREITE, stuecke_aus_datei, strom


def wav_schreiben(pfad: Path, sekunden: float) -> None:
    """Eine stille WAV-Datei der gewuenschten Laenge."""
    with wave.open(str(pfad), "wb") as datei:
        datei.setnchannels(1)
        datei.setsampwidth(BREITE)
        datei.setframerate(ABTASTRATE)
        datei.writeframes(b"\x00" * int(ABTASTRATE * sekunden) * BREITE)


class Mithoeren(unittest.TestCase):
    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.quelle = self.ordner / "probe.wav"
        wav_schreiben(self.quelle, sekunden=6.0)

    def test_erzeugt_strom_mit_zeit_und_text(self) -> None:
        """Fall 1: Aus einer WAV-Datei wird ein Strom mit zeit und text."""
        saetze = iter(["erster Satz", "zweiter Satz"])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, sekunden=3.0), lambda _: next(saetze, ""))
        )

        self.assertEqual(len(zeilen), 2)
        self.assertEqual(zeilen[0], {"zeit": 0.0, "text": "erster Satz"})
        self.assertEqual(zeilen[1], {"zeit": 3.0, "text": "zweiter Satz"})

    def test_ohne_mitschneiden_entsteht_keine_datei(self) -> None:
        """Fall 2: Ohne --mitschneiden wird keine Audiodatei geschrieben."""
        vorher = set(self.ordner.iterdir())

        list(strom(stuecke_aus_datei(self.quelle, sekunden=3.0), lambda _: "irgendwas"))

        self.assertEqual(set(self.ordner.iterdir()), vorher)

    def test_mitschneiden_schreibt_die_stuecke(self) -> None:
        """Gegenprobe zu Fall 2: Mit Angabe entsteht die Datei sehr wohl."""
        ziel = self.ordner / "mitschnitt" / "sitzung.wav"

        list(strom(stuecke_aus_datei(self.quelle, sekunden=3.0), lambda _: "x", ziel))

        self.assertTrue(ziel.exists())
        with wave.open(str(ziel), "rb") as datei:
            self.assertEqual(datei.getframerate(), ABTASTRATE)
            self.assertEqual(datei.getnframes(), int(ABTASTRATE * 6.0))

    def test_stille_erzeugt_keine_zeile(self) -> None:
        """Fall 3: Ein Stueck ohne erkennbare Sprache erzeugt keine Zeile."""
        saetze = iter(["gesprochen", "   ", ""])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, sekunden=2.0), lambda _: next(saetze, ""))
        )

        self.assertEqual(len(zeilen), 1)
        self.assertEqual(zeilen[0]["text"], "gesprochen")


if __name__ == "__main__":
    unittest.main()
