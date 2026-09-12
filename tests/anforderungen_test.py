"""
Tests fuer scripts/anforderungen.py.

Kein Test ruft `claude` auf. Der Aufruf ist als Parameter einsetzbar, damit
die Tests ohne Abo, ohne Netz und ohne Kosten laufen — und damit sie immer
dasselbe pruefen, was bei einem echten Modellaufruf nicht ginge.
"""

from __future__ import annotations

import unittest

from scripts.anforderungen import (
    HOECHSTZEICHEN,
    ableiten,
    als_issue,
    eingabe,
    entwuerfe_aus_text,
    gespraech,
)

PUNKTE = [
    {"titel": "Abnahme", "frage": "Woran merkst du, dass es fertig ist?", "fuellt": "Das Kriterium."},
]

EINER = (
    '[{"titel": "Timer", "kontext": "Der Vortrag geht über die Zeit.",'
    ' "fertig_wenn": "Nach 5 Minuten klingelt es.", "offene_frage": "",'
    ' "groesse": "S", "zeit": 65, "zitat": "Wir brauchen einen Timer."}]'
)


class Transkript(unittest.TestCase):
    def test_setzt_zeitmarken_davor(self) -> None:
        text = gespraech([{"zeit": 65, "text": "Hallo"}])
        self.assertEqual(text, "[01:05] Hallo")

    def test_ueberspringt_leere_zeilen(self) -> None:
        text = gespraech([{"zeit": 0, "text": "  "}, {"zeit": 1, "text": "Da"}])
        self.assertEqual(text, "[00:01] Da")

    def test_kuerzt_vorne_nicht_hinten(self) -> None:
        """Beschluesse stehen haeufiger am Ende eines Gespraechs als am Anfang."""
        viele = [{"zeit": i, "text": "x" * 100} for i in range(2000)]
        text = gespraech(viele)

        self.assertLess(len(text), HOECHSTZEICHEN + 100)
        self.assertTrue(text.startswith("… (Anfang gekürzt) …"))
        self.assertTrue(text.rstrip().endswith("x" * 100))


class Anweisung(unittest.TestCase):
    def test_nennt_die_leitfadenfragen(self) -> None:
        """Wonach gefragt wurde, danach wird gesucht — eine Quelle fuer beides."""
        text = eingabe("[00:00] Hallo", PUNKTE)

        self.assertIn("Woran merkst du, dass es fertig ist?", text)
        self.assertIn("[00:00] Hallo", text)

    def test_verbietet_erfundene_kriterien(self) -> None:
        text = eingabe("x", PUNKTE)

        self.assertIn("Erfinde niemals ein Kriterium", text)


class AntwortLesen(unittest.TestCase):
    def test_liest_ein_blankes_array(self) -> None:
        self.assertEqual(entwuerfe_aus_text(EINER)[0]["titel"], "Timer")

    def test_liest_auch_durch_einen_codeblock_hindurch(self) -> None:
        roh = f"Hier:\n```json\n{EINER}\n```\nViel Erfolg."
        self.assertEqual(entwuerfe_aus_text(roh)[0]["zeit"], 65.0)

    def test_leere_antwort_ist_ein_fehler_keine_leere_liste(self) -> None:
        """
        Der teuerste Fall dieses Projekts: Etwas scheitert und sieht aus wie
        Normalbetrieb. Ein Gespraech laesst sich nicht wiederholen.
        """
        with self.assertRaises(ValueError):
            entwuerfe_aus_text("")
        with self.assertRaises(ValueError):
            entwuerfe_aus_text("Ich konnte leider nichts finden.")

    def test_leeres_array_ist_ein_gueltiges_ergebnis(self) -> None:
        self.assertEqual(entwuerfe_aus_text("[]"), [])

    def test_entwurf_ohne_titel_faellt_weg(self) -> None:
        self.assertEqual(entwuerfe_aus_text('[{"kontext": "nur Kontext"}]'), [])

    def test_fehlende_felder_werden_leer_statt_zu_fehlen(self) -> None:
        entwurf = entwuerfe_aus_text('[{"titel": "T"}]')[0]

        self.assertEqual(
            set(entwurf),
            {"titel", "kontext", "fertig_wenn", "offene_frage", "groesse", "zeit", "zitat"},
        )
        self.assertEqual(entwurf["fertig_wenn"], "")

    def test_unbekannte_groesse_wird_zu_m(self) -> None:
        self.assertEqual(entwuerfe_aus_text('[{"titel": "T", "groesse": "riesig"}]')[0]["groesse"], "M")
        self.assertEqual(entwuerfe_aus_text('[{"titel": "T", "groesse": "l"}]')[0]["groesse"], "L")

    def test_unlesbare_zeit_wird_null_statt_zu_krachen(self) -> None:
        self.assertEqual(entwuerfe_aus_text('[{"titel": "T", "zeit": "spaeter"}]')[0]["zeit"], 0.0)


class Ableiten(unittest.TestCase):
    def test_reicht_transkript_und_leitfaden_an_den_aufruf(self) -> None:
        gesehen = []

        ableiten([{"zeit": 0, "text": "Wir brauchen einen Timer."}], PUNKTE,
                 aufrufen=lambda a: (gesehen.append(a), EINER)[1])

        self.assertIn("Wir brauchen einen Timer.", gesehen[0])
        self.assertIn("Woran merkst du, dass es fertig ist?", gesehen[0])

    def test_leeres_transkript_fuehrt_zu_keinem_aufruf(self) -> None:
        """Kein Modellaufruf ohne Inhalt — das kostet Geld und liefert nichts."""
        aufrufe = []

        with self.assertRaises(ValueError):
            ableiten([], PUNKTE, aufrufen=lambda a: aufrufe.append(a) or "[]")

        self.assertEqual(aufrufe, [])


class IssueText(unittest.TestCase):
    def test_uebernimmt_kriterium_und_zitat(self) -> None:
        titel, koerper = als_issue(entwuerfe_aus_text(EINER)[0])

        self.assertEqual(titel, "Timer")
        self.assertIn("Nach 5 Minuten klingelt es.", koerper)
        self.assertIn("> Wir brauchen einen Timer.", koerper)
        self.assertIn("bei 01:05", koerper)
        self.assertIn("groesse:S", koerper)

    def test_erfindet_kein_kriterium_sondern_stellt_die_frage(self) -> None:
        """
        CLAUDE.md: "Wenn du es nicht formulieren kannst, weisst du zu wenig —
        dann schreib die offene Frage ins Issue statt eine Vermutung."
        """
        ohne = entwuerfe_aus_text(
            '[{"titel": "T", "fertig_wenn": "", "offene_frage": "Wie lange genau?"}]'
        )[0]
        _, koerper = als_issue(ohne)

        self.assertIn("im Gespräch nicht genannt", koerper)
        self.assertIn("Wie lange genau?", koerper)

    def test_sagt_dass_der_wortlaut_aus_spracherkennung_stammt(self) -> None:
        _, koerper = als_issue(entwuerfe_aus_text(EINER)[0])

        self.assertIn("automatische", koerper.lower())


if __name__ == "__main__":
    unittest.main()
