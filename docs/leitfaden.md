# Gesprächsleitfaden

Ein Gespräch lässt sich nicht wiederholen. Was nicht gefragt wurde, steht
später auch nicht im Transkript — und was nicht im Transkript steht, kann kein
Werkzeug daraus ableiten.

Dieser Leitfaden ist rückwärts gebaut: aus dem, was ein brauchbares Issue
braucht (siehe `CLAUDE.md`). Jede Frage füllt genau ein Feld. Wer alle fünf
gestellt hat, kann das Issue schreiben, ohne zu raten.

Die Fragen stehen wörtlich da, damit man sie vorlesen kann. Umformulieren ist
erlaubt — auslassen fällt später auf, wenn das Feld leer bleibt.

Zwei Felder steuern das geführte Gespräch (#114): **Prüfung** sagt, woran der
Rechner erkennt, dass eine Antwort trägt. **Rückfrage** ist der eine Satz, der
kommt, wenn sie es nicht tut — genau einer, danach geht es weiter. Wer hier
einen Punkt ergänzt, ergänzt damit auch das Interview; wer eine unbekannte
Prüfung einträgt, bekommt einen roten Test statt eines stillen Durchwinkens.

## Die fünf Fragen

### Ausgangslage

Frage: Wer hat das Problem, und was tut die Person heute stattdessen?
Füllt: Den einen Satz Kontext.
Achtung: „Wir brauchen X" ist keine Antwort, sondern schon eine Lösung. Dann
noch einmal fragen: Was passiert gerade, wenn X fehlt?
Prüfung: inhalt
Rückfrage: Was passiert heute, wenn das fehlt?

### Abnahme

Frage: Woran merkst du, dass es fertig ist?
Füllt: Das „fertig, wenn …".
Achtung: Die wichtigste Frage im ganzen Gespräch. Kommt hier nichts Prüfbares
heraus, ist das kein Grund weiterzugehen, sondern der Grund, hier zu bleiben.
Prüfung: pruefbar
Rückfrage: Woran würdest du es festmachen — was müsste man sehen können?

### Abgrenzung

Frage: Was gehört ausdrücklich nicht dazu?
Füllt: Die Liste „Was nicht dazugehört" in `docs/plan.md`.
Achtung: Antworten hier sind wertvoller als sie klingen. Sie sind das
Einzige, was später einen Streit über den Umfang entscheiden kann.
Prüfung: abgrenzung
Rückfrage: Gibt es etwas, das ausdrücklich nicht dazugehört?

### Größenordnung

Frage: Wie oft, wie viele, wie lange?
Füllt: `groesse:` — und macht aus „einige", „später", „schnell" Zahlen.
Achtung: Wer keine Zahl nennen kann, weiß es noch nicht. Das ist ein
Ergebnis, kein Versagen; es gehört als offene Frage ins Issue.
Prüfung: zahl
Rückfrage: Kannst du eine Zahl nennen — wie oft, wie viele, wie lange?

### Fehlerfall

Frage: Was passiert, wenn es schiefgeht?
Füllt: Den Teil, den sonst niemand aufschreibt.
Achtung: Fast jedes Gespräch beschreibt den Sonnenschein-Pfad. Der Fehlerfall
entscheidet, ob das Gebaute im Ernstfall taugt.
Prüfung: fehlerfall
Rückfrage: Und wenn es schiefgeht — was passiert dann?

## Nach dem Gespräch

Die Punkte abhaken, solange die Aufnahme noch läuft. Ein nicht abgehakter
Punkt am Ende ist kein Makel — er ist die Liste dessen, was beim nächsten Mal
zuerst drankommt.
