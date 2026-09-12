"""
Tests fuer das gefuehrte Erstgespraech (#114).

Kein Whisper, kein Mikrofon, keine Uhr: Das Interview bekommt Text und
Zeitpunkte als Zahlen uebergeben. Dadurch laesst sich ein ganzes Gespraech
Schritt fuer Schritt durchspielen — auch die Faelle, die man im echten
Gespraech nur schwer herstellt.
"""

from __future__ import annotations

import unittest

from scripts.interview import (
    ENDE,
    NACHFRAGEN,
    OFFEN,
    PAUSE,
    WEITER,
    Interview,
    UnbekanntePruefung,
    prueft_abgrenzung,
    prueft_fehlerfall,
    prueft_pruefbar,
    prueft_zahl,
)
from scripts.leitfaden import lesen

ZWEI = [
    {"titel": "Menge", "frage": "Wie viele?", "pruefung": "zahl",
     "rueckfrage": "Kannst du eine Zahl nennen?"},
    {"titel": "Grenze", "frage": "Was nicht?", "pruefung": "abgrenzung",
     "rueckfrage": "Was gehört nicht dazu?"},
]


class Pruefungen(unittest.TestCase):
    def test_zahl_erkennt_ziffern_und_zahlwoerter(self) -> None:
        self.assertTrue(prueft_zahl("etwa 20 Stück"))
        self.assertTrue(prueft_zahl("so drei bis vier"))
        self.assertTrue(prueft_zahl("täglich"))

    def test_zahl_laesst_mengenwoerter_nicht_durch(self) -> None:
        """Genau der Fall, der den Zwischenruf ausgeloest hat — nur ohne Einwurf."""
        for satz in ["einige", "ein paar Leute", "nicht so viele", "mehrere"]:
            self.assertFalse(prueft_zahl(satz), satz)

    def test_pruefbar_will_eine_bedingung_nicht_einen_wunsch(self) -> None:
        self.assertTrue(prueft_pruefbar("Fertig ist es, wenn die Liste nach dem Speichern erscheint"))
        self.assertFalse(prueft_pruefbar("Es soll einfach gut sein"))

    def test_abgrenzung_will_eine_verneinung(self) -> None:
        self.assertTrue(prueft_abgrenzung("Anmeldung brauchen wir nicht"))
        self.assertFalse(prueft_abgrenzung("Alles Mögliche wäre schön"))

    def test_fehlerfall_will_den_fall_nicht_den_sonnenschein(self) -> None:
        self.assertTrue(prueft_fehlerfall("Wenn das Netz ausfällt, soll es lokal weiterlaufen"))
        self.assertFalse(prueft_fehlerfall("Dann freuen sich alle"))


class MittenImSatzPassiertNichts(unittest.TestCase):
    """
    Der ganze Unterschied zum Zwischenruf. `ausloeser.py` haette hier
    zugeschlagen, sobald das Wort fiel.
    """

    def test_kein_ereignis_solange_gesprochen_wird(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "Wir brauchen einige")

        self.assertIsNone(i.takt(1.0))
        self.assertIsNone(i.takt(2.9))

        i.gehoert(3.0, "also ungefähr 20 Stück pro Abend")

        self.assertIsNone(i.takt(5.0), "Die Uhr muss beim Weitersprechen neu laufen")

    def test_erst_die_pause_entscheidet(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "etwa 20 Stück")

        self.assertIsNone(i.takt(2.0))
        self.assertEqual(i.takt(3.1)["art"], WEITER)

    def test_stille_vor_dem_ersten_wort_ist_nachdenken(self) -> None:
        i = Interview(ZWEI, pause=3.0)

        self.assertIsNone(i.takt(60.0))
        self.assertEqual(i.stand()["nummer"], 1)

    def test_die_pause_ist_einstellbar_und_hat_einen_vorgabewert(self) -> None:
        self.assertEqual(PAUSE, 3.0)


class HoechstensEineRueckfrage(unittest.TestCase):
    def test_erst_nachfragen_dann_weiter(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "so einige halt")
        erstes = i.takt(4.0)

        self.assertEqual(erstes["art"], NACHFRAGEN)
        self.assertEqual(erstes["rueckfrage"], "Kannst du eine Zahl nennen?")

        i.gehoert(5.0, "kann ich nicht sagen")
        zweites = i.takt(9.0)

        self.assertEqual(zweites["art"], OFFEN)
        self.assertEqual(i.stand()["offene"], ["Menge"])

    def test_nach_der_rueckfrage_darf_man_ueberlegen(self) -> None:
        """
        Die Stilleuhr laeuft neu. Sonst kaeme das "offen" im selben Takt
        hinterher, ohne dass jemand antworten konnte.
        """
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "einige")
        i.takt(4.0)

        self.assertIsNone(i.takt(4.1))
        self.assertIsNone(i.takt(20.0))

    def test_eine_gute_antwort_auf_die_rueckfrage_zaehlt(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "einige")
        i.takt(4.0)
        i.gehoert(5.0, "sagen wir 30 pro Woche")

        self.assertEqual(i.takt(9.0)["art"], WEITER)
        self.assertEqual(i.stand()["offene"], [])

    def test_nie_zwei_rueckfragen_zur_selben_frage(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        arten = []
        for n in range(6):
            i.gehoert(n * 10.0, "weiß nicht")
            ereignis = i.takt(n * 10.0 + 4.0)
            if ereignis:
                arten.append(ereignis["art"])

        self.assertEqual(arten.count(NACHFRAGEN), 1, arten)


class DasEndeKommtVonSelbst(unittest.TestCase):
    def test_nach_dem_letzten_punkt_ist_schluss(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "20 Stück")
        i.takt(4.0)
        i.gehoert(5.0, "Anmeldung brauchen wir nicht")
        letztes = i.takt(9.0)

        self.assertEqual(letztes["art"], ENDE)
        self.assertTrue(i.stand()["fertig"])

    def test_danach_passiert_nichts_mehr(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        for text in ["20 Stück", "ohne Anmeldung"]:
            i.gehoert(0.0, text)
            i.takt(4.0)

        i.gehoert(100.0, "und noch eine Idee")

        self.assertIsNone(i.takt(200.0), "Das Interview fragt nicht nach Details")

    def test_es_fragt_nur_so_viele_fragen_wie_im_leitfaden_stehen(self) -> None:
        i = Interview(ZWEI, pause=3.0)

        self.assertEqual(i.stand()["von"], 2)


class DerLeitfadenSteuert(unittest.TestCase):
    def test_der_echte_leitfaden_laesst_sich_fuehren(self) -> None:
        """
        Jeder Punkt in docs/leitfaden.md nennt eine Pruefung, die es gibt.
        Ohne diesen Test wuerde ein Tippfehler dort zu einem Punkt fuehren,
        der im Gespraech nie nachfragt — und das saehe aus wie eine gute
        Antwort.
        """
        i = Interview(lesen())

        self.assertEqual(i.stand()["von"], 5)

    def test_jeder_punkt_hat_eine_rueckfrage(self) -> None:
        for punkt in lesen():
            self.assertTrue(punkt["rueckfrage"].strip(), punkt["titel"])

    def test_unbekannte_pruefung_ist_ein_fehler_kein_durchwinken(self) -> None:
        with self.assertRaises(UnbekanntePruefung):
            Interview([{"titel": "X", "frage": "F?", "pruefung": "hellsehen", "rueckfrage": "R"}])

    def test_fehlende_pruefung_ist_auch_ein_fehler(self) -> None:
        with self.assertRaises(UnbekanntePruefung):
            Interview([{"titel": "X", "frage": "F?", "pruefung": "", "rueckfrage": "R"}])


class Stand(unittest.TestCase):
    def test_zeigt_frage_nummer_und_bisheriges(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "20 Stück")
        i.takt(4.0)
        stand = i.stand()

        self.assertEqual(stand["nummer"], 2)
        self.assertEqual(stand["frage"], "Was nicht?")
        self.assertEqual(stand["beantwortet"][0]["titel"], "Menge")
        self.assertFalse(stand["beantwortet"][0]["offen"])

    def test_zeigt_die_rueckfrage_solange_sie_offen_ist(self) -> None:
        i = Interview(ZWEI, pause=3.0)
        i.gehoert(0.0, "einige")

        self.assertEqual(i.stand()["rueckfrage"], "")
        i.takt(4.0)
        self.assertEqual(i.stand()["rueckfrage"], "Kannst du eine Zahl nennen?")
        self.assertTrue(i.stand()["nachgefragt"])


if __name__ == "__main__":
    unittest.main()


class GespraechAmTranskript(unittest.TestCase):
    """
    Das Interview im Server (#114).

    Es bekommt keinen eigenen Draht zum Mikrofon, sondern liest, was
    mithoeren.py ohnehin schreibt. Die Uhr ist eingesetzt, damit ein ganzes
    Gespraech in Millisekunden ablaeuft statt in Sekunden.
    """

    class Transkript:
        def __init__(self) -> None:
            self.zeilen: list[dict] = []

        def transkript(self) -> list[dict]:
            return list(self.zeilen)

    def _gespraech(self):
        from werkzeuge.server import Gespraech

        self.quelle = self.Transkript()
        self.jetzt = [0.0]
        g = Gespraech(self.quelle, uhr=lambda: self.jetzt[0])
        g.zuruecksetzen()
        return g

    def test_fuehrt_durch_die_fragen_aus_dem_leitfaden(self) -> None:
        g = self._gespraech()

        self.assertTrue(g.stand()["laeuft"])
        self.assertEqual(g.stand()["von"], 5)

    def test_ein_neues_gespraech_ignoriert_das_bisherige_transkript(self) -> None:
        """
        Die Transkriptdatei laeuft ueber den ganzen Tag, das Gespraech nicht.
        Ohne diesen Schnitt beantwortete das Vormittagsgespraech die Fragen
        des Nachmittagsgespraechs.
        """
        g = self._gespraech()
        self.quelle.zeilen.append({"zeit": 0, "text": "Das war heute Morgen und geht niemanden mehr etwas an"})
        g.zuruecksetzen()
        self.jetzt[0] = 100.0

        self.assertIsNone(g.stand()["letztes"])
        self.assertEqual(g.stand()["nummer"], 1)

    def test_erst_die_pause_bringt_das_gespraech_weiter(self) -> None:
        g = self._gespraech()
        self.quelle.zeilen.append(
            {"zeit": 0, "text": "Niemand liest die Protokolle und die Anforderungen gehen dabei verloren"}
        )
        self.jetzt[0] = 1.0

        self.assertIsNone(g.stand()["letztes"])

        self.jetzt[0] = 5.0

        self.assertEqual(g.stand()["letztes"]["art"], WEITER)

    def test_ein_kaputter_leitfaden_verhindert_die_aufnahme_nicht(self) -> None:
        """
        Aber er sieht auch nicht aus, als liefe ein Gespraech. Die Aufnahme
        ist das Wichtige — ein Gespraech laesst sich nicht wiederholen.
        """
        from werkzeuge.server import Gespraech

        def kaputt():
            return [{"titel": "X", "frage": "F?", "pruefung": "hellsehen", "rueckfrage": "R"}]

        g = Gespraech(self.Transkript(), punkte_lesen=kaputt)
        g.zuruecksetzen()
        stand = g.stand()

        self.assertFalse(stand["laeuft"])
        self.assertIn("hellsehen", stand["fehler"])


class KeinZwischenrufMehr(unittest.TestCase):
    """
    ausloeser.py haengt nicht mehr in der Aufnahme (#114).

    Geprueft wird der Quelltext, nicht das Verhalten: Ein echter Start
    braeuchte ein Mikrofon. Die Stelle ist klein genug, dass das Lesen
    aussagekraeftig ist — und gross genug, dass ein Wiedereinhaengen auffaellt.
    """

    def test_die_pipeline_startet_ausloeser_nicht(self) -> None:
        import inspect

        from werkzeuge import server

        quelle = inspect.getsource(server._pipeline_starten)

        self.assertNotIn('"ausloeser.py"', quelle)
        self.assertIn('"mithoeren.py"', quelle)

    def test_ausloeser_bleibt_im_repo(self) -> None:
        """Nicht geloescht, nur abgehaengt. Was aus ihm wird, entscheidet ein Issue."""
        from pathlib import Path

        self.assertTrue((Path(__file__).resolve().parent.parent / "scripts" / "ausloeser.py").exists())
