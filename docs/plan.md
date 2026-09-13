# Projektplan — Protokoll-Werkzeug

> Diese Datei ist die Quelle der Wahrheit. GitHub-Milestones werden hieraus
> erzeugt. Jede Änderung ist ein Pull Request. Gate: **G1**.

**Stand:** 2026-09-12 — Produkt gewechselt, siehe „Abweichungen"
**Freigegeben durch:** _(Merge-Commit von Firat)_

---

## Ziel in einem Satz

Wer ein Projektgespräch führt, soll danach geprüfte Anforderungen im Repo
haben statt einer Tonaufnahme, die niemand mehr abhört — und sie im selben
Werkzeug nachfragen und freigeben können, in dem sie entstanden sind.

Das Werkzeug **führt** dieses Gespräch, es kommentiert es nicht. Es fragt der
Reihe nach, hakt nach, wenn es etwas nicht verstanden hat, und hört auf,
bevor es zu genau wird. Und es tut das nicht einmal, sondern in Runden: erst
der grobe Rahmen, dann ein Plan, dann gebautes Produkt, dann Rückmeldung —
und von dort wieder von vorn.

## Für wen zuerst

Projektmanager in kleinen Teams, die Anforderungen aus Gesprächen gewinnen
und danach mit Entwicklung arbeiten. Eine Person führt das Gespräch, dieselbe
Person entscheidet, was daraus ein Ticket wird.

Erster Nutzer ist Firat selbst. Das ist eine Schwäche und keine Lösung:
Wer sein eigenes Werkzeug baut, merkt nicht, was er schon weiß. Ein zweiter
Nutzer von außen ist offen — siehe „Offene Punkte".

## Was nicht dazugehört

- Mehrere Teilnehmer, die gleichzeitig am selben Gespräch arbeiten
- Ein eigener Anforderungs-Speicher — die Wahrheit steht in GitHub-Issues
- Aufnahme in der Cloud. Ton verlässt den Rechner nie
- Automatische Freigabe von Anforderungen. Gate G2 bleibt beim Menschen
- Einwürfe mitten im Satz. Das Werkzeug fragt in Pausen, nicht dazwischen
- Ein Erstgespräch, das ins Detail geht — der erste Durchgang klärt den Rahmen
- Mail, Kalender, Kontakte (war Block 02, zurückgestellt am 2026-09-12, #3)

## Was uns eng macht

**Ein Gespräch lässt sich nicht wiederholen.** Wenn die Aufnahme abbricht,
die Erkennung hängt oder das Werkzeug abstürzt, ist das Gespräch weg — und
mit ihm die Anforderungen, um derentwillen es geführt wurde.

Daraus folgt, was ein Entwurf nicht verletzen darf: Die Aufnahme läuft
lokal, sie braucht kein Netz, und sie schreibt fortlaufend mit statt am Ende
auf einmal. Ein Werkzeug, das ein Gespräch verlieren kann, wird nach dem
ersten Verlust nicht mehr benutzt.

---

## Was den Rechner verlässt

Bis zum 2026-09-12 stand hier pauschal „keine Verarbeitung in der Cloud".
Der Satz ist mit der Ableitung von Anforderungen nicht mehr haltbar, und ein
Plan, der etwas verbietet, das täglich passiert, schützt niemanden. Deshalb
statt eines Verbots eine Liste.

**Verlässt den Rechner nie:**

- die Audioaufnahme, roh oder geschnitten
- die Spracherkennung selbst — Whisper läuft lokal, ohne Netz

**Verlässt den Rechner, wenn jemand es auslöst:**

- der Text eines Transkripts, wenn auf „Anforderungen ableiten" gedrückt wird
- die Entwürfe, die dabei zurückkommen
- während eines **geführten** Gesprächs: fortlaufend das zuletzt Gesagte,
  damit daraus die nächste Frage entsteht. Nur nach einem ausdrücklichen
  Start; ohne ihn läuft die Aufnahme vollständig lokal

Zwei Bedingungen hängen daran, und sie sind Teil der Regel, nicht Beiwerk:
Es passiert **nur auf Klick**, nie im Hintergrund, und die Oberfläche sagt
vorher, dass Text herausgeht. Wer ein Gespräch mitschneidet, in dem etwas
gesagt wurde, das nirgends hin soll, muss den Schritt auslassen können, ohne
das Werkzeug zu verlassen.

Beim geführten Gespräch steht der Klick **am Anfang** statt am Ende. Das ist
kein aufgeweichter Klick, sondern ein anderer: Er gilt für die ganze Sitzung,
und deshalb muss die Ansage davor stehen und nicht danach. Ohne ihn beginnt
eine gewöhnliche Aufnahme — dieselbe wie vorher, ohne Netz, ohne Aufruf nach
draußen. Das ist die Voreinstellung, nicht die Ausnahme.

Der Grund für die Änderung steht in #125: Am 2026-09-13 sagte Firat „Ich
möchte ein Spiel entwickeln", und die nächste Frage war „Woran merkst du,
dass es fertig ist?". Vier von fünf Punkten blieben offen. Eine Frage, die
zuhört, kann nur stellen, wer gehört hat, wovon die Rede ist.

---

## Die Runde

Ein Gespräch reicht nicht, und ein langes Gespräch erst recht nicht. Wer am
Anfang alles fragt, bekommt Antworten auf Fragen, die noch niemand beurteilen
kann — der Gesprächspartner sieht ja nichts. Deshalb arbeitet das Werkzeug in
Runden:

1. **Erstgespräch — der Rahmen.** Kurz. Wofür, für wen, was gehört nicht
   dazu, woran merkt man, dass es gut ist. Keine Details, keine Felder, keine
   Bildschirme. Wer hier schon Masken bespricht, bespricht ein Produkt, das
   noch niemand gesehen hat.
2. **Projektplan.** Aus dem Rahmen entsteht ein Vorschlag: Meilensteine, jeder
   etwas, das man vorführen und beurteilen kann. Der Plan ist ein Vorschlag,
   kein Beschluss — er wird freigegeben wie alles andere.
3. **Bauen.** Der bestehende Weg: Issue, Agent, vier Checks, Merge.
4. **Produkt-Review.** Was gebaut wurde, wird gezeigt. Nicht beschrieben.
5. **Rückmeldung.** Direkt danach, als Gespräch, mit demselben Werkzeug — und
   damit ist Runde 1 zu Ende und Runde 2 fängt an, mit einem
   Gesprächspartner, der diesmal etwas gesehen hat.

Was daran hängt: Jede Runde ist kurz genug, dass eine falsche Annahme
höchstens eine Runde kostet. Ein Erstgespräch, das drei Stunden dauert und
alles klärt, klärt in Wahrheit nichts — es schreibt nur Vermutungen auf, die
niemand prüfen konnte.

---

## Meilensteine

| # | Meilenstein | Abnahmekriterium (ein Projektmanager kann …) | Ziel | Status |
|---|-------------|-----------------------------------------------|------|--------|
| P1 | Aus dem Gespräch werden Anforderungen | … eine Aufnahme in der Oberfläche starten und stoppen, und findet danach die abgeleiteten Anforderungen als Issues mit `status:vorschlag` im Repo | | offen |
| P2 | Der Projektmanager entscheidet | … zu jeder Anforderung eine Rückfrage stellen und sie freigeben — in derselben Oberfläche, in der sie entstand | | offen |
| P3 | Der Fortschritt ist sichtbar | … sehen, was aus jeder Anforderung geworden ist: offen, in Arbeit, gemergt | | offen |
| P4 | Das Werkzeug führt das Gespräch | … ein Erstgespräch führen, in dem das Werkzeug die Fragen stellt, in Pausen nachfragt und von selbst aufhört, bevor es ins Detail geht | | offen |
| P5 | Aus dem Rahmen wird ein Plan | … nach dem Erstgespräch einen vorgeschlagenen Projektplan mit Meilensteinen sehen und freigeben | | offen |
| P6 | Die Runde schließt sich | … nach einem Produkt-Review eine Rückmeldung aufnehmen, aus der die nächsten Anforderungen entstehen | | offen |

Jeder Meilenstein endet mit einer **Vorführung an einem echten Gespräch** —
nicht an einer Beispieldatei. Kein Meilenstein gilt als erledigt, weil der
Code gemergt ist.

---

## Testfall: Quizbaukasten

Bis zum 2026-09-12 war der Quizbaukasten das Produkt dieses Plans. Er ist
es nicht mehr — er war der Testfall, an dem das Werkzeug geprüft wurde, und
er bleibt es.

Sein Nutzen ändert sich damit nicht: Er ist echte Arbeit mit echten Tickets,
und ohne ihn hätte niemand gemerkt, dass zwei von vier Gates nichts taten.
Was daran gebaut wird, wird weiter richtig gebaut.

| # | Meilenstein | Abnahmekriterium (der Quizmaster kann …) | Status |
|---|-------------|-------------------------------------------|--------|
| M1 | Quiz bauen | … ein Quiz mit Runden und Fragen anlegen, speichern und wieder öffnen | teilweise |
| M2 | Abend moderieren | … das Quiz Frage für Frage anzeigen, Antworten erfassen, Punktestand sehen | offen |
| M3 | Wiederverwenden | … ein Quiz als Vorlage kopieren und Runden austauschen | offen |

Auf `main` liegen aus M1: Fragen umsortieren (#21), Runden umsortieren (#31),
vollständige Prüfung beim Laden (#26).

Der Pilotnutzer Marek Sowa (`pilotnutzer.md`) gehört zum Testfall, nicht zum
Produkt. Was ihm zugesagt wurde, gilt trotzdem.

---

## Annahmen

- **A1:** Ein Projektmanager will Anforderungen prüfen, bevor sie Tickets
  werden — nicht danach. Kippt das, ist die Freigabe in P2 überflüssig.
- **A2:** Lokale Spracherkennung ist gut genug, um Anforderungen zu erkennen.
  Ungeprüft: Bisher lief sie nur gegen erzeugte Testdateien, nie gegen ein
  echtes Gespräch.
- **A3:** ~~Die Hinweise aus `ausloeser.py` treffen oft genug, um zu nützen,
  und selten genug, um nicht zu stören.~~ **Hinfällig am 2026-09-12.** Nicht
  widerlegt, sondern überholt: Firat will keinen Zwischenrufer, sondern einen
  Gesprächsführer. Die Frage, ob ein Einwurf im richtigen Moment kommt,
  stellt sich nicht mehr, wenn gar nicht eingeworfen wird.
- **A6:** ~~Ein geführtes Gespräch mit fünf Fragen und höchstens einer
  Rückfrage je Frage liefert einen brauchbaren Rahmen.~~ **Widerlegt am
  2026-09-13:** Im ersten funktionierenden Gespräch blieben vier von fünf
  Punkten offen. Nicht weil die Prüfung zu streng war, sondern weil feste
  Fragen an jemandem vorbeigehen, der gerade etwas anderes gesagt hat.
- **A8:** Eine Frage, die ein Wort aus der vorherigen Antwort aufgreift,
  holt mehr heraus als eine vorformulierte. Ungeprüft. Kippt das, liegt es
  nicht an den Fragen, sondern daran, dass ein Erstgespräch für diese Art
  von Klärung der falsche Ort ist.
- **A7:** Der Gesprächspartner kann nach einem Produkt-Review mehr sagen als
  davor. Darauf steht die ganze Runde. Kippt das, sind Runden nur Aufwand.
- **A4:** Wer das Werkzeug benutzt, arbeitet ohnehin mit GitHub. Sonst ist
  „Anforderung = Issue" eine Zumutung statt einer Vereinfachung.
- **A5:** Aus Gesprächstext lassen sich Anforderungen ableiten, die ein
  prüfbares „fertig, wenn …" enthalten. Ungeprüft. Kippt das, ist der
  Ableitungsschritt nur ein Stichwortzettel — nützlich, aber nicht das,
  wofür er gebaut wurde.

## Offene Punkte

| # | Frage | An wen | Seit |
|---|-------|--------|------|
| 1 | Wer ist der zweite Nutzer, der nicht Firat ist? | Firat | 2026-09-12 |
| 2 | Braucht P2 mehrere Freigeber, oder reicht einer? | Firat | 2026-09-12 |

## Abweichungen

| Datum | Was weicht ab | Ursache | Option A | Option B | Entscheidung |
|-------|---------------|---------|----------|----------|--------------|
| 2026-09-12 | Produkt gewechselt: Protokoll-Werkzeug statt Quizbaukasten | Beim Aufsetzen des Prozesses zeigte sich, dass das Werkzeug selbst das Ergebnis ist. Der Quizbaukasten war der Testfall, an dem es geprüft wurde. | Quizbaukasten wird Testfall, Werkzeug wird Produkt | Zwei Produkte, zwei Pläne | **A**, von Firat am 2026-09-12 |
| 2026-09-12 | Text verlässt den Rechner: Anforderungen werden von Claude abgeleitet | Lokal bliebe die Qualität unter dem, was ein „fertig, wenn …" braucht. Ein Ableitungsschritt, der schlechte Anforderungen liefert, ist schlimmer als keiner — man sieht ihm an, dass er lief, nicht dass er danebenlag. | Lokales Modell, Plan bleibt unverändert | Claude über das vorhandene Abo, Plan wird präzisiert | **B**, von Firat am 2026-09-12, #102 |
| 2026-09-12 | Vom Zwischenruf zum geführten Interview, und von einem Gespräch zu Runden | Der Zwischenruf unterbricht mitten im Satz, und ein einzelnes Gespräch fragt nach Dingen, die der Gesprächspartner ohne gebautes Produkt nicht beurteilen kann. | Zwischenruf verbessern, ein Gespräch bleibt ein Gespräch | Werkzeug führt das Interview, Runden aus Plan, Bauen, Review und Rückmeldung | **B**, von Firat am 2026-09-12 |
| 2026-09-13 | Während eines geführten Gesprächs geht fortlaufend Text hinaus | Feste Fragen gehen an dem vorbei, was gerade gesagt wurde: Auf „ich möchte ein Spiel entwickeln" folgte „woran merkst du, dass es fertig ist?", und vier von fünf Punkten blieben offen. | Tieferer Fragebaum, alles lokal, kein Aufruf nach draußen | Claude bildet die nächste Frage aus dem Gesagten, Klick am Anfang der Sitzung | **B**, von Firat am 2026-09-13, #125 |
