/**
 * Kern des Quizbaukastens.
 *
 * Ein Kneipenquiz ist in Runden organisiert, nicht in einer flachen
 * Fragenliste — das ist der Unterschied zwischen einem Quiz und einem
 * Fragebogen, und deshalb steckt die Runde hier im Modell.
 *
 * M1, Abnahmekriterium: Ein Quizmaster kann ein Quiz mit Runden und
 * Fragen anlegen, speichern und wieder öffnen.
 */

export type Fragetyp = "auswahl" | "freitext" | "schaetzen";

export interface Frage {
  readonly id: string;
  readonly typ: Fragetyp;
  readonly text: string;
  /** Nur bei "auswahl": die Optionen, aus denen gewählt wird. */
  readonly optionen?: readonly string[];
  /** Auswahl: der richtige Text. Freitext: die Musterlösung. Schätzen: die Zahl. */
  readonly loesung: string | number;
  readonly punkte: number;
}

export interface Runde {
  readonly id: string;
  readonly titel: string;
  readonly fragen: readonly Frage[];
}

export interface Quiz {
  readonly id: string;
  readonly titel: string;
  readonly runden: readonly Runde[];
}

export class QuizFehler extends Error {}

function kennung(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/ä/g, "ae")
    .replace(/ö/g, "oe")
    .replace(/ü/g, "ue")
    .replace(/ß/g, "ss")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function quizAnlegen(titel: string): Quiz {
  if (titel.trim() === "") {
    throw new QuizFehler("Ein Quiz braucht einen Titel.");
  }
  return { id: kennung(titel), titel: titel.trim(), runden: [] };
}

export function rundeHinzufuegen(quiz: Quiz, titel: string): Quiz {
  if (titel.trim() === "") {
    throw new QuizFehler("Eine Runde braucht einen Titel.");
  }
  const id = `${quiz.id}-r${quiz.runden.length + 1}`;
  return { ...quiz, runden: [...quiz.runden, { id, titel: titel.trim(), fragen: [] }] };
}

/** Beschreibt eine Frage, bevor sie eine Kennung bekommt. */
export type FrageEntwurf = Omit<Frage, "id">;

export function frageHinzufuegen(quiz: Quiz, rundenId: string, entwurf: FrageEntwurf): Quiz {
  const index = quiz.runden.findIndex((r) => r.id === rundenId);
  if (index === -1) {
    throw new QuizFehler(`Runde "${rundenId}" gibt es in diesem Quiz nicht.`);
  }
  pruefeEntwurf(entwurf);

  const runde = quiz.runden[index];
  const frage: Frage = { ...entwurf, id: `${runde.id}-f${runde.fragen.length + 1}` };
  const neueRunde: Runde = { ...runde, fragen: [...runde.fragen, frage] };
  const runden = [...quiz.runden];
  runden[index] = neueRunde;
  return { ...quiz, runden };
}

function pruefeEntwurf(e: FrageEntwurf): void {
  if (e.text.trim() === "") {
    throw new QuizFehler("Eine Frage braucht einen Text.");
  }
  if (!Number.isFinite(e.punkte) || e.punkte <= 0) {
    throw new QuizFehler(`Punkte müssen positiv sein, waren: ${e.punkte}`);
  }
  if (e.typ === "auswahl") {
    if (!e.optionen || e.optionen.length < 2) {
      throw new QuizFehler("Eine Auswahlfrage braucht mindestens zwei Optionen.");
    }
    if (!e.optionen.includes(String(e.loesung))) {
      throw new QuizFehler("Die Lösung muss eine der Optionen sein.");
    }
  }
  if (e.typ === "schaetzen" && typeof e.loesung !== "number") {
    throw new QuizFehler("Eine Schätzfrage braucht eine Zahl als Lösung.");
  }
}

/** Wie viele Punkte im ganzen Quiz zu holen sind. */
export function punkteGesamt(quiz: Quiz): number {
  return quiz.runden.reduce(
    (summe, r) => summe + r.fragen.reduce((s, f) => s + f.punkte, 0),
    0,
  );
}

/**
 * Bewertet eine Antwort.
 *
 * Schätzfragen sind hier bewusst streng: Sie geben nur Punkte bei exakter
 * Zahl. Wer am nächsten dran gewinnt, ist eine Regel über alle Teams
 * hinweg und gehört deshalb in die Auswertung des Abends (M2),
 * nicht in die Bewertung einer einzelnen Antwort.
 */
export function antwortPruefen(frage: Frage, antwort: string | number): number {
  if (frage.typ === "schaetzen") {
    return Number(antwort) === Number(frage.loesung) ? frage.punkte : 0;
  }
  const gegeben = String(antwort).trim().toLowerCase();
  const richtig = String(frage.loesung).trim().toLowerCase();
  return gegeben === richtig ? frage.punkte : 0;
}

export function quizSpeichern(quiz: Quiz): string {
  return JSON.stringify(quiz, null, 2);
}

export function quizLaden(roh: string): Quiz {
  let daten: unknown;
  try {
    daten = JSON.parse(roh);
  } catch {
    throw new QuizFehler("Gespeichertes Quiz ist kein gültiges JSON.");
  }
  const q = daten as Partial<Quiz>;
  if (!q?.id || !q?.titel || !Array.isArray(q.runden)) {
    throw new QuizFehler("Gespeichertes Quiz ist unvollständig.");
  }
  return q as Quiz;
}
