// Fortschritt je Meilenstein (#73).
//
// Was aus jeder Anforderung geworden ist — offen, in Arbeit, gemergt.
// Keine eigene Buchfuehrung: Die Wahrheit steht in den Issues.

export const STAENDE = [
  { schluessel: "vorgeschlagen", name: "wartet auf Freigabe" },
  { schluessel: "freigegeben", name: "freigegeben" },
  { schluessel: "in_arbeit", name: "in Arbeit" },
  { schluessel: "geschlossen", name: "erledigt" },
  { schluessel: "pruefung", name: "Betriebsprüfung" },
];

export function maskiert(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Ein Balken aus den Zählungen — Anteile, keine absoluten Breiten.
 *
 * Meilensteine haben sehr verschiedene Größen; ein Balken, der die Anzahl
 * abbildet, sagt über den Fortschritt nichts.
 */
export function balken(zaehlung) {
  const gesamt = STAENDE.reduce((s, { schluessel }) => s + (zaehlung[schluessel] ?? 0), 0);
  if (!gesamt) return `<div class="balken leer"></div>`;
  const teile = STAENDE.filter(({ schluessel }) => zaehlung[schluessel])
    .map(({ schluessel, name }) => {
      const anteil = ((zaehlung[schluessel] / gesamt) * 100).toFixed(1);
      return `<span class="teil teil-${schluessel}" style="width:${anteil}%" title="${maskiert(name)}: ${zaehlung[schluessel]}"></span>`;
    })
    .join("");
  return `<div class="balken">${teile}</div>`;
}

function anforderungZuHtml(a) {
  const name = STAENDE.find((s) => s.schluessel === a.stand)?.name ?? a.stand;
  return (
    `<li class="anforderung stand-${maskiert(a.stand)}">` +
    `<span class="nummer">#${a.nummer}</span>` +
    `<span class="titel">${maskiert(a.titel)}</span>` +
    `<span class="stand">${maskiert(name)}</span>` +
    `</li>`
  );
}

export function meilensteinZuHtml(m) {
  const z = m.zaehlung ?? {};
  const offen = (z.vorgeschlagen ?? 0) + (z.freigegeben ?? 0) + (z.in_arbeit ?? 0);
  return (
    `<section class="meilenstein">` +
    `<h2>${maskiert(m.titel)}</h2>` +
    `<p class="summe">${offen} offen · ${z.geschlossen ?? 0} erledigt</p>` +
    balken(z) +
    `<ul class="anforderungen">${(m.anforderungen ?? []).map(anforderungZuHtml).join("")}</ul>` +
    `</section>`
  );
}

export function fortschrittZuHtml(daten) {
  const m = daten?.meilensteine ?? [];
  if (!m.length) {
    return `<p class="leer">Keine Meilensteine. Sie entstehen aus docs/plan.md.</p>`;
  }
  return m.map(meilensteinZuHtml).join("");
}
