"""
Tests fuer scripts/pfad_pruefung.py — Gate G3.

Dieses Skript entscheidet, ob ein PR geschuetzte Pfade anfasst und ob eine
menschliche Freigabe vorliegt. Es ist der Code hinter jeder Aussage dieses
Repos ueber CLAUDE.md, die Workflows und die Testverzeichnisse — und hatte
bis #47 keinen einzigen Test.

Die Muster kommen hier aus einer festen Liste, nicht aus
.github/geschuetzte-pfade.txt. Sonst wuerde jede Aenderung an der echten
Liste diese Tests kippen, und die Liste soll sich aendern duerfen.
"""

from __future__ import annotations

import unittest

from scripts.pfad_pruefung import menschliche_freigaben, nur_neue_zeilen, passt, treffer
from datetime import date
from scripts.pfad_pruefung import aufbauphase_aktiv, aufbauphase_lesen, filtere_aufbauphase

MUSTER = [
    "CLAUDE.md",
    ".claude/**",
    ".github/workflows/**",
    "scripts/menschen.txt",
    "docs/plan.md",
    "tests/**",
    "**/*_test.*",
    "**/*.test.*",
    "package.json",
]


class Musterabgleich(unittest.TestCase):
    def test_workflow_ist_geschuetzt(self) -> None:
        """Fall 1."""
        self.assertTrue(passt(".github/workflows/pr-pruefung.yml", ".github/workflows/**"))

    def test_quellcode_ist_nicht_geschuetzt(self) -> None:
        """Fall 2."""
        for muster in MUSTER:
            self.assertFalse(passt("src/quiz.ts", muster), f"src/quiz.ts vs {muster}")

    def test_verzeichnis_selbst_ist_nicht_geschuetzt(self) -> None:
        """Das Muster meint den Inhalt, nicht den Namen des Ordners."""
        self.assertFalse(passt(".github/workflowsX/datei.yml", ".github/workflows/**"))

    def test_muster_ohne_pfadtrenner_greift_tief(self) -> None:
        """package.json auch in einem Unterprojekt — so ist es dokumentiert."""
        self.assertTrue(passt("werkzeuge/unterprojekt/package.json", "package.json"))

    def test_treffer_nennt_das_erste_passende_muster(self) -> None:
        gefunden = treffer(["CLAUDE.md", "src/quiz.ts", "docs/plan.md"], MUSTER)

        self.assertEqual([d for d, _ in gefunden], ["CLAUDE.md", "docs/plan.md"])

    def test_neue_python_tests_gelten_als_testdatei(self) -> None:
        """Die Dateien aus #35 und #36 muessen unter die Testmuster fallen."""
        self.assertTrue(
            any(passt("tests/mithoeren_test.py", m) for m in MUSTER),
            "tests/mithoeren_test.py wird von keinem Testmuster erfasst",
        )


class ReineErgaenzung(unittest.TestCase):
    def test_nur_hinzugefuegt(self) -> None:
        """Fall 3."""
        pr = {"files": [{"path": "tests/quiz.test.ts", "additions": 30, "deletions": 0}]}

        self.assertTrue(nur_neue_zeilen(pr, "tests/quiz.test.ts"))

    def test_mit_loeschung(self) -> None:
        """Fall 4 — der wichtigste. Hier wird das Netz gelockert."""
        pr = {"files": [{"path": "tests/quiz.test.ts", "additions": 30, "deletions": 1}]}

        self.assertFalse(nur_neue_zeilen(pr, "tests/quiz.test.ts"))

    def test_datei_gar_nicht_im_pr(self) -> None:
        """Im Zweifel nicht durchlassen."""
        self.assertFalse(nur_neue_zeilen({"files": []}, "tests/quiz.test.ts"))

    def test_leerer_diff_ist_keine_ergaenzung(self) -> None:
        """additions == 0 ist nichts Hinzugefuegtes, auch ohne Loeschung."""
        pr = {"files": [{"path": "tests/quiz.test.ts", "additions": 0, "deletions": 0}]}

        self.assertFalse(nur_neue_zeilen(pr, "tests/quiz.test.ts"))

    def test_fehlende_angaben_gelten_als_loeschung(self) -> None:
        """Ein PR-JSON ohne additions/deletions darf nicht durchrutschen."""
        pr = {"files": [{"path": "tests/quiz.test.ts"}]}

        self.assertFalse(nur_neue_zeilen(pr, "tests/quiz.test.ts"))


class Freigaben(unittest.TestCase):
    MENSCHEN = ["DenErsten"]

    def test_freigabe_eines_menschen_zaehlt(self) -> None:
        """Fall 5."""
        pr = {"reviews": [{"author": {"login": "DenErsten"}, "state": "APPROVED"}]}

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), ["DenErsten"])

    def test_spaeter_verworfene_freigabe_zaehlt_nicht(self) -> None:
        """Fall 6. dismiss_stale_reviews steht auf true — der Fall ist haeufig."""
        pr = {
            "reviews": [
                {"author": {"login": "DenErsten"}, "state": "APPROVED"},
                {"author": {"login": "DenErsten"}, "state": "DISMISSED"},
            ]
        }

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), [])

    def test_erneute_freigabe_nach_verwerfen_zaehlt_wieder(self) -> None:
        """Der Normalfall nach jedem zweiten Push."""
        pr = {
            "reviews": [
                {"author": {"login": "DenErsten"}, "state": "APPROVED"},
                {"author": {"login": "DenErsten"}, "state": "DISMISSED"},
                {"author": {"login": "DenErsten"}, "state": "APPROVED"},
            ]
        }

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), ["DenErsten"])

    def test_freigabe_eines_bots_zaehlt_nicht(self) -> None:
        """Der Agent arbeitet als quizberater und steht nicht in menschen.txt."""
        pr = {"reviews": [{"author": {"login": "quizberater"}, "state": "APPROVED"}]}

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), [])

    def test_kommentar_verwirft_eine_freigabe_nicht(self) -> None:
        """Ein COMMENTED nach dem APPROVED darf die Freigabe nicht loeschen."""
        pr = {
            "reviews": [
                {"author": {"login": "DenErsten"}, "state": "APPROVED"},
                {"author": {"login": "DenErsten"}, "state": "COMMENTED"},
            ]
        }

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), ["DenErsten"])

    def test_aenderungswunsch_hebt_die_freigabe_auf(self) -> None:
        pr = {
            "reviews": [
                {"author": {"login": "DenErsten"}, "state": "APPROVED"},
                {"author": {"login": "DenErsten"}, "state": "CHANGES_REQUESTED"},
            ]
        }

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), [])

    def test_review_ohne_autor_bricht_nicht(self) -> None:
        pr = {"reviews": [{"state": "APPROVED"}, {"author": None, "state": "APPROVED"}]}

        self.assertEqual(menschliche_freigaben(pr, self.MENSCHEN), [])


if __name__ == "__main__":
    unittest.main()


class WaechterSchuetztSichSelbst(unittest.TestCase):
    """
    Gegen die echte Liste, nicht gegen MUSTER oben.

    Die anderen Tests nehmen eine feste Musterliste, damit eine Aenderung an
    .github/geschuetzte-pfade.txt sie nicht kippt. Hier ist es umgekehrt: Es
    geht genau um den Inhalt der echten Datei. Faellt eine dieser Zeilen bei
    einer spaeteren Aufraeumaktion weg, soll es rot werden — sonst merkt es
    niemand, so wie es bis #52 niemand gemerkt hat.
    """

    DURCHSETZER = [
        "scripts/pfad_pruefung.py",
        "scripts/setup-repo.sh",
        "scripts/setup-labels.sh",
    ]

    def test_durchsetzende_skripte_sind_geschuetzt(self) -> None:
        from scripts.pfad_pruefung import MUSTERDATEI, zeilen

        muster = zeilen(MUSTERDATEI)
        for datei in self.DURCHSETZER:
            with self.subTest(datei=datei):
                self.assertTrue(
                    any(passt(datei, m) for m in muster),
                    f"{datei} setzt Leitplanken durch, steht aber unter keinem Muster",
                )

    def test_gewoehnliche_skripte_bleiben_frei(self) -> None:
        """Die Gegenprobe zu A: scripts/** waere zu viel gewesen."""
        from scripts.pfad_pruefung import MUSTERDATEI, zeilen

        muster = zeilen(MUSTERDATEI)
        for datei in ("scripts/mithoeren.py", "scripts/ausloeser.py"):
            with self.subTest(datei=datei):
                self.assertFalse(
                    any(passt(datei, m) for m in muster),
                    f"{datei} ist gewöhnlicher Code und sollte ohne Freigabe änderbar sein",
                )


class Aufbauphase(unittest.TestCase):
    """
    Befristete Ausnahme mit Ablaufdatum, siehe Issue #61 und
    .github/aufbauphase.txt.

    Feste Werte hier, nicht die echte Datei — aus demselben Grund wie bei
    MUSTER oben: eine Verlaengerung des Datums soll diese Tests nicht kippen.
    """

    ABLAUF = date(2026, 9, 30)
    AUFBAU_MUSTER = [".github/workflows/**", ".claude/**"]

    def test_vor_dem_datum_ist_aufbaupfad_frei(self) -> None:
        """Fall: vor dem Datum frei."""
        gefunden = [(".github/workflows/pr-pruefung.yml", ".github/workflows/**")]
        aktiv = aufbauphase_aktiv(self.ABLAUF, date(2026, 9, 29))

        rest, durchgelassen = filtere_aufbauphase(gefunden, self.AUFBAU_MUSTER, aktiv)

        self.assertTrue(aktiv)
        self.assertEqual(rest, [])
        self.assertEqual(durchgelassen, [".github/workflows/pr-pruefung.yml"])

    def test_nach_dem_datum_ist_aufbaupfad_blockiert(self) -> None:
        """Fall: nach dem Datum blockiert."""
        gefunden = [(".github/workflows/pr-pruefung.yml", ".github/workflows/**")]
        aktiv = aufbauphase_aktiv(self.ABLAUF, date(2026, 10, 1))

        rest, durchgelassen = filtere_aufbauphase(gefunden, self.AUFBAU_MUSTER, aktiv)

        self.assertFalse(aktiv)
        self.assertEqual(rest, gefunden)
        self.assertEqual(durchgelassen, [])

    def test_tests_bleiben_in_beiden_faellen_gesperrt(self) -> None:
        """Fall: tests/** in beiden Faellen blockiert."""
        gefunden = [("tests/quiz_test.py", "tests/**")]

        for heute in (date(2026, 9, 29), date(2026, 10, 1)):
            with self.subTest(heute=heute):
                aktiv = aufbauphase_aktiv(self.ABLAUF, heute)
                rest, durchgelassen = filtere_aufbauphase(gefunden, self.AUFBAU_MUSTER, aktiv)

                self.assertEqual(rest, gefunden)
                self.assertEqual(durchgelassen, [])

    def test_ohne_datum_ist_keine_aufbauphase_aktiv(self) -> None:
        """Fehlt das Ablaufdatum, ist die sichere Seite: keine Ausnahme."""
        self.assertFalse(aufbauphase_aktiv(None, date(2026, 9, 1)))

    def test_aufbauphase_lesen_parst_datum_und_muster(self) -> None:
        import tempfile
        from pathlib import Path

        inhalt = (
            "# Kommentar\n"
            "aufbauphase-bis: 2026-09-30\n"
            "\n"
            ".github/workflows/**\n"
            ".claude/**\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(inhalt)
            pfad = Path(f.name)

        try:
            datum, muster = aufbauphase_lesen(pfad)
        finally:
            pfad.unlink()

        self.assertEqual(datum, date(2026, 9, 30))
        self.assertEqual(muster, [".github/workflows/**", ".claude/**"])

    def test_aufbauphase_lesen_ohne_datei_ergibt_keine_ausnahme(self) -> None:
        from pathlib import Path

        datum, muster = aufbauphase_lesen(Path("/nicht/vorhanden/aufbauphase.txt"))

        self.assertIsNone(datum)
        self.assertEqual(muster, [])
