# Projektplan — Nordlicht Tourenplaner

> Diese Datei ist die Quelle der Wahrheit. GitHub-Milestones werden hieraus
> erzeugt. Jede Änderung ist ein Pull Request. Gate: **G1**.

**Stand:** _(vom Agenten gepflegt)_
**Freigegeben durch:** _(Merge-Commit von Firat)_

---

## Ziel in einem Satz

Nordlicht Logistik plant Touren heute in Excel; der Tourenplaner soll das
Anlegen, Zuweisen und Ausdrucken einer Tagestour für vier Disponenten ersetzen.

## Was nicht dazugehört

Ausdrücklich außerhalb des Scopes — hier steht, was **nicht** gebaut wird,
damit „Können wir noch schnell…" eine Planänderung ist und keine Nebenbemerkung.

- Routenoptimierung / Kartenmaterial
- Anbindung an das Bestandssystem (nur CSV-Import)
- Mobile App für Fahrer

---

## Meilensteine

| # | Meilenstein | Abnahmekriterium (der Kunde kann …) | Ziel | Status |
|---|-------------|--------------------------------------|------|--------|
| M1 | Touren anlegen | … eine Tour mit Stopps anlegen und speichern | | offen |
| M2 | Zuweisen & drucken | … eine Tour einem Fahrer zuweisen und als PDF drucken | | offen |
| M3 | CSV-Import | … die Aufträge des Tages aus dem Bestandssystem importieren | | offen |

Jeder Meilenstein endet mit einer **Demo am geteilten Bildschirm** und einem
veröffentlichten Release. Kein Meilenstein gilt als erledigt, weil der Code
gemergt ist.

---

## Annahmen

Was wir glauben, ohne es geprüft zu haben. Kippt eine Annahme, ist das ein
PR auf diese Datei, kein stiller Umbau.

- A1: Die CSV aus dem Bestandssystem hat ein stabiles Format.
- A2: Vier gleichzeitige Nutzer, keine Lastanforderungen.
- A3: Der Druck läuft über den Browser, kein eigener Druckserver.

## Offene Punkte

| # | Frage | An wen | Seit |
|---|-------|--------|------|
| | | | |

## Abweichungen

Vom Agenten befüllt, wenn Termine kippen. Jede Zeile mit zwei Optionen.

| Datum | Was weicht ab | Ursache | Option A | Option B | Entscheidung |
|-------|---------------|---------|----------|----------|--------------|
| | | | | | |
