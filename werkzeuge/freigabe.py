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
        freigegeben = any(r.get("state") == "APPROVED" for r in p.get("reviews", []))
        bezug = re.search(r"(?im)^\s*refs\s+#(\d+)", p.get("body") or "")
        offen.append({
            "nummer": p["number"],
            "titel": p["title"],
            "issue": int(bezug.group(1)) if bezug else None,
            "rote_checks": rot,
            "freigegeben": freigegeben,
            "dateien": [f["path"] for f in (p.get("files") or [])][:10],
        })
    return offen


def issue_freigeben(nummer: int, aufruf: Aufruf = _gh) -> None:
    """Gate G2. Nur ein Mensch darf das — deshalb ohne Bot-Token."""
    aufruf(["issue", "edit", str(nummer), "--add-label", "status:freigegeben"])


def pr_freigeben(nummer: int, aufruf: Aufruf = _gh) -> None:
    aufruf(["pr", "review", str(nummer), "--approve"])


def kommentieren(art: str, nummer: int, text: str, aufruf: Aufruf = _gh) -> None:
    if art not in ("issue", "pr"):
        raise ValueError(f"Weder Issue noch PR: {art!r}")
    aufruf([art, "comment", str(nummer), "--body", text])
