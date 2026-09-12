// Das gefuehrte Erstgespraech in der Aufnahme-Ansicht (#114).
//
// Die Fragen stehen NICHT hier. Sie kommen ueber /interview aus
// docs/leitfaden.md — dieselbe Quelle wie der stille Leitfaden daneben.
//
// Wie die anderen Module unter werkzeuge/: HTML als Zeichenkette, kein DOM.

function maskiert(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Was schon beantwortet ist — klein, in der Reihenfolge des Gespraechs.
 *
 * Offene Punkte werden als offen gezeigt und nicht weggelassen. Eine Frage,
 * auf die nichts Tragfaehiges kam, ist ein Ergebnis: die Liste fuer das
 * naechste Gespraech (docs/leitfaden.md).
 */
function beantwortetHtml(beantwortet) {
  if (!beantwortet?.length) return "";
  const zeilen = beantwortet
    .map(
      (e) =>
        `<li class="erledigt${e.offen ? " offen" : ""}">` +
        `<span class="titel">${maskiert(e.titel)}</span>` +
        (e.offen ? `<span class="marke">offen</span>` : "") +
        `</li>`,
    )
    .join("");
  return `<ol class="bisher">${zeilen}</ol>`;
}

/**
 * Der ganze Stand des Interviews.
 *
 * `laeuft: false` heisst: Es wird gerade keins gefuehrt. Dann gibt dieses
 * Modul nichts zurueck und die Seite zeigt den stillen Leitfaden — nicht
 * eine leere Flaeche, die aussaehe wie ein kaputtes Interview (#99).
 */
export function interviewHtml(stand) {
  if (!stand || stand.laeuft === false) {
    if (stand?.fehler) {
      return (
        `<div class="interview">` +
        `<p class="titel">Gespräch</p>` +
        `<p class="fehler">Kein Gespräch möglich: ${maskiert(stand.fehler)}</p>` +
        `</div>`
      );
    }
    return "";
  }

  if (stand.fertig) {
    const offene = stand.offene ?? [];
    return (
      `<div class="interview interview-fertig">` +
      `<p class="titel">Gespräch</p>` +
      `<p class="frage">Das war alles, was ich fragen wollte.</p>` +
      `<p class="rat">` +
      (offene.length
        ? `Offen geblieben: ${maskiert(offene.join(", "))}. Das ist die Liste fürs nächste Mal.`
        : `Alle fünf Fragen haben eine Antwort.`) +
      `</p>` +
      beantwortetHtml(stand.beantwortet) +
      `</div>`
    );
  }

  const rueckfrage = stand.nachgefragt && stand.rueckfrage
    ? `<p class="rueckfrage">${maskiert(stand.rueckfrage)}</p>`
    : "";

  return (
    `<div class="interview${stand.nachgefragt ? " interview-nachgefragt" : ""}">` +
    `<p class="titel">Frage ${maskiert(String(stand.nummer))} von ${maskiert(String(stand.von))}` +
    (stand.titel ? ` · ${maskiert(stand.titel)}` : "") +
    `</p>` +
    `<p class="frage">${maskiert(stand.frage)}</p>` +
    rueckfrage +
    beantwortetHtml(stand.beantwortet) +
    `</div>`
  );
}
