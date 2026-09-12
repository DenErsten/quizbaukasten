"""
Tests fuer die offenen Entscheidungen in der Freigabe-Konsole (#108).

Kein Test ruft gh auf: `aufruf` ist ueberall einsetzbar. Geprueft wird vor
allem die Grenze — ein Klick entscheidet, er gibt nicht frei.
"""

from __future__ import annotations

import json
import unittest

from werkzeuge import freigabe

MIT_BLOCK = """Kontext oben, der nicht dazugehört.

## Entscheidung

Soll der Text des Transkripts an Claude gehen?

- **A** — Lokal bleiben. Nichts verlässt den Rechner.
- **B** — Claude benutzen. Text geht raus, Ton nie.

Empfehlung: B — lokal reicht die Qualität nicht für ein „fertig, wenn …".

## fertig, wenn

- **C** — steht im falschen Abschnitt
"""


class Lesen(unittest.TestCase):
    def test_liest_frage_optionen_und_empfehlung(self) -> None:
        e = freigabe.entscheidung_aus_text(MIT_BLOCK)

        self.assertEqual(e["frage"], "Soll der Text des Transkripts an Claude gehen?")
        self.assertEqual([o["buchstabe"] for o in e["optionen"]], ["A", "B"])
        self.assertEqual(e["empfehlung"]["buchstabe"], "B")
        self.assertIn("Qualität", e["empfehlung"]["grund"])

    def test_nimmt_nur_den_eigenen_abschnitt(self) -> None:
        """Eine Option unter 'fertig, wenn' ist keine Option."""
        e = freigabe.entscheidung_aus_text(MIT_BLOCK)

        self.assertNotIn("C", [o["buchstabe"] for o in e["optionen"]])

    def test_ohne_block_gibt_es_nichts(self) -> None:
        self.assertIsNone(freigabe.entscheidung_aus_text("Ein ganz normales Issue."))
        self.assertIsNone(freigabe.entscheidung_aus_text(""))

    def test_block_ohne_optionen_gibt_es_nicht(self) -> None:
        """Eine Frage ohne Auswahl waere ein Knopf, der nirgendwohin führt."""
        self.assertIsNone(freigabe.entscheidung_aus_text("## Entscheidung\n\nWas nun?\n"))

    def test_empfehlung_darf_fehlen(self) -> None:
        e = freigabe.entscheidung_aus_text("## Entscheidung\n\nF?\n\n- **A** — eins\n- **B** — zwei\n")

        self.assertIsNone(e["empfehlung"])
        self.assertEqual(len(e["optionen"]), 2)


def _liste(issues: list[dict]):
    return lambda befehl: json.dumps(issues)


class Offene(unittest.TestCase):
    ISSUE = {"number": 102, "title": "Frage", "body": MIT_BLOCK, "comments": []}

    def test_zeigt_issues_mit_block(self) -> None:
        offen = freigabe.offene_entscheidungen(aufruf=_liste([self.ISSUE]), menschen={"DenErsten"})

        self.assertEqual(offen[0]["nummer"], 102)
        self.assertEqual(offen[0]["empfehlung"]["buchstabe"], "B")

    def test_ueberspringt_issues_ohne_block(self) -> None:
        ohne = {"number": 7, "title": "X", "body": "nichts", "comments": []}
        offen = freigabe.offene_entscheidungen(aufruf=_liste([ohne]), menschen={"DenErsten"})

        self.assertEqual(offen, [])

    def test_verschwindet_wenn_ein_mensch_geantwortet_hat(self) -> None:
        beantwortet = dict(self.ISSUE, comments=[{"author": {"login": "DenErsten"}, "body": "B"}])
        offen = freigabe.offene_entscheidungen(aufruf=_liste([beantwortet]), menschen={"DenErsten"})

        self.assertEqual(offen, [])

    def test_eine_antwort_vom_bot_zaehlt_nicht(self) -> None:
        """
        Sonst koennte sich die Kette ihre eigenen Fragen beantworten — genau
        das, was Gate G2 verhindern soll.
        """
        vom_bot = dict(self.ISSUE, comments=[{"author": {"login": "quizberater"}, "body": "B"}])
        offen = freigabe.offene_entscheidungen(aufruf=_liste([vom_bot]), menschen={"DenErsten"})

        self.assertEqual(len(offen), 1)

    def test_ein_langer_kommentar_zaehlt_nicht_als_antwort(self) -> None:
        geplauder = dict(self.ISSUE, comments=[
            {"author": {"login": "DenErsten"}, "body": "Bin mir noch unsicher, melde mich."},
        ])
        offen = freigabe.offene_entscheidungen(aufruf=_liste([geplauder]), menschen={"DenErsten"})

        self.assertEqual(len(offen), 1)


class Entscheiden(unittest.TestCase):
    def test_schreibt_genau_einen_kommentar(self) -> None:
        befehle: list = []
        freigabe.entscheiden(102, "b", aufruf=lambda b: befehle.append(b) or "")

        self.assertEqual(len(befehle), 1)
        self.assertEqual(befehle[0], ["issue", "comment", "102", "--body", "B"])

    def test_setzt_kein_label(self) -> None:
        """
        Entscheiden ist nicht freigeben. Waeren es ein Handgriff, waere eines
        von beiden irgendwann versehentlich.
        """
        befehle: list = []
        freigabe.entscheiden(102, "A", aufruf=lambda b: befehle.append(b) or "")

        zusammen = " ".join(befehle[0])
        self.assertNotIn("--add-label", zusammen)
        self.assertNotIn("status:freigegeben", zusammen)
        self.assertNotIn("edit", zusammen)

    def test_weist_unsinn_ab_ohne_etwas_zu_schreiben(self) -> None:
        befehle: list = []
        for schlecht in ["", "AB", "1", "ja", "--add-label"]:
            with self.assertRaises(ValueError, msg=schlecht):
                freigabe.entscheiden(102, schlecht, aufruf=lambda b: befehle.append(b) or "")

        self.assertEqual(befehle, [])


class MenschenListe(unittest.TestCase):
    def test_kommt_aus_derselben_datei_wie_gate_g3(self) -> None:
        """Zwei Listen von Menschen liefen frueher oder spaeter auseinander."""
        from scripts.pfad_pruefung import MENSCHENDATEI as g3

        self.assertEqual(freigabe.MENSCHENDATEI.resolve(), g3.resolve())

    def test_enthaelt_firat(self) -> None:
        self.assertIn("DenErsten", freigabe._menschen())


if __name__ == "__main__":
    unittest.main()


class CodebloeckeZaehlenNicht(unittest.TestCase):
    """
    Wer ueber die Form schreibt, benutzt sie nicht.

    Beim ersten Versuch las der Parser den Beispielblock aus #108 als echte
    Entscheidung — die Anleitung wurde selbst zu einer Frage in der Konsole.
    Dasselbe Muster wie bei Gate G2 am 2026-09-12, wo "Refs #31" in einem
    Codeblock als echte Referenz zaehlte.
    """

    ANLEITUNG = """So schreibt man eine Entscheidung:

```markdown
## Entscheidung

Beispielfrage?

- **A** — eins
- **B** — zwei

Empfehlung: A — weil.
```

Mehr ist es nicht.
"""

    def test_ein_beispiel_im_codeblock_ist_keine_entscheidung(self) -> None:
        self.assertIsNone(freigabe.entscheidung_aus_text(self.ANLEITUNG))

    def test_eine_echte_entscheidung_neben_einem_beispiel_zaehlt(self) -> None:
        text = self.ANLEITUNG + "\n## Entscheidung\n\nEcht?\n\n- **A** — ja\n- **B** — nein\n"
        e = freigabe.entscheidung_aus_text(text)

        self.assertEqual(e["frage"], "Echt?")
        self.assertEqual([o["buchstabe"] for o in e["optionen"]], ["A", "B"])

    def test_option_im_codeblock_landet_nicht_in_einer_echten_frage(self) -> None:
        text = "## Entscheidung\n\nF?\n\n- **A** — echt\n\n```\n- **Z** — nur Beispiel\n```\n"
        e = freigabe.entscheidung_aus_text(text)

        self.assertEqual([o["buchstabe"] for o in e["optionen"]], ["A"])


class WegEntscheidungen(unittest.TestCase):
    """
    GET /entscheidungen und POST /entscheidung/<nr>/<buchstabe> (#108).

    Ein eigener Weg, nicht ein Anhaengsel an /freigaben: Freigeben und
    entscheiden sind zwei verschiedene Dinge.
    """

    def setUp(self) -> None:
        import threading

        from werkzeuge.server import Aufnahme, server_starten

        self.verwaltung = Aufnahme(prozess_starten=lambda: None)
        self.server = server_starten(self.verwaltung, port=0)
        self.basis = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def test_der_weg_existiert_und_liefert_die_liste(self) -> None:
        """
        Mit Attrappe statt echtem gh: Auf dem Bauserver gibt es keine
        Anmeldung, und ein Test, der Netz braucht, prueft das Netz statt den
        Code. Beim ersten Versuch schlug genau das fehl.
        """
        import urllib.request
        from unittest.mock import patch

        from werkzeuge import server

        class Attrappe:
            @staticmethod
            def offene_entscheidungen():
                return [{"nummer": 1, "titel": "T", "frage": "F?",
                         "optionen": [{"buchstabe": "A", "text": "eins"}],
                         "empfehlung": None}]

        with patch.object(server, "_freigabe_modul", lambda: Attrappe):
            with urllib.request.urlopen(f"{self.basis}/entscheidungen", timeout=20) as antwort:
                self.assertEqual(antwort.status, 200)
                daten = json.loads(antwort.read())

        # Eine Liste, auch wenn gerade nichts offen ist. Ein Fehlerobjekt
        # waere hier das Muster aus #99: sieht aus wie "nichts offen".
        self.assertIsInstance(daten, list)
        self.assertEqual(daten[0]["nummer"], 1)
        self.assertIn("optionen", daten[0])

    def test_ein_fehler_beim_holen_wird_gemeldet_statt_als_leere_liste(self) -> None:
        import urllib.error
        import urllib.request
        from unittest.mock import patch

        from werkzeuge import server

        class Kaputt:
            @staticmethod
            def offene_entscheidungen():
                raise RuntimeError("gh ist nicht angemeldet")

        with patch.object(server, "_freigabe_modul", lambda: Kaputt):
            with self.assertRaises(urllib.error.HTTPError) as fehler:
                urllib.request.urlopen(f"{self.basis}/entscheidungen", timeout=20)

        self.assertEqual(fehler.exception.code, 502)
        self.assertIn("nicht angemeldet", fehler.exception.read().decode())

    def test_freigaben_traegt_die_entscheidungen_nicht_mehr(self) -> None:
        """Eine Quelle, nicht zwei — sonst laufen sie auseinander."""
        import inspect

        from werkzeuge import server

        quelle = inspect.getsource(server.Anfrage._freigaben)
        self.assertNotIn("offene_entscheidungen", quelle)

    def test_unsinnige_wahl_wird_abgewiesen(self) -> None:
        import urllib.error
        import urllib.request

        anfrage = urllib.request.Request(
            f"{self.basis}/entscheidung/1/ZZZ", method="POST", data=b""
        )
        with self.assertRaises(urllib.error.HTTPError) as fehler:
            urllib.request.urlopen(anfrage, timeout=20)

        self.assertEqual(fehler.exception.code, 400)
