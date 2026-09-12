"""
Das Werkzeug laedt nichts nach.

"Ein Gespraech laesst sich nicht wiederholen" (docs/plan.md) heisst auch:
Die Oberflaeche muss ohne Netz funktionieren. Eine Web-Schrift oder eine
Icon-Bibliothek faellt im Buero niemandem auf und genau im Meeting, in dem
das WLAN klemmt, dann doch.

Geprueft wird zweierlei:

1. JEDE Datei unter werkzeuge/ — auch die Python-Dateien — auf Adressen, die
   woanders hinzeigen als auf diesen Rechner.
2. Was beim Anzeigen der Seite wirklich geladen wird: src- und href-Ziele im
   HTML, @import und url() im Stylesheet, die Importe im JavaScript.

Gesucht wird nach dem Schema "http://" bzw. "https://", nicht nach dem Wort
"http". `from http.server import ...` ist keine Adresse, sondern ein
Modulname; eine Regel, die daran haengenbleibt, wuerde beim naechsten Treffer
abgeschaltet und schuetzte dann gar nichts mehr.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

WERKZEUGE = Path(__file__).resolve().parent.parent / "werkzeuge"

# src="..." und href="..." — beides laedt beim Zeichnen der Seite.
ZIEL = re.compile(r'(?:src|href)\s*=\s*"([^"]*)"', re.IGNORECASE)
EXTERN = re.compile(r"^(?:https?:)?//|^https?:", re.IGNORECASE)


# Jede Adresse in einer Datei unter werkzeuge/, egal in welcher Sprache.
ADRESSE = re.compile(r"https?://[^\s\"'<>)\]]+", re.IGNORECASE)
EIGENER_RECHNER = ("http://127.0.0.1", "http://localhost", "https://127.0.0.1", "https://localhost")


class KeineFremdenAdressen(unittest.TestCase):
    """
    Alle Dateien unter werkzeuge/, ohne Ausnahme.

    Abnahmekriterium aus #106. Erlaubt ist genau eine Sorte Adresse: die auf
    diesen Rechner. Alles andere ist entweder ein Ladevorgang oder wird
    frueher oder spaeter einer.
    """

    def test_jede_datei_zeigt_nur_auf_diesen_rechner(self) -> None:
        geprueft = 0
        for datei in sorted(WERKZEUGE.rglob("*")):
            if not datei.is_file():
                continue
            try:
                text = datei.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            geprueft += 1
            for adresse in ADRESSE.findall(text):
                self.assertTrue(
                    adresse.lower().startswith(EIGENER_RECHNER),
                    f"{datei.name} nennt eine fremde Adresse: {adresse}",
                )

        # Ohne diese Zeile wuerde der Test auch dann gruen, wenn der Ordner
        # leer waere oder der Pfad nicht mehr stimmt.
        self.assertGreaterEqual(geprueft, 10, "Zu wenige Dateien geprüft — stimmt der Pfad noch?")


class OhneNetz(unittest.TestCase):
    def test_html_laedt_nur_aus_dem_eigenen_ordner(self) -> None:
        for seite in sorted(WERKZEUGE.glob("*.html")):
            for ziel in ZIEL.findall(seite.read_text(encoding="utf-8")):
                self.assertFalse(
                    EXTERN.match(ziel.strip()),
                    f"{seite.name} lädt von aussen: {ziel}",
                )

    def test_stylesheet_importiert_nichts(self) -> None:
        css = (WERKZEUGE / "stil.css").read_text(encoding="utf-8")

        self.assertNotIn("@import", css)
        self.assertNotIn("url(http", css.replace(" ", ""))

    def test_javascript_holt_keine_bibliothek(self) -> None:
        for modul in sorted(WERKZEUGE.glob("*.js")):
            text = modul.read_text(encoding="utf-8")
            for zeile in text.splitlines():
                if zeile.strip().startswith(("import ", "export ")) and "from" in zeile:
                    self.assertIn(
                        './',
                        zeile,
                        f"{modul.name} importiert nicht aus dem eigenen Ordner: {zeile.strip()}",
                    )


class SchriftAusDemSystem(unittest.TestCase):
    """Die Rundung kommt aus einer Schrift, die schon auf dem Rechner liegt."""

    def test_stil_nennt_eine_runde_systemschrift_und_einen_ersatz(self) -> None:
        css = (WERKZEUGE / "stil.css").read_text(encoding="utf-8")

        self.assertIn("Hiragino Maru Gothic ProN", css)
        self.assertIn("sans-serif", css)


if __name__ == "__main__":
    unittest.main()
