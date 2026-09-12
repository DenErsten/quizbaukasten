import { describe, expect, it } from "vitest";
import { leitfadenHtml } from "../werkzeuge/leitfaden.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.

const PUNKTE = [
  { titel: "Ausgangslage", frage: "Wer hat das Problem?", fuellt: "Den Kontext.", achtung: "Vorsicht." },
  { titel: "Abnahme", frage: "Woran merkst du, dass es fertig ist?", fuellt: "Das Kriterium.", achtung: "" },
];

describe("Leitfaden anzeigen", () => {
  it("zeigt jede Frage genau einmal, mit Kontrollkästchen", () => {
    const html = leitfadenHtml(PUNKTE);
    for (const punkt of PUNKTE) {
      expect(html).toContain(punkt.frage);
    }
    expect(html.match(/type="checkbox"/g)).toHaveLength(2);
  });

  it("nummeriert die Kästchen, damit die Seite weiß, was abgehakt wurde", () => {
    const html = leitfadenHtml(PUNKTE);
    expect(html).toContain('data-punkt="0"');
    expect(html).toContain('data-punkt="1"');
  });

  it("hakt genau die Punkte ab, die übergeben wurden", () => {
    const html = leitfadenHtml(PUNKTE, [1]);
    expect(html).toMatch(/data-punkt="1" checked/);
    expect(html).not.toMatch(/data-punkt="0" checked/);
    expect(html.match(/class="punkt erledigt"/g)).toHaveLength(1);
  });

  it("zählt, was offen ist — das ist die Liste fürs nächste Gespräch", () => {
    expect(leitfadenHtml(PUNKTE)).toContain("Noch offen: 2 von 2");
    expect(leitfadenHtml(PUNKTE, [0])).toContain("Noch offen: 1 von 2");
  });

  it("sagt es ausdrücklich, wenn alles gestellt wurde", () => {
    const html = leitfadenHtml(PUNKTE, [0, 1]);
    expect(html).toContain("Alle fünf Fragen gestellt.");
    expect(html).not.toContain("Noch offen");
  });

  it("lässt 'Worauf achten' weg, wenn im Leitfaden nichts dazu steht", () => {
    const html = leitfadenHtml(PUNKTE);
    expect(html.match(/<details/g)).toHaveLength(1);
  });

  // Der Fall, der dieses Projekt schon fünfmal Zeit gekostet hat: Etwas
  // scheitert und sieht aus wie Normalbetrieb (#99). Eine leere Spalte
  // hieße "keine Fragen" — das wäre gelogen.
  it("zeigt einen Lesefehler an, statt eine leere Spalte zu zeigen", () => {
    const html = leitfadenHtml({ fehler: "Leitfaden fehlt: docs/leitfaden.md" });
    expect(html).toContain("konnte nicht gelesen werden");
    expect(html).toContain("Leitfaden fehlt: docs/leitfaden.md");
    expect(html).not.toContain("Noch offen");
  });

  it("unterscheidet 'kein Punkt gefunden' von 'nicht lesbar'", () => {
    const html = leitfadenHtml([]);
    expect(html).toContain("Kein Punkt in docs/leitfaden.md.");
    expect(html).not.toContain("konnte nicht gelesen werden");
  });

  it("maskiert Text aus der Datei, damit Markdown kein HTML einschleust", () => {
    const html = leitfadenHtml([{ titel: "T", frage: "<script>alert(1)</script>", fuellt: "", achtung: "" }]);
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });
});
