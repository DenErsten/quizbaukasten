import { describe, expect, it } from "vitest";
import { balken, fortschrittZuHtml, meilensteinZuHtml } from "../werkzeuge/fortschritt.js";

describe("der Balken", () => {
  it("bildet Anteile ab, nicht Anzahlen", () => {
    // Meilensteine haben sehr verschiedene Größen; ein Balken nach Anzahl
    // sagt über den Fortschritt nichts.
    const html = balken({ freigegeben: 1, geschlossen: 3 });

    expect(html).toContain("width:25.0%");
    expect(html).toContain("width:75.0%");
  });

  it("ist bei einem leeren Meilenstein leer, nicht kaputt", () => {
    expect(balken({})).toContain("balken leer");
  });

  it("zeigt nur Stände, die vorkommen", () => {
    const html = balken({ geschlossen: 2 });

    expect(html).toContain("teil-geschlossen");
    expect(html).not.toContain("teil-vorgeschlagen");
  });
});

describe("ein Meilenstein", () => {
  it("zählt offen und erledigt getrennt", () => {
    const html = meilensteinZuHtml({
      titel: "P1", zaehlung: { vorgeschlagen: 1, freigegeben: 2, in_arbeit: 1, geschlossen: 4 },
      anforderungen: [],
    });

    expect(html).toContain("4 offen · 4 erledigt");
  });

  it("nennt den Stand jeder Anforderung im Klartext", () => {
    const html = meilensteinZuHtml({
      titel: "P1", zaehlung: {},
      anforderungen: [{ nummer: 7, titel: "Etwas", stand: "in_arbeit" }],
    });

    expect(html).toContain("#7");
    expect(html).toContain("in Arbeit");
  });

  it("maskiert Sonderzeichen in Titeln", () => {
    const html = meilensteinZuHtml({
      titel: "<b>P1</b>", zaehlung: {}, anforderungen: [],
    });

    expect(html).not.toContain("<b>P1</b>");
    expect(html).toContain("&lt;b&gt;");
  });
});

describe("die ganze Seite", () => {
  it("sagt, wenn es keine Meilensteine gibt", () => {
    expect(fortschrittZuHtml({ meilensteine: [] })).toContain("docs/plan.md");
  });

  it("verträgt fehlende Felder", () => {
    expect(() => fortschrittZuHtml({})).not.toThrow();
    expect(() => fortschrittZuHtml(null)).not.toThrow();
  });
});
