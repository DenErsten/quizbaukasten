"""
Tests fuer scripts/ausloeser.py.

Die Liste "Was nicht dazugehört" kommt in den Tests aus einem festen Text,
nicht aus docs/plan.md. Sonst wuerde eine Planaenderung diese Tests kippen —
und der Plan soll sich aendern duerfen, ohne dass rot wird, was mit ihm
nichts zu tun hat.
"""

from __future__ import annotations

import unittest

from scripts.ausloeser import ausserhalb_des_scopes, hinweise, pruefe

PLAN = """
## Was nicht dazugehört

- Teams antworten über ihre eigenen Handys (Live-Multiplayer)
- Benutzerkonten und Anmeldung

## Was uns eng macht

- Das hier gehört nicht in die Liste
"""


class Scopeliste(unittest.TestCase):
    def test_liest_nur_den_richtigen_abschnitt(self) -> None:
        punkte = ausserhalb_des_scopes(PLAN)
        self.assertEqual(len(punkte), 2)
        self.assertIn("Handys", punkte[0])
        self.assertNotIn("gehört nicht in die Liste", " ".join(punkte))


class Ausloeser(unittest.TestCase):
    def setUp(self) -> None:
        self.ausserhalb = ausserhalb_des_scopes(PLAN)

    def test_mengenwort_ohne_zahl(self) -> None:
        """Fall 1: „Das muss schnell gehen“ fragt nach der Vergleichsgröße."""
        treffer = pruefe(10.0, "Das muss schnell gehen", self.ausserhalb)

        self.assertIsNotNone(treffer)
        assert treffer is not None
        self.assertEqual(treffer["art"], "mengenwort")
        self.assertIn("Vergleich", treffer["frage"])

    def test_mengenwort_mit_zahl_ist_scharf(self) -> None:
        """Gegenprobe: Mit einer Zahl ist die Anforderung nicht mehr unscharf."""
        self.assertIsNone(
            pruefe(10.0, "Das muss schnell gehen, unter 2 Sekunden", self.ausserhalb)
        )

    def test_technische_aussage_erzeugt_nichts(self) -> None:
        """Fall 2: „Wir bauen das in TypeScript“ ist keine unscharfe Anforderung."""
        self.assertIsNone(pruefe(10.0, "Wir bauen das in TypeScript", self.ausserhalb))

    def test_ausserhalb_des_scopes(self) -> None:
        """Fall 3: Ein Satz gegen „Was nicht dazugehört“ verweist auf den Plan."""
        treffer = pruefe(10.0, "Die Teams antworten dann auf ihren Handys", self.ausserhalb)

        self.assertIsNotNone(treffer)
        assert treffer is not None
        self.assertEqual(treffer["art"], "ausserhalb")
        self.assertIn("docs/plan.md", treffer["grund"])

    def test_scope_schlaegt_mengenwort(self) -> None:
        """Ein Satz, ein Hinweis — und der Scope wiegt schwerer."""
        treffer = pruefe(
            10.0, "Die Teams antworten schnell auf ihren Handys", self.ausserhalb
        )

        assert treffer is not None
        self.assertEqual(treffer["art"], "ausserhalb")


class Wiederholung(unittest.TestCase):
    def setUp(self) -> None:
        self.ausserhalb = ausserhalb_des_scopes(PLAN)

    def test_gleichartig_und_kurz_hintereinander_gibt_einen_hinweis(self) -> None:
        """Fall 4: Zwei gleichartige Sätze kurz hintereinander → ein Hinweis."""
        strom = [
            {"zeit": 10.0, "text": "Das muss schnell gehen"},
            {"zeit": 25.0, "text": "Wirklich schnell, verstehst du"},
        ]

        self.assertEqual(len(list(hinweise(strom, self.ausserhalb, abstand=60.0))), 1)

    def test_nach_dem_abstand_wieder(self) -> None:
        """Gegenprobe: Später im Gespräch zählt dasselbe Thema wieder."""
        strom = [
            {"zeit": 10.0, "text": "Das muss schnell gehen"},
            {"zeit": 200.0, "text": "Und schnell muss es sein"},
        ]

        self.assertEqual(len(list(hinweise(strom, self.ausserhalb, abstand=60.0))), 2)

    def test_verschiedene_arten_unterdruecken_sich_nicht(self) -> None:
        """Ein Scope-Hinweis darf einen Mengenwort-Hinweis nicht verschlucken."""
        strom = [
            {"zeit": 10.0, "text": "Das muss schnell gehen"},
            {"zeit": 12.0, "text": "Die Teams antworten dann auf ihren Handys"},
        ]

        arten = [h["art"] for h in hinweise(strom, self.ausserhalb, abstand=60.0)]
        self.assertEqual(arten, ["mengenwort", "ausserhalb"])


if __name__ == "__main__":
    unittest.main()
