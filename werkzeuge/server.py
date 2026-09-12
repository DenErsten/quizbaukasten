#!/usr/bin/env python3
"""
Lokaler Server fuer die Live-Anzeige — #69.

Ein Browser kann scripts/mithoeren.py nicht selbst starten. Dieser Server
haengt die Bedienung (Start, Stop, Status) und die Datei mit den Hinweisen
an drei kleine Wege, und liefert sonst die Dateien aus werkzeuge/ aus.

WARUM DER STARTVORGANG EINSETZBAR IST
--------------------------------------
Wie `erkennen` in mithoeren.py: Ohne eine austauschbare Stelle bräuchte ein
Test entweder Whisper und ein Mikrofon, oder er würde behaupten, etwas
liefe, ohne dass ein echter Vorgang je gestartet wurde. `Aufnahme` nimmt
deshalb `prozess_starten` als Argument entgegen — die Tests setzen dort einen
echten, aber genügsamen Vorgang ein statt der Hoer-Kette.

WARUM /hinweise NICHT AN EINEN LAUFENDEN VORGANG GEBUNDEN IST
---------------------------------------------------------------
Die Datei mit den Hinweisen liegt unter einem Namen, der nur vom Datum
abhängt (aufnahmen/<datum>-hinweise.jsonl). Wer die Seite neu lädt, nachdem
der Server neu gestartet wurde, soll trotzdem die Hinweise des Tages sehen —
nicht nur die einer laufenden Aufnahme.

WARUM EINE KAPUTTE ZEILE NICHT DIE ANTWORT KIPPT
--------------------------------------------------
Die Datei wird geschrieben, waehrend sie gelesen wird. Eine halb
geschriebene letzte Zeile ist der Normalfall, nicht die Ausnahme — siehe
Fall 5 in tests/server_test.py.

NUR 127.0.0.1
-------------
Das Werkzeug hoert ein Gespraech mit. Es hat im Netz nichts zu suchen.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Protocol

WURZEL = Path(__file__).resolve().parent.parent
WERKZEUGE = Path(__file__).resolve().parent
ANLAUF_SEKUNDEN = 0.5

# Dasselbe Modell wie in scripts/mithoeren.py. Import statt Kopie: Zwei
# Stellen, die dasselbe behaupten, laufen frueher oder spaeter auseinander.
try:
    from scripts.mithoeren import MODELL
except ImportError:  # pragma: no cover
    MODELL = "mlx-community/whisper-small-mlx"
AUFNAHMEN = WURZEL / "aufnahmen"

# Der Leitfaden hat bewusst KEINEN Ersatzwert im Code. Er steht in
# docs/leitfaden.md und nirgends sonst; eine Kopie hier waere genau die zweite
# Wahrheit, die der Punkt vermeiden soll (#101). Fehlt die Datei, sagt das
# Werkzeug das, statt einen leeren Leitfaden zu zeigen.
if str(WURZEL) not in sys.path:
    sys.path.insert(0, str(WURZEL))
from scripts.anforderungen import ableiten, als_issue  # noqa: E402
from scripts.interview import Interview  # noqa: E402
from scripts.leitfaden import lesen as leitfaden_lesen  # noqa: E402


class Prozess(Protocol):
    """Das Stueck Schnittstelle von subprocess.Popen, das Aufnahme braucht."""

    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...
    def fehler_text(self) -> str:
        """Was schiefging, wenn der Vorgang starb. Leer, wenn nichts."""
        ...


class Pipeline:
    """mithoeren.py | ausloeser.py als ein Vorgang, den Aufnahme steuern kann."""

    def __init__(
        self, prozesse: list[subprocess.Popen], fehlerdatei: Path | None = None
    ) -> None:
        self._prozesse = prozesse
        self._fehlerdatei = fehlerdatei

    def poll(self) -> int | None:
        # Ein Teil der Pipeline reicht: Stirbt mithoeren.py mit einem Fehler,
        # endet ausloeser.py sauber am geschlossenen Eingang — und die
        # Pipeline haette "beendet, alles gut" gemeldet, obwohl nie ein Wort
        # erkannt wurde.
        for p in self._prozesse:
            ergebnis = p.poll()
            if ergebnis is not None and ergebnis != 0:
                return ergebnis
        return self._prozesse[-1].poll()

    def fehler_text(self) -> str:
        if self._fehlerdatei is None or not self._fehlerdatei.exists():
            return ""
        zeilen = [z.strip() for z in self._fehlerdatei.read_text(
            encoding="utf-8", errors="replace").splitlines() if z.strip()]
        # Die letzte Zeile eines Tracebacks ist die, die den Grund nennt.
        return zeilen[-1] if zeilen else ""

    def terminate(self) -> None:
        for p in self._prozesse:
            if p.poll() is None:
                p.terminate()

    def wait(self, timeout: float | None = None) -> int:
        ergebnis = 0
        for p in self._prozesse:
            ergebnis = p.wait(timeout=timeout)
        return ergebnis


def _pipeline_starten(datei: Path) -> Pipeline:
    """
    Der echte Vorgang: nur noch mithoeren.py, Transkript in eine Datei.

    ausloeser.py haengt seit #114 nicht mehr darin. Es rief mitten im Satz
    dazwischen; das Gespraech wird jetzt gefuehrt statt kommentiert, und die
    Entscheidung faellt in Gespraechspausen (scripts/interview.py). Die Datei
    bleibt im Repo und laesst sich weiter allein aufrufen — was aus ihr wird,
    entscheidet ein eigenes Issue.

    `datei` (die Hinweisdatei) wird weiterhin angelegt, aber leer. So bleibt
    /hinweise ein gueltiger Weg mit einer ehrlichen Antwort: nichts.
    """
    datei.parent.mkdir(parents=True, exist_ok=True)
    # stderr in eine Datei statt ins Nichts. Vorher ging jede Fehlermeldung
    # der Pipeline verloren — fehlte Whisper, stand nirgends warum (#76).
    fehlerdatei = datei.with_name(datei.stem + ".fehler.log")
    # --transkript: Der erkannte Text wird abgelegt, nicht nur das, was
    # ein Hinweis wird. Sonst ist "nichts gesagt" von "nichts gehoert"
    # nicht zu unterscheiden, und meeting-nacharbeit hat kein Protokoll
    # zum Nacharbeiten (#81).
    transkript = datei.with_name(datei.name.replace("-hinweise", "-transkript"))
    if not datei.exists():
        datei.touch()
    with fehlerdatei.open("w", encoding="utf-8") as fehler:
        mithoeren = subprocess.Popen(
            [sys.executable, str(WURZEL / "scripts" / "mithoeren.py"),
             "--transkript", str(transkript)],
            stdout=subprocess.DEVNULL,
            stderr=fehler,
        )
    return Pipeline([mithoeren], fehlerdatei)


def modell_vorhanden(modell: str = MODELL) -> bool:
    """
    Liegt das Modell vollstaendig im Cache? Ohne es zu laden.

    local_files_only wirft, wenn etwas fehlt — auch wenn ein angefangener
    Download Bruchstuecke hinterlassen hat. Genau das war am 2026-09-12 der
    Fall: 3,7 MB von 459 (#87).
    """
    try:
        from huggingface_hub import snapshot_download  # noqa: PLC0415

        snapshot_download(modell, local_files_only=True)
        return True
    except Exception:
        return False


def modell_laden(modell: str = MODELL) -> None:
    """Holt das Modell. Dauert beim ersten Mal Minuten."""
    from huggingface_hub import snapshot_download  # noqa: PLC0415

    snapshot_download(modell)


class Aufnahme:
    """Startet, stoppt und befragt genau eine Aufnahme gleichzeitig."""

    def __init__(
        self,
        aufnahmen_ordner: Path = AUFNAHMEN,
        prozess_starten: Callable[[Path], Prozess] = _pipeline_starten,
        modell_pruefen: Callable[[], bool] = modell_vorhanden,
        modell_holen: Callable[[], None] = modell_laden,
    ) -> None:
        self.aufnahmen_ordner = aufnahmen_ordner
        self._prozess_starten = prozess_starten
        self._modell_pruefen = modell_pruefen
        self._modell_holen = modell_holen
        self._laedt = False
        self._sperre = threading.Lock()
        self._prozess: Prozess | None = None
        self._seit: str | None = None
        self._fehler: str | None = None

    def _datei(self) -> Path:
        datum = datetime.now().strftime("%Y-%m-%d")
        return self.aufnahmen_ordner / f"{datum}-hinweise.jsonl"

    def _transkriptdatei(self) -> Path:
        return self._datei().with_name(self._datei().name.replace("-hinweise", "-transkript"))

    def _laeuft(self) -> bool:
        return self._prozess is not None and self._prozess.poll() is None

    def start(self) -> None:
        """
        Fall 2: Ein zweiter Aufruf bei laufender Aufnahme tut nichts.

        Nach dem Start wird kurz nachgesehen, ob der Vorgang ueberhaupt
        lebt. Ohne das war ein gescheiterter Start von "nicht gestartet"
        nicht zu unterscheiden: Die Ansicht fiel stumm auf "bereit"
        zurueck, und niemand erfuhr warum (#76).
        """
        with self._sperre:
            if self._laeuft() or self._laedt:
                return
            self._fehler = None

            # Das Modell wird beim ersten Erkennungsaufruf geholt — mitten in
            # der laufenden Aufnahme, 459 MB, unsichtbar. Am 2026-09-12 hat
            # das zwei Versuche gekostet: Download beginnt, Aufnahme wird
            # gestoppt, Vorgang stirbt, beim naechsten Mal von vorn (#87).
            if not self._modell_pruefen():
                self._laedt = True
                threading.Thread(target=self._modell_holen_und_melden, daemon=True).start()
                return

            prozess = self._prozess_starten(self._datei())

            # Ein Importfehler faellt in Sekundenbruchteilen an. Wer bis
            # hierhin lebt, ist gestartet; was spaeter stirbt, faellt beim
            # naechsten Status auf.
            time.sleep(ANLAUF_SEKUNDEN)
            if prozess.poll() is not None:
                self._fehler = prozess.fehler_text() or "Der Vorgang endete sofort."
                self._prozess = None
                self._seit = None
                return

            self._prozess = prozess
            self._seit = datetime.now().isoformat(timespec="seconds")

    def _modell_holen_und_melden(self) -> None:
        """
        Holt das Modell und startet danach, wonach gefragt wurde.

        Ohne den zweiten start() stuende nach dem Download wieder "bereit"
        da — und wer auf Start gedrueckt hat, muesste ein zweites Mal
        druecken, ohne zu wissen warum.
        """
        geglueckt = False
        try:
            self._modell_holen()
            geglueckt = True
        except Exception as fehler:  # noqa: BLE001
            # Ein abgebrochener Download darf nicht als "bereit" erscheinen.
            self._fehler = f"Modell konnte nicht geladen werden: {fehler}"
        finally:
            self._laedt = False

        if geglueckt:
            self.start()

    def stop(self) -> None:
        """Fall 3: Ohne laufende Aufnahme ist stop wirkungslos, kein Fehler."""
        with self._sperre:
            # Zuerst, und vor jedem Ausstieg: Ein alter Fehler darf nicht am
            # naechsten Start kleben. Nach einem gescheiterten Start ist
            # _prozess bereits None — wuerde hier frueher ausgestiegen,
            # zeigte die Oberflaeche beim zweiten Versuch den ersten Fehler.
            self._fehler = None
            if self._prozess is None:
                return
            if self._prozess.poll() is None:
                self._prozess.terminate()
                self._prozess.wait(timeout=5)
            self._prozess = None
            self._seit = None

    def _zeilen(self, datei: Path) -> list[dict]:
        """
        Fehlende Datei -> leer, kaputte Zeile -> ueberspringen.

        Die Datei wird geschrieben, waehrend sie gelesen wird: Eine halb
        geschriebene letzte Zeile ist der Normalfall, nicht die Ausnahme.
        """
        if not datei.exists():
            return []
        ergebnisse = []
        for zeile in datei.read_text(encoding="utf-8").splitlines():
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                ergebnisse.append(json.loads(zeile))
            except json.JSONDecodeError:
                continue
        return ergebnisse

    def hinweise(self) -> list[dict]:
        return self._zeilen(self._datei())

    def transkript(self) -> list[dict]:
        """
        Was das Werkzeug gehoert hat.

        Ohne das sehen "hoert zu, nichts war unscharf" und "hoert nichts"
        gleich aus — beide eine leere Flaeche (#99).
        """
        return self._zeilen(self._transkriptdatei())

    def status(self) -> dict:
        """Fall 1: laeuft spiegelt start/stop."""
        laeuft = self._laeuft()
        # Ein Vorgang, der nach dem Start stirbt, meldet sich hier.
        if not laeuft and self._prozess is not None:
            self._fehler = self._prozess.fehler_text() or "Der Vorgang endete unerwartet."
            self._prozess = None
            self._seit = None
        return {
            "laeuft": laeuft,
            "laedt_modell": self._laedt,
            "seit": self._seit if laeuft else None,
            "hinweise": len(self.hinweise()),
            "fehler": self._fehler,
        }


class Gespraech:
    """
    Das gefuehrte Erstgespraech, gefuettert aus dem Transkript (#114).

    Das Interview bekommt keinen eigenen Draht zum Mikrofon. Es liest, was
    mithoeren.py ohnehin schreibt — eine Quelle, kein zweiter Lauschposten.

    `uhr` ist einsetzbar, damit Tests ein ganzes Gespraech in Millisekunden
    durchspielen koennen, statt drei Sekunden zu warten.
    """

    def __init__(
        self,
        verwaltung: "Aufnahme",
        punkte_lesen: Callable[[], list[dict]] = leitfaden_lesen,
        uhr: Callable[[], float] = time.monotonic,
    ) -> None:
        self._verwaltung = verwaltung
        self._punkte_lesen = punkte_lesen
        self._uhr = uhr
        self._sperre = threading.Lock()
        self._interview: Interview | None = None
        self._ab = 0
        self._gelesen = 0
        self._letztes: dict | None = None
        self._fehler: str | None = None

    def zuruecksetzen(self) -> None:
        """
        Neues Gespraech. Alles, was heute schon im Transkript steht, gilt als
        vergangen — die Datei laeuft ueber den Tag, das Gespraech nicht.
        """
        with self._sperre:
            self._ab = len(self._verwaltung.transkript())
            self._gelesen = self._ab
            self._letztes = None
            self._fehler = None
            try:
                self._interview = Interview(self._punkte_lesen())
            except Exception as fehler:  # noqa: BLE001
                # Ein kaputter Leitfaden darf die Aufnahme nicht verhindern —
                # aber er darf auch nicht so aussehen, als liefe ein Interview.
                self._interview = None
                self._fehler = str(fehler)

    def stand(self) -> dict:
        with self._sperre:
            if self._interview is None:
                return {"laeuft": False, "fehler": self._fehler}

            zeilen = self._verwaltung.transkript()
            jetzt = self._uhr()
            for zeile in zeilen[self._gelesen:]:
                self._interview.gehoert(jetzt, str(zeile.get("text", "")))
            self._gelesen = len(zeilen)

            ereignis = self._interview.takt(jetzt)
            if ereignis is not None:
                self._letztes = ereignis
            return {"laeuft": True, "fehler": None, "letztes": self._letztes,
                    **self._interview.stand()}


class Ableitung:
    """
    Der Schritt vom Transkript zu Anforderungs-Entwuerfen (#102).

    Zwei Eigenschaften sind nicht Bequemlichkeit, sondern Regel aus
    docs/plan.md, Abschnitt "Was den Rechner verlaesst":

    1. Es passiert nur, wenn jemand `ableiten()` aufruft — nie beim Start,
       nie nach dem Stoppen der Aufnahme, nie im Hintergrund.
    2. Es entsteht kein Issue. `uebernehmen()` ist ein zweiter, eigener
       Schritt, und den loest ein Mensch aus.

    `ableiten_mit` und `anlegen_mit` sind einsetzbar, damit die Tests weder
    das Abo noch GitHub brauchen.
    """

    def __init__(
        self,
        verwaltung: "Aufnahme",
        ableiten_mit: Callable[..., list[dict]] = ableiten,
        anlegen_mit: Callable[[str, str], str] | None = None,
        punkte_lesen: Callable[[], list[dict]] = leitfaden_lesen,
    ) -> None:
        self._verwaltung = verwaltung
        self._ableiten = ableiten_mit
        self._anlegen = anlegen_mit
        self._punkte_lesen = punkte_lesen
        self._sperre = threading.Lock()
        self._laeuft = False
        self._fehler: str | None = None
        self._entwuerfe: list[dict] = []
        self._angelegt: dict[int, str] = {}
        # Ohne dieses Feld sehen "noch nie abgeleitet" und "abgeleitet, nichts
        # gefunden" in der Anzeige gleich aus — eine leere Liste (#99).
        self._abgeleitet = False

    def _stand(self) -> dict:
        """Ohne Sperre — nur aufrufen, wer sie schon haelt."""
        return {
            "laeuft": self._laeuft,
            "abgeleitet": self._abgeleitet,
            "fehler": self._fehler,
            "entwuerfe": list(self._entwuerfe),
            "angelegt": {str(k): v for k, v in self._angelegt.items()},
        }

    def stand(self) -> dict:
        with self._sperre:
            return self._stand()

    def ableiten(self) -> dict:
        """Startet die Ableitung im Hintergrund. Zweimal druecken tut nichts."""
        with self._sperre:
            if self._laeuft:
                return self._stand()
            zeilen = self._verwaltung.transkript()
            if not zeilen:
                self._fehler = "Kein Transkript da. Erst ein Gespräch aufnehmen."
                return self._stand()
            self._laeuft = True
            self._fehler = None
            self._entwuerfe = []
            self._angelegt = {}
        threading.Thread(target=self._arbeiten, args=(zeilen,), daemon=True).start()
        return self.stand()

    def _arbeiten(self, zeilen: list[dict]) -> None:
        try:
            gefunden = self._ableiten(zeilen, self._punkte_lesen())
        except Exception as fehler:  # noqa: BLE001
            # Ein stiller Fehlschlag saehe aus wie "nichts gefunden". Genau
            # dieser Unterschied hat in #99 einen Tag gekostet.
            with self._sperre:
                self._fehler = str(fehler)
                self._laeuft = False
            return
        with self._sperre:
            self._entwuerfe = gefunden
            self._abgeleitet = True
            self._laeuft = False

    def uebernehmen(self, nummer: int) -> str:
        """Macht aus genau einem Entwurf ein Issue — nach einem Klick."""
        with self._sperre:
            if nummer < 0 or nummer >= len(self._entwuerfe):
                raise IndexError(f"Kein Entwurf Nummer {nummer}.")
            if nummer in self._angelegt:
                return self._angelegt[nummer]
            entwurf = self._entwuerfe[nummer]

        anlegen = self._anlegen or _freigabe_modul().issue_anlegen
        url = anlegen(*als_issue(entwurf))
        with self._sperre:
            self._angelegt[nummer] = url
        return url


def _freigabe_modul():
    """
    Beim Aufruf `python3 werkzeuge/server.py` liegt werkzeuge/ selbst im
    Suchpfad, nicht das Repo — dann gibt es kein Paket "werkzeuge". Die Tests
    rufen aus der Wurzel und sehen es. Beide Wege muessen gehen.
    """
    try:
        from werkzeuge import freigabe  # noqa: PLC0415

        return freigabe
    except ImportError:
        import freigabe  # noqa: PLC0415

        return freigabe


class Anfrage(SimpleHTTPRequestHandler):
    """Drei bediente Wege, alles andere aus werkzeuge/ ausgeliefert."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(WERKZEUGE), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 (Name kommt aus der Standardbibliothek)
        if self.path == "/status":
            self._json(self.server.verwaltung.status())  # type: ignore[attr-defined]
            return
        if self.path == "/hinweise":
            self._json(self.server.verwaltung.hinweise())  # type: ignore[attr-defined]
            return
        if self.path == "/transkript":
            self._json(self.server.verwaltung.transkript())  # type: ignore[attr-defined]
            return
        if self.path == "/interview":
            self._json(self.server.gespraech.stand())  # type: ignore[attr-defined]
            return
        if self.path == "/leitfaden":
            self._leitfaden()
            return
        if self.path == "/anforderungen":
            self._json(self.server.ableitung.stand())  # type: ignore[attr-defined]
            return
        if self.path == "/entscheidungen":
            self._entscheidungen()
            return
        if self.path == "/freigaben":
            self._freigaben()
            return
        if self.path == "/fortschritt":
            self._fortschritt()
            return
        super().do_GET()

    def _leitfaden(self) -> None:
        """
        Die fuenf Fragen aus docs/leitfaden.md.

        Ein Fehler wird durchgereicht statt verschluckt: Wer im Gespraech eine
        leere Spalte sieht, soll wissen, ob nichts da ist oder nichts gelesen
        werden konnte.
        """
        try:
            self._json(leitfaden_lesen())
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def _entscheidungen(self) -> None:
        """
        Die offenen Entscheidungen (#108).

        Eigener Weg statt Anhaengsel an /freigaben: Freigeben und entscheiden
        sind zwei verschiedene Dinge, und was in der Oberflaeche getrennt ist,
        soll es auch hier sein.
        """
        try:
            self._json(_freigabe_modul().offene_entscheidungen())
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def _freigaben(self) -> None:
        freigabe = _freigabe_modul()

        try:
            self._json({
                "issues": freigabe.offene_issues(),
                "prs": freigabe.offene_prs(),
                "laeufe": freigabe.laufende_laeufe(),
            })
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/aufnahme/start":
            self.server.verwaltung.start()  # type: ignore[attr-defined]
            self.server.gespraech.zuruecksetzen()  # type: ignore[attr-defined]
            self._json(self.server.verwaltung.status())  # type: ignore[attr-defined]
            return
        if self.path == "/aufnahme/stop":
            self.server.verwaltung.stop()  # type: ignore[attr-defined]
            self._json(self.server.verwaltung.status())  # type: ignore[attr-defined]
            return
        if self.path == "/anforderungen/ableiten":
            self._json(self.server.ableitung.ableiten())  # type: ignore[attr-defined]
            return
        if self.path.startswith("/anforderungen/uebernehmen/"):
            self._uebernehmen()
            return
        if self.path.startswith("/entscheidung/"):
            self._entscheiden()
            return
        if self.path.startswith("/freigabe/") or self.path.startswith("/kommentar/"):
            self._handeln()
            return
        self.send_error(404)

    def _fortschritt(self) -> None:
        freigabe = _freigabe_modul()

        try:
            self._json(freigabe.fortschritt())
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def _entscheiden(self) -> None:
        """
        /entscheidung/<nr>/<buchstabe> — schreibt die Wahl als Kommentar.

        Setzt kein Label. Entscheiden und freigeben bleiben zwei Handgriffe
        (#108).
        """
        teile = self.path.strip("/").split("/")
        if len(teile) != 3:
            self.send_error(404)
            return
        try:
            nummer = int(teile[1])
        except ValueError:
            self.send_error(404)
            return
        try:
            _freigabe_modul().entscheiden(nummer, teile[2])
            self._json({"ok": True})
        except ValueError as fehler:
            self._json({"fehler": str(fehler)}, 400)
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def _uebernehmen(self) -> None:
        """Ein Entwurf, ein Issue, ein Klick. Fehler werden durchgereicht."""
        try:
            nummer = int(self.path.rsplit("/", 1)[-1])
        except ValueError:
            self.send_error(404)
            return
        try:
            self._json({"url": self.server.ableitung.uebernehmen(nummer)})  # type: ignore[attr-defined]
        except IndexError as fehler:
            self._json({"fehler": str(fehler)}, 404)
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def _handeln(self) -> None:
        """
        Freigeben und kommentieren. Fehler werden durchgereicht: Ein Knopf,
        der nichts tut und Erfolg meldet, ist schlimmer als keiner.
        """
        freigabe = _freigabe_modul()

        teile = self.path.strip("/").split("/")
        laenge = int(self.headers.get("Content-Length") or 0)
        daten = json.loads(self.rfile.read(laenge) or b"{}") if laenge else {}

        try:
            if teile[0] == "freigabe" and len(teile) == 3:
                art, nummer = teile[1], int(teile[2])
                if art == "issue":
                    freigabe.issue_freigeben(nummer)
                elif art == "pr":
                    freigabe.pr_freigeben(nummer)
                else:
                    self.send_error(404)
                    return
            elif teile[0] == "kommentar" and len(teile) == 3:
                text = str(daten.get("text", "")).strip()
                if not text:
                    self._json({"fehler": "Ein leerer Kommentar hilft niemandem."}, 400)
                    return
                freigabe.kommentieren(teile[1], int(teile[2]), text)
            else:
                self.send_error(404)
                return
            self._json({"ok": True})
        except Exception as fehler:  # noqa: BLE001
            self._json({"fehler": str(fehler)}, 502)

    def _json(self, daten: object, code: int = 200) -> None:
        koerper = json.dumps(daten).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(koerper)))
        self.end_headers()
        self.wfile.write(koerper)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass  # Zugriffe aufs Werkzeug sind kein Betriebslog


def server_starten(
    verwaltung: Aufnahme,
    port: int = 0,
    ableitung: Ableitung | None = None,
    gespraech: Gespraech | None = None,
) -> ThreadingHTTPServer:
    """Baut den Server, bindet ihn nur an 127.0.0.1 — kein Port nach aussen."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Anfrage)
    server.verwaltung = verwaltung  # type: ignore[attr-defined]
    server.ableitung = ableitung or Ableitung(verwaltung)  # type: ignore[attr-defined]
    server.gespraech = gespraech or Gespraech(verwaltung)  # type: ignore[attr-defined]
    return server


def main() -> int:
    verwaltung = Aufnahme()
    server = server_starten(verwaltung, port=8000)
    print(f"Server läuft auf http://127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    finally:
        verwaltung.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
