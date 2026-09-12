"""
Tests fuer die Fortschrittsansicht (#73).

Die Zaehlung liegt in werkzeuge/freigabe.py, die Tests aber hier: Das
Abnahmekriterium nennt diese Datei woertlich, und ein Kriterium, das eine
Datei nennt, ist nicht erfuellt, wenn die Datei woanders liegt. abnahme hat
PR #98 genau deswegen blockiert.
"""

from __future__ import annotations

import json
import unittest


class Fortschritt(unittest.TestCase):
    """
    #73: Was aus jeder Anforderung geworden ist. Die Faelle 3 und 4 sind die,
    an denen solche Uebersichten sonst luegen — was nicht ins Raster passt,
    faellt heraus, und die Summe stimmt trotzdem.
    """

    def _daten(self, issues, prs=()):
        from werkzeuge.freigabe import fortschritt

        antworten = [json.dumps(issues), json.dumps(list(prs))]

        def aufruf(befehl):
            return antworten.pop(0)

        return fortschritt(aufruf)

    def _issue(self, nummer, labels, meilenstein="P1", zu=False, titel="X"):
        return {
            "number": nummer, "title": titel,
            "labels": [{"name": l} for l in labels],
            "milestone": {"title": meilenstein} if meilenstein else None,
            "state": "CLOSED" if zu else "OPEN",
        }

    def test_zaehlt_je_meilenstein(self) -> None:
        """Fall 1."""
        f = self._daten([
            self._issue(1, ["status:vorschlag"]),
            self._issue(2, ["status:vorschlag", "status:freigegeben"]),
            self._issue(3, ["status:vorschlag"], zu=True),
        ])

        z = f["meilensteine"][0]["zaehlung"]
        self.assertEqual((z["vorgeschlagen"], z["freigegeben"], z["geschlossen"]), (1, 1, 1))

    def test_offener_pr_macht_in_arbeit(self) -> None:
        """Fall 2: Sonst staende es fuer immer unter 'freigegeben'."""
        f = self._daten(
            [self._issue(7, ["status:vorschlag", "status:freigegeben"])],
            [{"body": "Etwas.\n\nRefs #7\n"}],
        )

        z = f["meilensteine"][0]["zaehlung"]
        self.assertEqual(z["in_arbeit"], 1)
        self.assertEqual(z["freigegeben"], 0)

    def test_pruefungen_stehen_getrennt(self) -> None:
        """Fall 3: Sie durchlaufen keinen PR und waeren sonst ewig 'freigegeben'."""
        f = self._daten([self._issue(9, ["art:pruefung"])])

        self.assertEqual(f["meilensteine"][0]["zaehlung"]["pruefung"], 1)

    def test_ohne_meilenstein_verschwindet_nichts(self) -> None:
        """Fall 4: Was nicht ins Raster passt, faellt sonst heraus."""
        f = self._daten([self._issue(5, ["status:vorschlag"], meilenstein=None)])

        namen = [m["titel"] for m in f["meilensteine"]]
        self.assertIn("ohne Meilenstein", namen)

    def test_lageberichte_zaehlen_nicht_als_arbeit(self) -> None:
        """Automatisch erzeugte Uebersichten sind keine Anforderungen."""
        f = self._daten([
            self._issue(1, ["lagebericht"], meilenstein=None),
            self._issue(2, ["status:vorschlag"], meilenstein=None),
        ])

        self.assertEqual(len(f["meilensteine"][0]["anforderungen"]), 1)
