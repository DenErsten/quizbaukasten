// Die Entwuerfe aus einem Gespraech (#102).
//
// Wie die anderen Module unter werkzeuge/: HTML als Zeichenkette, kein DOM,
// damit die Tests ohne Browser laufen.

import { zeitFormatieren } from "./anzeige.js";

function maskiert(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Ein Entwurf.
 *
 * Fehlt das Abnahmekriterium, steht das ausdruecklich da — mit der Frage,
 * die man nachreichen muss. Ein leeres Feld saehe aus wie ein vergessenes;
 * hier heisst es "im Gespraech wurde nichts dazu gesagt", und das ist ein
 * Ergebnis, kein Versaeumnis (docs/leitfaden.md).
 */
export function entwurfHtml(entwurf, nr, url) {
  const kriterium = entwurf.fertig_wenn
    ? `<p class="kriterium"><span class="feld">fertig, wenn</span> ${maskiert(entwurf.fertig_wenn)}</p>`
    : `<p class="kriterium offen"><span class="feld">fertig, wenn</span> im Gespräch nicht genannt` +
      (entwurf.offene_frage ? ` — nachfragen: ${maskiert(entwurf.offene_frage)}` : "") +
      `</p>`;

  const knopf = url
    ? `<a class="angelegt" href="${maskiert(url)}" target="_blank" rel="noopener">Als Issue angelegt</a>`
    : `<button type="button" data-entwurf="${nr}">Als Issue anlegen</button>`;

  return (
    `<li class="entwurf${url ? " fertig" : ""}">` +
    `<h3>${maskiert(entwurf.titel)}</h3>` +
    `<p class="marke">${zeitFormatieren(entwurf.zeit ?? 0)} · groesse:${maskiert(entwurf.groesse ?? "M")}</p>` +
    (entwurf.kontext ? `<p class="kontext">${maskiert(entwurf.kontext)}</p>` : "") +
    kriterium +
    (entwurf.zitat ? `<blockquote>${maskiert(entwurf.zitat)}</blockquote>` : "") +
    knopf +
    `</li>`
  );
}

/**
 * Der ganze Stand.
 *
 * `nochNichts` unterscheidet "wurde noch nicht abgeleitet" von "wurde
 * abgeleitet und es kam nichts heraus". Beides saehe sonst gleich aus —
 * dasselbe Muster wie die leere Transkript-Spalte in #99.
 */
export function anforderungenHtml(stand) {
  const kopf = `<p class="hinweis">Beim Ableiten geht der <strong>Text</strong> des Gesprächs an Claude. Der Ton bleibt auf diesem Rechner.</p>`;

  if (stand?.fehler) {
    return (
      `<div class="anforderungen">${kopf}` +
      `<p class="fehler">${maskiert(stand.fehler)}</p>` +
      `<button id="ableiten" type="button">Nochmal ableiten</button></div>`
    );
  }
  if (stand?.laeuft) {
    return (
      `<div class="anforderungen">${kopf}` +
      `<p class="laeuft">Das Gespräch wird gelesen …</p></div>`
    );
  }

  const entwuerfe = stand?.entwuerfe ?? [];
  const angelegt = stand?.angelegt ?? {};

  if (entwuerfe.length === 0) {
    const text = stand?.abgeleitet
      ? "Aus diesem Gespräch ließ sich keine Anforderung ableiten."
      : "Noch nichts abgeleitet.";
    return (
      `<div class="anforderungen">${kopf}<p class="leer">${text}</p>` +
      `<button id="ableiten" type="button">Anforderungen ableiten</button></div>`
    );
  }

  const offen = entwuerfe.length - Object.keys(angelegt).length;
  return (
    `<div class="anforderungen">${kopf}` +
    `<p class="stand">${entwuerfe.length} ${entwuerfe.length === 1 ? "Entwurf" : "Entwürfe"}, ` +
    `${offen} noch nicht übernommen</p>` +
    `<ol class="entwuerfe">` +
    entwuerfe.map((e, nr) => entwurfHtml(e, nr, angelegt[String(nr)])).join("") +
    `</ol>` +
    `<button id="ableiten" type="button">Neu ableiten</button></div>`
  );
}
