---
name: kundenmail
description: Einen Mailentwurf an den Kunden schreiben — Status, Rückfrage, Verzugsmeldung oder Meilenstein-Übergabe. Nutzen bei "Mail an den Kunden", "Status schreiben", "Kunden informieren". Erzeugt immer nur einen Entwurf.
---

# Kundenmail entwerfen

Du erzeugst **ausschließlich Entwürfe**. Der Mail-Server hat kein `send` für dich,
und das ist Absicht: Gate **G5**.

## Vorher immer

Lies `docs/kunde.md` — Ansprechpartner, Tonfall, empfindliche Punkte. Lies das
letzte Protokoll in `docs/meetings/`, damit du nichts wiederholst und nichts
übergehst, was offen geblieben ist.

## Aufbau

Der wichtigste Satz steht **oben**. Kunden lesen Mails auf dem Handy zwischen
zwei Terminen; ein Fazit im letzten Absatz erreicht niemanden.

| Anlass | Erster Satz |
|--------|-------------|
| Status | Was seit der letzten Mail fertig wurde |
| Rückfrage | Die Frage selbst, nicht ihre Vorgeschichte |
| Verzug | Was sich verschiebt und um wie viel |
| Übergabe | Was ab jetzt benutzbar ist |

Danach: Details, Termine, Anhänge. Höchstens 200 Wörter.

## Verzugsmeldungen

Drei Sätze, in dieser Reihenfolge: **Was ist passiert. Was bedeutet das.
Was schlage ich vor.** Keine Entschuldigungsschleife, keine Erklärung der
technischen Ursache, wenn sie nicht zur Entscheidung beiträgt. Melde am Tag
der Erkenntnis, nicht am Tag des Termins.

## Verboten

- „Wir freuen uns auf die weitere Zusammenarbeit", „gerne", „zeitnah",
  „selbstverständlich", „im Rahmen unserer Möglichkeiten"
- Ausrufezeichen
- Zusagen zu Preisen, Aufwänden oder Terminen, die nicht schon in
  `docs/plan.md` stehen. Wenn eine Zusage nötig ist: Platzhalter
  `[[TERMIN — Firat setzt ein]]` schreiben und im PR darauf hinweisen.
- Eine Anforderung des Kunden als angenommen darstellen, bevor ein Issue
  freigegeben ist

## Wenn schlechte Nachrichten drinstehen

Markiere den Entwurf oben mit `<!-- HEIKEL: bitte Wort fuer Wort lesen -->`.
Hier kostet ein glattgebügelter KI-Satz echtes Vertrauen, und der Kunde in
`docs/kunde.md` hat bereits ein abgebrochenes Projekt hinter sich.

## Ablage

Entwurf in den Thunderbird-Ordner `Entwürfe/KI` schreiben. Ist der Mail-MCP
nicht verfügbar, stattdessen `docs/mailentwuerfe/JJJJ-MM-TT-<thema>.md`
anlegen und im PR darauf hinweisen — nie stillschweigend nichts tun.
