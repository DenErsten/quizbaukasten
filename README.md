# Studio-OS Starter-Kit

Repo-Skelett für eine Ein-Mann-Softwarefirma mit KI im Loop.
Gebaut für ein dreitägiges Codecamp mit 2–3 Personen.

**Leitprinzip:** Über Code entscheidet die KI — sie mergt ihre PRs selbst.
Über alles andere entscheidet der Mensch: Scope, Plan, welche Tickets
überhaupt gebaut werden, die Regeln des Agenten selbst, und was beim Kunden
landet. Der Merge ist frei, weil vier Checks ihn tragen; die Auslieferung
an Produktion ist es nicht.

---

## Was hier drin ist

```
.
├── CLAUDE.md                     Arbeitsregeln, die der Agent bei jedem Lauf liest
├── PLANSPIEL.md                  Drehbuch für den Live-Durchlauf an Tag 3
├── docs/
│   ├── plan.md                   Der Projektplan — Quelle der Wahrheit für Meilensteine
│   ├── kunde.md                  Kundenprofil, Ansprechpartner, Tonfall
│   ├── meetings/                 Protokolle (vom Agenten erzeugt, von dir gemergt)
│   ├── entscheidungen/           ADRs
│   └── angebote/                 Angebote als Markdown
├── .github/
│   ├── geschuetzte-pfade.txt     Was die KI nicht allein ändern darf
│   ├── workflows/
│   │   ├── claude.yml            @claude-Mentions in Issues und PRs
│   │   ├── pr-pruefung.yml       Die vier Merge-Checks + Auto-Merge
│   │   ├── deploy-staging.yml    Jeder Merge → Staging, automatisch
│   │   ├── deploy-produktion.yml Nur mit menschlicher Freigabe (G4)
│   │   ├── merge-tagebuch.yml    Werktags 18:00 — was ist heute reingekommen
│   │   ├── wochenuebersicht.yml  Montags 07:00 — Lagebericht als Issue
│   │   └── plan-drift.yml        Freitags — Plan gegen Realität prüfen
│   └── ISSUE_TEMPLATE/
├── .claude/
│   ├── settings.json             Permissions als harte Leitplanke
│   └── skills/
│       ├── projektplan/          Plan bauen und fortschreiben
│       ├── meeting-nacharbeit/   Transkript → Protokoll → Tickets
│       └── kundenmail/           Mailentwurf im richtigen Ton
├── scripts/
│   ├── menschen.txt              Wessen Freigabe zählt
│   ├── pfad_pruefung.py          Der Wächter über den Selbstumbau
│   ├── setup-labels.sh           Label-Set anlegen (Gates!)
│   ├── setup-repo.sh             Branch Protection, Checks, Umgebungen
│   ├── transkribieren.sh         Audio → Transkript mit Sprechertrennung
│   └── voice_dialog.py           Sprachdialog mit dem Agenten (Push-to-Talk)
└── n8n/
    ├── 01-meeting-pipeline.json  Importierbar
    └── README.md                 Bauanleitung für das Freigabe-Gate
```

---

## Setup in 20 Minuten

### 1. Repo anlegen

```bash
gh repo create nordlicht-tourenplaner --private --clone
cd nordlicht-tourenplaner
# Inhalt dieses Starter-Kits hineinkopieren
git add -A && git commit -m "Studio-OS Grundgerüst" && git push
```

### 2. Labels, Menschen und Gates

```bash
$EDITOR scripts/menschen.txt        # euren GitHub-Login eintragen — zuerst!
./scripts/setup-labels.sh
./scripts/setup-repo.sh             # Checks, Branch Protection, Umgebungen
```

`menschen.txt` zuerst, weil dieselbe Datei festlegt, wessen Freigabe zählt,
und weil `setup-repo.sh` den ersten Eintrag als Required Reviewer für
Produktion einträgt.

### 3. Claude in die CI

```bash
claude setup-token                 # OAuth-Token aus dem Abo, kein API-Key
gh secret set CLAUDE_CODE_OAUTH_TOKEN
# App installieren:
claude   # dann im Chat: /install-github-app
```

Test: In einem Issue `@claude fass diesen Issue in drei Sätzen zusammen` kommentieren.

### 4. GitHub-MCP an Claude Code lokal

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
```

### 5. Voice (Tag 2)

```bash
# Apple Silicon
pip install mlx-whisper sounddevice numpy soundfile
# alle anderen
pip install faster-whisper sounddevice numpy soundfile

python scripts/voice_dialog.py
```

---

## Die Gates

| Gate | Worüber ein Mensch entscheidet | Was es technisch erzwingt |
|------|-------------------------------|---------------------------|
| G0 | Angebot, Scope | PR auf `docs/angebote/` — geschützter Pfad |
| G1 | Meilensteinschnitt | PR auf `docs/plan.md` — geschützter Pfad |
| G2 | Welche Tickets überhaupt gebaut werden | Check `abnahme` blockt PRs ohne `status:freigegeben` |
| G3 | **Die Leitplanken der KI** | Check `pfade` — Merge blockiert ohne menschliche Freigabe |
| G4 | Was in Produktion geht | Environment `produktion` mit Required Reviewer |
| G5 | Jede Zeile an den Kunden | Agent hat nur Entwurf-Schreibrechte, kein `send` |

**G3 hat sich verschoben.** Früher war es der Diff. Jetzt entscheidet die KI
über den Diff, und der Mensch entscheidet über die Regeln, nach denen sie
entscheidet. Ein Agent, der `CLAUDE.md`, die Workflows oder die Tests
mitändern darf, kann sich in kleinen Schritten aus jeder Grenze herausarbeiten
— ohne bösen Willen, einfach weil das der kürzeste Weg zu einem grünen Lauf ist.

## Was einen Merge trägt

Vier Required Status Checks auf `main`. Der Agent schaltet Auto-Merge frei,
GitHub mergt — wenn alle vier grün sind:

| Check | Fragt |
|-------|-------|
| `pfade` | Fasst der PR die Leitplanken an? Dann braucht er einen Menschen. |
| `pruefen` | Halten Tests, Typen, Lint und Build? |
| `review` | Was sagt ein zweiter Agent, dessen Auftrag es ist, Gründe gegen den Merge zu finden? |
| `abnahme` | Ist das „fertig, wenn …" des Issues am Diff nachweisbar? |

Der Agent kann keinen davon abkürzen: Er hat Contents- und PR-Rechte, aber
keine Administration-Rechte, und `enforce_admins` gilt auch für dich.

Dazu zwei Beobachter, weil Autonomie ohne Sicht Autonomie ohne Rechenschaft ist:
das **Merge-Tagebuch** werktags um 18:00 (was ist heute reingekommen, wohin
driftet das Projekt) und der **Gate-Wächter** in n8n, der nachträglich prüft,
ob ein gemergter PR doch geschützte Pfade angefasst hat.

Ein Gate, das nur in einer Anleitung steht, ist kein Gate. Prüft an Tag 1 jedes
einzelne mit einem bewussten Verstoßversuch — siehe `PLANSPIEL.md`, Übung „Rote Karte".
