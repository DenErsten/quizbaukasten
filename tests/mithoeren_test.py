"""
Tests für scripts/mithoeren.py — siehe #35.

Laufen gegen eine kurze WAV-Datei im Repo (tests/mithoeren_probe.wav), nicht
gegen ein Mikrofon, sonst wären sie in der CI nicht ausführbar. Die
Spracherkennung selbst (mlx-whisper/faster-whisper) wird durch einen Stub
ersetzt — die CI installiert kein Whisper, und das ist auch nicht das, was
hier geprüft wird.

Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad: die KI
darf hier ergänzen, aber nichts entschärfen oder löschen, ohne dass ein
Mensch den PR freigibt.
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

WURZEL = Path(__file__).resolve().parent.parent
if str(WURZEL) not in sys.path:
    sys.path.insert(0, str(WURZEL))

from scripts import mithoeren  # noqa: E402

PROBE = WURZEL / "tests" / "mithoeren_probe.wav"


def stub_erkenner(antworten):
    """Ersetzt erkenner_laden(): liefert der Reihe nach vorgegebene Texte statt Whisper zu rufen."""
    folge = iter(antworten)

    def erkennen(stueck: io.BytesIO) -> str:
        return next(folge)

    return lambda: erkennen


def stdout_zeilen(argv: list[str], antworten: list[str]) -> list[dict]:
    puffer = io.StringIO()
    with patch.object(mithoeren, "erkenner_laden", stub_erkenner(antworten)):
        with redirect_stdout(puffer):
            mithoeren.main(argv)
    text = puffer.getvalue().strip()
    return [json.loads(z) for z in text.splitlines()] if text else []


class MithoerenTest(unittest.TestCase):
    def test_datei_erzeugt_json_strom_mit_zeit_und_text(self):
        zeilen = stdout_zeilen(
            ["--datei", str(PROBE), "--stueck-sekunden", "1.0"],
            ["Hallo Welt", "Guten Tag"],
        )
        self.assertEqual(len(zeilen), 2)
        for zeile in zeilen:
            self.assertIn("zeit", zeile)
            self.assertIn("text", zeile)
        self.assertEqual(zeilen[0]["zeit"], 0.0)
        self.assertEqual(zeilen[0]["text"], "Hallo Welt")
        self.assertEqual(zeilen[1]["zeit"], 1.0)
        self.assertEqual(zeilen[1]["text"], "Guten Tag")

    def test_stueck_ohne_sprache_erzeugt_keine_zeile_statt_einer_leeren(self):
        zeilen = stdout_zeilen(
            ["--datei", str(PROBE), "--stueck-sekunden", "1.0"],
            ["", "Hallo Welt"],
        )
        self.assertEqual(len(zeilen), 1)
        self.assertEqual(zeilen[0]["text"], "Hallo Welt")
        self.assertEqual(zeilen[0]["zeit"], 1.0)

    def test_ohne_mitschneiden_wird_keine_audiodatei_geschrieben(self):
        with TemporaryDirectory() as tmp:
            alt = os.getcwd()
            os.chdir(tmp)
            try:
                stdout_zeilen(["--datei", str(PROBE), "--stueck-sekunden", "1.0"], ["Hallo", ""])
            finally:
                os.chdir(alt)
            self.assertEqual(list(Path(tmp).rglob("*")), [])


if __name__ == "__main__":
    unittest.main()
