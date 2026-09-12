// Zustandslogik der Aufnahme-Ansicht (#70). Baut auf anzeige.js auf, das die
// Hinweise schon darstellt — hier kommen nur die drei Zustaende drumherum
// dazu: bereit, laeuft, beendet.
//
// Wie in anzeige.js: reines Modul, kein Framework, kein DOM. Die Logik gibt
// HTML als Zeichenkette zurueck, damit die Tests ohne DOM laufen.

import { hinweisZuHtml, sichtbareHinweise, zeitFormatieren } from "./anzeige.js";

export const ZUSTAND = {
  BEREIT: "bereit",
  LAEUFT: "laeuft",
  BEENDET: "beendet",
};

/**
 * Naechster Anzeige-Zustand aus dem vorherigen und einer neuen Antwort vom
 * Server — oder `null`, wenn die Verbindung verloren ist.
 *
 * Fall 4: Bei Verbindungsverlust bleibt der letzte Stand stehen, statt
 * zu leeren. Er wird als veraltet markiert, damit das nicht wie ein
 * aktueller Stand aussieht.
 */
export function naechsterZustand(vorheriger, antwort) {
  if (antwort === null) {
    return vorheriger === null ? null : { ...vorheriger, veraltet: true };
  }
  return { ...antwort, veraltet: false };
}

function knopf(id, text, deaktiviert) {
  return `<button id="${id}" type="button"${deaktiviert ? " disabled" : ""}>${text}</button>`;
}

function bereitHtml() {
  return (
    `<div class="aufnahme aufnahme-bereit">` +
    knopf("start", "Aufnahme starten", false) +
    knopf("stop", "Aufnahme stoppen", true) +
    `</div>`
  );
}

function veraltetHinweis(zustand) {
  return zustand.veraltet
    ? `<p class="veraltet">Verbindung zum Server verloren — letzter Stand, nicht aktuell</p>`
    : "";
}

function laeuftHtml(zustand) {
  return (
    `<div class="aufnahme aufnahme-laeuft">` +
    knopf("start", "Aufnahme starten", true) +
    knopf("stop", "Aufnahme stoppen", false) +
    `<p class="zeit">${zeitFormatieren(zustand.sekunden)}</p>` +
    veraltetHinweis(zustand) +
    `<div class="hinweise">${sichtbareHinweise(zustand.hinweise ?? []).map(hinweisZuHtml).join("")}</div>` +
    `</div>`
  );
}

function beendetHtml(zustand) {
  const anzahl = zustand.anzahlHinweise ?? 0;
  return (
    `<div class="aufnahme aufnahme-beendet">` +
    veraltetHinweis(zustand) +
    `<p class="anzahl">${anzahl} Hinweis${anzahl === 1 ? "" : "e"} in diesem Gespräch</p>` +
    `<a class="weiter" href="${zustand.anforderungenUrl ?? "#"}">Weiter zu den Anforderungen</a>` +
    `</div>`
  );
}

/** Rendert den gegebenen Zustand als HTML — das, was die Seite aufruft. */
export function zustandZuHtml(zustand) {
  if (!zustand) {
    return "";
  }
  switch (zustand.art) {
    case ZUSTAND.BEREIT:
      return bereitHtml();
    case ZUSTAND.LAEUFT:
      return laeuftHtml(zustand);
    case ZUSTAND.BEENDET:
      return beendetHtml(zustand);
    default:
      return "";
  }
}
