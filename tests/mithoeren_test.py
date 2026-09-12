"""
Tests fuer scripts/mithoeren.py.

Es gibt hier kein Mikrofon und kein Whisper — beides waere in der CI nicht
vorhanden. Geprueft wird deshalb gegen eine erzeugte WAV-Datei und eine
eingesetzte Erkennung. Das ist der Grund, warum `strom` die Erkennung als
Argument nimmt statt sie sich selbst zu holen.

Die WAV-Datei entsteht mit der Standardbibliothek. Eine Binaerdatei im Repo
waere hier ein Fremdkoerper: Niemand koennte nachsehen, was drin ist.
"""

from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from scripts.mithoeren import ABTASTRATE, BREITE, stuecke_aus_datei, strom


def wav_schreiben(pfad: Path, sekunden: float) -> None:
    """Eine stille WAV-Datei der gewuenschten Laenge."""
    with wave.open(str(pfad), "wb") as datei:
        datei.setnchannels(1)
        datei.setsampwidth(BREITE)
        datei.setframerate(ABTASTRATE)
        datei.writeframes(b"\x00" * int(ABTASTRATE * sekunden) * BREITE)


class Mithoeren(unittest.TestCase):
    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.quelle = self.ordner / "probe.wav"
        wav_schreiben(self.quelle, sekunden=6.0)

    def test_erzeugt_strom_mit_zeit_und_text(self) -> None:
        """Fall 1: Aus einer WAV-Datei wird ein Strom mit zeit und text."""
        saetze = iter(["erster Satz", "zweiter Satz"])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, sekunden=3.0), lambda _: next(saetze, ""))
        )

        self.assertEqual(len(zeilen), 2)
        self.assertEqual(zeilen[0], {"zeit": 0.0, "text": "erster Satz"})
        self.assertEqual(zeilen[1], {"zeit": 3.0, "text": "zweiter Satz"})

    def test_ohne_mitschneiden_entsteht_keine_datei(self) -> None:
        """Fall 2: Ohne --mitschneiden wird keine Audiodatei geschrieben."""
        vorher = set(self.ordner.iterdir())

        list(strom(stuecke_aus_datei(self.quelle, sekunden=3.0), lambda _: "irgendwas"))

        self.assertEqual(set(self.ordner.iterdir()), vorher)

    def test_mitschneiden_schreibt_die_stuecke(self) -> None:
        """Gegenprobe zu Fall 2: Mit Angabe entsteht die Datei sehr wohl."""
        ziel = self.ordner / "mitschnitt" / "sitzung.wav"

        list(strom(stuecke_aus_datei(self.quelle, sekunden=3.0), lambda _: "x", ziel))

        self.assertTrue(ziel.exists())
        with wave.open(str(ziel), "rb") as datei:
            self.assertEqual(datei.getframerate(), ABTASTRATE)
            self.assertEqual(datei.getnframes(), int(ABTASTRATE * 6.0))

    def test_stille_erzeugt_keine_zeile(self) -> None:
        """Fall 3: Ein Stueck ohne erkennbare Sprache erzeugt keine Zeile."""
        saetze = iter(["gesprochen", "   ", ""])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, sekunden=2.0), lambda _: next(saetze, ""))
        )

        self.assertEqual(len(zeilen), 1)
        self.assertEqual(zeilen[0]["text"], "gesprochen")


if __name__ == "__main__":
    unittest.main()


class Transkript(unittest.TestCase):
    """
    #81: Was kein Hinweis wird, verschwand. Damit war nicht zu unterscheiden,
    ob nichts gesagt wurde oder nichts gehoert.
    """

    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.quelle = self.ordner / "probe.wav"
        wav_schreiben(self.quelle, sekunden=6.0)
        self.ziel = self.ordner / "unter" / "transkript.jsonl"

    def _zeilen(self) -> list[dict]:
        import json

        if not self.ziel.exists():
            return []
        return [json.loads(z) for z in self.ziel.read_text(encoding="utf-8").splitlines() if z.strip()]

    def test_jedes_erkannte_stueck_steht_im_transkript(self) -> None:
        """Fall 1: auch was keinen Hinweis ausloest."""
        saetze = iter(["wir bauen das in TypeScript", "und zwar naechste Woche"])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""), None, self.ziel))

        self.assertEqual([z["text"] for z in self._zeilen()],
                         ["wir bauen das in TypeScript", "und zwar naechste Woche"])

    def test_stille_erzeugt_keine_zeile(self) -> None:
        """Fall 2: wie im Hinweis-Strom."""
        saetze = iter(["gesprochen", "  "])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""), None, self.ziel))

        self.assertEqual(len(self._zeilen()), 1)

    def test_ohne_schreibrecht_laeuft_die_aufnahme_weiter(self) -> None:
        """
        Fall 3: Ein Gespraech laesst sich nicht wiederholen, eine Datei schon.
        """
        gesperrt = self.ordner / "gesperrt"
        gesperrt.mkdir()
        gesperrt.chmod(0o500)
        self.addCleanup(gesperrt.chmod, 0o700)

        # Verschiedene Saetze, seit die Ueberlappung Wiederholungen
        # herausfiltert (#94). Geprueft wird hier das Schreibrecht, nicht die
        # Entdopplung — mit einem festen Satz pruefte der Test beides und
        # damit nichts Bestimmtes.
        saetze = iter(["erster Satz", "zweiter Satz"])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""), None,
                  gesperrt / "transkript.jsonl")
        )

        self.assertEqual(len(zeilen), 2, "Der Strom muss trotzdem liefern")

    def test_zeitmarken_stehen_im_transkript(self) -> None:
        saetze = iter(["etwas", "etwas anderes"])  # siehe oben, #94
        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""), None, self.ziel))

        self.assertEqual([z["zeit"] for z in self._zeilen()], [0.0, 3.0])


class KeinTonverlust(unittest.TestCase):
    """
    #80: Die Erkennung verdraengte die Aufnahme. Waehrend Whisper arbeitete,
    las niemand vom Mikrofon, und der Puffer des Geraets lief ueber.
    """

    def _langsame_quelle(self, anzahl: int, gelesen: list):
        def quelle():
            for i in range(anzahl):
                gelesen.append(i)
                yield float(i), b"\x00\x00"

        return quelle()

    def test_die_quelle_wird_gelesen_waehrend_erkannt_wird(self) -> None:
        """
        Fall 1, der Kern: Nach dem ERSTEN erkannten Stueck ist die Quelle
        bereits leergelesen. Ohne Puffer waere sie erst nach dem letzten
        durch — und beim Mikrofon hiesse "noch nicht gelesen" schlicht
        "verloren".
        """
        import time

        from scripts.mithoeren import Puffer

        gelesen: list = []
        puffer = Puffer(self._langsame_quelle(5, gelesen))

        erster = next(iter(puffer))
        time.sleep(0.2)  # Zeit, die eine Erkennung brauchen wuerde

        self.assertEqual(erster[0], 0.0)
        self.assertEqual(len(gelesen), 5, "Die Quelle muss weitergelesen worden sein")

    def test_reihenfolge_bleibt(self) -> None:
        """Fall 2."""
        from scripts.mithoeren import Puffer

        gelesen: list = []
        zeiten = [z for z, _ in Puffer(self._langsame_quelle(4, gelesen))]

        self.assertEqual(zeiten, [0.0, 1.0, 2.0, 3.0])

    def test_nichts_geht_verloren(self) -> None:
        """Fall 1, Gegenprobe: Alles, was gelesen wurde, kommt auch an."""
        from scripts.mithoeren import Puffer

        gelesen: list = []
        empfangen = list(Puffer(self._langsame_quelle(20, gelesen)))

        self.assertEqual(len(empfangen), len(gelesen))

    def test_rueckstand_erscheint_im_strom(self) -> None:
        """
        Fall 3: Ein Rueckstand gehoert in den Strom, nicht nur auf stderr.
        Eine Logdatei oeffnet im Gespraech niemand.
        """
        from scripts.mithoeren import RUECKSTAND_AB, strom

        class MitRueckstand(list):
            rueckstand = RUECKSTAND_AB + 2

        stuecke = MitRueckstand([(0.0, b"\x00"), (5.0, b"\x00")])
        zeilen = list(strom(stuecke, lambda _: "gesagt"))

        meldungen = [z for z in zeilen if z.get("art") == "rueckstand"]
        self.assertEqual(len(meldungen), 1, "genau einmal melden, nicht bei jedem Stueck")
        self.assertGreaterEqual(meldungen[0]["stuecke"], RUECKSTAND_AB)

    def test_ohne_rueckstand_keine_meldung(self) -> None:
        """Gegenprobe: Im Normalbetrieb schweigt die Meldung."""
        from scripts.mithoeren import strom

        zeilen = list(strom([(0.0, b"\x00")], lambda _: "gesagt"))

        self.assertEqual([z for z in zeilen if z.get("art") == "rueckstand"], [])


class ModellWirdGewaehlt(unittest.TestCase):
    """
    #84: Ohne Angabe nimmt mlx_whisper "whisper-tiny", das kleinste Modell.
    Eine Minute Deutsch ergab damit eine Zeile Kauderwelsch.
    """

    def test_modell_steht_als_konstante_im_modul(self) -> None:
        from scripts.mithoeren import MODELL

        self.assertTrue(MODELL, "Ein Modell muss ausdrücklich benannt sein")
        self.assertNotIn("tiny", MODELL, "tiny reicht für Deutsch nicht")

    def test_beide_zweige_nehmen_ein_modell_entgegen(self) -> None:
        """
        Ein Parameter, der nichts tut, ist schlimmer als keiner.

        Der faster-whisper-Zweig nahm die Konstante, egal was uebergeben
        wurde — gefunden von review an PR #85.
        """
        import inspect

        from scripts.mithoeren import MODELL, MODELL_FASTER, erkennung_whisper

        p = inspect.signature(erkennung_whisper).parameters
        self.assertEqual(p["modell"].default, MODELL)
        self.assertEqual(p["modell_faster"].default, MODELL_FASTER)

    def test_kein_zweig_greift_an_der_konstante_vorbei(self) -> None:
        """
        Im Rumpf darf keine Konstante mehr direkt stehen — sonst haengt der
        Zweig wieder an ihr statt am Parameter.
        """
        import inspect

        from scripts.mithoeren import erkennung_whisper

        rumpf = inspect.getsource(erkennung_whisper)
        for konstante in ("MODELL_FASTER,", "MODELL,"):
            self.assertNotIn(
                konstante + " device", rumpf, "Zweig nutzt die Konstante statt des Parameters"
            )
        self.assertIn("modell_faster", rumpf)
        self.assertIn("path_or_hf_repo=modell", rumpf)


class UeberlappendeStuecke(unittest.TestCase):
    """
    #94: Starre Schnitte zerlegen Saetze. Eine Minute Gespraech ergab eine
    Zeile, weil Whisper aus Bruchstuecken nichts macht und leere Zeilen
    verworfen werden.
    """

    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.quelle = self.ordner / "probe.wav"
        wav_schreiben(self.quelle, sekunden=9.0)

    def test_stuecke_ueberlappen_sich(self) -> None:
        """Fall 1: Jedes Stueck traegt das Ende des vorigen."""
        stuecke = list(stuecke_aus_datei(self.quelle, sekunden=3.0, ueberlappung=1.0))

        self.assertGreaterEqual(len(stuecke), 2)
        erwartet = int(ABTASTRATE * 3.0) * BREITE
        self.assertEqual(len(stuecke[0][1]), erwartet, "Das erste hat nichts davor")
        self.assertEqual(
            len(stuecke[1][1]), erwartet + int(ABTASTRATE * 1.0) * BREITE,
            "Das zweite traegt eine Sekunde mehr",
        )

    def test_ohne_ueberlappung_bleibt_alles_wie_vorher(self) -> None:
        """Gegenprobe: ueberlappung=0 ergibt die alten, starren Stuecke."""
        stuecke = list(stuecke_aus_datei(self.quelle, sekunden=3.0, ueberlappung=0.0))

        erwartet = int(ABTASTRATE * 3.0) * BREITE
        for _, daten in stuecke:
            self.assertEqual(len(daten), erwartet)

    def test_derselbe_satz_zweimal_gibt_eine_zeile(self) -> None:
        """Fall 2: Die Ueberlappung darf keinen Hinweis verdoppeln."""
        saetze = iter(["das muss schnell gehen", "das muss schnell gehen", "und noch etwas"])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""))
        )

        texte = [z["text"] for z in zeilen]
        self.assertEqual(texte, ["das muss schnell gehen", "und noch etwas"])

    def test_zwei_verschiedene_saetze_geben_zwei_zeilen(self) -> None:
        """
        Fall 3, die Gegenprobe zu Fall 2: Ohne ihn bestuende der auch bei
        einer Umsetzung, die alles nach der ersten Zeile verwirft.
        """
        saetze = iter(["erster Satz", "zweiter Satz", "dritter Satz"])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""))
        )

        self.assertEqual([z["text"] for z in zeilen],
                         ["erster Satz", "zweiter Satz", "dritter Satz"])

    def test_ein_satz_darf_spaeter_wiederkehren(self) -> None:
        """Nur unmittelbare Wiederholung zaehlt — wer zweimal dasselbe sagt, sagt es zweimal."""
        saetze = iter(["das muss schnell gehen", "etwas anderes", "das muss schnell gehen"])
        zeilen = list(
            strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""))
        )

        self.assertEqual(len(zeilen), 3)


class TaktKanal(unittest.TestCase):
    """
    Eine Zeile je Stueck, auch fuer Stille (#127).

    Getrennt vom Transkript: Dort steht weiterhin nur, was gesagt wurde —
    `test_stille_erzeugt_keine_zeile` gilt unveraendert. Der Unterschied ist
    der Punkt: Im Transkript ist Stille ein Ausbleiben, im Takt eine Aussage.
    """

    def setUp(self) -> None:
        self.ordner = Path(tempfile.mkdtemp())
        self.quelle = self.ordner / "ton.wav"
        wav_schreiben(self.quelle, sekunden=9.0)
        self.takt = self.ordner / "takt.jsonl"
        self.transkript = self.ordner / "transkript.jsonl"

    def _takte(self) -> list[dict]:
        import json

        if not self.takt.exists():
            return []
        return [json.loads(z) for z in self.takt.read_text(encoding="utf-8").splitlines() if z.strip()]

    def test_jedes_stueck_steht_im_takt_auch_das_stille(self) -> None:
        saetze = iter(["gesprochen", "   ", "wieder gesprochen"])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""),
                   None, self.transkript, self.takt))

        self.assertEqual([t["gesprochen"] for t in self._takte()], [True, False, True])

    def test_das_transkript_bleibt_frei_von_stille(self) -> None:
        import json

        saetze = iter(["gesprochen", "   ", "wieder gesprochen"])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""),
                   None, self.transkript, self.takt))

        zeilen = [json.loads(z) for z in self.transkript.read_text(encoding="utf-8").splitlines() if z.strip()]
        self.assertEqual([z["text"] for z in zeilen], ["gesprochen", "wieder gesprochen"])

    def test_der_takt_traegt_die_zeitmarke_des_stuecks(self) -> None:
        saetze = iter(["eins", "zwei", "drei"])

        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: next(saetze, ""),
                   None, self.transkript, self.takt))

        self.assertEqual([t["zeit"] for t in self._takte()], [0.0, 3.0, 6.0])

    def test_ohne_takt_pfad_entsteht_keine_datei(self) -> None:
        """Ein Kanal, den niemand bestellt hat, wird nicht geoeffnet."""
        list(strom(stuecke_aus_datei(self.quelle, 3.0), lambda _: "x", None, self.transkript))

        self.assertFalse(self.takt.exists())
