# 0001 — Branchschutz ohne GitHub Pro

**Status:** offen — wartet auf Firat
**Datum:** 2026-09-11
**Betrifft:** Gate G1 (kein Merge ohne die vier Checks), Gate G4 (Freigabe Produktion)
**Issue:** #1

## Kontext

Das Modell dieses Repos steht auf einem einzigen technischen Fundament: Die
vier Checks `pfade`, `pruefen`, `review` und `abnahme` sind Required Status
Checks auf `main`, und `enforce_admins` steht auf `true`. Erst das macht aus
den Regeln in `CLAUDE.md` etwas anderes als eine Bitte — und erst das erlaubt
es, der KI das Mergen zu überlassen.

Dieses Fundament lässt sich auf `DenErsten/quizbaukasten` nicht legen.
Das Repo ist privat, der Account ist auf dem Free-Plan, und beide Wege zur
Branch Protection sind dort gesperrt:

    PUT  /repos/.../branches/main/protection   → 403
    GET  /repos/.../rulesets                   → 403
    "Upgrade to GitHub Pro or make this repository public"

`scripts/setup-repo.sh` bricht deshalb bei 2/5 ab. Die Schritte 3/5
(Umgebung `staging`), 4/5 (Umgebung `produktion` mit Required Reviewer) und
5/5 sind nicht gelaufen.

Es geht dabei nicht um eine fehlende Bequemlichkeit. Ohne required Checks
lässt GitHub Auto-Merge nicht aktivieren — der Job `freischalten` fällt in
seinen `|| echo`-Zweig, und **kein PR mergt jemals von allein.** Der Kern von
Block 04 ist damit nicht abgeschwächt, sondern abwesend.

Randbedingung: Alle Werkzeuge außer dem Claude-Abo müssen kostenlos bleiben.
GitHub Pro und Team scheiden damit aus, auch wenn sie die technisch
geradlinigste Lösung wären.

## Optionen

**A — Repo öffentlich schalten.** Branch Protection, Rulesets und unbegrenzte
Actions-Minuten sind für öffentliche Repos kostenlos. `setup-repo.sh` läuft
danach unverändert durch. Preis: `docs/pilotnutzer.md`, `docs/angebote/**` und
die Meeting-Protokolle werden öffentlich. Das ist Kundenmaterial, und der
Schritt ist praktisch nicht umkehrbar — was einmal geforkt oder indexiert ist,
holt kein Zurückschalten ein.

**A′ — Zweigeteilt.** Code, `docs/plan.md` und die ADRs öffentlich, alles
Kundenbezogene in ein zweites privates Repo. Die Gates greifen vollständig,
das Kundenmaterial bleibt geschützt. Preis: Die Skills `kundenmail` und
`meeting-nacharbeit` müssen über zwei Repos hinweg arbeiten, und der
Pfad-Wächter verliert die Dateien aus dem Blick, die er heute mitschützt.

**B — Privat bleiben.** Nichts wird veröffentlicht, die vier Checks laufen
weiter und sind lesbar — aber sie binden nicht, und gemergt wird von Hand.
Preis: Das Planspiel verliert seinen Gegenstand. Die Frage „kommt der Agent an
seinen eigenen Leitplanken vorbei?" ist dann nicht mehr prüfbar, weil es keine
Leitplanken gibt, an denen er scheitern könnte.

## Entscheidung

_(offen — trägt Firat ein)_

## Folgen

_(nach der Entscheidung ausfüllen)_

## Was sofort gilt, unabhängig von der Entscheidung

`allow_auto_merge` steht seit Schritt 1/5 auf `true`, ohne dass ein einziger
Check required ist. Solange das so bleibt, ist die einzige Sicherung gegen
einen ungeprüften Merge die `deny`-Liste in `.claude/settings.json` — also
genau die Datei, von der dort selbst steht, dass sie die erste
Verteidigungslinie ist und nicht die letzte.
