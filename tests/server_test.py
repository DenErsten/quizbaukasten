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
import pathlib
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

        # modell_pruefen wird gesetzt, seit start() das Modell prueft (#87).
        # Diese Tests pruefen start/stop, nicht den Modell-Download — ohne die
        # Vorgabe landen sie in "laedt" statt in "laeuft", und zwar ueberall
        # dort, wo kein Modell im Cache liegt. Also in der CI.
        self.verwaltung = Aufnahme(
            self.ordner, prozess_starten=starter, modell_pruefen=lambda: True
        )
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


class StummerFehlstart(unittest.TestCase):
    """
    #76: Ein gescheiterter Start war von "nicht gestartet" nicht zu
    unterscheiden. Die Ansicht fiel stumm auf "bereit" zurueck.
    """

    class SofortTot:
        """Ein Vorgang, der beim Start stirbt — wie mithoeren.py ohne Whisper."""

        def __init__(self, meldung: str = "ModuleNotFoundError: No module named 'sounddevice'"):
            self._meldung = meldung

        def poll(self): return 1
        def terminate(self): pass
        def wait(self, timeout=None): return 1
        def fehler_text(self): return self._meldung

    class Laeuft:
        def poll(self): return None
        def terminate(self): pass
        def wait(self, timeout=None): return 0
        def fehler_text(self): return ""

    def _aufnahme(self, prozess):
        import tempfile
        from werkzeuge.server import Aufnahme

        return Aufnahme(
            aufnahmen_ordner=pathlib.Path(tempfile.mkdtemp()),
            prozess_starten=lambda _: prozess,
            modell_pruefen=lambda: True,  # siehe oben, #87
        )

    def test_sofortiger_tod_meldet_fehler(self) -> None:
        """Fall 1: laeuft false UND fehler nicht leer."""
        a = self._aufnahme(self.SofortTot())

        a.start()
        status = a.status()

        self.assertFalse(status["laeuft"])
        self.assertIn("sounddevice", status["fehler"])

    def test_laufender_vorgang_hat_keinen_fehler(self) -> None:
        """Fall 2."""
        a = self._aufnahme(self.Laeuft())

        a.start()

        self.assertTrue(a.status()["laeuft"])
        self.assertIsNone(a.status()["fehler"])

    def test_stop_raeumt_den_fehler_weg(self) -> None:
        """Fall 3: Sonst zeigt die Oberflaeche beim zweiten Versuch den ersten Fehler."""
        a = self._aufnahme(self.SofortTot())
        a.start()
        self.assertIsNotNone(a.status()["fehler"])

        a.stop()

        self.assertIsNone(a.status()["fehler"])

    def test_ohne_meldung_trotzdem_ein_fehler(self) -> None:
        """Ein stummer Tod darf nicht als 'kein Fehler' durchgehen."""
        a = self._aufnahme(self.SofortTot(meldung=""))

        a.start()

        self.assertTrue(a.status()["fehler"])


class PipelineMeldetJedesGlied(unittest.TestCase):
    """
    Nicht im Ticket, beim Bauen gefunden: poll() fragte nur den letzten
    Prozess. Stirbt mithoeren.py mit Fehler, endet ausloeser.py sauber am
    geschlossenen Eingang — die Pipeline haette "beendet, alles gut"
    gemeldet, obwohl nie ein Wort erkannt wurde.
    """

    class Glied:
        def __init__(self, code): self._code = code
        def poll(self): return self._code
        def terminate(self): pass
        def wait(self, timeout=None): return self._code or 0

    def test_fehler_im_ersten_glied_zaehlt(self) -> None:
        from werkzeuge.server import Pipeline

        p = Pipeline([self.Glied(1), self.Glied(0)])

        self.assertEqual(p.poll(), 1)

    def test_alle_sauber_beendet_ist_kein_fehler(self) -> None:
        from werkzeuge.server import Pipeline

        p = Pipeline([self.Glied(0), self.Glied(0)])

        self.assertEqual(p.poll(), 0)

    def test_laufend_bleibt_laufend(self) -> None:
        from werkzeuge.server import Pipeline

        p = Pipeline([self.Glied(None), self.Glied(None)])

        self.assertIsNone(p.poll())


class ModellVorabLaden(unittest.TestCase):
    """
    #87: Das Modell wurde beim ersten Erkennungsaufruf geholt — mitten in der
    laufenden Aufnahme, 459 MB, unsichtbar. Zwei Versuche gingen so verloren.
    """

    class Laeuft:
        def poll(self): return None
        def terminate(self): pass
        def wait(self, timeout=None): return 0
        def fehler_text(self): return ""

    def _aufnahme(self, vorhanden, holen=lambda: None, prozess=None):
        import tempfile
        from werkzeuge.server import Aufnahme

        return Aufnahme(
            aufnahmen_ordner=pathlib.Path(tempfile.mkdtemp()),
            prozess_starten=lambda _: prozess or self.Laeuft(),
            modell_pruefen=lambda: vorhanden,
            modell_holen=holen,
        )

    def test_fehlendes_modell_wird_gemeldet_statt_zu_starten(self) -> None:
        """Fall 1."""
        import threading

        haelt = threading.Event()
        a = self._aufnahme(vorhanden=False, holen=haelt.wait)
        self.addCleanup(haelt.set)

        a.start()
        status = a.status()

        self.assertTrue(status["laedt_modell"])
        self.assertFalse(status["laeuft"])

    def test_vorhandenes_modell_startet_sofort(self) -> None:
        """Fall 2: kein Umweg, wenn nichts zu holen ist."""
        geholt = []
        a = self._aufnahme(vorhanden=True, holen=lambda: geholt.append(1))

        a.start()

        self.assertTrue(a.status()["laeuft"])
        self.assertFalse(a.status()["laedt_modell"])
        self.assertEqual(geholt, [], "Es gab nichts zu laden")

    def test_abgebrochener_download_wird_zum_fehler(self) -> None:
        """Fall 3: kein stiller Ruecksprung auf 'bereit'."""
        import time

        def kaputt():
            raise OSError("Verbindung abgebrochen")

        a = self._aufnahme(vorhanden=False, holen=kaputt)

        a.start()
        for _ in range(50):
            if not a.status()["laedt_modell"]:
                break
            time.sleep(0.02)

        status = a.status()
        self.assertFalse(status["laedt_modell"])
        self.assertIn("Verbindung abgebrochen", status["fehler"])

    def test_zweiter_start_waehrend_des_ladens_tut_nichts(self) -> None:
        """Sonst laufen zwei Downloads nebeneinander."""
        import threading

        haelt = threading.Event()
        versuche = []

        def holen():
            versuche.append(1)
            haelt.wait()

        a = self._aufnahme(vorhanden=False, holen=holen)
        self.addCleanup(haelt.set)

        a.start()
        a.start()

        self.assertEqual(len(versuche), 1)


class NachDemLadenLaeuftEs(unittest.TestCase):
    """
    Wer auf Start drueckt, will aufnehmen — nicht ein Modell laden.
    Ohne diesen Schritt stand nach dem Download wieder "bereit" da.
    """

    class Laeuft:
        def poll(self): return None
        def terminate(self): pass
        def wait(self, timeout=None): return 0
        def fehler_text(self): return ""

    def test_nach_erfolgreichem_download_startet_die_aufnahme(self) -> None:
        import tempfile
        import time

        from werkzeuge.server import Aufnahme

        vorhanden = [False]

        def holen():
            vorhanden[0] = True

        a = Aufnahme(
            aufnahmen_ordner=pathlib.Path(tempfile.mkdtemp()),
            prozess_starten=lambda _: self.Laeuft(),
            modell_pruefen=lambda: vorhanden[0],
            modell_holen=holen,
        )

        a.start()
        for _ in range(50):
            if a.status()["laeuft"]:
                break
            time.sleep(0.02)

        self.assertTrue(a.status()["laeuft"], "Nach dem Laden muss die Aufnahme laufen")

    def test_nach_fehlgeschlagenem_download_laeuft_nichts(self) -> None:
        """Gegenprobe: Kein Start auf ein Modell, das nicht da ist."""
        import tempfile
        import time

        from werkzeuge.server import Aufnahme

        def kaputt():
            raise OSError("abgebrochen")

        a = Aufnahme(
            aufnahmen_ordner=pathlib.Path(tempfile.mkdtemp()),
            prozess_starten=lambda _: self.Laeuft(),
            modell_pruefen=lambda: False,
            modell_holen=kaputt,
        )

        a.start()
        for _ in range(50):
            if a.status()["fehler"]:
                break
            time.sleep(0.02)

        self.assertFalse(a.status()["laeuft"])
        self.assertIn("abgebrochen", a.status()["fehler"])
