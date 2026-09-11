import { describe, expect, it } from "vitest";
import { anzeigen, hinweisZuHtml, sichtbareHinweise } from "../werkzeuge/anzeige.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.

function hinweis(zeit: number) {
  return {
    zeit,
    zitat: `Zitat ${zeit}`,
    art: "mengenwort",
    grund: `Grund ${zeit}`,
    frage: `Frage ${zeit}`,
  };
}

function fakeContainer() {
  return { innerHTML: "" };
}

describe("hinweisZuHtml", () => {
  it("Fall 1: stellt einen Hinweis mit Zitat, Grund und Frage dar", () => {
    const html = hinweisZuHtml({
      zeit: 14 * 60 + 23,
      zitat: "muss schnell gehen",
      art: "mengenwort",
      grund: "Mengenwort ohne Zahl: „schnell“",
      frage: "Schnell im Vergleich wozu?",
    });

    expect(html).toContain("muss schnell gehen");
    expect(html).toContain("Mengenwort ohne Zahl");
    expect(html).toContain("Schnell im Vergleich wozu?");
  });
});

describe("sichtbareHinweise", () => {
  it("Fall 2: der neueste Hinweis steht oben", () => {
    const liste = [hinweis(10), hinweis(30), hinweis(20)];

    expect(sichtbareHinweise(liste).map((h) => h.zeit)).toEqual([30, 20, 10]);
  });

  it("Fall 3: bei mehr als fünf Hinweisen verschwinden die ältesten", () => {
    const liste = [0, 1, 2, 3, 4, 5, 6].map(hinweis);

    const sichtbar = sichtbareHinweise(liste);

    expect(sichtbar).toHaveLength(5);
    expect(sichtbar.map((h) => h.zeit)).toEqual([6, 5, 4, 3, 2]);
    expect(sichtbar.some((h) => h.zeit === 0)).toBe(false);
  });
});

describe("anzeigen", () => {
  it("rendert höchstens fünf Hinweise, neuester oben, statt das Fenster wachsen zu lassen", () => {
    const liste = [0, 1, 2, 3, 4, 5, 6].map(hinweis);
    const container = fakeContainer();

    anzeigen(liste, container);

    const eintraege = container.innerHTML.match(/class="hinweis"/g) ?? [];
    expect(eintraege).toHaveLength(5);
    expect(container.innerHTML.indexOf("Zitat 6")).toBeLessThan(
      container.innerHTML.indexOf("Zitat 5"),
    );
    expect(container.innerHTML).not.toContain("Zitat 0");
  });
});
