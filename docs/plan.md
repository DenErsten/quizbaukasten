# Projektplan — Quizbaukasten

> Diese Datei ist die Quelle der Wahrheit. GitHub-Milestones werden hieraus
> erzeugt. Jede Änderung ist ein Pull Request. Gate: **G1**.

**Stand:** _(vom Agenten gepflegt)_
**Freigegeben durch:** _(Merge-Commit von Firat)_

---

## Ziel in einem Satz

Wer ein Kneipenquiz veranstaltet, soll ein Quiz in einer halben Stunde
zusammenstellen können statt an zwei Abenden — und es am Quizabend sicher
vom Bildschirm ablesen können.

## Für wen zuerst

Quizmaster privater Abende: Kneipen-, Vereins- und Geburtstagsquiz. Eine
Person baut, eine Person moderiert, Teams spielen auf Papier.
Erster Pilotnutzer: siehe [`pilotnutzer.md`](pilotnutzer.md).

## Was nicht dazugehört

Ausdrücklich außerhalb des Scopes — hier steht, was **nicht** gebaut wird,
damit „können wir noch schnell…" eine Planänderung ist und keine Nebenbemerkung.

- Teams antworten über ihre eigenen Handys (Live-Multiplayer)
- Benutzerkonten und Anmeldung
- Fragen-Datenbank, Import fertiger Fragenkataloge, KI-generierte Fragen
- Buzzer, Zeitdruck, Musik- oder Videofragen
- Mehrere Quizmaster gleichzeitig am selben Quiz

## Was uns eng macht

Ein Quizabend lässt sich nicht wiederholen. Was am Abend selbst läuft,
muss auch ohne Netz und ohne Nachfrage funktionieren — das ist keine
Qualitätsanforderung, sondern eine Produkteigenschaft, und sie gilt ab M2.

---

## Meilensteine

| # | Meilenstein | Abnahmekriterium (der Quizmaster kann …) | Ziel | Status |
|---|-------------|-------------------------------------------|------|--------|
| M1 | Quiz bauen | … ein Quiz mit Runden und Fragen anlegen, speichern und wieder öffnen | | offen |
| M2 | Abend moderieren | … das Quiz Frage für Frage anzeigen, Antworten der Teams erfassen und den Punktestand sehen | | offen |
| M3 | Wiederverwenden | … ein Quiz als Vorlage kopieren und einzelne Runden austauschen | | offen |

Jeder Meilenstein endet mit einer **Demo am geteilten Bildschirm** mit dem
Pilotnutzer und einem veröffentlichten Release. Kein Meilenstein gilt als
erledigt, weil der Code gemergt ist.

---

## Annahmen

Was wir glauben, ohne es geprüft zu haben. Kippt eine Annahme, ist das ein
PR auf diese Datei, kein stiller Umbau.

- A1: Fünf Runden à sechs Fragen ist die übliche Größe. Wenn Quizze deutlich
  größer werden, trägt die flache Darstellung aus M1 nicht.
- A2: Der Quizmaster arbeitet am Laptop, nicht am Handy.
- A3: Ein Quiz im Browser zu speichern reicht fürs Erste — bis jemand sein
  Quiz verliert. Dann ist A3 widerlegt und M3 wird dringend.
- A4: Schätzfragen brauchen „wer am nächsten dran ist", nicht „exakt richtig".
  Im Code ist das bewusst noch nicht so; die Regel gehört zur Auswertung in M2.

## Offene Punkte

| # | Frage | An wen | Seit |
|---|-------|--------|------|
| | | | |

## Abweichungen

Vom Agenten befüllt, wenn Termine kippen. Jede Zeile mit zwei Optionen.

| Datum | Was weicht ab | Ursache | Option A | Option B | Entscheidung |
|-------|---------------|---------|----------|----------|--------------|
| | | | | | |
