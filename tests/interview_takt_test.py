"""
Der Takt der Erkennung gegen die Pause im Gespraech (#127).

Am 2026-09-12 ist das erste echte Erstgespraech daran gescheitert: Die
Erkennung arbeitet in Stuecken von fuenf Sekunden, die Pause stand auf drei.
Zwischen zwei Stuecken liegen also immer rund fuenf Sekunden ohne neue Zeile
— das Interview ging nach JEDEM Stueck weiter, mitten im Satz.

Diese Tests spielen den echten Takt nach, statt Zeitpunkte zu erfinden, die
zufaellig passen. Genau das war die Luecke: Die bestehenden Tests bewiesen,
dass die Logik stimmt, nicht dass die Zahlen zueinander passen.
"""

from __future__ import annotations

import unittest

from scripts.interview import (
    PAUSE,
    STILLE_STUECKE,
    WEITER,
    Interview,
)
from scripts.mithoeren import STUECK_SEKUNDEN

ZWEI = [
    {"titel": "Menge", "frage": "Wie viele?", "pruefung": "zahl",
     "rueckfrage": "Kannst du eine Zahl nennen?"},
    {"titel": "Grenze", "frage": "Was nicht?", "pruefung": "abgrenzung",
     "rueckfrage": "Was gehört nicht dazu?"},
]


class DieZahlenPassenZueinander(unittest.TestCase):
    def test_die_pause_ist_laenger_als_ein_stueck(self) -> None:
        """
        Die eine Bedingung, deren Verletzung das Gespraech ruiniert hat.
        Ist sie verletzt, loest das Interview zwischen je zwei Stuecken aus,
        ohne dass jemand eine Pause gemacht haette.
        """
        self.assertGreater(PAUSE, STUECK_SEKUNDEN)

    def test_die_stuecklaenge_hat_genau_eine_quelle(self) -> None:
        """Zwei Zahlen, die dasselbe behaupten, laufen auseinander."""
        import scripts.interview as interview

        self.assertIs(interview.STUECK_SEKUNDEN, STUECK_SEKUNDEN)


class DurchgehendesSprechen(unittest.TestCase):
    """
    Der Fall aus dem echten Gespraech: Jemand spricht ohne Pause, die
    Erkennung liefert im Stuecktakt.
    """

    def test_loest_waehrend_des_sprechens_nie_aus(self) -> None:
        i = Interview(ZWEI)
        ereignisse = []

        # Zwei Minuten durchgehend reden, Stueck fuer Stueck.
        for n in range(24):
            zeit = n * STUECK_SEKUNDEN
            i.gehoert(zeit, f"und dann noch Satz Nummer {n} ohne eine Zahl darin")
            # Zwischen den Stuecken wird mehrmals nachgesehen, wie es die
            # Oberflaeche tut — jede Sekunde.
            for zwischen in range(int(STUECK_SEKUNDEN)):
                ereignis = i.takt(zeit + zwischen)
                if ereignis:
                    ereignisse.append((zeit + zwischen, ereignis["art"]))

        self.assertEqual(ereignisse, [], "Mitten im Sprechen darf nichts passieren")

    def test_mit_der_alten_schwelle_waere_es_schiefgegangen(self) -> None:
        """
        Der Gegenbeweis, damit niemand die Schwelle wieder senkt: Mit einer
        Pause, die kuerzer ist als ein Stueck, feuert es sofort.
        """
        i = Interview(ZWEI, pause=3.0)

        i.gehoert(0.0, "ich rede immer noch und habe keine Zahl genannt")
        ereignis = i.takt(STUECK_SEKUNDEN - 0.1)

        self.assertIsNotNone(ereignis, "Belegt genau den Fehler aus #127")


class GemeldeteStille(unittest.TestCase):
    """
    Stille ist eine Aussage der Erkennung, kein Ausbleiben von Zeilen.
    """

    def test_zwei_stille_stuecke_bringen_das_gespraech_weiter(self) -> None:
        i = Interview(ZWEI)
        i.gehoert(0.0, "etwa 20 Stück")

        self.assertIsNone(i.takt(1.0))

        for n in range(STILLE_STUECKE):
            i.stille((n + 1) * STUECK_SEKUNDEN)

        self.assertEqual(i.takt(2.0)["art"], WEITER)

    def test_ein_einzelnes_stilles_stueck_reicht_nicht(self) -> None:
        """Eine Atempause ist keine Antwort."""
        i = Interview(ZWEI)
        i.gehoert(0.0, "etwa 20 Stück")
        i.stille(STUECK_SEKUNDEN)

        self.assertIsNone(i.takt(1.0))

    def test_weitersprechen_setzt_die_stille_zurueck(self) -> None:
        i = Interview(ZWEI)
        i.gehoert(0.0, "also")
        i.stille(5.0)
        i.gehoert(10.0, "etwa 20 Stück")
        i.stille(15.0)

        self.assertIsNone(i.takt(11.0), "Nach dem Weitersprechen zaehlt es neu")

    def test_stille_ohne_ein_einziges_wort_loest_nichts_aus(self) -> None:
        """
        Wer die Aufnahme startet und erst einmal nachdenkt, bekommt keine
        Rueckfrage auf eine Frage, die er noch gar nicht gehoert hat.
        """
        i = Interview(ZWEI)
        for n in range(10):
            i.stille(n * STUECK_SEKUNDEN)

        self.assertIsNone(i.takt(100.0))


class DerTaktKommtAusDerDatei(unittest.TestCase):
    """Der Weg vom Erkenner bis ins Interview, ohne Mikrofon."""

    class Quelle:
        def __init__(self) -> None:
            self.zeilen: list[dict] = []
            self.takte: list[dict] = []

        def transkript(self) -> list[dict]:
            return list(self.zeilen)

        def takt(self) -> list[dict]:
            return list(self.takte)

    def test_stille_aus_dem_takt_bringt_das_gespraech_weiter(self) -> None:
        from werkzeuge.server import Gespraech

        quelle = self.Quelle()
        jetzt = [0.0]
        g = Gespraech(quelle, uhr=lambda: jetzt[0])
        g.zuruecksetzen()

        quelle.zeilen.append({"zeit": 0, "text": "Weil niemand die Protokolle liest gehen Anforderungen verloren"})
        quelle.takte.append({"zeit": 0, "gesprochen": True})
        jetzt[0] = 1.0

        self.assertIsNone(g.stand()["letztes"])

        quelle.takte.append({"zeit": 5, "gesprochen": False})
        quelle.takte.append({"zeit": 10, "gesprochen": False})
        jetzt[0] = 2.0

        self.assertEqual(g.stand()["letztes"]["art"], WEITER)

    def test_gesprochene_stuecke_bringen_es_nicht_weiter(self) -> None:
        from werkzeuge.server import Gespraech

        quelle = self.Quelle()
        jetzt = [0.0]
        g = Gespraech(quelle, uhr=lambda: jetzt[0])
        g.zuruecksetzen()

        for n in range(6):
            quelle.zeilen.append({"zeit": n * 5, "text": f"weiter reden Teil {n}"})
            quelle.takte.append({"zeit": n * 5, "gesprochen": True})
            jetzt[0] = n + 1.0

            self.assertIsNone(g.stand()["letztes"], f"Stück {n}")

    def test_ein_neues_gespraech_ignoriert_den_alten_takt(self) -> None:
        from werkzeuge.server import Gespraech

        quelle = self.Quelle()
        quelle.takte = [{"zeit": 0, "gesprochen": False}] * 20
        g = Gespraech(quelle, uhr=lambda: 0.0)
        g.zuruecksetzen()

        quelle.zeilen.append({"zeit": 0, "text": "und jetzt rede ich"})

        self.assertIsNone(g.stand()["letztes"], "Stille von vorhin zählt nicht")


if __name__ == "__main__":
    unittest.main()
