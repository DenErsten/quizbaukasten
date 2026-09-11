#!/usr/bin/env bash
# Legt das Label-Set an. Die status:-Labels sind Gate G2:
# Automationen triggern ausschliesslich auf status:freigegeben,
# und dieses Label setzt nur ein Mensch.
set -euo pipefail

command -v gh >/dev/null || { echo "gh CLI fehlt: https://cli.github.com"; exit 1; }

anlegen() {
  # $1 Name, $2 Farbe, $3 Beschreibung
  if gh label create "$1" --color "$2" --description "$3" 2>/dev/null; then
    echo "  angelegt:  $1"
  else
    gh label edit "$1" --color "$2" --description "$3" >/dev/null
    echo "  aktualisiert: $1"
  fi
}

echo "Gate-Labels (G2)"
anlegen "status:vorschlag"    "E4A853" "Von der KI vorgeschlagen — noch nicht freigegeben"
anlegen "status:freigegeben"  "0E7C6B" "Von Firat freigegeben — Automationen duerfen laufen"
anlegen "status:wartet"       "9AA5A2" "Wartet auf Kunde oder Dritte"
anlegen "status:blockiert"    "B23A2F" "Kommt nicht weiter"

echo "Art"
anlegen "art:anforderung"     "1F6FB2" "Etwas, das gebaut werden soll"
anlegen "art:fehler"          "B23A2F" "Etwas ist kaputt"
anlegen "art:frage"           "6B4FA8" "Klaerungsbedarf beim Kunden"
anlegen "art:pruefung"        "7A6BA8" "Betriebspruefung — ein Mensch fuehrt aus und schliesst, kein PR"
anlegen "lagebericht"         "3D4B48" "Automatisch erzeugte Wochenuebersicht"

echo "Auslöser"
anlegen "agent:bauen"        "0E7C6B" "Anheften startet den Agenten (Gate G2 vorher setzen!)"

echo "Groesse"
anlegen "groesse:S"           "D8E0DD" "unter einem halben Tag"
anlegen "groesse:M"           "B9C6C2" "ein bis zwei Tage"
anlegen "groesse:L"           "8FA29D" "muss geschnitten werden"

echo
echo "Fertig. Merksatz fuer das Camp:"
echo "  status:vorschlag  darf die KI setzen."
echo "  status:freigegeben setzt nur ein Mensch. Das ist Gate G2."
