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

/**
 * Verschiebt eine Frage innerhalb ihrer Runde an eine andere Position.
 *
 * Die Kennungen der Fragen bleiben unverändert — eine Frage-ID ist ein
 * Name, keine Position. Nur die Reihenfolge in der Liste ändert sich.
 */
export function frageVerschieben(
  quiz: Quiz,
  rundenId: string,
  vonIndex: number,
  nachIndex: number,
): Quiz {
  const index = quiz.runden.findIndex((r) => r.id === rundenId);
  if (index === -1) {
    throw new QuizFehler(`Runde "${rundenId}" gibt es in diesem Quiz nicht.`);
  }
  const runde = quiz.runden[index];
  const anzahl = runde.fragen.length;
  if (
    !Number.isInteger(vonIndex) ||
    !Number.isInteger(nachIndex) ||
    vonIndex < 0 ||
    vonIndex >= anzahl ||
    nachIndex < 0 ||
    nachIndex >= anzahl
  ) {
    throw new QuizFehler(
      `Index außerhalb der Liste: ${vonIndex} -> ${nachIndex} (Runde hat ${anzahl} Fragen).`,
    );
  }

  const fragen = [...runde.fragen];
  const [frage] = fragen.splice(vonIndex, 1);
  fragen.splice(nachIndex, 0, frage);
  const neueRunde: Runde = { ...runde, fragen };
  const runden = [...quiz.runden];
  runden[index] = neueRunde;
  return { ...quiz, runden };
}

/**
 * Verschiebt eine Runde innerhalb des Quiz an eine andere Position.
 *
 * Die Kennungen der Runden und ihrer Fragen bleiben unverändert — eine
 * Runden-ID ist ein Name, keine Position. Nur die Reihenfolge in der
 * Liste ändert sich.
 */
export function rundeVerschieben(quiz: Quiz, vonIndex: number, nachIndex: number): Quiz {
  const anzahl = quiz.runden.length;
  if (
    !Number.isInteger(vonIndex) ||
    !Number.isInteger(nachIndex) ||
    vonIndex < 0 ||
    vonIndex >= anzahl ||
    nachIndex < 0 ||
    nachIndex >= anzahl
  ) {
    throw new QuizFehler(
      `Index außerhalb der Liste: ${vonIndex} -> ${nachIndex} (Quiz hat ${anzahl} Runden).`,
    );
  }

  const runden = [...quiz.runden];
  const [runde] = runden.splice(vonIndex, 1);
  runden.splice(nachIndex, 0, runde);
  return { ...quiz, runden };
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

const FRAGETYPEN: readonly Fragetyp[] = ["auswahl", "freitext", "schaetzen"];

function pruefeGeladeneFrage(f: unknown, rundenNr: number, frageNr: number): void {
  const ort = `Runde ${rundenNr}, Frage ${frageNr}`;
  const frage = f as Partial<Frage> | null;
  if (!frage || typeof frage !== "object") {
    throw new QuizFehler(`${ort}: keine gültige Frage.`);
  }
  if (!frage.id) {
    throw new QuizFehler(`${ort}: fehlende Kennung.`);
  }
  if (!FRAGETYPEN.includes(frage.typ as Fragetyp)) {
    throw new QuizFehler(`${ort}: unbekannter Fragetyp.`);
  }
  if (!frage.text) {
    throw new QuizFehler(`${ort}: fehlender Text.`);
  }
  if (frage.loesung === undefined || frage.loesung === null) {
    throw new QuizFehler(`${ort}: fehlende Lösung.`);
  }
  if (typeof frage.punkte !== "number") {
    throw new QuizFehler(`${ort}: fehlende oder ungültige Punktzahl.`);
  }
}

function pruefeGeladeneRunde(r: unknown, rundenNr: number): void {
  const ort = `Runde ${rundenNr}`;
  const runde = r as Partial<Runde> | null;
  if (!runde || typeof runde !== "object") {
    throw new QuizFehler(`${ort}: keine gültige Runde.`);
  }
  if (!runde.id) {
    throw new QuizFehler(`${ort}: fehlende Kennung.`);
  }
  if (!runde.titel) {
    throw new QuizFehler(`${ort}: fehlender Titel.`);
  }
  if (!Array.isArray(runde.fragen)) {
    throw new QuizFehler(`${ort}: fehlendes Fragen-Array.`);
  }
  runde.fragen.forEach((f, i) => pruefeGeladeneFrage(f, rundenNr, i + 1));
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
  q.runden.forEach((r, i) => pruefeGeladeneRunde(r, i + 1));
  return q as Quiz;
}
