#!/usr/bin/env bash
#
# Prüft, ob die Gates wirklich stehen. Ändert nichts, legt nichts an.
#
#   ./scripts/pruefe-gates.sh
#
# Jederzeit laufen lassen — vor dem Camp, nach jeder Änderung an den
# Workflows, und am Ende jedes Tages. Ein rotes Ergebnis hier bedeutet,
# dass ab diesem Moment jemand etwas merged, das niemand geprüft hat.
#
# Der eine Test, den dieses Skript wirklich durchführt statt nur nachzuschlagen,
# ist der Push auf main. Alles andere liest nur die Einstellungen — und eine
# Einstellung, die richtig aussieht, ist noch kein funktionierendes Gate.

set -uo pipefail

GRUEN=$'\033[32m'; ROT=$'\033[31m'; GRAU=$'\033[90m'; AUS=$'\033[0m'
ROT_ZAEHLER=0

ja()   { printf "  ${GRUEN}✓${AUS} %s\n" "$1"; }
nein() { printf "  ${ROT}✗${AUS} %s\n" "$1"; ROT_ZAEHLER=$((ROT_ZAEHLER+1)); }
info() { printf "    ${GRAU}%s${AUS}\n" "$1"; }

cd "$(dirname "$0")/.." || exit 1
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)" || exit 1
printf "Repo: %s\n" "$REPO"

# --- G1/G3: main ist geschützt ------------------------------------------
printf "\nmain ist geschützt\n"
PFAD="repos/$REPO/branches/main/protection"
if ! gh api "$PFAD" >/dev/null 2>&1; then
  nein "Branch Protection fehlt vollständig"
else
  C="$(gh api "$PFAD" --jq '.required_status_checks.contexts[]?' 2>/dev/null)"
  for c in pfade pruefen review abnahme; do
    grep -qx "$c" <<<"$C" && ja "Required Check: $c" || nein "Required Check fehlt: $c"
  done
  [ "$(gh api "$PFAD" --jq '.enforce_admins.enabled' 2>/dev/null)" = "true" ] \
    && ja "enforce_admins" || nein "enforce_admins ist aus"
  [ "$(gh api "$PFAD" --jq '.allow_force_pushes.enabled' 2>/dev/null)" = "false" ] \
    && ja "keine Force-Pushes" || nein "Force-Pushes erlaubt"
fi

# --- der echte Test -----------------------------------------------------
printf "\nEin Push auf main wird abgelehnt\n"
AKTUELL="$(git --no-optional-locks rev-parse HEAD)"
ZWEIG="$(git --no-optional-locks rev-parse --abbrev-ref HEAD)"
if [ "$ZWEIG" != "main" ]; then
  info "übersprungen — du stehst auf '$ZWEIG', nicht auf main"
else
  git commit --allow-empty -q -m "Gate-Probe, wird gleich verworfen"
  if git push origin main >/dev/null 2>&1; then
    nein "Der Push ging DURCH. Alle weiteren Gates sind damit Dekoration."
    info "Sofort anhalten und die Branch Protection reparieren."
  else
    ja "abgelehnt"
  fi
  git reset --hard -q "$AKTUELL"
fi

# --- G4: Produktion wartet auf einen Menschen ---------------------------
printf "\nProduktion wartet auf einen Menschen\n"
if ! gh api "repos/$REPO/environments/produktion" >/dev/null 2>&1; then
  nein "Umgebung 'produktion' gibt es nicht"
else
  NAMEN="$(gh api "repos/$REPO/environments/produktion" --jq '[.protection_rules[]? | select(.type=="required_reviewers") | .reviewers[].reviewer.login] | join(", ")' 2>/dev/null)"
  [ -n "$NAMEN" ] && ja "Required Reviewer: $NAMEN" || nein "kein Required Reviewer — G4 ist offen"
fi

# --- G2: Labels ---------------------------------------------------------
printf "\nDie Freigabe-Labels existieren\n"
L="$(gh label list --limit 100 --json name --jq '.[].name' 2>/dev/null)"
for l in status:vorschlag status:freigegeben; do
  grep -qx "$l" <<<"$L" && ja "$l" || nein "$l fehlt"
done

# --- Der Pfad-Wächter tut, was er soll ----------------------------------
printf "\nDer Pfad-Wächter unterscheidet richtig\n"
python3 scripts/pfad_pruefung.py --dateien src/quiz.ts >/dev/null 2>&1 \
  && ja "normaler Code darf ohne Menschen durch" \
  || nein "normaler Code wird blockiert — der Wächter ist zu streng"

python3 scripts/pfad_pruefung.py --dateien CLAUDE.md >/dev/null 2>&1 \
  && nein "CLAUDE.md darf ohne Menschen geändert werden — G3 ist offen" \
  || ja "CLAUDE.md braucht einen Menschen"

python3 scripts/pfad_pruefung.py --dateien tests/quiz.test.ts >/dev/null 2>&1 \
  && nein "Tests dürfen ohne Menschen geändert werden — das Netz ist lose" \
  || ja "bestehende Tests brauchen einen Menschen"

# --- Die Werkzeuge des Agenten ------------------------------------------
printf "\nDer Agent kann arbeiten\n"
gh secret list 2>/dev/null | grep -qE 'CLAUDE_CODE_OAUTH_TOKEN|ANTHROPIC_API_KEY' \
  && ja "Token ist gesetzt" || nein "kein Token — die Checks laufen nie an"
[ "$(gh api "repos/$REPO/installation" --jq .app_slug 2>/dev/null)" = "claude" ] \
  && ja "GitHub-App installiert" || nein "GitHub-App fehlt"

printf "\n%s\n" "────────────────────────────────────────────────────────"
if [ $ROT_ZAEHLER -eq 0 ]; then
  printf "${GRUEN}Alle Gates stehen.${AUS}\n"
  printf "Was ein Skript nicht prüfen kann, steht in PLANSPIEL.md unter\n"
  printf "\"Rote Karte\": ob der Agent einen Test entschärft, um grün zu werden.\n"
else
  printf "${ROT}%d Punkte offen. Bis die stehen, merged etwas, das niemand geprüft hat.${AUS}\n" "$ROT_ZAEHLER"
fi
exit $(( ROT_ZAEHLER > 0 ? 1 : 0 ))
