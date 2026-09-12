"""
Rauchtest der ganzen Kette: Sprache -> Transkript -> Hinweis.

Am 2026-09-12 blieben drei Aufnahmen hintereinander ergebnislos, aus drei
verschiedenen Gruenden: fehlende Mikrofonfreigabe, das Modell "tiny", ein
abgebrochener Modell-Download. Jeder sah gleich aus — hinweise: 0, kein
Fehler. Zwei der drei haette dieser Test gefunden.

Die Sprache entsteht zur Laufzeit mit `say`. Keine Binaerdatei im Repo: Wer
den Test liest, sieht, was gesprochen wird.

WAS DIESER TEST NICHT LEISTET
-----------------------------
Er beantwortet nicht, ob Whisper einen Menschen in einem Raum versteht.
`say` erzeugt sauberere Sprache als jedes echte Gespraech. Das ist Annahme
A2 in docs/plan.md und bleibt eine Betriebspruefung.

Geprueft wird die KETTE, nicht die Erkennungsguete.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def _say_vorhanden() -> bool:
    if shutil.which("say") is None:
        return False
    stimmen = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
    return "de_DE" in stimmen.stdout


def _whisper_vorhanden() -> bool:
    try:
        import mlx_whisper  # noqa: F401, PLC0415

        return True
    except ImportError:
        try:
            import faster_whisper  # noqa: F401, PLC0415

            return True
        except ImportError:
            return False


def _modell_vorhanden() -> bool:
    """Fall 4: Fehlt das Modell, soll der Test das SAGEN, nicht stumm nichts finden."""
    try:
        from huggingface_hub import snapshot_download  # noqa: PLC0415

        from scripts.mithoeren import MODELL  # noqa: PLC0415

        snapshot_download(MODELL, local_files_only=True)
        return True
    except Exception:
        return False


@unittest.skipUnless(_say_vorhanden(), "kein `say` mit deutscher Stimme (nur macOS)")
@unittest.skipUnless(_whisper_vorhanden(), "kein Whisper installiert — siehe transkribieren.sh")
class Kette(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _modell_vorhanden():
            from scripts.mithoeren import MODELL

            raise unittest.SkipTest(
                f"Modell {MODELL} liegt nicht vollständig im Cache. "
                "Vorab laden mit: python3 -c \"from huggingface_hub import "
                f"snapshot_download; snapshot_download('{MODELL}')\""
            )
        from scripts.mithoeren import erkennung_whisper

        cls.erkennen = staticmethod(erkennung_whisper())
        cls.ordner = Path(tempfile.mkdtemp())

    def _gesprochen(self, satz: str) -> Path:
        ziel = self.ordner / f"{abs(hash(satz))}.wav"
        subprocess.run(
            ["say", "-v", "Anna", "--data-format=LEI16@16000", "-o", str(ziel), satz],
            check=True,
        )
        return ziel

    def _durch_die_kette(self, satz: str):
        from scripts.ausloeser import ausserhalb_des_scopes, hinweise
        from scripts.mithoeren import stuecke_aus_datei, strom

        zeilen = list(strom(stuecke_aus_datei(self._gesprochen(satz), 30.0), self.erkennen))
        plan = (WURZEL / "docs" / "plan.md").read_text(encoding="utf-8")
        return zeilen, list(hinweise(zeilen, ausserhalb_des_scopes(plan)))

    def test_gesprochenes_wird_erkannt(self) -> None:
        """Fall 1: Das Transkript enthaelt das gesprochene Wort."""
        zeilen, _ = self._durch_die_kette("Das Laden muss schnell gehen.")

        text = " ".join(z.get("text", "") for z in zeilen).lower()
        self.assertIn("schnell", text, f"erkannt wurde: {text!r}")

    def test_unscharfer_satz_erzeugt_genau_einen_hinweis(self) -> None:
        """Fall 2."""
        _, h = self._durch_die_kette("Das Laden muss schnell gehen.")

        self.assertEqual(len(h), 1, f"Hinweise: {h}")
        self.assertEqual(h[0]["art"], "mengenwort")

    def test_technischer_satz_erzeugt_keinen_hinweis(self) -> None:
        """
        Fall 3. Genauso wichtig wie Fall 2: Ein Ausloeser, der bei allem
        anspringt, ist so nutzlos wie einer, der schweigt.
        """
        _, h = self._durch_die_kette("Wir bauen das in TypeScript.")

        self.assertEqual(h, [], f"unerwartete Hinweise: {h}")
