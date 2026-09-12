import { describe, expect, it } from "vitest";
import { WESEN, wesenHtml, wesenSatz } from "../werkzeuge/wesen.js";
import { ZUSTAND, zustandZuHtml } from "../werkzeuge/aufnahme.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.

const ALLE = Object.values(WESEN);

describe("Die sechs Zustände", () => {
  it("sind alle verschieden", () => {
    const gezeichnet = new Set(ALLE.map((art) => wesenHtml(art)));

    expect(ALLE).toHaveLength(6);
    expect(gezeichnet.size).toBe(6);
  });

  it("unterscheiden sich auch ohne Animation — Haltung steckt im SVG", () => {
    // Wer prefers-reduced-motion setzt, muss den Zustand trotzdem sehen.
    // Deshalb dürfen sich die Zustände nicht nur in der CSS-Klasse
    // unterscheiden, sondern müssen andere Formen zeichnen.
    const ohneKlasse = ALLE.map((art) => wesenHtml(art).replace(`wesen-${art}`, ""));

    expect(new Set(ohneKlasse).size).toBe(6);
  });

  it("sagt in jedem Zustand einen Satz in der ersten Person", () => {
    for (const art of ALLE) {
      expect(wesenSatz(art)).toMatch(/^Ich |^Darf ich |^Danke /);
      expect(wesenHtml(art)).toContain(wesenSatz(art));
    }
  });

  it("nennt den Zustand auch für Vorlesesoftware", () => {
    for (const art of ALLE) {
      expect(wesenHtml(art)).toContain(`aria-label="${wesenSatz(art)}"`);
    }
  });

  it("gibt bei unbekanntem Zustand nichts aus statt zu raten", () => {
    expect(wesenHtml("tanzt")).toBe("");
  });

  it("maskiert einen Zusatztext", () => {
    expect(wesenHtml(WESEN.HOERT, "<b>x</b>")).toContain("&lt;b&gt;x&lt;/b&gt;");
  });
});

describe("Die Grenze: ausdrücken, nie verstecken", () => {
  // Ein süßes Werkzeug, das Fehler niedlich verpackt, ist gefährlicher als
  // ein hässliches, das sie nennt (#99, #106).
  it("lässt den Fehlertext wörtlich stehen", () => {
    const roh = "ModuleNotFoundError: No module named 'sounddevice'";
    const html = zustandZuHtml({ art: ZUSTAND.GESCHEITERT, fehler: roh });

    expect(html).toContain(roh);
    expect(html).toContain('class="wesen wesen-gescheitert"');
  });

  it("beschönigt den Fehlerzustand nicht mit einer Entschuldigung", () => {
    const html = zustandZuHtml({ art: ZUSTAND.GESCHEITERT, fehler: "kaputt" });

    for (const floskel of ["Ups", "Tut mir leid", "Entschuldigung", "leider"]) {
      expect(html).not.toContain(floskel);
    }
  });

  it("zeigt das Wesen in jedem Zustand der Aufnahme", () => {
    const erwartet = {
      [ZUSTAND.BEREIT]: WESEN.SCHLAEFT,
      [ZUSTAND.LAEDT]: WESEN.LAEDT,
      [ZUSTAND.BEENDET]: WESEN.BEENDET,
      [ZUSTAND.GESCHEITERT]: WESEN.GESCHEITERT,
    };
    for (const [art, wesen] of Object.entries(erwartet)) {
      expect(zustandZuHtml({ art, fehler: art === ZUSTAND.GESCHEITERT ? "x" : undefined }))
        .toContain(`wesen-${wesen}`);
    }
  });

  it("hört zu, solange nichts unscharf war — und fragt, sobald etwas auffiel", () => {
    const ohne = zustandZuHtml({ art: ZUSTAND.LAEUFT, sekunden: 5, hinweise: [], transkript: [] });
    const mit = zustandZuHtml({
      art: ZUSTAND.LAEUFT, sekunden: 5, transkript: [],
      hinweise: [{ zeit: 1, zitat: "einige", art: "mengenwort", grund: "G", frage: "F" }],
    });

    expect(ohne).toContain(`wesen-${WESEN.HOERT}`);
    expect(mit).toContain(`wesen-${WESEN.HINWEIS}`);
  });
});
