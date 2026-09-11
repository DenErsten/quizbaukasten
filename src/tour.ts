/**
 * Kern des Tourenplaners. Bewusst klein gehalten: Das Planspiel soll die
 * Gates prüfen, nicht eure Architekturkenntnisse.
 *
 * M1, Abnahmekriterium: Ein Disponent kann eine Tour mit Stopps anlegen
 * und speichern.
 */

export interface Stopp {
  readonly id: string;
  readonly adresse: string;
  /** Geplante Ankunft als "HH:MM". Leer, solange nicht disponiert. */
  readonly ankunft?: string;
}

export interface Tour {
  readonly id: string;
  readonly datum: string; // ISO, "2026-09-14"
  readonly fahrzeug: string;
  readonly stopps: readonly Stopp[];
}

export class TourFehler extends Error {}

/** Legt eine neue, leere Tour an. */
export function tourAnlegen(datum: string, fahrzeug: string): Tour {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(datum)) {
    throw new TourFehler(`Datum muss JJJJ-MM-TT sein, war: "${datum}"`);
  }
  if (fahrzeug.trim() === "") {
    throw new TourFehler("Eine Tour braucht ein Fahrzeug.");
  }
  return {
    id: `tour-${datum}-${fahrzeug.trim().toLowerCase().replace(/\s+/g, "-")}`,
    datum,
    fahrzeug: fahrzeug.trim(),
    stopps: [],
  };
}

/** Hängt einen Stopp an. Gibt eine neue Tour zurück, ändert nichts. */
export function stoppHinzufuegen(tour: Tour, adresse: string, ankunft?: string): Tour {
  if (adresse.trim() === "") {
    throw new TourFehler("Ein Stopp braucht eine Adresse.");
  }
  if (ankunft !== undefined && !/^\d{2}:\d{2}$/.test(ankunft)) {
    throw new TourFehler(`Ankunft muss HH:MM sein, war: "${ankunft}"`);
  }
  const stopp: Stopp = {
    id: `${tour.id}-s${tour.stopps.length + 1}`,
    adresse: adresse.trim(),
    ...(ankunft !== undefined ? { ankunft } : {}),
  };
  return { ...tour, stopps: [...tour.stopps, stopp] };
}

/** Serialisiert eine Tour zum Speichern. */
export function tourSpeichern(tour: Tour): string {
  return JSON.stringify(tour, null, 2);
}

/** Liest eine gespeicherte Tour zurück. */
export function tourLaden(roh: string): Tour {
  let daten: unknown;
  try {
    daten = JSON.parse(roh);
  } catch {
    throw new TourFehler("Gespeicherte Tour ist kein gültiges JSON.");
  }
  const t = daten as Partial<Tour>;
  if (!t?.id || !t?.datum || !t?.fahrzeug || !Array.isArray(t.stopps)) {
    throw new TourFehler("Gespeicherte Tour ist unvollständig.");
  }
  return t as Tour;
}
