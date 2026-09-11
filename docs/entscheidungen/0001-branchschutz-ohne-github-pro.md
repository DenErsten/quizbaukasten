# 0001 — Branchschutz ohne GitHub Pro

**Status:** entschieden — Option A
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

**Option A.** Das Repo ist öffentlich. Firat hat am 2026-09-11 entschieden.

Ausschlaggebend war, dass das Argument gegen A bei genauerem Hinsehen keines
war: Marek Sowa ist eine Planspiel-Figur, `docs/angebote/` ist leer, und es
gibt kein Kundenmaterial, das geschützt werden müsste. Option A′ hätte ein
Problem gelöst, das nicht existiert. Übrig blieb ein Nachteil — die
Commit-Historie wird mitveröffentlicht — gegen zwei Vorteile: funktionierende
Gates und unbegrenzte Actions-Minuten.

## Folgen

`scripts/setup-repo.sh` läuft bis 5/5 durch. Nachgeprüft über die API:

    required_status_checks : pfade, pruefen, review, abnahme   (strict)
    enforce_admins         : true
    allow_force_pushes     : false
    allow_deletions        : false
    required_linear_history: true
    Umgebung produktion    : Required Reviewer DenErsten
    Umgebung staging       : keine Freigabe

Damit gilt Gate G1 technisch und nicht nur als Absicht, und Gate G4 hält den
Produktions-Deploy an, bis ein Mensch klickt. `enforce_admins: true` schließt
Firat ausdrücklich mit ein — das ist der Punkt der Übung, nicht ein Versehen.

### Beleg: `scripts/setup-repo.sh` läuft bis 5/5

Lauf vom 2026-09-11, nachdem das Repo öffentlich geschaltet war. Vorher brach
dasselbe Skript bei 2/5 mit `403 Upgrade to GitHub Pro` ab.

    $ ./scripts/setup-repo.sh
    Repo:   DenErsten/quizbaukasten
    Mensch: DenErsten

    1/5  Auto-Merge einschalten
         an

    2/5  Branch Protection auf main
         Required Checks: pfade, pruefen, review, abnahme

    3/5  Umgebung 'staging'
         ohne Freigabe — jeder Merge geht durch

    4/5  Umgebung 'produktion' mit menschlicher Freigabe  (Gate G4)
         Required Reviewer: DenErsten

    5/5  Gegenproben

Die Werte im Abschnitt oben stammen nicht aus dieser Ausgabe, sondern aus
einem anschließenden Lesen von `branches/main/protection`. Ein Skript, das
meldet, es habe etwas gesetzt, ist kein Beleg dafür, dass es gesetzt ist —
diese Unterscheidung hat an diesem Tag zweimal den Unterschied gemacht.

### Gegenprobe: direkter Push auf main

Am 2026-09-11 von Firat ausgeführt, auf seinem eigenen Repo, mit
Admin-Rechten. GitHub hat abgelehnt:

    $ git commit --allow-empty -m "darf nicht durchgehen"
    $ git push origin main

    remote: error: GH006: Protected branch update failed for refs/heads/main.
    remote:
    remote: - Changes must be made through a pull request.
    remote:
    remote: - 4 of 4 required status checks are expected.
    To https://github.com/DenErsten/quizbaukasten.git
     ! [remote rejected] main -> main (protected branch hook declined)

Beide genannten Gründe zählen. Der erste bestätigt, dass der Weg über einen
Pull Request führt; der zweite, dass die vier Checks tatsächlich als
*required* eingetragen sind und nicht bloß laufen.

Dass die Ablehnung den Inhaber des Repos trifft, ist der eigentliche
Nachweis. Ein Schutz, der für alle außer den Besitzer gilt, schützt an dem
Tag nicht, an dem es darauf ankommt — das war am selben Vormittag zu
besichtigen, als ein Merge mit zwei roten Checks durchging, weil es zu
diesem Zeitpunkt keine Branch Protection gab.

Was der Schritt nach sich zieht:

- Die Commit-Mailadresse `firat.keskin@cap3.de` steht in der öffentlichen
  Historie. Für künftige Commits lässt sich das über eine
  GitHub-noreply-Adresse vermeiden; rückwirkend nur durch Umschreiben.
- Actions-Minuten sind unbegrenzt. Vier Claude-Checks je PR plus drei
  Terminläufe wären auf 2.000 Minuten im Monat eine echte Grenze gewesen.
- Alles im Repo ist lesbar, auch `.claude/settings.json` und `n8n/*.json`.
  Beide enthalten keine Zugangsdaten — das bleibt zu prüfen, bevor je ein
  echter Kunde in diesem Repo auftaucht.

## Was noch offen ist

Die Gates greifen, aber zwei der vier Checks können noch nicht grün werden:
`review` und `abnahme` brauchen `CLAUDE_CODE_OAUTH_TOKEN`, und das Secret ist
nicht gesetzt. Bis dahin mergt nichts — was richtig herum falsch ist: das
System hält an, statt durchzuwinken.
