import { describe, expect, it } from "vitest";
import {
  QuizFehler,
  antwortPruefen,
  frageHinzufuegen,
  frageVerschieben,
  punkteGesamt,
  quizAnlegen,
  quizLaden,
  quizSpeichern,
  rundeHinzufuegen,
  type Frage,
} from "../src/quiz";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt. Genau das wird an Tag 1 geprüft.

function beispielQuiz() {
  let q = quizAnlegen("Sudhaus Monatsquiz");
  q = rundeHinzufuegen(q, "Musik der Neunziger");
  q = frageHinzufuegen(q, q.runden[0].id, {
    typ: "auswahl",
    text: "Wer sang „Wonderwall“?",
    optionen: ["Blur", "Oasis", "Pulp"],
    loesung: "Oasis",
    punkte: 1,
  });
  q = frageHinzufuegen(q, q.runden[0].id, {
    typ: "schaetzen",
    text: "In welchem Jahr erschien „Nevermind“?",
    loesung: 1991,
    punkte: 2,
  });
  return q;
}

describe("quizAnlegen", () => {
  it("legt ein leeres Quiz mit lesbarer Kennung an", () => {
    const q = quizAnlegen("Sudhaus Monatsquiz");
    expect(q.titel).toBe("Sudhaus Monatsquiz");
    expect(q.id).toBe("sudhaus-monatsquiz");
    expect(q.runden).toEqual([]);
  });

  it("macht Umlaute in der Kennung lesbar statt sie zu verschlucken", () => {
    expect(quizAnlegen("Größter Käse-Abend").id).toBe("groesster-kaese-abend");
  });

  it("weist ein Quiz ohne Titel zurück", () => {
    expect(() => quizAnlegen("   ")).toThrow(QuizFehler);
  });
});

describe("Runden und Fragen", () => {
  it("hängt Runden in der Reihenfolge an, in der sie kommen", () => {
    let q = quizAnlegen("Testquiz");
    q = rundeHinzufuegen(q, "Erdkunde");
    q = rundeHinzufuegen(q, "Musik");
    expect(q.runden.map((r) => r.titel)).toEqual(["Erdkunde", "Musik"]);
  });

  it("hängt Fragen an die richtige Runde", () => {
    const q = beispielQuiz();
    expect(q.runden[0].fragen).toHaveLength(2);
    expect(q.runden[0].fragen[1].text).toContain("Nevermind");
  });

  it("lässt das ursprüngliche Quiz unberührt", () => {
    const vorher = quizAnlegen("Testquiz");
    rundeHinzufuegen(vorher, "Erdkunde");
    expect(vorher.runden).toHaveLength(0);
  });

  it("weist eine Frage für eine unbekannte Runde zurück", () => {
    const q = quizAnlegen("Testquiz");
    expect(() =>
      frageHinzufuegen(q, "gibt-es-nicht", {
        typ: "freitext",
        text: "Was denn?",
        loesung: "nichts",
        punkte: 1,
      }),
    ).toThrow(QuizFehler);
  });

  it("weist eine Auswahlfrage zurück, deren Lösung nicht unter den Optionen steht", () => {
    let q = quizAnlegen("Testquiz");
    q = rundeHinzufuegen(q, "Musik");
    expect(() =>
      frageHinzufuegen(q, q.runden[0].id, {
        typ: "auswahl",
        text: "Wer sang „Wonderwall“?",
        optionen: ["Blur", "Pulp"],
        loesung: "Oasis",
        punkte: 1,
      }),
    ).toThrow(QuizFehler);
  });

  it("weist eine Auswahlfrage mit nur einer Option zurück", () => {
    let q = quizAnlegen("Testquiz");
    q = rundeHinzufuegen(q, "Musik");
    expect(() =>
      frageHinzufuegen(q, q.runden[0].id, {
        typ: "auswahl",
        text: "Einzige Wahl?",
        optionen: ["Oasis"],
        loesung: "Oasis",
        punkte: 1,
      }),
    ).toThrow(QuizFehler);
  });

  it("weist null oder negative Punkte zurück", () => {
    let q = quizAnlegen("Testquiz");
    q = rundeHinzufuegen(q, "Musik");
    expect(() =>
      frageHinzufuegen(q, q.runden[0].id, {
        typ: "freitext",
        text: "Gratis?",
        loesung: "nein",
        punkte: 0,
      }),
    ).toThrow(QuizFehler);
  });
});

describe("punkteGesamt", () => {
  it("zählt über alle Runden hinweg", () => {
    expect(punkteGesamt(beispielQuiz())).toBe(3);
  });

  it("ist bei einem leeren Quiz null", () => {
    expect(punkteGesamt(quizAnlegen("Leer"))).toBe(0);
  });
});

describe("antwortPruefen", () => {
  const auswahl = beispielQuiz().runden[0].fragen[0];
  const schaetzen = beispielQuiz().runden[0].fragen[1];

  it("gibt Punkte für die richtige Auswahl", () => {
    expect(antwortPruefen(auswahl, "Oasis")).toBe(1);
  });

  it("ist bei Groß- und Kleinschreibung und Leerzeichen nachsichtig", () => {
    expect(antwortPruefen(auswahl, "  oasis ")).toBe(1);
  });

  it("gibt null Punkte für die falsche Auswahl", () => {
    expect(antwortPruefen(auswahl, "Blur")).toBe(0);
  });

  it("wertet Schätzfragen nur bei exakter Zahl", () => {
    expect(antwortPruefen(schaetzen, 1991)).toBe(2);
    expect(antwortPruefen(schaetzen, "1991")).toBe(2);
    expect(antwortPruefen(schaetzen, 1992)).toBe(0);
  });
});

describe("speichern und laden", () => {
  it("überlebt den Weg durch JSON unverändert", () => {
    const q = beispielQuiz();
    expect(quizLaden(quizSpeichern(q))).toEqual(q);
  });

  it("weist kaputtes JSON zurück", () => {
    expect(() => quizLaden("{nicht wirklich json")).toThrow(QuizFehler);
  });

  it("weist ein unvollständiges Quiz zurück", () => {
    expect(() => quizLaden('{"id":"x"}')).toThrow(QuizFehler);
  });
});

describe("Fragetypen", () => {
  it("kennt Freitextfragen", () => {
    let q = quizAnlegen("Testquiz");
    q = rundeHinzufuegen(q, "Wissen");
    q = frageHinzufuegen(q, q.runden[0].id, {
      typ: "freitext",
      text: "Hauptstadt von Schleswig-Holstein?",
      loesung: "Kiel",
      punkte: 1,
    });
    const frage: Frage = q.runden[0].fragen[0];
    expect(antwortPruefen(frage, "kiel")).toBe(1);
  });

  it("weist eine Schätzfrage ohne Zahl als Lösung zurück", () => {
    let q = quizAnlegen("Testquiz");
    q = rundeHinzufuegen(q, "Zahlen");
    expect(() =>
      frageHinzufuegen(q, q.runden[0].id, {
        typ: "schaetzen",
        text: "Wie viele?",
        loesung: "viele",
        punkte: 1,
      }),
    ).toThrow(QuizFehler);
  });
});

describe("frageVerschieben", () => {
  it("ändert die Reihenfolge der Fragen in der Runde", () => {
    const q = beispielQuiz();
    const rundenId = q.runden[0].id;
    const ids = q.runden[0].fragen.map((f) => f.id);
    const verschoben = frageVerschieben(q, rundenId, 1, 0);
    expect(verschoben.runden[0].fragen.map((f) => f.id)).toEqual([ids[1], ids[0]]);
  });

  it("lässt das übergebene Quiz unverändert", () => {
    const q = beispielQuiz();
    const rundenId = q.runden[0].id;
    const vorher = q.runden[0].fragen.map((f) => f.id);
    frageVerschieben(q, rundenId, 1, 0);
    expect(q.runden[0].fragen.map((f) => f.id)).toEqual(vorher);
  });

  it("weist einen Index außerhalb der Liste zurück", () => {
    const q = beispielQuiz();
    const rundenId = q.runden[0].id;
    expect(() => frageVerschieben(q, rundenId, 0, 5)).toThrow(QuizFehler);
  });

  it("weist eine unbekannte rundenId zurück", () => {
    const q = beispielQuiz();
    expect(() => frageVerschieben(q, "gibt-es-nicht", 0, 1)).toThrow(QuizFehler);
  });
});
