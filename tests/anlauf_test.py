"""
Jede Seite sagt es, wenn ihr Modul nicht anlaeuft (#122).

Firat am 2026-09-12: "Screen Freigabe bleibt im 'Wird geladen' haengen."
Der Platzhalter stand, das Modul war nie angelaufen, und nichts auf der
Seite sagte es.

Geprueft wird nicht das Verhalten im Browser — dafuer braeuchte es einen
Browser —, sondern die Verdrahtung: Jede Seite mit einem Modul hat den
Melder und einen markierten Platzhalter. Das ist die Bedingung, unter der
der Melder ueberhaupt greifen kann, und es ist die Stelle, die beim
Anlegen der naechsten Seite vergessen wird.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

WERKZEUGE = Path(__file__).resolve().parent.parent / "werkzeuge"
MELDER = WERKZEUGE / "anlauf.js"


def _seiten_mit_modul() -> list[Path]:
    return [
        seite for seite in sorted(WERKZEUGE.glob("*.html"))
        if 'type="module"' in seite.read_text(encoding="utf-8")
    ]


class JedeSeiteMeldet(unittest.TestCase):
    def test_es_gibt_ueberhaupt_seiten_mit_modul(self) -> None:
        """Sonst waeren die Tests darunter gruen, ohne etwas zu pruefen."""
        self.assertGreaterEqual(len(_seiten_mit_modul()), 4)

    def test_jede_laedt_den_melder(self) -> None:
        for seite in _seiten_mit_modul():
            self.assertIn('src="anlauf.js"', seite.read_text(encoding="utf-8"), seite.name)

    def test_jede_hat_einen_markierten_platzhalter(self) -> None:
        for seite in _seiten_mit_modul():
            self.assertIn("data-anlauf=", seite.read_text(encoding="utf-8"), seite.name)

    def test_der_platzhaltertext_steht_auch_im_element(self) -> None:
        """
        Der Melder vergleicht den Inhalt mit dem Wert von data-anlauf. Stehen
        die auseinander, schlaegt die Acht-Sekunden-Regel nie an — und das
        waere wieder ein Melder, der stumm bleibt.
        """
        muster = re.compile(r'data-anlauf="([^"]*)"[^>]*>([^<]*)<')
        for seite in _seiten_mit_modul():
            treffer = muster.search(seite.read_text(encoding="utf-8"))
            self.assertIsNotNone(treffer, seite.name)
            self.assertEqual(treffer.group(1).strip(), treffer.group(2).strip(), seite.name)

    def test_der_melder_laedt_vor_dem_modul(self) -> None:
        """Danach waere er nutzlos: Der Ladefehler ist dann schon vorbei."""
        for seite in _seiten_mit_modul():
            text = seite.read_text(encoding="utf-8")
            self.assertLess(text.index('src="anlauf.js"'), text.index('type="module"'), seite.name)


class DerMelderIstKeinModul(unittest.TestCase):
    """
    Der ganze Trick. Ein Melder, der selbst ein Modul waere, teilt das
    Schicksal des Moduls, das er melden soll.
    """

    def test_er_importiert_nichts_und_exportiert_nichts(self) -> None:
        quelle = MELDER.read_text(encoding="utf-8")

        for zeile in quelle.splitlines():
            self.assertFalse(zeile.strip().startswith(("import ", "export ")), zeile)

    def test_er_wird_nirgends_als_modul_eingebunden(self) -> None:
        for seite in _seiten_mit_modul():
            text = seite.read_text(encoding="utf-8")
            self.assertNotIn('type="module" src="anlauf.js"', text, seite.name)

    def test_er_faengt_auch_ladefehler_von_dateien(self) -> None:
        """
        Ladefehler von <script> steigen nicht auf; sie sind nur in der
        Erfassungsphase zu sehen. Ohne das dritte Argument true bliebe genau
        der Fall unbemerkt, der diesen Melder noetig gemacht hat.
        """
        quelle = MELDER.read_text(encoding="utf-8")

        self.assertIn('"error"', quelle)
        self.assertIn("true", quelle.split('"error"')[1][:400])

    def test_er_setzt_den_text_ohne_html(self) -> None:
        """
        Die Meldung kommt vom Browser. Sie wird gezeigt, nicht ausgefuehrt.

        Gesucht wird die Zuweisung, nicht das Wort: Ein Kommentar, der
        erklaert, warum hier kein innerHTML steht, ist kein innerHTML.
        """
        quelle = MELDER.read_text(encoding="utf-8")

        self.assertIn("textContent", quelle)
        self.assertIsNone(re.search(r"\.innerHTML\s*=", quelle))


if __name__ == "__main__":
    unittest.main()
