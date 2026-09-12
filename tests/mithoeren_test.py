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


class Transkript(unittest.TestCase):
    """
    #81: Was kein Hinweis wird, verschwand. Damit war nicht zu unterscheiden,
    ob nichts gesagt wurde oder nichts gehoert.
    """

    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.quelle = self.ordner / "probe.wav"
        wav_schreiben(self.quelle, sekunden=6.0)
        self.ziel = self.ordner / "unter" / "transkript.jsonl"

    def _zeilen(self) -> list[dict]:
        import json

        if not self.ziel.exists():
            return []
        return [json.loads(z) for z in self.ziel.read_text(encoding="utf-8").splitlines() if z.strip()]

    def test_jedes_erkannte_stueck_steht_im_transkript(self) -> None:
        """Fall 1: auch was keinen Hinweis ausloest."""
        saetze = iter(["wir bauen das in TypeScript", "und zwar naechste Woche"])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""), None, self.ziel))

        self.assertEqual([z["text"] for z in self._zeilen()],
                         ["wir bauen das in TypeScript", "und zwar naechste Woche"])

    def test_stille_erzeugt_keine_zeile(self) -> None:
        """Fall 2: wie im Hinweis-Strom."""
        saetze = iter(["gesprochen", "  "])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""), None, self.ziel))

        self.assertEqual(len(self._zeilen()), 1)

    def test_ohne_schreibrecht_laeuft_die_aufnahme_weiter(self) -> None:
        """
        Fall 3: Ein Gespraech laesst sich nicht wiederholen, eine Datei schon.
        """
        gesperrt = self.ordner / "gesperrt"
        gesperrt.mkdir()
        gesperrt.chmod(0o500)
        self.addCleanup(gesperrt.chmod, 0o700)

        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: "gesagt", None,
                  gesperrt / "transkript.jsonl")
        )

        self.assertEqual(len(zeilen), 2, "Der Strom muss trotzdem liefern")

    def test_zeitmarken_stehen_im_transkript(self) -> None:
        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: "etwas", None, self.ziel))

        self.assertEqual([z["zeit"] for z in self._zeilen()], [0.0, 3.0])
