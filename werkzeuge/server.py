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
AUFNAHMEN = WURZEL / "aufnahmen"


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
    """Der echte Vorgang: mithoeren.py | ausloeser.py, Ausgabe in `datei`."""
    datei.parent.mkdir(parents=True, exist_ok=True)
    # stderr in eine Datei statt ins Nichts. Vorher ging jede Fehlermeldung
    # der Pipeline verloren — fehlte Whisper, stand nirgends warum (#76).
    fehlerdatei = datei.with_name(datei.stem + ".fehler.log")
    with fehlerdatei.open("w", encoding="utf-8") as fehler:
        mithoeren = subprocess.Popen(
            [sys.executable, str(WURZEL / "scripts" / "mithoeren.py")],
            stdout=subprocess.PIPE,
            stderr=fehler,
        )
        with datei.open("w", encoding="utf-8") as ziel:
            ausloeser = subprocess.Popen(
                [sys.executable, str(WURZEL / "scripts" / "ausloeser.py")],
                stdin=mithoeren.stdout,
                stdout=ziel,
                stderr=fehler,
            )
    assert mithoeren.stdout is not None
    mithoeren.stdout.close()  # sonst haelt der Server selbst die Pipe offen
    return Pipeline([mithoeren, ausloeser], fehlerdatei)


class Aufnahme:
    """Startet, stoppt und befragt genau eine Aufnahme gleichzeitig."""

    def __init__(
        self,
        aufnahmen_ordner: Path = AUFNAHMEN,
        prozess_starten: Callable[[Path], Prozess] = _pipeline_starten,
    ) -> None:
        self.aufnahmen_ordner = aufnahmen_ordner
        self._prozess_starten = prozess_starten
        self._sperre = threading.Lock()
        self._prozess: Prozess | None = None
        self._seit: str | None = None
        self._fehler: str | None = None

    def _datei(self) -> Path:
        datum = datetime.now().strftime("%Y-%m-%d")
        return self.aufnahmen_ordner / f"{datum}-hinweise.jsonl"

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
            if self._laeuft():
                return
            self._fehler = None
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

    def hinweise(self) -> list[dict]:
        """Fall 4 und 5: fehlende Datei -> leer, kaputte Zeile -> ueberspringen."""
        datei = self._datei()
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
            "seit": self._seit if laeuft else None,
            "hinweise": len(self.hinweise()),
            "fehler": self._fehler,
        }


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
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/aufnahme/start":
            self.server.verwaltung.start()  # type: ignore[attr-defined]
            self._json(self.server.verwaltung.status())  # type: ignore[attr-defined]
            return
        if self.path == "/aufnahme/stop":
            self.server.verwaltung.stop()  # type: ignore[attr-defined]
            self._json(self.server.verwaltung.status())  # type: ignore[attr-defined]
            return
        self.send_error(404)

    def _json(self, daten: object) -> None:
        koerper = json.dumps(daten).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(koerper)))
        self.end_headers()
        self.wfile.write(koerper)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass  # Zugriffe aufs Werkzeug sind kein Betriebslog


def server_starten(verwaltung: Aufnahme, port: int = 0) -> ThreadingHTTPServer:
    """Baut den Server, bindet ihn nur an 127.0.0.1 — kein Port nach aussen."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Anfrage)
    server.verwaltung = verwaltung  # type: ignore[attr-defined]
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
