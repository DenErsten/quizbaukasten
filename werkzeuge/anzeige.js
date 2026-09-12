// Reine Anzeige-Logik fuer die Live-Mitschrift (#37, Teil 3 von #34).
//
// Bewusst als schlichtes ES-Modul ohne Framework und ohne Abhaengigkeit:
// Der zweite Bildschirm soll laufen, ohne dass am Quizabend irgendetwas
// gebaut oder installiert werden muss.

export const MAX_SICHTBAR = 5;

/** Neueste zuerst, hoechstens `max` Eintraege — Fall 2 und Fall 3 aus #37. */
export function sichtbareHinweise(hinweise, max = MAX_SICHTBAR) {
  return [...hinweise].sort((a, b) => b.zeit - a.zeit).slice(0, max);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function zeitFormatieren(sekunden) {
  const gesamt = Math.max(0, Math.round(sekunden));
  const minuten = Math.floor(gesamt / 60);
  const sek = gesamt % 60;
  return `${String(minuten).padStart(2, "0")}:${String(sek).padStart(2, "0")}`;
}

/** Die drei Zeilen eines Hinweises: Zitat, Grund, vorgeschlagene Frage. */
export function hinweisZuHtml(hinweis) {
  return (
    `<article class="hinweis">` +
    `<p class="zitat">${zeitFormatieren(hinweis.zeit)}  „${escapeHtml(hinweis.zitat)}“</p>` +
    `<p class="grund">${escapeHtml(hinweis.grund)}</p>` +
    `<p class="frage">→ ${escapeHtml(hinweis.frage)}</p>` +
    `</article>`
  );
}

/** Rendert die sichtbaren Hinweise in den Container — das, was die Seite aufruft. */
export function anzeigen(hinweise, container, max = MAX_SICHTBAR) {
  container.innerHTML = sichtbareHinweise(hinweise, max).map(hinweisZuHtml).join("");
}
