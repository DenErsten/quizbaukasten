"""
Wer darf freigeben — und warum nicht (#119).

GitHub laesst niemanden den eigenen Pull Request freigeben. Das steht
vorher fest und muss nicht erst beim Druecken auffallen.
"""

from __future__ import annotations

import json
import unittest

from werkzeuge import freigabe


def _antwort(prs: list[dict], angemeldet: str = "DenErsten"):
    def aufruf(befehl):
        if befehl[0] == "api":
            return json.dumps({"login": angemeldet})
        return json.dumps(prs)
    return aufruf


def _pr(nummer: int, autor: str, reviews: list | None = None) -> dict:
    return {
        "number": nummer, "title": "T", "body": "Refs #9",
        "reviews": reviews or [], "statusCheckRollup": [], "files": [],
        "author": {"login": autor},
    }


class DarfFreigeben(unittest.TestCase):
    def test_fremder_pr_darf_freigegeben_werden(self) -> None:
        pr = freigabe.offene_prs(aufruf=_antwort([_pr(1, "quizberater")]))[0]

        self.assertTrue(pr["darf_freigeben"])
        self.assertEqual(pr["grund"], "")

    def test_eigener_pr_nicht_und_der_grund_steht_dabei(self) -> None:
        pr = freigabe.offene_prs(aufruf=_antwort([_pr(1, "DenErsten")]))[0]

        self.assertFalse(pr["darf_freigeben"])
        self.assertIn("Selbstfreigabe", pr["grund"])

    def test_schon_freigegeben_nennt_seinen_eigenen_grund(self) -> None:
        pr = freigabe.offene_prs(
            aufruf=_antwort([_pr(1, "quizberater", [{"state": "APPROVED"}])])
        )[0]

        self.assertFalse(pr["darf_freigeben"])
        self.assertIn("Schon freigegeben", pr["grund"])

    def test_ein_grund_ist_nie_leer_wenn_der_knopf_aus_ist(self) -> None:
        """Ein abgeschalteter Knopf ohne Begruendung ist genauso stumm."""
        for autor, reviews in [("DenErsten", []), ("quizberater", [{"state": "APPROVED"}])]:
            pr = freigabe.offene_prs(aufruf=_antwort([_pr(1, autor, reviews)]))[0]

            self.assertFalse(pr["darf_freigeben"])
            self.assertTrue(pr["grund"].strip(), (autor, reviews))

    def test_unbekannte_anmeldung_sperrt_nichts(self) -> None:
        """
        Leer heisst "ich weiss es nicht", nicht "es ist jemand anderes".
        Lieber ein Versuch, der scheitert und es sagt, als ein Knopf, der
        grundlos fehlt.
        """
        def kaputt(befehl):
            if befehl[0] == "api":
                raise RuntimeError("gh nicht angemeldet")
            return json.dumps([_pr(1, "DenErsten")])

        pr = freigabe.offene_prs(aufruf=kaputt)[0]

        self.assertTrue(pr["darf_freigeben"])

    def test_der_autor_wird_mitgeliefert(self) -> None:
        pr = freigabe.offene_prs(aufruf=_antwort([_pr(1, "quizberater")]))[0]

        self.assertEqual(pr["autor"], "quizberater")


if __name__ == "__main__":
    unittest.main()


class DerFehlerStehtAmKnopf(unittest.TestCase):
    """
    Wohin die Meldung geschrieben wird (#119).

    GRENZE DIESES TESTS, ausdruecklich: Er liest den Quelltext von
    freigabe.html, er fuehrt ihn nicht aus. Ein echter Nachweis braeuchte
    einen Browser oder jsdom — eine neue Abhaengigkeit in einer geschuetzten
    Datei, und das waere eine groessere Aenderung als der Fehler, den sie
    absichern soll.

    Was er dafuer wirklich zeigt: Das Ziel der Einfuegung wird aus dem
    gedrueckten Knopf abgeleitet, nicht aus einem festen Element irgendwo
    auf der Seite. Genau das war der Fehler — die Meldung ging in die
    Statuszeile am Seitenende, weit weg vom Knopf.
    """

    def _seite(self) -> str:
        from pathlib import Path

        return (Path(__file__).resolve().parent.parent / "werkzeuge" / "freigabe.html").read_text(
            encoding="utf-8"
        )

    def test_die_meldung_geht_in_den_kasten_des_knopfes(self) -> None:
        seite = self._seite()

        self.assertIn("knopf.parentElement.insertAdjacentHTML", seite)
        self.assertIn("tatFehlerZuHtml(daten.fehler)", seite)

    def test_eine_alte_meldung_wird_vorher_entfernt(self) -> None:
        """Sonst stapeln sich beim zweiten Versuch zwei Meldungen uebereinander."""
        seite = self._seite()

        self.assertIn('knopf.parentElement.querySelector(".tat-fehler")', seite)
        self.assertIn(".remove()", seite)

    def test_die_statuszeile_bleibt_zusaetzlich(self) -> None:
        """
        Sie war nicht falsch, nur zu weit weg. Zwei Orte sind hier besser als
        einer: einer am Knopf, einer fuer den Gesamtzustand der Seite.
        """
        seite = self._seite()

        self.assertIn("stand.textContent = `Fehler: ${daten.fehler}`", seite)

    def test_der_knopf_wird_wieder_bedienbar(self) -> None:
        """Ein gescheiterter Versuch darf den Knopf nicht endgueltig sperren."""
        seite = self._seite()
        nach_fehler = seite.split("tatFehlerZuHtml(daten.fehler)")[1][:300]

        self.assertIn("knopf.disabled = false", nach_fehler)
