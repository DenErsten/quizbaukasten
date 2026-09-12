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

/**
 * Rote Checks beim Namen nennen. Ein Knopf ohne diese Angabe lädt zum
 * Wegsehen ein (#5).
 *
 * Laufende zaehlen weder als gruen noch als rot: "conclusion: null" heisst
 * "noch nicht entschieden". Wer das als "kein Fehler" liest, gibt frei,
 * bevor geprueft wurde (#95).
 */
function checkStand(pr) {
  const teile = [];
  if (pr.rote_checks?.length) {
    teile.push(`<p class="warnung">Rot: ${pr.rote_checks.map(maskiert).join(", ")}</p>`);
  }
  if (pr.laufende_checks?.length) {
    teile.push(`<p class="laeuft">Läuft noch: ${pr.laufende_checks.map(maskiert).join(", ")}</p>`);
  }
  if (!teile.length) {
    teile.push(`<p class="gut">Alle Checks grün</p>`);
  }
  return teile.join("");
}

/** Die Zeile oben: Eine leere Liste sieht sonst aus wie "nichts zu tun". */
export function laufZeile(laeufe) {
  if (!laeufe?.length) {
    return `<p class="stand">Es läuft gerade nichts.</p>`;
  }
  const namen = laeufe
    .map((l) => `${maskiert(l.workflow)}${l.zweig ? ` (${maskiert(l.zweig)})` : ""}`)
    .join(", ");
  return `<p class="stand laeuft">${laeufe.length} Lauf${laeufe.length === 1 ? "" : "e"} in Arbeit: ${namen}</p>`;
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
  // Kommt aus /entscheidungen, nicht aus /freigaben — eine Fehlermeldung
  // von dort ist kein Array und darf nicht als "nichts offen" durchgehen.
  const entscheidungen = Array.isArray(daten.entscheidungen) ? daten.entscheidungen : [];
  // Entscheidungen stehen oben: Sie blockieren meist etwas weiter unten.
  const oben = entscheidungen.length
    ? `<section class="entscheidungen"><h2>Deine Entscheidung (${entscheidungen.length})</h2>` +
      entscheidungen.map(entscheidungZuHtml).join("") +
      `</section>`
    : "";
  return (
    oben +
    laufZeile(daten.laeufe) +
    `<section><h2>Warten auf Freigabe (${issues.length})</h2>` +
    (issues.length ? issues.map(issueZuHtml).join("") : `<p class="leer">Nichts offen.</p>`) +
    `</section>` +
    `<section><h2>Pull Requests (${prs.length})</h2>` +
    (prs.length ? prs.map(prZuHtml).join("") : `<p class="leer">Nichts offen.</p>`) +
    `</section>`
  );
}

/**
 * Eine offene Entscheidung (#108).
 *
 * Die Empfehlung wird ausgeschrieben, nicht nur markiert: Ein Haken ohne
 * Grund ist eine Anweisung, kein Rat. Wer sie ablehnen soll, muss wissen,
 * wogegen er sich entscheidet.
 */
export function entscheidungZuHtml(e) {
  const empfohlen = e.empfehlung?.buchstabe;
  const optionen = (e.optionen ?? [])
    .map((o) => {
      const ist = o.buchstabe === empfohlen;
      return (
        `<button type="button" class="option${ist ? " empfohlen" : ""}" ` +
        `data-entscheidung="${maskiert(String(e.nummer))}" data-wahl="${maskiert(o.buchstabe)}">` +
        `<span class="buchstabe">${maskiert(o.buchstabe)}</span>` +
        `<span class="was">${maskiert(o.text)}</span>` +
        (ist ? `<span class="marke">empfohlen</span>` : "") +
        `</button>`
      );
    })
    .join("");

  const grund = e.empfehlung?.grund
    ? `<p class="grund"><strong>${maskiert(empfohlen)}</strong>, weil ${maskiert(e.empfehlung.grund)}</p>`
    : `<p class="grund ohne">Keine Empfehlung — beide Wege sind vertretbar.</p>`;

  return (
    `<article class="entscheidung">` +
    `<h3>#${maskiert(String(e.nummer))} ${maskiert(e.titel)}</h3>` +
    (e.frage ? `<p class="frage">${maskiert(e.frage)}</p>` : "") +
    `<div class="optionen">${optionen}</div>` +
    grund +
    `</article>`
  );
}
