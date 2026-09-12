#!/usr/bin/env python3
"""
Was auf Firat wartet — Issues fuer Gate G2, PRs fuer eine Freigabe.

Am 11. und 12.09.2026 hat er rund dreissig Mal
"gh issue edit --add-label status:freigegeben" getippt. Das war die
tatsaechliche Reibung dieser Tage, mehr als jede Regel.

MIT WESSEN ZUGANG
-----------------
Ohne gesetztes GH_TOKEN, also mit Firats Anmeldung. Laeuft es ueber das
Bot-Token, steht in der Historie der Bot — und Gate G2 ist eine Attrappe.
Genau das ist am 2026-09-11 zweimal passiert (#10, #57). Deshalb gibt es
dafuer einen eigenen Test und nicht nur einen Kommentar.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Sequence

Aufruf = Callable[[Sequence[str]], str]

FERTIG_WENN = re.compile(r"##\s*Fertig,\s*wenn", re.IGNORECASE)


def _gh(befehl: Sequence[str]) -> str:
    """
    Ruft gh mit Firats Anmeldung.

    GH_TOKEN wird ausdruecklich aus der Umgebung genommen: Der Server laeuft
    unter Umstaenden neben einer Sitzung, die es fuer den Bot gesetzt hat.
    """
    umgebung = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    ergebnis = subprocess.run(
        ["gh", *befehl], capture_output=True, text=True, env=umgebung, check=False
    )
    if ergebnis.returncode != 0:
        # Durchreichen, nicht verschlucken. Ein Fehler, den niemand sieht,
        # sieht aus wie Erfolg — das Muster dieses Projekts (#7, #9, #76).
        raise RuntimeError(ergebnis.stderr.strip() or "gh ist fehlgeschlagen")
    return ergebnis.stdout


def hat_abnahmekriterium(text: str) -> bool:
    """CLAUDE.md: Kein Issue ohne Abnahmekriterium. PR #68 ist daran gescheitert."""
    return bool(FERTIG_WENN.search(text or ""))


def offene_issues(aufruf: Aufruf = _gh) -> list[dict]:
    """Was auf Gate G2 wartet: vorgeschlagen, aber nicht freigegeben."""
    roh = json.loads(aufruf([
        "issue", "list", "--state", "open", "--limit", "100",
        "--json", "number,title,labels,body,milestone",
    ]) or "[]")

    offen = []
    for i in roh:
        namen = {l["name"] for l in i.get("labels", [])}
        if "status:freigegeben" in namen or "status:vorschlag" not in namen:
            continue
        offen.append({
            "nummer": i["number"],
            "titel": i["title"],
            "groesse": next((n for n in namen if n.startswith("groesse:")), None),
            "art": next((n for n in namen if n.startswith("art:")), None),
            "meilenstein": (i.get("milestone") or {}).get("title"),
            "kriterium": hat_abnahmekriterium(i.get("body", "")),
        })
    return offen


MENSCHENDATEI = Path(__file__).resolve().parent.parent / "scripts" / "menschen.txt"


def _menschen() -> set[str]:
    """
    Wessen Kommentar als Entscheidung zaehlt.

    Dieselbe Datei, die Gate G3 benutzt (scripts/pfad_pruefung.py). Zwei
    Listen von Menschen liefen auseinander, und dann zaehlte hier jemand,
    der dort nicht zaehlt.
    """
    if not MENSCHENDATEI.exists():
        return set()
    namen = set()
    for zeile in MENSCHENDATEI.read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#", 1)[0].strip()
        if zeile:
            namen.add(zeile)
    return namen


# --- Entscheidungen (#108) ------------------------------------------------
#
# Eine Entscheidung, die nur in einer Unterhaltung existiert, ist kein
# Review-Objekt. Damit sie eines wird, steht sie im Issue an einer festen
# Stelle — und von dort holt die Konsole sie ab.

ENTSCHEIDUNG = re.compile(r"^##\s+Entscheidung\s*$", re.IGNORECASE)
UEBERSCHRIFT = re.compile(r"^##\s+")
OPTION = re.compile(r"^[-*]\s+\*\*([A-Z])\*\*\s*[—–-]\s*(.+)$")
EMPFEHLUNG = re.compile(r"^Empfehlung:\s*([A-Z])\b\s*[—–-]?\s*(.*)$", re.IGNORECASE)


def _ohne_codebloecke(text: str) -> str:
    """
    Alles zwischen ``` heraus.

    Beim ersten Versuch las der Parser den Beispielblock aus #108 als echte
    Entscheidung — die Anleitung, wie man eine Entscheidung schreibt, wurde
    selbst zu einer. Dasselbe Muster hatte Gate G2 am 2026-09-12: "Refs #31"
    in einem Codeblock zaehlte als echte Referenz. Wer ueber eine Form
    schreibt, benutzt sie nicht.
    """
    zeilen = []
    im_zaun = False
    for zeile in text.splitlines():
        if zeile.lstrip().startswith("```"):
            im_zaun = not im_zaun
            continue
        if not im_zaun:
            zeilen.append(zeile)
    return "\n".join(zeilen)


def entscheidung_aus_text(text: str) -> dict | None:
    """
    Frage, Optionen und Empfehlung aus dem Abschnitt "## Entscheidung".

    Fehlt der Abschnitt, gibt es nichts — das ist der Normalfall und kein
    Fehler. Fehlen Optionen, gibt es ebenfalls nichts: Eine Frage ohne
    Auswahl waere in der Konsole ein Knopf, der nirgendwohin fuehrt.

    Pro Issue gibt es hoechstens EINE Entscheidung. Eine zweite Frage im
    selben Issue waere unsichtbar, sobald die erste beantwortet ist — dann
    gehoert sie in ein eigenes Issue. Eine Entscheidung ist ein
    Review-Objekt, und zwei Objekte sind zwei Objekte.
    """
    text = _ohne_codebloecke(text or "")
    im_block = False
    frage: list[str] = []
    optionen: list[dict] = []
    empfehlung: dict | None = None

    for zeile in text.splitlines():
        blank = zeile.strip()
        if ENTSCHEIDUNG.match(blank):
            im_block = True
            continue
        if im_block and UEBERSCHRIFT.match(blank):
            break
        if not im_block:
            continue

        treffer = OPTION.match(blank)
        if treffer:
            optionen.append({"buchstabe": treffer.group(1), "text": treffer.group(2).strip()})
            continue

        treffer = EMPFEHLUNG.match(blank)
        if treffer:
            empfehlung = {"buchstabe": treffer.group(1).upper(), "grund": treffer.group(2).strip()}
            continue

        if blank and not optionen:
            frage.append(blank)

    if not optionen:
        return None
    return {
        "frage": " ".join(frage).strip(),
        "optionen": optionen,
        "empfehlung": empfehlung,
    }


def _hat_schon_entschieden(kommentare: list[dict], menschen: set[str], buchstaben: set[str]) -> bool:
    """
    Hat ein Mensch die Frage schon beantwortet?

    Geprueft wird auf einen Kommentar, der aus dem Buchstaben besteht oder
    mit ihm beginnt. Eine laengere Antwort, die zufaellig mit "A" anfaengt,
    ist selten; eine Entscheidung, die faelschlich noch offen aussieht, ist
    dagegen nur laestig — die sichere Richtung ist also: lieber zu lange
    anzeigen als zu frueh verschwinden lassen.
    """
    for k in kommentare:
        autor = (k.get("author") or {}).get("login", "")
        if autor not in menschen:
            continue
        koerper = (k.get("body") or "").strip()
        erstes = koerper.split()[0].strip(".,:!").upper() if koerper else ""
        if erstes in buchstaben:
            return True
    return False


def offene_entscheidungen(aufruf: Aufruf = _gh, menschen: set[str] | None = None) -> list[dict]:
    """Alle offenen Issues mit einem Entscheidungs-Block, den noch niemand beantwortet hat."""
    leute = menschen if menschen is not None else _menschen()
    roh = json.loads(aufruf([
        "issue", "list", "--state", "open", "--limit", "100",
        "--json", "number,title,body,comments",
    ]) or "[]")

    offen = []
    for i in roh:
        gefunden = entscheidung_aus_text(i.get("body", ""))
        if gefunden is None:
            continue
        buchstaben = {o["buchstabe"] for o in gefunden["optionen"]}
        if _hat_schon_entschieden(i.get("comments", []) or [], leute, buchstaben):
            continue
        offen.append({"nummer": i["number"], "titel": i["title"], **gefunden})
    return offen


def entscheiden(nummer: int, buchstabe: str, aufruf: Aufruf = _gh) -> None:
    """
    Schreibt die Wahl als Kommentar — und sonst nichts.

    Kein Label, keine Freigabe. Entscheiden und freigeben sind zwei Dinge;
    waeren sie ein Handgriff, waere eines von beiden irgendwann versehentlich.
    """
    wahl = str(buchstabe).strip().upper()
    if not re.fullmatch(r"[A-Z]", wahl):
        raise ValueError(f"Keine gültige Option: {buchstabe!r}")
    aufruf(["issue", "comment", str(nummer), "--body", wahl])


def offene_prs(aufruf: Aufruf = _gh) -> list[dict]:
    """Offene PRs mit dem Stand ihrer Checks."""
    roh = json.loads(aufruf([
        "pr", "list", "--state", "open", "--limit", "50",
        "--json", "number,title,body,reviews,statusCheckRollup,files",
    ]) or "[]")

    offen = []
    for p in roh:
        checks = p.get("statusCheckRollup") or []
        rot = sorted({c.get("name") for c in checks if c.get("conclusion") == "FAILURE"})
        # conclusion None heisst "noch nicht entschieden", nicht "kein Fehler".
        # Genau hier luegen solche Anzeigen sonst (#95).
        laeuft = sorted({
            c.get("name") for c in checks
            if c.get("conclusion") in (None, "") and c.get("name")
        })
        freigegeben = any(r.get("state") == "APPROVED" for r in p.get("reviews", []))
        bezug = re.search(r"(?im)^\s*refs\s+#(\d+)", p.get("body") or "")
        offen.append({
            "nummer": p["number"],
            "titel": p["title"],
            "issue": int(bezug.group(1)) if bezug else None,
            "rote_checks": rot,
            "laufende_checks": laeuft,
            "freigegeben": freigegeben,
            "dateien": [f["path"] for f in (p.get("files") or [])][:10],
        })
    return offen


def laufende_laeufe(aufruf: Aufruf = _gh) -> list[dict]:
    """
    Was GitHub gerade rechnet. Fuer die Zeile oben in der Konsole.

    Ohne sie sieht eine leere Liste aus wie "nichts zu tun" — auch dann,
    wenn gerade fuenf Gates arbeiten.
    """
    roh = json.loads(aufruf([
        "run", "list", "--status", "in_progress", "--limit", "20",
        "--json", "displayTitle,workflowName,startedAt,headBranch",
    ]) or "[]")
    return [{
        "titel": r.get("displayTitle", ""),
        "workflow": r.get("workflowName", ""),
        "zweig": r.get("headBranch", ""),
        "seit": r.get("startedAt", ""),
    } for r in roh]


# --- Fortschritt (#73) ----------------------------------------------------

def _stand(labels: set[str], offene_pr_issues: set[int], nummer: int, zu: bool) -> str:
    """
    Ein Issue hat genau einen Stand.

    Die Reihenfolge ist die Aussage: Ein Issue mit offenem PR ist "in Arbeit",
    auch wenn es freigegeben ist — sonst staende es fuer immer unter
    "freigegeben, nichts passiert".
    """
    if "art:pruefung" in labels:
        return "geschlossen" if zu else "pruefung"
    if zu:
        return "geschlossen"
    if nummer in offene_pr_issues:
        return "in_arbeit"
    if "status:freigegeben" in labels:
        return "freigegeben"
    return "vorgeschlagen"


def fortschritt(aufruf: Aufruf = _gh) -> dict:
    """
    Was aus jeder Anforderung geworden ist, je Meilenstein.

    Keine eigene Buchfuehrung: Die Wahrheit steht in den Issues, hier wird
    nur gezaehlt.
    """
    issues = json.loads(aufruf([
        "issue", "list", "--state", "all", "--limit", "200",
        "--json", "number,title,labels,milestone,state",
    ]) or "[]")
    prs = json.loads(aufruf([
        "pr", "list", "--state", "open", "--limit", "100", "--json", "body",
    ]) or "[]")

    mit_pr = set()
    for p in prs:
        for treffer in re.finditer(r"(?im)^\s*(?:refs|closes|fixes)\s+#(\d+)", p.get("body") or ""):
            mit_pr.add(int(treffer.group(1)))

    nach_meilenstein: dict[str, list[dict]] = {}
    for i in issues:
        labels = {l["name"] for l in i.get("labels", [])}
        if "lagebericht" in labels:
            continue  # Automatisch erzeugte Uebersichten sind keine Arbeit.
        meilenstein = (i.get("milestone") or {}).get("title") or "ohne Meilenstein"
        nach_meilenstein.setdefault(meilenstein, []).append({
            "nummer": i["number"],
            "titel": i["title"],
            "stand": _stand(labels, mit_pr, i["number"], i.get("state") == "CLOSED"),
        })

    return {
        "meilensteine": [
            {
                "titel": name,
                "anforderungen": sorted(eintraege, key=lambda e: -e["nummer"]),
                "zaehlung": {
                    stand: sum(1 for e in eintraege if e["stand"] == stand)
                    for stand in ("vorgeschlagen", "freigegeben", "in_arbeit", "geschlossen", "pruefung")
                },
            }
            for name, eintraege in sorted(nach_meilenstein.items())
        ]
    }


def issue_freigeben(nummer: int, aufruf: Aufruf = _gh) -> None:
    """Gate G2. Nur ein Mensch darf das — deshalb ohne Bot-Token."""
    aufruf(["issue", "edit", str(nummer), "--add-label", "status:freigegeben"])


def pr_freigeben(nummer: int, aufruf: Aufruf = _gh) -> None:
    aufruf(["pr", "review", str(nummer), "--approve"])


def kommentieren(art: str, nummer: int, text: str, aufruf: Aufruf = _gh) -> None:
    if art not in ("issue", "pr"):
        raise ValueError(f"Weder Issue noch PR: {art!r}")
    aufruf([art, "comment", str(nummer), "--body", text])
