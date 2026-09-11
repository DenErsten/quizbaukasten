#!/usr/bin/env bash
# Audio -> Transkript mit Sprechertrennung und Zeitmarken.
# Alles laeuft lokal; keine Aufnahme verlaesst den Rechner.
#
#   ./scripts/transkribieren.sh aufnahmen/kickoff.m4a
#   -> aufnahmen/kickoff.transkript.md
#
# Einmalig installieren:
#   Apple Silicon:  pip install mlx-whisper && brew install ffmpeg
#   sonst:          pip install faster-whisper && apt install ffmpeg
#   Sprechertrennung (optional, deutlich besser):
#     pip install whisperx
#     Zugang zu pyannote/speaker-diarization auf HuggingFace akzeptieren,
#     dann HF_TOKEN in der Umgebung setzen.
set -euo pipefail

AUDIO="${1:?Aufruf: $0 <audiodatei> [sprache]}"
SPRACHE="${2:-de}"
[[ -f "$AUDIO" ]] || { echo "Datei nicht gefunden: $AUDIO"; exit 1; }

BASIS="${AUDIO%.*}"
WAV="${BASIS}.16k.wav"
ZIEL="${BASIS}.transkript.md"

command -v ffmpeg >/dev/null || { echo "ffmpeg fehlt"; exit 1; }

echo "1/3  Audio normalisieren"
# 16 kHz mono ist das Format, das alle Whisper-Varianten am liebsten mögen.
ffmpeg -nostdin -loglevel error -y -i "$AUDIO" -ac 1 -ar 16000 -c:a pcm_s16le "$WAV"

echo "2/3  Transkribieren"
if command -v whisperx >/dev/null && [[ -n "${HF_TOKEN:-}" ]]; then
  echo "     whisperx mit Sprechertrennung"
  whisperx "$WAV" \
    --language "$SPRACHE" \
    --model large-v3 \
    --diarize \
    --hf_token "$HF_TOKEN" \
    --output_format srt \
    --output_dir "$(dirname "$AUDIO")" >/dev/null
  QUELLE="${WAV%.*}.srt"
  HINWEIS="Sprecher automatisch getrennt (whisperx). Zuordnung zu echten Namen pruefen."
elif python3 -c "import mlx_whisper" 2>/dev/null; then
  echo "     mlx-whisper (Apple Silicon), ohne Sprechertrennung"
  python3 - "$WAV" "$SPRACHE" <<'PY'
import sys, json, mlx_whisper
wav, lang = sys.argv[1], sys.argv[2]
r = mlx_whisper.transcribe(
    wav, path_or_hf_repo="mlx-community/whisper-large-v3-mlx", language=lang
)
with open(wav.rsplit(".", 1)[0] + ".json", "w") as f:
    json.dump(r, f, ensure_ascii=False)
PY
  QUELLE="${WAV%.*}.json"
  HINWEIS="Ohne Sprechertrennung. Sprecherwechsel aus dem Inhalt erschliessen."
else
  echo "     faster-whisper, ohne Sprechertrennung"
  python3 - "$WAV" "$SPRACHE" <<'PY'
import sys, json
from faster_whisper import WhisperModel
wav, lang = sys.argv[1], sys.argv[2]
model = WhisperModel("large-v3", device="auto", compute_type="int8")
segments, _ = model.transcribe(wav, language=lang, vad_filter=True)
out = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
with open(wav.rsplit(".", 1)[0] + ".json", "w") as f:
    json.dump({"segments": out}, f, ensure_ascii=False)
PY
  QUELLE="${WAV%.*}.json"
  HINWEIS="Ohne Sprechertrennung. Sprecherwechsel aus dem Inhalt erschliessen."
fi

echo "3/3  Als Markdown ablegen"
python3 - "$QUELLE" "$ZIEL" "$AUDIO" "$HINWEIS" <<'PY'
import json, os, re, sys

quelle, ziel, audio, hinweis = sys.argv[1:5]

def mmss(sek):
    sek = int(float(sek))
    return f"{sek // 60:02d}:{sek % 60:02d}"

zeilen = []
if quelle.endswith(".srt"):
    blocks = re.split(r"\n\s*\n", open(quelle, encoding="utf-8").read().strip())
    for b in blocks:
        teile = b.strip().split("\n")
        if len(teile) < 3:
            continue
        anfang = teile[1].split(" --> ")[0].split(",")[0]
        h, m, s = anfang.split(":")
        text = " ".join(teile[2:]).strip()
        treffer = re.match(r"\[?(SPEAKER_\d+)\]?:?\s*(.*)", text)
        sprecher, text = (treffer.group(1), treffer.group(2)) if treffer else ("SPEAKER_?", text)
        zeilen.append(f"**[{int(h)*60+int(m):02d}:{s}] {sprecher}:** {text}")
else:
    daten = json.load(open(quelle, encoding="utf-8"))
    for s in daten.get("segments", []):
        zeilen.append(f"**[{mmss(s['start'])}]** {s['text'].strip()}")

with open(ziel, "w", encoding="utf-8") as f:
    f.write(f"# Rohtranskript — {os.path.basename(audio)}\n\n")
    f.write(f"> {hinweis}\n")
    f.write("> Rohmaterial, nicht das Protokoll. Nicht direkt an den Kunden geben.\n\n")
    f.write("## Sprecherzuordnung\n\n")
    f.write("| Kennung | Echter Name | sicher? |\n|---|---|---|\n")
    for k in sorted({z.split()[1].rstrip(":*") for z in zeilen if "SPEAKER_" in z}):
        f.write(f"| {k} | | |\n")
    f.write("\n## Transkript\n\n")
    f.write("\n\n".join(zeilen) + "\n")
print(f"     {ziel}")
PY

rm -f "$WAV"
echo
echo "Weiter im Claude Code:  /meeting-nacharbeit  $ZIEL"
