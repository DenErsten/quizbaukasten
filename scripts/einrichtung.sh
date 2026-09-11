#!/usr/bin/env bash
#
# Richtet alles ein, was sich ohne menschliches Urteil einrichten lässt —
# und prüft danach, ob es wirklich steht.
#
#   ./scripts/einrichtung.sh
#
# Idempotent: mehrfach laufen lassen ist ungefährlich, das Skript legt nichts
# doppelt an und meldet jeden Punkt als OK, FEHLT oder MENSCH.
#
# WAS DIESES SKRIPT BEWUSST NICHT TUT
# -----------------------------------
# Es setzt kein Label status:freigegeben, es merged nichts, es gibt nichts
# für Produktion frei und es bewertet die Rote Karte nicht. Das sind die
# Gates. Ein Skript, das seine eigenen Gates passieren darf, ist kein Gate —
# und ein Agent, der seine eigenen Schranken aufstellt und danach prüft, ob
# er sie überwinden kann, ist der schlechteste denkbare Prüfer.
#
# Der Agent darf dieses Skript ausführen. Die Punkte mit MENSCH bleiben bei dir.

set -uo pipefail

GRUEN=$'\033[32m'; ROT=$'\033[31m'; GELB=$'\033[33m'; GRAU=$'\033[90m'; AUS=$'\033[0m'
FEHLER=0
MENSCH_OFFEN=()

ok()     { printf "  ${GRUEN}OK${AUS}      %s\n" "$1"; }
fehlt()  { printf "  ${ROT}FEHLT${AUS}   %s\n" "$1"; FEHLER=$((FEHLER+1)); }
mensch() { printf "  ${GELB}MENSCH${AUS}  %s\n" "$1"; MENSCH_OFFEN+=("$1"); }
info()   { printf "  ${GRAU}%s${AUS}\n" "$1"; }
titel()  { printf "\n%s\n" "$1"; }

cd "$(dirname "$0")/.." || exit 1

# ----------------------------------------------------------------- 0 Werkzeug
titel "0  Werkzeuge"
for w in git gh node npm; do
  if command -v "$w" >/dev/null 2>&1; then ok "$w"; else fehlt "$w fehlt"; fi
done
if command -v claude >/dev/null 2>&1; then
  ok "claude ($(claude --version 2>/dev/null | head -1))"
else
  fehlt "claude fehlt — curl -fsSL https://claude.ai/install.sh | bash"
fi
[ $FEHLER -gt 0 ] && { printf "\n${ROT}Abbruch: erst die Werkzeuge.${AUS}\n"; exit 1; }

if ! gh auth status >/dev/null 2>&1; then
  fehlt "gh ist nicht angemeldet — gh auth login"
  exit 1
fi
ok "gh angemeldet"

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)"
[ -z "$REPO" ] && { fehlt "kein GitHub-Repo in diesem Ordner"; exit 1; }
info "Repo: $REPO"

# ------------------------------------------------------------ 1 Menschenliste
titel "1  Wessen Freigabe zählt"
MENSCH_LOGIN="$(grep -v '^[[:space:]]*#' scripts/menschen.txt | grep -v '^[[:space:]]*$' | head -1)"
ICH="$(gh api user --jq .login 2>/dev/null)"
if [ -z "$MENSCH_LOGIN" ]; then
  fehlt "scripts/menschen.txt ist leer"
elif [ "$MENSCH_LOGIN" = "$ICH" ]; then
  ok "$MENSCH_LOGIN (stimmt mit dem angemeldeten Konto überein)"
else
  fehlt "menschen.txt sagt '$MENSCH_LOGIN', angemeldet ist '$ICH'"
  info "Ohne Übereinstimmung wartet Gate G4 auf ein Konto, das niemand bedient."
fi

# ------------------------------------------------------------------- 2 Secret
titel "2  Token für die CI"
if gh secret list 2>/dev/null | grep -q CLAUDE_CODE_OAUTH_TOKEN; then
  ok "CLAUDE_CODE_OAUTH_TOKEN ist gesetzt"
elif gh secret list 2>/dev/null | grep -q ANTHROPIC_API_KEY; then
  ok "ANTHROPIC_API_KEY ist gesetzt"
  info "Läuft über API-Abrechnung statt über das Abo. Bei vier Checks pro PR"
  info "summiert sich das — 'claude setup-token' wäre der günstigere Weg."
else
  mensch "Token fehlt: claude setup-token && gh secret set CLAUDE_CODE_OAUTH_TOKEN"
fi

# --------------------------------------------------------------- 3 GitHub-App
titel "3  GitHub-App"
APP="$(gh api "repos/$REPO/installation" --jq .app_slug 2>/dev/null)"
if [ "$APP" = "claude" ]; then
  ok "Claude-App ist installiert"
else
  mensch "App fehlt: claude → /install-github-app (Workflow-Dateien: 'Skip for now')"
fi

# ------------------------------------------------------------------- 4 Labels
titel "4  Labels (Gate G2)"
if [ -x scripts/setup-labels.sh ]; then
  ./scripts/setup-labels.sh >/dev/null 2>&1
fi
VORHANDEN="$(gh label list --limit 100 --json name --jq '.[].name' 2>/dev/null)"
for l in status:vorschlag status:freigegeben status:wartet status:blockiert \
         art:anforderung art:fehler art:frage lagebericht \
         groesse:S groesse:M groesse:L; do
  if grep -qx "$l" <<<"$VORHANDEN"; then ok "$l"; else fehlt "$l"; fi
done

# ------------------------------------------------------------------ 5 Repo-Ops
titel "5  Repo-Einstellungen"
EIN="$(gh api "repos/$REPO" --jq .allow_auto_merge 2>/dev/null)"
if [ "$EIN" = "true" ]; then ok "Auto-Merge aktiv"; else
  gh api -X PATCH "repos/$REPO" -F allow_auto_merge=true -F delete_branch_on_merge=true \
    -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false >/dev/null 2>&1 \
    && ok "Auto-Merge eingeschaltet" || fehlt "Auto-Merge ließ sich nicht setzen"
fi

# ------------------------------------------------------- 6 Branch Protection
titel "6  Branch Protection auf main"
SCHUTZ="$(gh api "repos/$REPO/branches/main/protection" 2>/dev/null)"
if [ -z "$SCHUTZ" ]; then
  info "noch nicht gesetzt — setze jetzt"
  gh api -X PUT "repos/$REPO/branches/main/protection" \
    -H "Accept: application/vnd.github+json" --input - >/dev/null 2>&1 <<'JSON'
{
  "required_status_checks": { "strict": true,
    "contexts": ["pfade", "pruefen", "review", "abnahme"] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_linear_history": true,
  "required_conversation_resolution": true
}
JSON
  SCHUTZ="$(gh api "repos/$REPO/branches/main/protection" 2>/dev/null)"
fi

if [ -n "$SCHUTZ" ]; then
  CONTEXTS="$(gh api "repos/$REPO/branches/main/protection" --jq '.required_status_checks.contexts[]?' 2>/dev/null)"
  for c in pfade pruefen review abnahme; do
    if grep -qx "$c" <<<"$CONTEXTS"; then ok "Required Check: $c"; else fehlt "Required Check fehlt: $c"; fi
  done
  ADMINS="$(gh api "repos/$REPO/branches/main/protection" --jq '.enforce_admins.enabled' 2>/dev/null)"
  if [ "$ADMINS" = "true" ]; then
    ok "enforce_admins — gilt auch für dich"
  else
    fehlt "enforce_admins ist aus; die Gates sind für den Besitzer wirkungslos"
  fi
else
  fehlt "Branch Protection konnte nicht gesetzt werden (Admin-Rechte?)"
fi

# --------------------------------------------------------------- 7 Umgebungen
titel "7  Umgebungen"
gh api -X PUT "repos/$REPO/environments/staging" --input - >/dev/null 2>&1 <<'JSON'
{ "wait_timer": 0 }
JSON
ok "staging (ohne Freigabe — jeder Merge geht durch)"

if [ -n "${ICH:-}" ]; then
  ICH_ID="$(gh api "users/$ICH" -q .id 2>/dev/null)"
  if [ -n "$ICH_ID" ]; then
    gh api -X PUT "repos/$REPO/environments/produktion" --input - >/dev/null 2>&1 <<JSON
{ "wait_timer": 0, "prevent_self_review": false,
  "reviewers": [{ "type": "User", "id": $ICH_ID }],
  "deployment_branch_policy": { "protected_branches": true, "custom_branch_policies": false } }
JSON
    PRUEFER="$(gh api "repos/$REPO/environments/produktion" \
      --jq '[.protection_rules[]? | select(.type=="required_reviewers") | .reviewers[].reviewer.login] | join(", ")' 2>/dev/null)"
    if [ -n "$PRUEFER" ]; then
      ok "produktion — Required Reviewer: $PRUEFER  (Gate G4)"
    else
      fehlt "produktion hat keinen Required Reviewer — G4 wäre offen"
    fi
  fi
fi

# ---------------------------------------------------------------------- 8 MCP
titel "8  GitHub an Claude Code lokal"
if claude mcp list 2>/dev/null | grep -q '^github'; then
  ok "MCP-Server github ist eingetragen"
else
  claude mcp add --transport http github https://api.githubcopilot.com/mcp/ >/dev/null 2>&1 \
    && ok "MCP-Server github eingetragen" \
    || mensch "MCP ließ sich nicht eintragen: claude mcp add --transport http github https://api.githubcopilot.com/mcp/"
fi

# -------------------------------------------------------------------- Bericht
printf "\n%s\n" "────────────────────────────────────────────────────────"
if [ $FEHLER -eq 0 ] && [ ${#MENSCH_OFFEN[@]} -eq 0 ]; then
  printf "${GRUEN}Alles eingerichtet.${AUS}\n"
else
  [ $FEHLER -gt 0 ] && printf "${ROT}%d Punkte fehlen.${AUS}\n" "$FEHLER"
  if [ ${#MENSCH_OFFEN[@]} -gt 0 ]; then
    printf "${GELB}Diese Punkte kann kein Skript erledigen:${AUS}\n"
    for m in "${MENSCH_OFFEN[@]}"; do printf "  · %s\n" "$m"; done
  fi
fi

cat <<'ENDE'

Was jetzt noch offen ist und bei einem Menschen bleibt:

  1. Ein Issue anlegen und mit status:freigegeben versehen.
     Das ist Gate G2. Setzt der Agent es selbst, habt ihr das Gate
     am ersten Tag ausgehebelt — und niemand würde es merken.

  2. Die Rote Karte durchführen und bewerten.
     Ein Agent, der prüft, ob er seine eigenen Schranken überwinden
     kann, ist der schlechteste denkbare Prüfer. Diese halbe Stunde
     ist die einzige im Camp, die sich nicht delegieren lässt.

  Prüfen, ob alles steht:  ./scripts/pruefe-gates.sh
ENDE

exit $(( FEHLER > 0 ? 1 : 0 ))
