"""
Das Gespraech hoert zu (#125).

Kein Test ruft `claude` auf: Der Aufruf ist ueberall einsetzbar. Die Faelle
stammen aus Firats Gespraech vom 2026-09-13 — dort sagte er "Ich moechte ein
Spiel entwickeln", und die naechste Frage war trotzdem "Woran merkst du, dass
es fertig ist?". Vier von fuenf Punkten blieben offen.
"""

from __future__ import annotations

import json
import unittest

from scripts.gespraechsfuehrung import (
    ANTWORTEN,
    NACHFRAGEN,
    TRAEGT,
    eingabe,
    naechster_zug,
    zug_aus_text,
)
from scripts.interview import ANTWORT, ENDE, Interview
from scripts.interview import NACHFRAGEN as I_NACHFRAGEN

PUNKT = {"titel": "Ausgangslage", "frage": "Wer hat das Problem?",
         "fuellt": "Den Kontext.", "pruefung": "inhalt",
         "rueckfrage": "Was passiert heute, wenn das fehlt?"}


def _antwortet(zug: str, satz: str = "", grund: str = "x"):
    return lambda _: json.dumps({"zug": zug, "satz": satz, "grund": grund})


class DieAnweisung(unittest.TestCase):
    def test_traegt_das_gesagte_woertlich(self) -> None:
        text = eingabe(PUNKT, "Ich möchte ein Spiel entwickeln.", [])

        self.assertIn("Ich möchte ein Spiel entwickeln.", text)
        self.assertIn("Wer hat das Problem?", text)

    def test_nennt_das_bisher_geklaerte(self) -> None:
        text = eingabe(PUNKT, "x", [{"titel": "Abnahme", "antwort": "nach fünf Minuten"}])

        self.assertIn("nach fünf Minuten", text)

    def test_verbietet_fachbegriffe_und_allgemeine_rueckfragen(self) -> None:
        """Die Zielgruppe weiss nicht, was ein Pull Request ist (#131)."""
        text = eingabe(PUNKT, "x", [])

        self.assertIn("Keine Fachbegriffe", text)
        self.assertIn("Was fuer ein Spiel?", text)

    def test_ohne_gesagtes_kein_aufruf(self) -> None:
        """Kein Modellaufruf ins Leere — das kostet und liefert nichts."""
        aufrufe: list = []

        with self.assertRaises(ValueError):
            naechster_zug(PUNKT, "   ", [], aufrufen=lambda a: aufrufe.append(a) or "{}")

        self.assertEqual(aufrufe, [])


class DieAntwortLesen(unittest.TestCase):
    def test_liest_die_drei_zuege(self) -> None:
        for zug in (TRAEGT, NACHFRAGEN, ANTWORTEN):
            satz = "" if zug == TRAEGT else "Was für ein Spiel?"
            gelesen = zug_aus_text(json.dumps({"zug": zug, "satz": satz}))

            self.assertEqual(gelesen["zug"], zug)

    def test_liest_durch_einen_codeblock_hindurch(self) -> None:
        roh = '```json\n{"zug": "traegt", "satz": ""}\n```'

        self.assertEqual(zug_aus_text(roh)["zug"], TRAEGT)

    def test_unbekannter_zug_ist_ein_fehler(self) -> None:
        with self.assertRaises(ValueError):
            zug_aus_text('{"zug": "schweigen"}')

    def test_nachfragen_ohne_satz_ist_ein_fehler(self) -> None:
        """Es gibt sonst nichts vorzulesen — und das saehe aus wie Stille."""
        with self.assertRaises(ValueError):
            zug_aus_text('{"zug": "nachfragen", "satz": ""}')

    def test_leere_antwort_ist_ein_fehler_kein_weiter(self) -> None:
        """
        Wer im Zweifel weitergeht, baut den Fehler vom 2026-09-13 nach: Das
        Gespraech sah vollstaendig aus und war leer.
        """
        with self.assertRaises(ValueError):
            zug_aus_text("")


class DasInterviewFolgtDerFuehrung(unittest.TestCase):
    def _interview(self, zug: str, satz: str = ""):
        return Interview(
            [PUNKT],
            pause=3.0,
            fuehrung=lambda p, g, v: json.loads(_antwortet(zug, satz)(None)),
        )

    def test_traegt_bringt_den_punkt_zu_ende(self) -> None:
        i = self._interview(TRAEGT)
        i.gehoert(0.0, "Beim Eierkochen vergesse ich die Zeit")

        # Ein Interview mit einem einzigen Punkt ist danach fertig.
        self.assertEqual(i.takt(4.0)["art"], ENDE)
        self.assertFalse(i.stand()["beantwortet"][0]["offen"])

    def test_die_rueckfrage_kommt_aus_der_fuehrung_nicht_aus_dem_leitfaden(self) -> None:
        i = self._interview(NACHFRAGEN, "Was für ein Spiel?")
        i.gehoert(0.0, "Ich möchte ein Spiel entwickeln")
        ereignis = i.takt(4.0)

        self.assertEqual(ereignis["art"], I_NACHFRAGEN)
        self.assertEqual(ereignis["rueckfrage"], "Was für ein Spiel?")
        self.assertEqual(i.stand()["rueckfrage"], "Was für ein Spiel?")

    def test_eine_frage_an_das_werkzeug_wird_beantwortet(self) -> None:
        """
        Firat hat am 2026-09-12 und am 2026-09-13 gefragt und beide Male
        keine Antwort bekommen (#131).
        """
        i = self._interview(ANTWORTEN, "Ja, ich höre die ganze Zeit mit.")
        i.gehoert(0.0, "Hast du noch weitere Fragen?")
        ereignis = i.takt(4.0)

        self.assertEqual(ereignis["art"], ANTWORT)
        self.assertEqual(ereignis["satz"], "Ja, ich höre die ganze Zeit mit.")

    def test_eine_antwort_verbraucht_die_rueckfrage_nicht(self) -> None:
        i = self._interview(ANTWORTEN, "Ja, ich höre mit.")
        i.gehoert(0.0, "Hörst du mit?")
        i.takt(4.0)

        self.assertFalse(i.stand()["nachgefragt"], "Antworten ist kein Nachhaken")

    def test_zweite_absage_macht_den_punkt_offen(self) -> None:
        i = self._interview(NACHFRAGEN, "Was für ein Spiel?")
        i.gehoert(0.0, "weiß nicht")
        i.takt(4.0)
        i.gehoert(5.0, "immer noch nicht")
        i.takt(9.0)

        self.assertEqual(i.stand()["offene"], ["Ausgangslage"])

    def test_das_gespraech_laesst_sich_nicht_endlos_ablenken(self) -> None:
        """Ohne Grenze fuehrt jede Gegenfrage weiter vom Thema weg."""
        i = self._interview(ANTWORTEN, "Ja.")
        arten = []
        for n in range(6):
            i.gehoert(n * 10.0, "Und was machst du sonst so?")
            ereignis = i.takt(n * 10.0 + 4.0)
            if ereignis:
                arten.append(ereignis["art"])

        self.assertLessEqual(arten.count(ANTWORT), 2, arten)


class OhneFuehrungBleibtAllesLokal(unittest.TestCase):
    """
    Der Weg ohne Klick. Er muss unveraendert weiterlaufen, sonst haengt die
    Aufnahme am Netz — und ein Gespraech laesst sich nicht wiederholen.
    """

    def test_ohne_fuehrung_wird_nichts_aufgerufen(self) -> None:
        i = Interview([PUNKT], pause=3.0)
        i.gehoert(0.0, "Beim Eierkochen vergesse ich regelmäßig die Zeit und dann ist es hart")

        self.assertEqual(i.takt(4.0)["art"], ENDE)
        self.assertFalse(i.stand()["beantwortet"][0]["offen"])
        self.assertFalse(i.stand()["gefuehrt"])

    def test_faellt_die_fuehrung_aus_entscheidet_die_lokale_pruefung(self) -> None:
        def kaputt(p, g, v):
            raise RuntimeError("claude antwortet nicht")

        i = Interview([PUNKT], pause=3.0, fuehrung=kaputt)
        i.gehoert(0.0, "Beim Eierkochen vergesse ich regelmäßig die Zeit und dann ist es hart")

        self.assertEqual(i.takt(4.0)["art"], ENDE, "Das Gespräch läuft weiter")
        self.assertFalse(i.stand()["beantwortet"][0]["offen"])

    def test_ein_ausfall_wird_genannt_nicht_verschwiegen(self) -> None:
        def kaputt(p, g, v):
            raise RuntimeError("claude antwortet nicht")

        i = Interview([PUNKT], pause=3.0, fuehrung=kaputt)
        i.gehoert(0.0, "irgendwas")
        i.takt(4.0)

        self.assertIn("antwortet nicht", i.stand()["fuehrung_fehler"])


if __name__ == "__main__":
    unittest.main()
