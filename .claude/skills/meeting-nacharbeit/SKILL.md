---
name: meeting-nacharbeit
description: Aus einem Meeting-Transkript ein Protokoll, Draft-Issues, Kalendereinträge und einen Mail-Entwurf erzeugen. Nutzen, wenn eine Datei unter aufnahmen/ oder ein Transkript vorliegt, oder wenn der Nutzer sagt "Meeting nacharbeiten", "Protokoll bauen", "aus dem Gespräch Tickets machen".
---

# Meeting nacharbeiten

Du machst aus einem Rohtranskript vier Dinge — und keines davon ist endgültig.

## Ablauf

### 1. Transkript einlesen

Liegt eine Audiodatei statt eines Transkripts vor:

```bash
./scripts/transkribieren.sh aufnahmen/<datei>
```

Das Ergebnis landet in `aufnahmen/<name>.transkript.md` mit Sprecherkennzeichnung
und Zeitmarken. Sprecher heißen dort `SPEAKER_00`, `SPEAKER_01` … — ordne sie
anhand von `docs/pilotnutzer.md` und dem Gesprächsinhalt echten Namen zu und schreib
die Zuordnung oben ins Protokoll. Wenn du dir bei einem Sprecher nicht sicher
bist, schreib `SPEAKER_01 (unklar)` — rate nicht.

### 2. Protokoll schreiben

Neue Datei `docs/meetings/JJJJ-MM-TT-<thema>.md`, exakt diese Struktur:

```markdown
# <Thema> — <Datum>

**Teilnehmer:** …
**Dauer:** …
**Aufnahme:** aufnahmen/<datei>

## Entscheidungen
Nur, was wirklich entschieden wurde. Jede Zeile: was, von wem, ab wann gültig.

## Zusagen
| Was | Wer | Bis wann | Issue |
|-----|-----|----------|-------|

## Offene Punkte
Fragen, die im Raum stehen geblieben sind — mit der Person, die sie klären muss.

## Nicht entschieden
Themen, die besprochen wurden, ohne dass etwas herauskam. Dieser Abschnitt
ist wichtiger als er aussieht: hier stehen die Dinge, die in vier Wochen
als "das hatten wir doch geklärt" wiederkommen.

## Zitate
Höchstens drei wörtliche Sätze, die den Ton oder eine Sorge des Pilotnutzers tragen.
```

Regeln: Keine Interpretation im Protokoll. Wenn jemand „eigentlich müssten wir
mal" gesagt hat, ist das keine Zusage — das gehört unter „Nicht entschieden".
Nichts glätten, was unangenehm war.

### 3. Draft-Issues

Für jede Zusage und jede Anforderung ein Issue:

- Label `status:vorschlag` — **nie** `status:freigegeben`
- Titel: was der Nutzer danach kann, nicht was gebaut wird
- Body nach der Vorlage in `.github/ISSUE_TEMPLATE/anforderung.yml`
- Verlinke das Protokoll und zitiere die relevante Stelle mit Zeitmarke
- Kein Abnahmekriterium erfindbar? Dann als `art:frage` anlegen und die offene
  Frage hineinschreiben

**Vorher entscheiden, welche Sorte Issue es ist.** `CLAUDE.md`, Abschnitt
„Issues", verlangt: Ein Abnahmekriterium muss am Diff nachweisbar sein. Der
Prüfer in Gate G3 sieht nichts als den Diff und das Issue.

Aus einem Meeting kommen aber fast nur betriebliche Zusagen. Drei Fälle:

| Was gesagt wurde | Sorte | Warum |
|---|---|---|
| „Ein Quiz soll sich kopieren lassen" | gewöhnliches Issue | Code, Test, Datei — am Diff belegbar |
| „Das muss am Abend ohne Netz laufen" | `art:pruefung` | kein Diff belegt, dass es im Betrieb hielt |
| „Kopieren soll gehen, und zwar offline" | **zwei Issues** | gemischt — teilen, nicht zusammenpressen |

Ein `art:pruefung`-Issue hat keinen PR und durchläuft keine Abnahme: Ein
Mensch führt die Prüfung aus, trägt das Ergebnis ein und schließt sie. Schreib
ins Issue, **wie** geprüft wird und **woran** man Bestehen erkennt — sonst ist
es in vier Wochen unentscheidbar.

Im Zweifel `art:pruefung`. Ein Issue, das ein Mensch abnimmt, kostet zehn
Minuten. Ein gewöhnliches Issue mit einem Kriterium, das kein Diff erfüllen
kann, blockiert für immer — das ist an #1 dreimal passiert, bevor es auffiel.

Trag die Issue-Nummern in die Zusagen-Tabelle des Protokolls nach.

### 4. Kalender

Für jede Zusage mit Datum einen Eintrag im Kalender `Projekte` anlegen,
Titel `Zusage: <kurz> (#<issue>)`, Erinnerung zwei Tage vorher.

### 5. Mail-Entwurf

Zusammenfassung für den Pilotnutzer — **als Entwurf**, nie senden. Ton nach
`docs/pilotnutzer.md`. Aufbau: ein Satz Dank, die Entscheidungen als Liste, die
Zusagen mit Terminen, die offenen Fragen als nummerierte Rückfragen. Höchstens
200 Wörter. Kein „wir freuen uns auf die weitere Zusammenarbeit".

### 6. Pull Request

Protokoll und Planänderungen in einen PR. Der PR-Text listet auf: welche
Issues du angelegt hast, welche Kalendereinträge, wo der Mailentwurf liegt,
und **worüber Firat entscheiden muss**.

## Was du hier nie tust

- Ein Issue direkt freigeben
- Die Mail senden
- `docs/plan.md` ändern, weil im Meeting ein Termin genannt wurde — das ist
  eine Zeile in „Abweichungen" und ein eigener PR
- Sprecher raten, die du nicht sicher zuordnen kannst
- Ein Und-Kriterium formulieren, dessen Teile in beide Sorten fallen. Der
  Prüfer geht sie einzeln durch und blockiert, sobald ein Teil nicht am Diff
  belegt ist — zu Recht. Teile das Issue beim Schreiben, nicht hinterher.
