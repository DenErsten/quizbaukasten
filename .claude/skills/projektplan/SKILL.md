---
name: projektplan
description: Einen Projektplan mit Meilensteinen bauen oder fortschreiben, und daraus GitHub-Milestones erzeugen. Nutzen bei "Plan bauen", "Meilensteine schneiden", "Projekt aufsetzen", "Plan aktualisieren" oder nach einem freigegebenen Angebot.
---

# Projektplan bauen und fortschreiben

`docs/plan.md` ist die Quelle der Wahrheit. Milestones entstehen aus dem Plan,
nie umgekehrt. Jede Änderung ist ein Pull Request. Das ist Gate **G1**.

## Einen Plan neu bauen

### Meilensteine schneiden

Ein Meilenstein ist etwas, das der Kunde **sehen und beurteilen** kann.
Prüfe jeden Kandidaten mit diesem Satz:

> „Nach diesem Meilenstein kann <Rolle> <Tätigkeit>."

Geht der Satz nicht auf, ist es kein Meilenstein, sondern eine Aufgabe.
„Datenbankschema steht" fällt durch. „Der Disponent kann eine Tour anlegen
und ausdrucken" besteht.

Weitere Regeln:

- Zwei bis fünf Meilensteine. Mehr heißt, du schneidest nach Technik statt nach Nutzen.
- Der erste Meilenstein ist der kleinste. Bei einem Kunden mit einem
  abgebrochenen Vorprojekt in der Historie ist früh sichtbar wichtiger als vollständig.
- Jeder Meilenstein endet mit einer Demo und einem Release. Kein Meilenstein
  gilt als erledigt, weil Code gemergt ist.

### Was nicht dazugehört

Fülle den Abschnitt „Was nicht dazugehört" so konkret wie den Scope selbst.
Diese Liste ist das Werkzeug, mit dem später aus „können wir noch schnell…"
ein bewusstes Gespräch wird statt einer stillen Ausweitung.

### Annahmen

Alles, was du glaubst, ohne es geprüft zu haben, kommt in den Abschnitt
„Annahmen" — nummeriert. Eine widerlegte Annahme ist später eine Zeile in
„Abweichungen" und kein Schuldvorwurf.

### Schätzen

Du schätzt Größenordnungen (S/M/L), keine Tage und keine Preise. Tage und
Preise sagt Firat zu, weil es sein Risiko ist. Wenn du zu einer Zahl gedrängt
wirst, nenne stattdessen die drei Unbekannten, die die Zahl bestimmen.

## Milestones erzeugen

**Erst nachdem der Plan-PR gemergt ist.** Prüfe das vorher:

```bash
git log origin/main --oneline -- docs/plan.md | head -1
```

Dann je Zeile der Meilensteintabelle:

```bash
gh api repos/:owner/:repo/milestones -f title="M1 — Touren anlegen" \
  -f description="Fertig, wenn …" -f due_on="JJJJ-MM-TTT23:59:59Z"
```

Existiert ein Milestone mit dem Titel schon, aktualisiere ihn, statt einen
zweiten anzulegen.

## Einen Plan fortschreiben

Nie still ändern. Der Ablauf ist immer:

1. Abweichung erkennen (Termin kippt, Annahme widerlegt, Scope wächst)
2. Zeile in der Tabelle „Abweichungen" ergänzen: was, Ursache, **zwei Optionen**
3. Branch `plan/<kurz>` und Pull Request
4. Im PR-Text nur Fakten und die zwei Optionen — keine Empfehlung, keine
   dritte Option, kein „ich würde"

Zwei Optionen, weil eine Option keine Entscheidung ist und drei Optionen eine
Diskussion sind, die in einen PR-Kommentar nicht hineinpasst. Braucht es eine
dritte, schreib das als offene Frage und bitte um ein Gespräch.
