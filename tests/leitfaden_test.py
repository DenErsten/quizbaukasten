"""
Tests fuer scripts/leitfaden.py.

Der Parser wird an einem festen Text geprueft, damit eine Aenderung am
Wortlaut in docs/leitfaden.md nicht die Parser-Tests kippt — dieselbe
Trennung wie bei ausloeser_test.py und der Scopeliste.

Ein Test greift bewusst doch auf die echte Datei zu: der, der beweist, dass
die echte Datei ueberhaupt lesbar ist. Genau der soll rot werden, wenn jemand
den Abschnitt umbenennt.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.leitfaden import LEITFADENDATEI, lesen, punkte

TEXT = """
# Gesprächsleitfaden

Vorwort, das keine Frage ist.

## Die fünf Fragen

### Ausgangslage

Frage: Wer hat das Problem?
Füllt: Den Kontext.
Achtung: Eine Lösung ist keine Antwort.

### Abnahme

Frage: Woran merkst du,
dass es fertig ist?
Füllt: Das „fertig, wenn …".

## Nach dem Gespräch

### Nachbereitung

Frage: Diese Frage steht im falschen Abschnitt.
"""


class Parser(unittest.TestCase):
    def test_liest_titel_frage_und_felder(self) -> None:
        gefunden = punkte(TEXT)
        self.assertEqual(gefunden[0]["titel"], "Ausgangslage")
        self.assertEqual(gefunden[0]["frage"], "Wer hat das Problem?")
        self.assertEqual(gefunden[0]["fuellt"], "Den Kontext.")
        self.assertEqual(gefunden[0]["achtung"], "Eine Lösung ist keine Antwort.")

    def test_zieht_mehrzeilige_frage_zusammen(self) -> None:
        self.assertEqual(punkte(TEXT)[1]["frage"], "Woran merkst du, dass es fertig ist?")

    def test_nimmt_nur_den_abschnitt_die_fuenf_fragen(self) -> None:
        titel = [p["titel"] for p in punkte(TEXT)]
        self.assertEqual(titel, ["Ausgangslage", "Abnahme"])

    def test_fehlendes_achtung_bleibt_leer_statt_zu_fehlen(self) -> None:
        self.assertEqual(punkte(TEXT)[1]["achtung"], "")

    def test_punkt_ohne_frage_wird_weggelassen(self) -> None:
        ohne = "## Die fünf Fragen\n\n### Leer\n\nFüllt: nichts.\n"
        self.assertEqual(punkte(ohne), [])


class EchteDatei(unittest.TestCase):
    """
    Die Quelle der Wahrheit muss lesbar sein.

    Ohne diesen Test koennte docs/leitfaden.md umbenannt oder umgebaut werden,
    waehrend alle Parser-Tests gruen bleiben — und im Gespraech stuende dann
    eine leere Spalte.
    """

    def test_docs_leitfaden_liefert_fuenf_punkte_mit_frage(self) -> None:
        gefunden = lesen()
        self.assertEqual(len(gefunden), 5)
        for punkt in gefunden:
            self.assertTrue(punkt["frage"].endswith("?"), punkt)

    def test_fehlende_datei_ist_ein_fehler_kein_leerer_leitfaden(self) -> None:
        with self.assertRaises(FileNotFoundError):
            lesen(Path("docs/gibtesnicht.md"))


class KeineZweiteQuelle(unittest.TestCase):
    """
    Abnahmekriterium aus #101: Die Fragen stehen an genau einer Stelle.

    Eine Kopie im JavaScript faellt niemandem auf — bis jemand den Leitfaden
    aendert und im Gespraech die alte Frage vorliest.
    """

    def test_keine_frage_steht_im_javascript(self) -> None:
        js = Path("werkzeuge/leitfaden.js").read_text(encoding="utf-8")
        html = Path("werkzeuge/aufnahme.html").read_text(encoding="utf-8")
        for punkt in lesen():
            self.assertNotIn(punkt["frage"], js)
            self.assertNotIn(punkt["frage"], html)

    def test_kein_titel_steht_im_javascript(self) -> None:
        js = Path("werkzeuge/leitfaden.js").read_text(encoding="utf-8")
        for punkt in lesen():
            self.assertNotIn(punkt["titel"], js)

    def test_leitfadendatei_zeigt_auf_docs(self) -> None:
        self.assertEqual(LEITFADENDATEI.name, "leitfaden.md")
        self.assertEqual(LEITFADENDATEI.parent.name, "docs")


if __name__ == "__main__":
    unittest.main()
