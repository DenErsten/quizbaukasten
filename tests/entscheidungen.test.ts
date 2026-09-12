import { describe, expect, it } from "vitest";
import { entscheidungZuHtml, konsoleZuHtml } from "../werkzeuge/freigabe.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.
//
// Eigene Datei statt Anhang an freigabe.test.ts: Eine bestehende Testdatei
// zu ändern verlangt eine menschliche Freigabe (Gate G3), eine neue nicht.
// Das ist kein Schlupfloch, sondern der Sinn der Regel — geschützt ist,
// was schon jemanden schützt.

describe("Offene Entscheidungen (#108)", () => {
  const E = {
    nummer: 102,
    titel: "Weg zurück in die Pipeline",
    frage: "Soll der Text an Claude gehen?",
    optionen: [
      { buchstabe: "A", text: "Lokal bleiben." },
      { buchstabe: "B", text: "Claude benutzen." },
    ],
    empfehlung: { buchstabe: "B", grund: "lokal reicht die Qualität nicht." },
  };

  it("zeigt Nummer, Titel, Frage und beide Optionen", () => {
    const html = entscheidungZuHtml(E);

    expect(html).toContain("#102");
    expect(html).toContain("Weg zurück in die Pipeline");
    expect(html).toContain("Soll der Text an Claude gehen?");
    expect(html).toContain("Lokal bleiben.");
    expect(html).toContain("Claude benutzen.");
  });

  it("markiert genau die empfohlene Option", () => {
    const html = entscheidungZuHtml(E);

    expect(html.match(/class="option empfohlen"/g)).toHaveLength(1);
    expect(html).toMatch(/data-wahl="B"[^>]*>[^]*?empfohlen/);
  });

  // Ein Haken ohne Grund ist eine Anweisung, kein Rat. Wer die Empfehlung
  // ablehnen soll, muss wissen, wogegen er sich entscheidet.
  it("schreibt den Grund aus, nicht nur die Markierung", () => {
    expect(entscheidungZuHtml(E)).toContain("lokal reicht die Qualität nicht.");
  });

  it("sagt es, wenn es keine Empfehlung gibt", () => {
    const html = entscheidungZuHtml({ ...E, empfehlung: null });

    expect(html).not.toContain("empfohlen");
    expect(html).toContain("Keine Empfehlung");
  });

  it("gibt jeder Option Issue-Nummer und Buchstaben mit", () => {
    const html = entscheidungZuHtml(E);

    expect(html).toContain('data-entscheidung="102" data-wahl="A"');
    expect(html).toContain('data-entscheidung="102" data-wahl="B"');
  });

  it("steht in der Konsole über den Freigaben", () => {
    const html = konsoleZuHtml({ entscheidungen: [E], issues: [], prs: [], laeufe: [] });

    expect(html).toContain("Deine Entscheidung (1)");
    expect(html.indexOf("Deine Entscheidung")).toBeLessThan(html.indexOf("Warten auf Freigabe"));
  });

  it("zeigt den Abschnitt nicht, wenn nichts offen ist", () => {
    const html = konsoleZuHtml({ entscheidungen: [], issues: [], prs: [], laeufe: [] });

    expect(html).not.toContain("Deine Entscheidung");
  });

  it("maskiert Text aus dem Issue", () => {
    const html = entscheidungZuHtml({ ...E, titel: "<script>x</script>" });

    expect(html).not.toContain("<script>");
  });
});
