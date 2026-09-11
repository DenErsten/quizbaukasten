#!/usr/bin/env python3
"""
Sprachdialog mit dem Projektagenten — Push-to-Talk im Terminal.

Enter drücken, sprechen, Enter drücken. Der Agent antwortet vorgelesen und
behält den Gesprächsfaden über die ganze Sitzung.

WARUM DIE CLI UND NICHT DAS AGENT-SDK
-------------------------------------
Das Agent SDK erwartet einen API-Key. Die Claude-Code-CLI nutzt die Anmeldung
deines Abos. Deshalb ruft dieses Skript `claude -p` als Unterprozess auf und
liest die JSON-Antwort — dieselbe Agentenschleife, dieselben Skills, dieselbe
CLAUDE.md, ohne zusätzliche Kosten.

GATES BLEIBEN
-------------
Der Sprachagent bekommt bewusst nur lesende Werkzeuge plus Issue-Entwürfe.
Gesprochene Sprache wird falsch erkannt, und ein verhörtes "merge das" darf
keine Tatsache erzeugen. Was etwas verändert, passiert getippt und gesehen.

INSTALLATION
------------
    pip install sounddevice numpy soundfile
    # Apple Silicon:
    pip install mlx-whisper
    # sonst:
    pip install faster-whisper
    # Sprachausgabe (optional, sonst 'say' auf macOS bzw. Textausgabe):
    pip install kokoro soundfile

AUFRUF
------
    python scripts/voice_dialog.py
    python scripts/voice_dialog.py --stumm      # ohne Sprachausgabe
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading

SAMPLERATE = 16000

SYSTEM_ZUSATZ = (
    "Du sprichst mit Firat per Sprache. Antworte deutsch, in hoechstens vier "
    "Saetzen, ohne Aufzaehlungszeichen und ohne Markdown — der Text wird "
    "vorgelesen. Sprache wird manchmal falsch erkannt: wenn eine Anweisung "
    "unplausibel klingt, frag nach, statt zu handeln. Du darfst lesen und "
    "Issue-Entwuerfe anlegen. Du mergest nichts, gibst nichts frei und "
    "sendest nichts."
)

WERKZEUGE = ",".join(
    [
        "Read",
        "Glob",
        "Grep",
        "Bash(gh issue list:*)",
        "Bash(gh issue view:*)",
        "Bash(gh pr list:*)",
        "Bash(gh pr view:*)",
        "Bash(gh pr diff:*)",
        "Bash(gh run list:*)",
        "Bash(git log:*)",
        "Bash(git status:*)",
        "Bash(gh issue create:*)",
    ]
)


# ----------------------------------------------------------------- Aufnahme
def aufnehmen() -> str:
    """Nimmt auf, bis Enter gedrückt wird. Gibt den Pfad zur WAV-Datei zurück."""
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    puffer: queue.Queue = queue.Queue()
    laeuft = threading.Event()
    laeuft.set()

    def callback(indata, frames, zeit, status):  # noqa: ANN001
        if status:
            print(f"  (Audio-Status: {status})", file=sys.stderr)
        puffer.put(indata.copy())

    def warte_auf_enter():
        try:
            input()
        except EOFError:
            pass
        laeuft.clear()

    threading.Thread(target=warte_auf_enter, daemon=True).start()

    with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype="float32",
                        callback=callback):
        while laeuft.is_set():
            sd.sleep(80)

    stuecke = []
    while not puffer.empty():
        stuecke.append(puffer.get())
    if not stuecke:
        return ""

    audio = np.concatenate(stuecke, axis=0)
    pfad = tempfile.mktemp(suffix=".wav")
    sf.write(pfad, audio, SAMPLERATE)
    return pfad


# ----------------------------------------------------------------- Erkennung
class Erkenner:
    """Lädt das Spracherkennungsmodell einmal und hält es warm."""

    def __init__(self) -> None:
        self.art = None
        self.modell = None
        try:
            import mlx_whisper  # noqa: F401

            self.art = "mlx"
            print("Spracherkennung: mlx-whisper (large-v3)")
            return
        except ImportError:
            pass
        try:
            from faster_whisper import WhisperModel

            self.modell = WhisperModel("large-v3", device="auto", compute_type="int8")
            self.art = "faster"
            print("Spracherkennung: faster-whisper (large-v3)")
            return
        except ImportError:
            pass
        sys.exit("Kein Spracherkenner gefunden. pip install mlx-whisper "
                 "(Apple Silicon) oder faster-whisper")

    def __call__(self, wav: str) -> str:
        if self.art == "mlx":
            import mlx_whisper

            ergebnis = mlx_whisper.transcribe(
                wav,
                path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
                language="de",
            )
            return ergebnis.get("text", "").strip()

        segmente, _ = self.modell.transcribe(wav, language="de", vad_filter=True)
        return " ".join(s.text.strip() for s in segmente).strip()


# ----------------------------------------------------------------- Ausgabe
class Stimme:
    def __init__(self, stumm: bool) -> None:
        self.modus = "stumm" if stumm else None
        if self.modus:
            return
        try:
            from kokoro import KPipeline  # noqa: F401

            self.pipeline = KPipeline(lang_code="d")
            self.modus = "kokoro"
            return
        except Exception:
            pass
        if shutil.which("say"):
            self.modus = "say"
        else:
            self.modus = "stumm"

    def __call__(self, text: str) -> None:
        if self.modus == "stumm" or not text:
            return
        if self.modus == "say":
            subprocess.run(["say", "-v", "Anna", text], check=False)
            return
        try:
            import numpy as np
            import sounddevice as sd

            stuecke = [a for _, _, a in self.pipeline(text, voice="df_alpha")]
            if stuecke:
                sd.play(np.concatenate(stuecke), 24000)
                sd.wait()
        except Exception as fehler:  # noqa: BLE001
            print(f"  (Sprachausgabe übersprungen: {fehler})", file=sys.stderr)


# ----------------------------------------------------------------- Agent
def frage_agenten(text: str, sitzung: str | None) -> tuple[str, str | None]:
    """Ruft die Claude-Code-CLI auf. Gibt (Antworttext, Sitzungs-ID) zurück."""
    befehl = [
        "claude", "-p", text,
        "--output-format", "json",
        "--append-system-prompt", SYSTEM_ZUSATZ,
        "--allowedTools", WERKZEUGE,
        "--max-turns", "12",
    ]
    if sitzung:
        befehl += ["--resume", sitzung]

    lauf = subprocess.run(befehl, capture_output=True, text=True, check=False)
    if lauf.returncode != 0:
        return f"Der Agent hat abgebrochen: {lauf.stderr.strip()[:300]}", sitzung

    try:
        daten = json.loads(lauf.stdout)
    except json.JSONDecodeError:
        return lauf.stdout.strip()[:1000], sitzung

    if isinstance(daten, list):
        daten = daten[-1] if daten else {}
    antwort = daten.get("result") or daten.get("text") or ""
    return antwort.strip(), daten.get("session_id") or sitzung


# ----------------------------------------------------------------- Hauptlauf
def main() -> None:
    zerleger = argparse.ArgumentParser(description="Sprachdialog mit dem Projektagenten")
    zerleger.add_argument("--stumm", action="store_true", help="keine Sprachausgabe")
    argumente = zerleger.parse_args()

    if not shutil.which("claude"):
        sys.exit("Claude Code nicht gefunden. Erst installieren und anmelden.")

    erkenner = Erkenner()
    stimme = Stimme(argumente.stumm)
    sitzung: str | None = None

    print()
    print("Sprachdialog. Enter = Aufnahme starten, Enter = beenden.")
    print("Strg-C beendet. Der Agent liest, legt aber nur Issue-Entwürfe an.")
    print()

    while True:
        try:
            input("  [Enter] sprechen …")
            print("  ● Aufnahme — Enter beendet")
            wav = aufnehmen()
            if not wav:
                print("  nichts aufgenommen\n")
                continue

            gesagt = erkenner(wav)
            os.unlink(wav)
            if not gesagt:
                print("  nichts erkannt\n")
                continue

            print(f"  Du:     {gesagt}")
            antwort, sitzung = frage_agenten(gesagt, sitzung)
            print(f"  Agent:  {antwort}\n")
            stimme(antwort)

        except KeyboardInterrupt:
            print("\nBeendet.")
            if sitzung:
                print(f"Sitzung fortsetzen mit:  claude --resume {sitzung}")
            return


if __name__ == "__main__":
    main()
