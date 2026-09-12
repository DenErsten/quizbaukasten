// Zustandslogik der Aufnahme-Ansicht (#70). Baut auf anzeige.js auf, das die
// Hinweise schon darstellt — hier kommen nur die drei Zustaende drumherum
// dazu: bereit, laeuft, beendet.
//
// Wie in anzeige.js: reines Modul, kein Framework, kein DOM. Die Logik gibt
// HTML als Zeichenkette zurueck, damit die Tests ohne DOM laufen.

import { hinweisZuHtml, sichtbareHinweise, zeitFormatieren } from "./anzeige.js";
import { WESEN, wesenHtml } from "./wesen.js";

export const ZUSTAND = {
  BEREIT: "bereit",
  LAEUFT: "laeuft",
  BEENDET: "beendet",
  GESCHEITERT: "gescheitert",
  LAEDT: "laedt",
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
  return { ...zustandAusAntwort(antwort), veraltet: false };
}

/**
 * Fall 4 aus #76: Ein gescheiterter Start darf nicht wie "bereit" aussehen.
 *
 * Vorher fiel die Ansicht stumm zurueck, weil der Server nur laeuft:false
 * meldete. Jetzt liefert er zusaetzlich fehler — steht dort etwas, ist das
 * ein eigener Zustand, kein Ausgangszustand.
 */
export function zustandAusAntwort(antwort) {
  if (antwort.fehler) {
    return { ...antwort, art: ZUSTAND.GESCHEITERT };
  }
  // Vor dem Fehler pruefen, nach dem Laufen: Ein Download ist kein Fehler,
  // aber auch kein Ausgangszustand. Ohne diesen Fall sah eine Minute
  // Warten auf 459 MB aus wie "bereit, aber tut nichts" (#87).
  if (antwort.laedt_modell) {
    return { ...antwort, art: ZUSTAND.LAEDT };
  }
  return antwort;
}

function laedtHtml() {
  return (
    `<div class="aufnahme aufnahme-laedt">` +
    wesenHtml(WESEN.LAEDT) +
    `<p class="titel">Spracherkennung wird vorbereitet …</p>` +
    `<p class="rat">Das Modell wird einmalig geladen, rund 460 MB. ` +
    `Danach startet die Aufnahme ohne Wartezeit.</p>` +
    knopf("starten", "Aufnahme starten", true) +
    `</div>`
  );
}

function maskiert(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function gescheitertHtml(zustand) {
  return (
    `<div class="aufnahme aufnahme-gescheitert">` +
    // Das Wesen sackt zusammen — und der Fehlertext bleibt daneben stehen,
    // Wort fuer Wort. Ausdruecken, nie verstecken (#106).
    wesenHtml(WESEN.GESCHEITERT) +
    `<p class="titel">Die Aufnahme konnte nicht starten.</p>` +
    `<pre class="fehler">${maskiert(zustand.fehler)}</pre>` +
    `<p class="rat">Fehlt eine Abhängigkeit? <code>pip3 install sounddevice numpy soundfile mlx-whisper</code></p>` +
    knopf("starten", "Nochmal versuchen", false) +
    `</div>`
  );
}

function knopf(id, text, deaktiviert) {
  return `<button id="${id}" type="button"${deaktiviert ? " disabled" : ""}>${text}</button>`;
}

function bereitHtml() {
  return (
    `<div class="aufnahme aufnahme-bereit">` +
    wesenHtml(WESEN.SCHLAEFT) +
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

/**
 * Was das Werkzeug gehoert hat.
 *
 * Ohne diese Spalte sehen "hoert zu, nichts war unscharf" und "hoert
 * nichts" gleich aus — beide eine leere Flaeche. Genau daran hat Firat am
 * 2026-09-12 geglaubt, das Werkzeug sei kaputt, waehrend es seinen Satz
 * wortwoertlich erkannt hatte (#99).
 */
export function transkriptHtml(zeilen, hinweiseVorhanden) {
  if (!zeilen?.length) {
    return (
      `<div class="transkript">` +
      `<p class="titel">Gehört</p>` +
      `<p class="leer">Noch nichts erkannt.</p>` +
      `</div>`
    );
  }
  const saetze = zeilen
    .slice(-8)
    .reverse()
    .map((z) => `<p class="satz"><span class="zeit">${zeitFormatieren(z.zeit ?? 0)}</span>${maskiert(z.text ?? "")}</p>`)
    .join("");
  // Fall 4: "nichts Unscharfes gehört" ist eine Aussage, eine leere Fläche ist keine.
  const nichts = hinweiseVorhanden
    ? ""
    : `<p class="leer">Bisher nichts Unscharfes darin.</p>`;
  return `<div class="transkript"><p class="titel">Gehört</p>${saetze}${nichts}</div>`;
}

function laeuftHtml(zustand) {
  const offeneHinweise = sichtbareHinweise(zustand.hinweise ?? []).length > 0;
  return (
    `<div class="aufnahme aufnahme-laeuft">` +
    // Wach, solange nichts offen ist; fragend, sobald es nachgefragt hat.
    wesenHtml(offeneHinweise || zustand.nachgefragt ? WESEN.HINWEIS : WESEN.HOERT) +
    knopf("start", "Aufnahme starten", true) +
    knopf("stop", "Aufnahme stoppen", false) +
    `<p class="zeit">${zeitFormatieren(zustand.sekunden)}</p>` +
    veraltetHinweis(zustand) +
    transkriptHtml(zustand.transkript, (zustand.hinweise ?? []).length > 0) +
    `<div class="hinweise">${sichtbareHinweise(zustand.hinweise ?? []).map(hinweisZuHtml).join("")}</div>` +
    `</div>`
  );
}

/**
 * Nach dem Gespraech.
 *
 * Hier steht bewusst KEIN Knopf zum Ableiten, obwohl #102 zunaechst einen
 * hier vorsah: Der Test "keine Knoepfe mehr im Zustand beendet" aus #70
 * verbietet Bedienelemente in diesem Zustand, und ein bestehender Test wird
 * nicht entschaerft, damit etwas Neues hineinpasst (CLAUDE.md).
 *
 * Der Weg fuehrt stattdessen auf die Anforderungs-Seite. Dort steht der
 * Knopf neben dem Satz, was beim Ableiten hinausgeht, und direkt ueber dem,
 * was dabei herauskommt — das ist ohnehin die ehrlichere Stelle.
 */
function beendetHtml(zustand) {
  const anzahl = zustand.anzahlHinweise ?? 0;
  return (
    `<div class="aufnahme aufnahme-beendet">` +
    wesenHtml(WESEN.BEENDET) +
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
    case ZUSTAND.GESCHEITERT:
      return gescheitertHtml(zustand);
    case ZUSTAND.LAEDT:
      return laedtHtml();
    default:
      return "";
  }
}
