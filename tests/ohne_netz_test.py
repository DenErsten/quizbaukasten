"""
Das Werkzeug laedt nichts nach.

"Ein Gespraech laesst sich nicht wiederholen" (docs/plan.md) heisst auch:
Die Oberflaeche muss ohne Netz funktionieren. Eine Web-Schrift oder eine
Icon-Bibliothek faellt im Buero niemandem auf und genau im Meeting, in dem
das WLAN klemmt, dann doch.

Geprueft wird, was beim Anzeigen der Seite wirklich geladen wird: src- und
href-Ziele im HTML, @import und url() im Stylesheet. Ein "http" in einem
Kommentar oder in einem Python-Import ist kein Ladevorgang.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

WERKZEUGE = Path(__file__).resolve().parent.parent / "werkzeuge"

# src="..." und href="..." — beides laedt beim Zeichnen der Seite.
ZIEL = re.compile(r'(?:src|href)\s*=\s*"([^"]*)"', re.IGNORECASE)
EXTERN = re.compile(r"^(?:https?:)?//|^https?:", re.IGNORECASE)


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
