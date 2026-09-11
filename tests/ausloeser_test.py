"""
Tests fuer scripts/auslöser.py.

Deckt die vier Faelle aus Issue #36 ab: Mengenwort ohne Zahl, eine negative
Gegenprobe (technische Aussagen sind nicht unscharf), Widerspruch zu
docs/plan.md, und die Deduplikation gleichartiger Hinweise.
"""

from __future__ import annotations

import unittest

from scripts.auslöser import ausloeser


def satz(text: str, zeit: float = 0.0) -> dict:
    return {"zeit": zeit, "text": text}


class Ausloeser(unittest.TestCase):
    def test_mengenwort_ohne_zahl_fragt_nach_vergleichsgroesse(self) -> None:
        """Fall 1: "Das muss schnell gehen" erzeugt einen Hinweis mit Vergleichsfrage."""
        hinweise = list(ausloeser([satz("Das muss schnell gehen")]))

        self.assertEqual(len(hinweise), 1)
        self.assertEqual(hinweise[0]["muster"], "mengenwort")
        self.assertEqual(hinweise[0]["frage"], "Schnell im Vergleich wozu?")

    def test_technische_aussage_erzeugt_keinen_hinweis(self) -> None:
        """Fall 2: "Wir bauen das in TypeScript" ist nicht unscharf im Sinne des Auslösers."""
        hinweise = list(ausloeser([satz("Wir bauen das in TypeScript")]))

        self.assertEqual(hinweise, [])

    def test_widerspruch_zu_plan_verweist_auf_was_nicht_dazugehoert(self) -> None:
        """Fall 3: Live-Multiplayer-Andeutung verweist auf docs/plan.md."""
        hinweise = list(ausloeser([satz("Die Teams antworten dann auf ihren Handys")]))

        self.assertEqual(len(hinweise), 1)
        self.assertEqual(hinweise[0]["muster"], "plan")
        self.assertIn("docs/plan.md", hinweise[0]["frage"])
        self.assertIn("Was nicht dazugehört", hinweise[0]["frage"])

    def test_gleichartige_saetze_erzeugen_nur_einen_hinweis(self) -> None:
        """Fall 4: Zwei aehnliche Saetze kurz hintereinander erzeugen einen Hinweis, nicht zwei."""
        hinweise = list(
            ausloeser(
                [
                    satz("Das muss schnell gehen", zeit=0.0),
                    satz("Das muss echt schnell gehen", zeit=3.0),
                ]
            )
        )

        self.assertEqual(len(hinweise), 1)

    def test_anderes_thema_dazwischen_gibt_das_alte_frei(self) -> None:
        """Gegenprobe zu Fall 4: Ein andersartiger Hinweis dazwischen hebt die Sperre auf."""
        hinweise = list(
            ausloeser(
                [
                    satz("Das muss schnell gehen", zeit=0.0),
                    satz("Die Teams antworten dann auf ihren Handys", zeit=5.0),
                    satz("Das muss schnell gehen", zeit=10.0),
                ]
            )
        )

        self.assertEqual([h["muster"] for h in hinweise], ["mengenwort", "plan", "mengenwort"])

    def test_zusage_ohne_termin_fragt_nach_dem_termin(self) -> None:
        """Zusatzfall zu Muster 2: Eine Zusage ohne Datum fragt nach dem Termin."""
        hinweise = list(ausloeser([satz("Das machen wir noch")]))

        self.assertEqual(len(hinweise), 1)
        self.assertEqual(hinweise[0]["muster"], "zusage")

    def test_zusage_mit_termin_erzeugt_keinen_hinweis(self) -> None:
        """Gegenprobe: Nennt der Satz schon einen Termin, ist er nicht unscharf."""
        hinweise = list(ausloeser([satz("Das machen wir noch bis Donnerstag")]))

        self.assertEqual(hinweise, [])

    def test_widerspruch_zu_pilotnutzer_verweist_auf_dessen_dokument(self) -> None:
        """Muster 4: Eine Netzabhaengigkeit am Quizabend widerspricht docs/pilotnutzer.md."""
        hinweise = list(ausloeser([satz("Das braucht dann Internet am Quizabend")]))

        self.assertEqual(len(hinweise), 1)
        self.assertEqual(hinweise[0]["muster"], "pilotnutzer")
        self.assertIn("docs/pilotnutzer.md", hinweise[0]["frage"])


if __name__ == "__main__":
    unittest.main()
