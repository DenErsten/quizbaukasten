/**
 * Anzeige der Hinweise aus scripts/ausloeser.py — Teil 3 von #34.
 *
 * Nach Option B ist das kein Nebenteil, sondern das Produkt: Was hier nicht
 * in zwei Sekunden lesbar ist, wird im Meeting nicht gelesen. Das Gespräch
 * hat Vorrang, immer.
 *
 * Die Funktionen geben HTML als Zeichenkette zurück statt Knoten in den
 * Baum zu hängen. Das ist kein Stil, sondern Prüfbarkeit: So laufen die
 * Tests ohne DOM und damit ohne jsdom als Abhängigkeit. Der Preis ist, dass
 * hier von Hand maskiert werden muss — siehe `maskiert`.
 */

export interface Hinweis {
  readonly zeit: number;
  readonly zitat: string;
  readonly art: string;
  readonly grund: string;
  readonly frage: string;
}

/**
 * Mehr als das passt nicht in einen Blick.
 *
 * Eine Liste, die wächst, zwingt zum Scrollen — und Scrollen im Gespräch
 * heißt, dass man nicht zuhört.
 */
export const HOECHSTENS = 5;

export function sichtbare(
  hinweise: readonly Hinweis[],
  hoechstens: number = HOECHSTENS,
): Hinweis[] {
  // Neueste oben: Der letzte Satz ist der, über den gerade geredet wird.
  return [...hinweise].reverse().slice(0, hoechstens);
}

export function alsZeit(sekunden: number): string {
  const minuten = Math.floor(sekunden / 60);
  const rest = Math.floor(sekunden % 60);
  return `${minuten}:${String(rest).padStart(2, "0")}`;
}

function maskiert(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function alsHtml(hinweis: Hinweis): string {
  return [
    `<article class="hinweis" data-art="${maskiert(hinweis.art)}">`,
    `<p class="kopf"><span class="zeit">${alsZeit(hinweis.zeit)}</span>`,
    `<q class="zitat">${maskiert(hinweis.zitat)}</q></p>`,
    `<p class="grund">${maskiert(hinweis.grund)}</p>`,
    `<p class="frage">${maskiert(hinweis.frage)}</p>`,
    `</article>`,
  ].join("");
}

export function liste(
  hinweise: readonly Hinweis[],
  hoechstens: number = HOECHSTENS,
): string {
  return sichtbare(hinweise, hoechstens).map(alsHtml).join("");
}
