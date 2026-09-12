// Darstellung der Freigabe-Konsole (#90).
//
// Zwei Listen, weil zwei verschiedene Entscheidungen dahinterstehen: Ein
// Issue freizugeben heisst "das soll gebaut werden". Einen PR freizugeben
// heisst "so, wie es gebaut wurde, ist es richtig".
//
// Die Knoepfe machen das Freigeben leichter — und damit auch das Freigeben
// ohne Hinsehen. Deshalb steht neben jedem Knopf das, was man wissen muss,
// um ihn nicht zu druecken: fehlendes Abnahmekriterium, rote Checks.

export function maskiert(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** CLAUDE.md verlangt ein Abnahmekriterium. PR #68 ist daran gescheitert. */
function warnungOhneKriterium(issue) {
  return issue.kriterium
    ? ""
    : `<p class="warnung">Kein „Fertig, wenn …“ — nach CLAUDE.md unvollständig.` +
      ` <code>abnahme</code> wird jeden PR dazu blockieren.</p>`;
}

export function issueZuHtml(issue) {
  const marken = [issue.groesse, issue.art, issue.meilenstein]
    .filter(Boolean)
    .map((m) => `<span class="marke">${maskiert(m)}</span>`)
    .join("");
  return (
    `<article class="eintrag${issue.kriterium ? "" : " unvollstaendig"}" data-nummer="${issue.nummer}">` +
    `<p class="kopf"><span class="nummer">#${issue.nummer}</span> ${maskiert(issue.titel)}</p>` +
    `<p class="marken">${marken}</p>` +
    warnungOhneKriterium(issue) +
    `<div class="knoepfe">` +
    `<button type="button" data-tat="freigeben" data-art="issue" data-nummer="${issue.nummer}">Freigeben</button>` +
    `<button type="button" data-tat="kommentieren" data-art="issue" data-nummer="${issue.nummer}">Rückfrage</button>` +
    `</div></article>`
  );
}

/** Rote Checks beim Namen nennen. Ein Knopf ohne diese Angabe lädt zum Wegsehen ein (#5). */
function checkStand(pr) {
  if (pr.rote_checks?.length) {
    return `<p class="warnung">Rot: ${pr.rote_checks.map(maskiert).join(", ")}</p>`;
  }
  return `<p class="gut">Alle Checks grün</p>`;
}

export function prZuHtml(pr) {
  const bezug = pr.issue ? `<span class="marke">Refs #${pr.issue}</span>` :
    `<span class="marke fehlt">kein Issue verlinkt</span>`;
  const dateien = (pr.dateien ?? []).slice(0, 5).map(maskiert).join(", ");
  return (
    `<article class="eintrag${pr.rote_checks?.length ? " unvollstaendig" : ""}" data-nummer="${pr.nummer}">` +
    `<p class="kopf"><span class="nummer">#${pr.nummer}</span> ${maskiert(pr.titel)}</p>` +
    `<p class="marken">${bezug}${pr.freigegeben ? `<span class="marke">freigegeben</span>` : ""}</p>` +
    checkStand(pr) +
    (dateien ? `<p class="dateien">${dateien}</p>` : "") +
    `<div class="knoepfe">` +
    `<button type="button" data-tat="freigeben" data-art="pr" data-nummer="${pr.nummer}"${pr.freigegeben ? " disabled" : ""}>Freigeben</button>` +
    `<button type="button" data-tat="kommentieren" data-art="pr" data-nummer="${pr.nummer}">Rückfrage</button>` +
    `</div></article>`
  );
}

export function konsoleZuHtml(daten) {
  const issues = daten.issues ?? [];
  const prs = daten.prs ?? [];
  return (
    `<section><h2>Warten auf Freigabe (${issues.length})</h2>` +
    (issues.length ? issues.map(issueZuHtml).join("") : `<p class="leer">Nichts offen.</p>`) +
    `</section>` +
    `<section><h2>Pull Requests (${prs.length})</h2>` +
    (prs.length ? prs.map(prZuHtml).join("") : `<p class="leer">Nichts offen.</p>`) +
    `</section>`
  );
}
