"""
Tests fuer werkzeuge/server.py — #69.

Kein Mikrofon, kein Whisper: `Aufnahme` nimmt den Startvorgang als Argument
entgegen (wie `mithoeren.strom` die Erkennung), die Tests setzen dort einen
echten, aber genuegsamen Fake-Prozess ein statt der Hoer-Kette. Gegen den
Server selbst wird per HTTP getestet — ueber echte Anfragen an
http://127.0.0.1, nicht gegen die Python-Klassen allein.
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from werkzeuge.server import Aufnahme, server_starten


class GenuegsamerProzess:
    """Ein echter, aber anspruchsloser Ersatz fuer die Hoer-Kette."""

    def __init__(self) -> None:
        self.beendet = False

    def poll(self) -> int | None:
        return 0 if self.beendet else None

    def terminate(self) -> None:
        self.beendet = True

    def wait(self, timeout: float | None = None) -> int:
        return 0


class ServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.gestartete: list[GenuegsamerProzess] = []

        def starter(_datei: Path) -> GenuegsamerProzess:
            prozess = GenuegsamerProzess()
            self.gestartete.append(prozess)
            return prozess

        self.verwaltung = Aufnahme(self.ordner, prozess_starten=starter)
        self.server = server_starten(self.verwaltung, port=0)
        self.basis = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def _post(self, pfad: str) -> dict:
        anfrage = urllib.request.Request(f"{self.basis}{pfad}", method="POST", data=b"")
        with urllib.request.urlopen(anfrage, timeout=5) as antwort:
            return json.loads(antwort.read())

    def _get(self, pfad: str) -> dict | list:
        with urllib.request.urlopen(f"{self.basis}{pfad}", timeout=5) as antwort:
            return json.loads(antwort.read())

    def _hinweisdatei(self) -> Path:
        datum = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        return self.ordner / f"{datum}-hinweise.jsonl"

    def test_start_und_stop_spiegeln_sich_in_status(self) -> None:
        """Fall 1: Nach start meldet /status laeuft: true, nach stop laeuft: false."""
        self.assertFalse(self._get("/status")["laeuft"])

        nach_start = self._post("/aufnahme/start")
        self.assertTrue(nach_start["laeuft"])
        self.assertTrue(self._get("/status")["laeuft"])

        nach_stop = self._post("/aufnahme/stop")
        self.assertFalse(nach_stop["laeuft"])
        self.assertFalse(self._get("/status")["laeuft"])

    def test_zweiter_start_startet_keinen_zweiten_vorgang(self) -> None:
        """Fall 2: Ein zweites start bei laufender Aufnahme bleibt wirkungslos."""
        self._post("/aufnahme/start")
        self._post("/aufnahme/start")

        self.assertEqual(len(self.gestartete), 1)
        self.assertTrue(self._get("/status")["laeuft"])

    def test_stop_ohne_laufende_aufnahme_ist_kein_fehler(self) -> None:
        """Fall 3: stop ohne laufende Aufnahme ist wirkungslos, nicht falsch."""
        antwort = self._post("/aufnahme/stop")

        self.assertFalse(antwort["laeuft"])
        self.assertEqual(len(self.gestartete), 0)

    def test_hinweise_ohne_datei_ist_leere_liste(self) -> None:
        """Fall 4: Fehlt die Datei, liefert /hinweise eine leere Liste, keinen Fehler."""
        self.assertEqual(self._get("/hinweise"), [])

    def test_hinweise_liest_die_zeilen_der_datei(self) -> None:
        """Fall 4: Vorhandene Zeilen kommen als JSON-Liste zurueck."""
        zeilen = [
            {"zeit": 1.0, "zitat": "erstes", "art": "mengenwort", "grund": "g", "frage": "f"},
            {"zeit": 2.0, "zitat": "zweites", "art": "mengenwort", "grund": "g", "frage": "f"},
        ]
        self._hinweisdatei().write_text(
            "\n".join(json.dumps(z) for z in zeilen) + "\n", encoding="utf-8"
        )

        self.assertEqual(self._get("/hinweise"), zeilen)
        self.assertEqual(self._get("/status")["hinweise"], 2)

    def test_kaputte_zeile_wird_uebersprungen(self) -> None:
        """Fall 5: Eine halb geschriebene letzte Zeile scheitert nicht die Antwort."""
        vollstaendig = {"zeit": 1.0, "zitat": "x", "art": "a", "grund": "g", "frage": "f"}
        inhalt = json.dumps(vollstaendig) + "\n" + '{"zeit": 2.0, "zitat": "abgeschni'
        self._hinweisdatei().write_text(inhalt, encoding="utf-8")

        self.assertEqual(self._get("/hinweise"), [vollstaendig])

    def test_liefert_dateien_aus_werkzeuge_aus(self) -> None:
        """Alles ausserhalb der drei Wege kommt aus werkzeuge/."""
        anfrage = urllib.request.Request(f"{self.basis}/anzeige.js", method="GET")
        with urllib.request.urlopen(anfrage, timeout=5) as antwort:
            self.assertEqual(antwort.status, 200)

    def test_unbekannter_pfad_bei_post_ist_404(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/nicht-vorhanden")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
