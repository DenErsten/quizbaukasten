"""
Eine Absage ist keine Antwort (#130).

Alle Faelle hier stammen aus Firats echtem Erstgespraech vom 2026-09-13 —
woertlich, samt Erkennungsfehlern. Das ist der Punkt: Erfundene Beispiele
haetten den Fehler nie gezeigt. Er bestand darin, dass die Pruefungen
Stichwoerter suchten, und "fertig", "nicht" und "wenn" stehen in einer
Absage genauso wie in einer Antwort.

Am Ende jenes Gespraechs stand: fuenf Fragen, null offen. Das sah nach
Erfolg aus und war ein Pruefer, der nicht hinsieht.
"""

from __future__ import annotations

import unittest

from scripts.interview import (
    PRUEFUNGEN,
    Interview,
    ist_absage,
    ohne_absagen,
    prueft_abgrenzung,
    prueft_pruefbar,
    prueft_zahl,
)

# Woertlich aus aufnahmen/2026-09-13-transkript.jsonl.
ECHT = {
    "inhalt": "Das Problem habe ich, weil ich möchte... Ich möchte eine Eieruhr haben.",
    "pruefbar": "Ich nutze Ich weiß nicht warum das fertig sein sollte. sein sollte.",
    "abgrenzung": "Ähm... Was gehört nicht dazu? Das weiß ich gerade nicht. Ist nicht sein sein.",
    "zahl": "Also ich nutze das täglich. Ich weiß es nicht.",
    "fehlerfall": "Wenn es schief geht, dann geht es... Gibts eine Fehlermeldung?",
}


class DieEchtenSaetze(unittest.TestCase):
    def test_ich_weiss_nicht_gilt_nicht_als_abnahmekriterium(self) -> None:
        self.assertFalse(PRUEFUNGEN["pruefbar"](ECHT["pruefbar"]))

    def test_rauschen_mit_nicht_darin_ist_keine_abgrenzung(self) -> None:
        self.assertFalse(PRUEFUNGEN["abgrenzung"](ECHT["abgrenzung"]))

    def test_eine_echte_antwort_neben_einer_absage_zaehlt(self) -> None:
        """
        "Ich nutze das täglich. Ich weiß es nicht." — da steht eine Antwort
        drin. Wer den ganzen Text verwirft, sobald irgendwo Unsicherheit
        steht, macht den umgekehrten Fehler.
        """
        self.assertTrue(PRUEFUNGEN["zahl"](ECHT["zahl"]))

    def test_der_kontext_war_wirklich_beantwortet(self) -> None:
        self.assertTrue(PRUEFUNGEN["inhalt"](ECHT["inhalt"]))

    def test_offen_geblieben_waere_richtig_gewesen(self) -> None:
        """
        Das Gespraech haette mit offenen Punkten enden muessen, nicht mit
        null. Genau diese Zahl war die Luege.
        """
        offen = [name for name, satz in ECHT.items() if not PRUEFUNGEN[name](satz)]

        self.assertGreaterEqual(len(offen), 2, "Mindestens zwei Antworten waren keine")


class WasUebrigBleibt(unittest.TestCase):
    def test_streicht_die_absage(self) -> None:
        self.assertEqual(ohne_absagen("Ich weiß es nicht. Es sind zwanzig."), "Es sind zwanzig")

    def test_streicht_die_rueckfrage_an_das_werkzeug(self) -> None:
        """Am 2026-09-13 stand "Gibt's eine Fehlermeldung?" als Antwort."""
        self.assertNotIn("Fehlermeldung", ohne_absagen("Gibt's eine Fehlermeldung?"))

    def test_laesst_eine_echte_antwort_stehen(self) -> None:
        satz = "Fertig ist es, wenn nach fünf Minuten ein Ton kommt"

        self.assertEqual(ohne_absagen(satz), satz)

    def test_bleibt_nichts_uebrig_ist_es_eine_absage(self) -> None:
        for satz in ["Weiß ich nicht.", "Keine Ahnung.", "Gute Frage.",
                     "Das kann ich gerade nicht sagen.", "Ähm...", ""]:
            self.assertTrue(ist_absage(satz), satz)

    def test_eine_antwort_ist_keine_absage(self) -> None:
        for satz in ["etwa 20 Stück", "ohne Anmeldung",
                     "Fertig ist es, wenn die Liste erscheint"]:
            self.assertFalse(ist_absage(satz), satz)


class EchteAntwortenGehenWeiterDurch(unittest.TestCase):
    """
    Die Gegenrichtung. Eine Sperre, die auch richtige Antworten verwirft,
    waere schlimmer als gar keine — dann redet der Mensch gegen eine Wand.
    """

    def test_kurze_abgrenzung_bleibt_gueltig(self) -> None:
        self.assertTrue(prueft_abgrenzung("ohne Anmeldung"))
        self.assertTrue(prueft_abgrenzung("Anmeldung brauchen wir nicht"))

    def test_kriterium_mit_denselben_stichwoertern_bleibt_gueltig(self) -> None:
        self.assertTrue(prueft_pruefbar("Fertig ist es, wenn die Liste nach dem Speichern erscheint"))

    def test_zahl_bleibt_gueltig(self) -> None:
        self.assertTrue(prueft_zahl("etwa 20 Stück"))
        self.assertTrue(prueft_zahl("täglich"))


class DasGespraechReagiert(unittest.TestCase):
    """Eine Absage fuehrt zur Rueckfrage, nicht zum stillen Weitergehen."""

    PUNKT = [{"titel": "Menge", "frage": "Wie viele?", "pruefung": "zahl",
              "rueckfrage": "Kannst du eine Zahl nennen?"}]

    def test_absage_fuehrt_zur_rueckfrage(self) -> None:
        i = Interview(self.PUNKT, pause=3.0)
        i.gehoert(0.0, "Das weiß ich gerade nicht")

        self.assertEqual(i.takt(4.0)["art"], "nachfragen")

    def test_zweite_absage_macht_den_punkt_offen(self) -> None:
        i = Interview(self.PUNKT, pause=3.0)
        i.gehoert(0.0, "keine Ahnung")
        i.takt(4.0)
        i.gehoert(5.0, "weiß ich immer noch nicht")
        i.takt(9.0)

        self.assertEqual(i.stand()["offene"], ["Menge"])


if __name__ == "__main__":
    unittest.main()
