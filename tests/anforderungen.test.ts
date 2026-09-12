import { describe, expect, it } from "vitest";
import { anforderungenHtml, entwurfHtml } from "../werkzeuge/anforderungen.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.

const ENTWURF = {
  titel: "Timer",
  kontext: "Der Vortrag geht über die Zeit.",
  fertig_wenn: "Nach 5 Minuten klingelt es.",
  offene_frage: "",
  groesse: "S",
  zeit: 65,
  zitat: "Wir brauchen einen Timer.",
};

describe("Ein Entwurf", () => {
  it("zeigt Titel, Zeitmarke, Größe, Kontext, Kriterium und Zitat", () => {
    const html = entwurfHtml(ENTWURF, 0);

    expect(html).toContain("Timer");
    expect(html).toContain("01:05");
    expect(html).toContain("groesse:S");
    expect(html).toContain("Der Vortrag geht über die Zeit.");
    expect(html).toContain("Nach 5 Minuten klingelt es.");
    expect(html).toContain("Wir brauchen einen Timer.");
  });

  it("sagt ausdrücklich, wenn kein Kriterium genannt wurde", () => {
    const html = entwurfHtml({ ...ENTWURF, fertig_wenn: "", offene_frage: "Wie lange?" }, 0);

    expect(html).toContain("im Gespräch nicht genannt");
    expect(html).toContain("Wie lange?");
  });

  it("zeigt einen Knopf, solange kein Issue daraus wurde", () => {
    expect(entwurfHtml(ENTWURF, 3)).toContain('data-entwurf="3"');
  });

  it("ersetzt den Knopf durch den Link, sobald das Issue existiert", () => {
    const html = entwurfHtml(ENTWURF, 3, "https://github.com/x/y/issues/9");

    expect(html).not.toContain("<button");
    expect(html).toContain("https://github.com/x/y/issues/9");
  });

  it("maskiert Text aus dem Gespräch", () => {
    const html = entwurfHtml({ ...ENTWURF, titel: "<script>x</script>" }, 0);

    expect(html).not.toContain("<script>");
  });
});

describe("Die Liste", () => {
  // Die Regel aus docs/plan.md, Abschnitt "Was den Rechner verlässt":
  // nur auf Klick, und die Oberfläche sagt vorher, was hinausgeht.
  it("sagt in jedem Zustand, dass beim Ableiten Text hinausgeht", () => {
    for (const stand of [
      { laeuft: false, abgeleitet: false, entwuerfe: [] },
      { laeuft: true, entwuerfe: [] },
      { fehler: "kaputt" },
      { laeuft: false, abgeleitet: true, entwuerfe: [ENTWURF], angelegt: {} },
    ]) {
      expect(anforderungenHtml(stand)).toContain("Der Ton bleibt auf diesem Rechner.");
    }
  });

  it("unterscheidet 'noch nicht abgeleitet' von 'nichts gefunden'", () => {
    expect(anforderungenHtml({ abgeleitet: false, entwuerfe: [] })).toContain("Noch nichts abgeleitet");
    expect(anforderungenHtml({ abgeleitet: true, entwuerfe: [] })).toContain("keine Anforderung ableiten");
  });

  it("zeigt einen Fehler an, statt eine leere Liste zu zeigen", () => {
    const html = anforderungenHtml({ fehler: "claude ist fehlgeschlagen" });

    expect(html).toContain("claude ist fehlgeschlagen");
    expect(html).not.toContain("Noch nichts abgeleitet");
  });

  it("zählt, was noch nicht übernommen wurde", () => {
    const html = anforderungenHtml({
      laeuft: false, abgeleitet: true,
      entwuerfe: [ENTWURF, { ...ENTWURF, titel: "Zweiter" }],
      angelegt: { "0": "https://x/1" },
    });

    expect(html).toContain("2 Entwürfe, 1 noch nicht übernommen");
  });

  it("zeigt während des Lesens keine Knöpfe zum Übernehmen", () => {
    const html = anforderungenHtml({ laeuft: true, entwuerfe: [] });

    expect(html).toContain("Das Gespräch wird gelesen");
    expect(html).not.toContain("data-entwurf");
  });
});
