// Der Gespraechsleitfaden in der Aufnahme-Ansicht (#101).
//
// Die Fragen stehen NICHT in dieser Datei. Sie kommen ueber /leitfaden aus
// docs/leitfaden.md. Wer sie hier einsetzt, hat zwei Leitfaeden, und der
// vorgelesene ist irgendwann der falsche.
//
// Wie die anderen Module unter werkzeuge/: HTML als Zeichenkette, kein DOM,
// damit die Tests ohne Browser laufen.

function maskiert(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Ein Punkt als Listeneintrag.
 *
 * `Worauf achten` ist eingeklappt: Im Gespraech zaehlt die Frage, der Rest
 * waere Text, den man waehrend des Zuhoerens nicht liest.
 */
function punktHtml(punkt, nr, erledigt) {
  const haken = erledigt ? " checked" : "";
  const achtung = punkt.achtung
    ? `<details class="achtung"><summary>Worauf achten</summary><p>${maskiert(punkt.achtung)}</p></details>`
    : "";
  return (
    `<li class="punkt${erledigt ? " erledigt" : ""}">` +
    `<label><input type="checkbox" data-punkt="${nr}"${haken} /> ` +
    `<span class="frage">${maskiert(punkt.frage)}</span></label>` +
    (punkt.fuellt ? `<p class="fuellt">${maskiert(punkt.fuellt)}</p>` : "") +
    achtung +
    `</li>`
  );
}

/**
 * Der ganze Leitfaden.
 *
 * @param antwort  Was /leitfaden geliefert hat: eine Liste von Punkten oder
 *                 ein Objekt mit `fehler`.
 * @param erledigt Nummern der abgehakten Punkte (Set oder Array).
 */
export function leitfadenHtml(antwort, erledigt = []) {
  const abgehakt = new Set(Array.from(erledigt, Number));

  if (antwort && antwort.fehler) {
    // Eine leere Spalte hiesse "keine Fragen". Das waere gelogen.
    return (
      `<div class="leitfaden">` +
      `<p class="titel">Leitfaden</p>` +
      `<p class="fehler">Der Leitfaden konnte nicht gelesen werden: ${maskiert(antwort.fehler)}</p>` +
      `</div>`
    );
  }

  const punkte = Array.isArray(antwort) ? antwort : [];
  if (punkte.length === 0) {
    return (
      `<div class="leitfaden">` +
      `<p class="titel">Leitfaden</p>` +
      `<p class="leer">Kein Punkt in docs/leitfaden.md.</p>` +
      `</div>`
    );
  }

  const eintraege = punkte.map((p, nr) => punktHtml(p, nr, abgehakt.has(nr))).join("");
  const offen = punkte.length - punkte.filter((_, nr) => abgehakt.has(nr)).length;
  // Der Satz am Ende ist die eigentliche Nachricht: Was am Schluss offen ist,
  // ist die Liste fuer das naechste Gespraech (docs/leitfaden.md).
  const stand =
    offen === 0
      ? `<p class="stand vollstaendig">Alle fünf Fragen gestellt.</p>`
      : `<p class="stand">Noch offen: ${offen} von ${punkte.length}</p>`;
  return `<div class="leitfaden"><p class="titel">Leitfaden</p><ol>${eintraege}</ol>${stand}</div>`;
}
