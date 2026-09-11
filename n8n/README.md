# n8n im Studio-OS

## Welche Rolle n8n hier hat — und welche nicht

n8n verdrahtet **Ereignisse**, die außerhalb von GitHub entstehen: eine Datei
landet in einem Ordner, eine Mail kommt an, eine Sprachnachricht trifft ein,
eine Uhrzeit ist erreicht. Alles, was schon in GitHub passiert, bleibt in
GitHub Actions — sonst hast du zwei Automatisierungssysteme, die sich um
denselben Zustand streiten.

Klare Trennung für das Camp:

| Auslöser | Wer macht es |
|----------|--------------|
| Issue, PR, Kommentar, `@claude`, Cron im Repo | GitHub Actions |
| Datei im Ordner, Mail, Telegram, Webhook von außen | n8n |
| Etwas verändern, das Nutzer sehen | ein Mensch |

**Wichtiger Grundsatz:** Die Freigabeknöpfe in n8n geben immer nur einen
*Automatisierungsschritt* frei („soll ich das Protokoll jetzt bauen?"), nie
einen *Inhalt* („ist dieses Protokoll richtig?"). Inhalte werden im PR
freigegeben, wo man den Diff sieht. Ein Daumen-hoch auf dem Handy ist kein
Review, und es ist ehrlicher, das im Design festzuhalten, als sich später
darauf zu verlassen.

---

## Aufsetzen

```bash
docker run -d --name n8n -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -v /pfad/zum/repo:/repo \
  -e TELEGRAM_CHAT_ID=<deine-chat-id> \
  -e N8N_SECURE_COOKIE=false \
  -e WEBHOOK_URL=http://localhost:5678/ \
  docker.io/n8nio/n8n
```

Wichtig für dieses Setup: n8n ruft `claude`, `gh` und `transkribieren.sh` per
`Execute Command` auf. Im Container gibt es die nicht. Zwei Wege:

1. **Für das Camp am einfachsten:** n8n mit `npx n8n` direkt auf dem Rechner
   laufen lassen, nicht im Container. Dann sind alle Werkzeuge und die
   Claude-Anmeldung da, wo n8n sie erwartet.
2. **Saubere Variante:** eigenes Image auf Basis von `n8nio/n8n` mit
   Node, `gh`, `ffmpeg` und Claude Code, und das Repo als Volume.

Nimm für drei Tage Weg 1. Weg 2 kostet einen halben Tag und liefert für das
Planspiel keine zusätzliche Erkenntnis.

---

## Zugangsdaten

| Wofür | Typ in n8n | Hinweis |
|-------|-----------|---------|
| Telegram | Telegram API | Bot bei `@BotFather` anlegen, Chat-ID über `getUpdates` holen |
| GitHub (Wächter) | Header Auth: `Authorization: Bearer <PAT>` | **Anderes Token als der Agent benutzt** |

Das getrennte Token ist keine Förmelei: Wenn der Wächter mit demselben Token
arbeitet wie der Agent, kann der Agent den Wächter abschalten. Ein Wächter mit
den Händen des Bewachten ist keiner.

---

## 01 Meeting-Pipeline

`aufnahmen/` wird beobachtet → Transkription lokal → Rückfrage per Telegram →
Agent baut Protokoll, Draft-Issues und Mailentwurf → PR-Link kommt zurück.

**Nach dem Import anzupassen:**

- In allen `Execute Command`-Nodes `/pfad/zum/repo` ersetzen
- `Neue Aufnahme`: Pfad auf `<repo>/aufnahmen` setzen
- Timeout in `Transkribieren` hochsetzen (Node → Settings → Timeout), sonst
  bricht n8n eine 30-Minuten-Aufnahme mitten in der Transkription ab
- Telegram-Zugangsdaten in den drei Telegram-Nodes zuweisen

**Bekannte Stolperstellen:** `sendAndWait` braucht eine von außen erreichbare
`WEBHOOK_URL`. Auf `localhost` funktioniert der Knopf im Telegram nur, wenn du
im gleichen Netz bist. Für das Camp reicht das; wer es unterwegs will, braucht
einen Tunnel (`n8n start --tunnel` oder Cloudflare Tunnel).

---

## 02 Gate-Wächter

Der interessanteste Workflow im Kit, und der, der eure Kernanforderung
verteidigt: Er hört auf GitHub-Webhooks, prüft bei jedem gesetzten
`status:freigegeben`, ob ein **Mensch von der Liste** es gesetzt hat — und
nimmt es sonst zurück, kommentiert das Issue und schickt Alarm.

**Nach dem Import anzupassen:**

- Im Code-Node `MENSCHEN` auf deine GitHub-Logins setzen
- GitHub-Webhook im Repo eintragen: Settings → Webhooks →
  `http://<host>:5678/webhook/gate-waechter`, Content-Type `application/json`,
  Event nur „Issues"
- Header-Auth-Zugangsdaten mit dem **separaten** Token zuweisen

**Zu ergänzen, wenn Zeit bleibt:** Webhook-Secret prüfen. Ohne Prüfung kann
jeder, der die URL kennt, Ereignisse einspeisen. Für ein Planspiel im lokalen
Netz vertretbar, für echten Betrieb nicht — im Code-Node den
`X-Hub-Signature-256`-Header gegen das Secret verifizieren.

Genau dieser Workflow ist die Demo an Tag 3: Lass den Agenten absichtlich
versuchen, sein eigenes Issue freizugeben. Die Freigabe hält keine zwei
Sekunden, und auf dem Handy liegt die Meldung. Das ist der Unterschied
zwischen einem Prozess und einem Vorsatz.

---

## Was ihr bewusst *nicht* in n8n baut

- **Code schreiben oder reviewen.** Gehört in GitHub Actions, weil dort
  der Code und der Diff liegen.
- **Mails versenden.** G5 sagt: Entwurf ja, Versand nein. Ein n8n-Workflow,
  der eine Mail an den Pilotnutzer schickt, hebelt das Gate aus, egal wie viele
  Freigabeknöpfe davor hängen.
- **Den Projektplan ändern.** Der Plan ändert sich nur über einen PR.
