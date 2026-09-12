# Wie eine Entscheidung ins Werkzeug kommt

Eine Entscheidung, die nur in einer Unterhaltung existiert, ist kein
Review-Objekt. Sie geht unter, sie lässt sich nicht nachlesen, und ein Gate
kann sie nicht sehen — am 2026-09-12 hat der `review`-Prüfer eine
Planänderung zu Recht blockiert, weil Firats „B" im Chat stand und nicht im
Issue.

Damit eine Frage in der Freigabe-Konsole erscheint, steht im Issue genau
dieser Abschnitt:

```markdown
## Entscheidung

Soll der Text des Transkripts an Claude gehen?

- **A** — Lokal bleiben. Nichts verlässt den Rechner.
- **B** — Claude benutzen. Text geht raus, Ton nie.

Empfehlung: B — lokal reicht die Qualität nicht für ein „fertig, wenn …".
```

## Die Regeln dahinter

**Der erste Absatz ist die Frage.** Alles vor der ersten Option, nach der
Überschrift.

**Optionen sind `- **A** — Text`.** Ein Buchstabe, ein Gedankenstrich, ein
Satz. Wer drei Optionen braucht, nimmt `C`; wer eine braucht, hat keine
Entscheidung, sondern einen Vorschlag.

**Die Empfehlung nennt den Grund.** `Empfehlung: B — weil …`. Eine Markierung
ohne Begründung ist eine Anweisung, kein Rat; wer sie ablehnen soll, muss
wissen, wogegen er sich entscheidet. Fehlt die Zeile, sagt die Konsole
ausdrücklich, dass es keine Empfehlung gibt.

**Der Abschnitt endet an der nächsten `##`-Überschrift.** Eine Liste unter
„fertig, wenn" ist keine Auswahl.

**Beantwortet wird mit einem Kommentar, der aus dem Buchstaben besteht.** Der
Knopf in der Konsole schreibt genau das. Danach verschwindet die Karte.

**Nur Kommentare von Menschen aus `scripts/menschen.txt` zählen.** Sonst
könnte sich die Kette ihre eigenen Fragen beantworten — genau das, was Gate
G2 verhindern soll.

**Ein Klick entscheidet, er gibt nicht frei.** `status:freigegeben` bleibt ein
eigener Knopf. Wären es ein Handgriff, wäre eines von beiden irgendwann
versehentlich.

**Ein Issue, eine Entscheidung.** Eine zweite Frage im selben Issue wäre
unsichtbar, sobald die erste beantwortet ist — der Buchstaben-Kommentar
gehört dann schon zur alten. Wer eine zweite Frage hat, legt ein zweites
Issue an. Eine Entscheidung ist ein Review-Objekt, und zwei Objekte sind
zwei Objekte.

**Beispiele stehen in Codeblöcken.** Was zwischen ``` steht, liest die
Konsole nicht. Sonst würde diese Anleitung selbst als offene Frage
erscheinen — dasselbe Muster wie bei Gate G2, wo ein `Refs #31` in einem
Codeblock als echte Referenz zählte.
