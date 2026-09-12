import { describe, expect, it } from "vitest";
import { prZuHtml, tatFehlerZuHtml } from "../werkzeuge/freigabe.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.
//
// Eigene Datei statt Anhang an freigabe.test.ts: Eine bestehende Testdatei
// zu ändern verlangt eine menschliche Freigabe (Gate G3).

const PR = {
  nummer: 118,
  titel: "Irgendwas",
  issue: 114,
  rote_checks: [],
  laufende_checks: [],
  freigegeben: false,
  dateien: [],
  autor: "quizberater",
  darf_freigeben: true,
  grund: "",
};

describe("Ein Knopf, der nicht kann, wird nicht angeboten (#119)", () => {
  it("bietet den Knopf an, wenn die Freigabe möglich ist", () => {
    const html = prZuHtml(PR);

    expect(html).toMatch(/data-tat="freigeben"[^>]*>Freigeben<\/button>/);
    expect(html).not.toContain("disabled");
  });

  // Firat am 2026-09-12: "Aber wenn ich auf Freigeben drücke passiert nichts."
  // Es passierte etwas — GitHub lehnte ab. Das steht jetzt vorher da.
  it("schaltet ihn ab UND nennt den Grund, wenn es der eigene PR ist", () => {
    const html = prZuHtml({
      ...PR,
      autor: "DenErsten",
      darf_freigeben: false,
      grund: "Eigener Pull Request (DenErsten) — GitHub lässt keine Selbstfreigabe zu.",
    });

    expect(html).toContain("disabled");
    expect(html).toContain("keine Selbstfreigabe");
  });

  it("nennt nie nur das eine ohne das andere", () => {
    const stumm = prZuHtml({ ...PR, darf_freigeben: false, grund: "" });

    // Ein abgeschalteter Knopf ohne Begründung ist genauso stumm wie ein
    // Fehler, den niemand sieht. Dann lieber den Knopf lassen.
    expect(stumm.includes("disabled") && !stumm.includes("grund-dafuer")).toBe(true);
    expect(prZuHtml({ ...PR, darf_freigeben: false, grund: "Weil." })).toContain("grund-dafuer");
  });

  it("kommt auch mit alten Antworten ohne das Feld zurecht", () => {
    const { darf_freigeben, grund, ...ohne } = PR;

    expect(prZuHtml(ohne)).not.toContain("disabled");
    expect(prZuHtml({ ...ohne, freigegeben: true })).toContain("disabled");
  });
});

describe("Der Fehler steht am Knopf (#119)", () => {
  it("gibt den Text als sichtbare Meldung aus", () => {
    const html = tatFehlerZuHtml("Can not approve your own pull request");

    expect(html).toContain("Can not approve your own pull request");
    expect(html).toContain('class="tat-fehler"');
  });

  it("meldet sich auch bei Vorlesesoftware", () => {
    expect(tatFehlerZuHtml("x")).toContain('role="alert"');
  });

  it("maskiert die Meldung von GitHub", () => {
    expect(tatFehlerZuHtml("<script>x</script>")).not.toContain("<script>");
  });
});
