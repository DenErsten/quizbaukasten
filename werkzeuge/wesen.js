// Das Gegenüber (#106).
//
// Ein einziges kleines Wesen, dessen Zustand der Zustand des Werkzeugs IST.
// Es sitzt neben der Aufnahme, schlaeft, wacht auf, hoert zu, legt bei einem
// Hinweis den Kopf schief, verbeugt sich am Ende.
//
// DIE GRENZE
// ----------
// Das Wesen darf einen Zustand ausdruecken, aber niemals einen verstecken.
// Ein suesses Werkzeug, das Fehler niedlich verpackt, ist gefaehrlicher als
// ein haessliches, das sie nennt: Dieses Projekt hat mehrfach Zeit verloren,
// weil etwas scheiterte und wie Normalbetrieb aussah (#99). Deshalb sackt das
// Wesen bei einem Fehler zusammen UND der Fehlertext steht unveraendert
// daneben — kein "Ups", keine Beschwichtigung (docs/pilotnutzer.md).
//
// Wie die anderen Module unter werkzeuge/: HTML als Zeichenkette, kein DOM.
// Kein Bild, keine Bibliothek, kein Ladevorgang — das Werkzeug laeuft ohne
// Netz, und das ist eine Produkteigenschaft, keine Vorliebe.

export const WESEN = {
  SCHLAEFT: "schlaeft",
  LAEDT: "laedt",
  HOERT: "hoert",
  HINWEIS: "hinweis",
  BEENDET: "beendet",
  GESCHEITERT: "gescheitert",
};

// Erste Person, nicht Systemmeldung. "Ich höre zu" statt "Aufnahme läuft".
const SAETZE = {
  schlaeft: "Ich warte hier.",
  laedt: "Ich wache gerade auf.",
  hoert: "Ich höre zu.",
  hinweis: "Darf ich kurz nachfragen?",
  beendet: "Danke für das Gespräch.",
  gescheitert: "Ich konnte nicht anfangen.",
};

const AUGEN = {
  // Schlafende und zufriedene Augen sind beide Boegen — aber in die
  // entgegengesetzte Richtung. Das reicht, um sie zu unterscheiden.
  zu: '<path class="auge-zu" d="M22 32q3 3.4 6 0" /><path class="auge-zu" d="M36 32q3 3.4 6 0" />',
  froh: '<path class="auge-zu" d="M22 34q3-3.4 6 0" /><path class="auge-zu" d="M36 34q3-3.4 6 0" />',
  offen: '<circle class="auge" cx="25" cy="32" r="2.8" /><circle class="auge" cx="39" cy="32" r="2.8" />',
  // Ein grosses und ein kleines Auge: der Blick, mit dem man nachfragt.
  fragend: '<circle class="auge" cx="25" cy="32" r="3.4" /><circle class="auge" cx="39" cy="32" r="2.4" />',
  // Flache Striche statt Boegen — das ist kein Zwinkern, das ist Luft raus.
  matt: '<path class="auge-zu" d="M22 33h6" /><path class="auge-zu" d="M36 33h6" />',
};

const MUENDER = {
  keiner: "",
  klein: '<circle class="mund" cx="32" cy="40" r="1.5" />',
  offen: '<ellipse class="mund" cx="32" cy="40" rx="2.2" ry="2.8" />',
  froh: '<path class="mund-strich" d="M28 39.5q4 3.6 8 0" />',
  flach: '<path class="mund-strich" d="M29 41h6" />',
};

/**
 * Die sechs Gesichter.
 *
 * `neigung` und `versatz` sind die ganze Koerpersprache: den Kopf schief
 * legen, sich verbeugen, in sich zusammensacken. Sie stehen hier und nicht
 * im Stylesheet, damit sie auch dann wirken, wenn jemand Bewegung
 * abgeschaltet hat — wer `prefers-reduced-motion` setzt, soll den Zustand
 * trotzdem sehen.
 */
const GESICHTER = {
  schlaeft: { augen: AUGEN.zu, mund: MUENDER.keiner, neigung: 0, versatz: 1, spross: 0 },
  laedt: { augen: AUGEN.zu, mund: MUENDER.klein, neigung: 0, versatz: 0, spross: 0 },
  hoert: { augen: AUGEN.offen, mund: MUENDER.klein, neigung: 0, versatz: 0, spross: -6 },
  hinweis: { augen: AUGEN.fragend, mund: MUENDER.offen, neigung: -9, versatz: 0, spross: -14 },
  beendet: { augen: AUGEN.froh, mund: MUENDER.froh, neigung: 5, versatz: 3, spross: -3 },
  gescheitert: { augen: AUGEN.matt, mund: MUENDER.flach, neigung: 3, versatz: 2, spross: 22 },
};

function maskiert(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Der Satz, den das Wesen zu einem Zustand sagt. */
export function wesenSatz(art) {
  return SAETZE[art] ?? "";
}

function beiwerk(art) {
  if (art === WESEN.SCHLAEFT) {
    // Drei Punkte, die aufsteigen — das "zzz" ohne Buchstaben.
    return (
      '<g class="schlummer">' +
      '<circle cx="50" cy="20" r="1.4" /><circle cx="55" cy="14" r="1.9" />' +
      '<circle cx="61" cy="7" r="2.4" /></g>'
    );
  }
  if (art === WESEN.HINWEIS) {
    return '<text class="fragezeichen" x="52" y="18" text-anchor="middle">?</text>';
  }
  if (art === WESEN.LAEDT) {
    // Ein offener Ring, der sich dreht. Steht die Bewegung still, bleibt ein
    // sichtbarer Bogen — der Zustand haengt nicht an der Animation.
    return '<path class="ring" d="M32 58a12 12 0 0 1-12-12" />';
  }
  return "";
}

/**
 * Das Wesen als SVG samt Satz.
 *
 * @param art   einer der Werte aus WESEN
 * @param zusatz optionaler Text unter dem Satz, woertlich uebernommen
 */
export function wesenHtml(art, zusatz = "") {
  const gesicht = GESICHTER[art];
  if (!gesicht) {
    return "";
  }
  const koerper =
    `<g class="kopf" transform="translate(0 ${gesicht.versatz}) rotate(${gesicht.neigung} 32 36)">` +
    `<path class="spross" transform="rotate(${gesicht.spross} 32 14)" d="M32 13c0-5 3-9 8-10 1 6-3 10-8 10Z" />` +
    `<path class="koerper" d="M32 12c-12 0-20 9-20 21 0 11 9 19 20 19s20-8 20-19c0-12-8-21-20-21Z" />` +
    `<ellipse class="wange" cx="19.5" cy="38" rx="4" ry="2.5" />` +
    `<ellipse class="wange" cx="44.5" cy="38" rx="4" ry="2.5" />` +
    gesicht.augen +
    gesicht.mund +
    `</g>`;

  return (
    `<figure class="wesen wesen-${art}">` +
    `<svg viewBox="0 0 64 64" role="img" aria-label="${maskiert(wesenSatz(art))}">` +
    beiwerk(art) +
    koerper +
    `</svg>` +
    `<figcaption>${maskiert(wesenSatz(art))}` +
    (zusatz ? `<span class="zusatz">${maskiert(zusatz)}</span>` : "") +
    `</figcaption></figure>`
  );
}
