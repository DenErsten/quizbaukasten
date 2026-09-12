"""
Tests fuer werkzeuge/freigabe.py — die Freigabe-Konsole (#90).

Der wichtigste Fall ist der, den man am leichtesten vergisst: Die Aufrufe
muessen OHNE GH_TOKEN erfolgen. Laeuft die Freigabe ueber das Bot-Token,
steht in der Historie der Bot, und Gate G2 ist eine Attrappe — am
2026-09-11 zweimal passiert (#10, #57).
"""

from __future__ import annotations

import json
import os
import unittest

from werkzeuge.freigabe import (
    hat_abnahmekriterium,
    issue_freigeben,
    kommentieren,
    offene_issues,
    offene_prs,
    pr_freigeben,
)


class Aufzeichnung:
    """Merkt sich die Aufrufe, statt gh wirklich zu rufen."""

    def __init__(self, antwort: str = "[]"):
        self.antwort = antwort
        self.aufrufe: list[list[str]] = []

    def __call__(self, befehl):
        self.aufrufe.append(list(befehl))
        return self.antwort


class Listen(unittest.TestCase):
    def test_freigegebene_issues_erscheinen_nicht(self) -> None:
        """Fall 1: Was schon freigegeben ist, wartet nicht mehr."""
        roh = json.dumps([
            {"number": 1, "title": "wartet", "body": "## Fertig, wenn …\nx",
             "labels": [{"name": "status:vorschlag"}], "milestone": None},
            {"number": 2, "title": "schon durch", "body": "",
             "labels": [{"name": "status:vorschlag"}, {"name": "status:freigegeben"}],
             "milestone": None},
        ])

        offen = offene_issues(Aufzeichnung(roh))

        self.assertEqual([i["nummer"] for i in offen], [1])

    def test_fehlendes_kriterium_wird_gekennzeichnet(self) -> None:
        """Fall 2: PR #68 ist genau daran gescheitert."""
        roh = json.dumps([
            {"number": 1, "title": "ohne", "body": "nur Text",
             "labels": [{"name": "status:vorschlag"}], "milestone": None},
        ])

        self.assertFalse(offene_issues(Aufzeichnung(roh))[0]["kriterium"])

    def test_rote_checks_werden_benannt(self) -> None:
        """Fall 3: Ein Knopf ohne diese Angabe lädt zum Wegsehen ein (#5)."""
        roh = json.dumps([{
            "number": 9, "title": "PR", "body": "Refs #7", "reviews": [],
            "statusCheckRollup": [
                {"name": "abnahme", "conclusion": "FAILURE"},
                {"name": "pruefen", "conclusion": "SUCCESS"},
                {"name": "review", "conclusion": "FAILURE"},
            ],
            "files": [{"path": "a.py"}],
        }])

        pr = offene_prs(Aufzeichnung(roh))[0]

        self.assertEqual(pr["rote_checks"], ["abnahme", "review"])
        self.assertEqual(pr["issue"], 7)

    def test_pr_ohne_verlinktes_issue(self) -> None:
        roh = json.dumps([{"number": 9, "title": "PR", "body": "ohne Bezug",
                           "reviews": [], "statusCheckRollup": [], "files": []}])

        self.assertIsNone(offene_prs(Aufzeichnung(roh))[0]["issue"])


class OhneBotToken(unittest.TestCase):
    """Fall 4: der Kern."""

    def test_gh_wird_ohne_gh_token_gerufen(self) -> None:
        import subprocess

        gesehen = {}
        echt = subprocess.run

        def mitschreiben(*args, **kwargs):
            gesehen["env"] = kwargs.get("env", {})
            class Ergebnis:
                returncode = 0
                stdout = "[]"
                stderr = ""
            return Ergebnis()

        subprocess.run = mitschreiben
        self.addCleanup(lambda: setattr(subprocess, "run", echt))
        alt = os.environ.get("GH_TOKEN")
        os.environ["GH_TOKEN"] = "bot-token-das-hier-nichts-zu-suchen-hat"
        self.addCleanup(
            lambda: os.environ.__setitem__("GH_TOKEN", alt) if alt else os.environ.pop("GH_TOKEN", None)
        )

        from werkzeuge.freigabe import _gh

        _gh(["issue", "list"])

        self.assertNotIn("GH_TOKEN", gesehen["env"], "Die Freigabe darf nicht dem Bot gehören")
        self.assertNotIn("GITHUB_TOKEN", gesehen["env"])


class Taten(unittest.TestCase):
    def test_issue_freigeben_setzt_das_label(self) -> None:
        a = Aufzeichnung()

        issue_freigeben(42, a)

        self.assertEqual(a.aufrufe, [["issue", "edit", "42", "--add-label", "status:freigegeben"]])

    def test_pr_freigeben_ist_ein_approve(self) -> None:
        a = Aufzeichnung()

        pr_freigeben(7, a)

        self.assertEqual(a.aufrufe, [["pr", "review", "7", "--approve"]])

    def test_kommentar_geht_an_die_richtige_stelle(self) -> None:
        a = Aufzeichnung()

        kommentieren("pr", 5, "Woran misst du das?", a)

        self.assertEqual(a.aufrufe, [["pr", "comment", "5", "--body", "Woran misst du das?"]])

    def test_unbekannte_art_wird_abgewiesen(self) -> None:
        with self.assertRaises(ValueError):
            kommentieren("milestone", 1, "x", Aufzeichnung())


class Fehlerdurchreichung(unittest.TestCase):
    """Fall 5: Ein Knopf, der nichts tut und Erfolg meldet, ist schlimmer als keiner."""

    def test_fehler_von_gh_wird_nicht_verschluckt(self) -> None:
        import subprocess

        echt = subprocess.run

        def scheitert(*args, **kwargs):
            class Ergebnis:
                returncode = 1
                stdout = ""
                stderr = "gh: kein Zugriff"
            return Ergebnis()

        subprocess.run = scheitert
        self.addCleanup(lambda: setattr(subprocess, "run", echt))

        from werkzeuge.freigabe import _gh

        with self.assertRaises(RuntimeError) as fehler:
            _gh(["issue", "list"])
        self.assertIn("kein Zugriff", str(fehler.exception))


class Abnahmekriterium(unittest.TestCase):
    def test_erkennt_die_ueberschrift(self) -> None:
        self.assertTrue(hat_abnahmekriterium("## Fertig, wenn …\n\n… etwas"))
        self.assertTrue(hat_abnahmekriterium("## fertig, WENN"))

    def test_erkennt_ihr_fehlen(self) -> None:
        self.assertFalse(hat_abnahmekriterium("Nur Kontext, kein Kriterium"))
        self.assertFalse(hat_abnahmekriterium(""))
