import { describe, expect, it } from "vitest";
import { issueZuHtml, konsoleZuHtml, maskiert, prZuHtml } from "../werkzeuge/freigabe.js";

describe("Issues in der Konsole", () => {
  it("zeigt ein fehlendes Abnahmekriterium deutlich", () => {
    // PR #68 ist daran gescheitert — gemerkt hat es erst der Prüfer.
    const html = issueZuHtml({ nummer: 7, titel: "Ohne Kriterium", kriterium: false });

    expect(html).toContain("Kein „Fertig, wenn");
    expect(html).toContain("unvollstaendig");
  });

  it("warnt nicht, wenn das Kriterium da ist", () => {
    const html = issueZuHtml({ nummer: 7, titel: "Mit Kriterium", kriterium: true });

    expect(html).not.toContain("Kein „Fertig, wenn");
  });

  it("maskiert Sonderzeichen im Titel", () => {
    const html = issueZuHtml({ nummer: 1, titel: "<script>x</script>", kriterium: true });

    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });
});

describe("Pull Requests in der Konsole", () => {
  it("nennt rote Checks beim Namen", () => {
    const html = prZuHtml({ nummer: 9, titel: "PR", rote_checks: ["abnahme", "review"] });

    expect(html).toContain("Rot: abnahme, review");
  });

  it("sagt es, wenn alles grün ist", () => {
    expect(prZuHtml({ nummer: 9, titel: "PR", rote_checks: [] })).toContain("Alle Checks grün");
  });

  it("kennzeichnet einen PR ohne verlinktes Issue", () => {
    const html = prZuHtml({ nummer: 9, titel: "PR", issue: null, rote_checks: [] });

    expect(html).toContain("kein Issue verlinkt");
  });

  it("der Freigabeknopf ist aus, wenn schon freigegeben", () => {
    const html = prZuHtml({ nummer: 9, titel: "PR", rote_checks: [], freigegeben: true });

    expect(html).toContain("disabled");
  });
});

describe("die ganze Konsole", () => {
  it("trennt Issues und Pull Requests und zählt sie", () => {
    const html = konsoleZuHtml({
      issues: [{ nummer: 1, titel: "A", kriterium: true }],
      prs: [{ nummer: 2, titel: "B", rote_checks: [] }, { nummer: 3, titel: "C", rote_checks: [] }],
    });

    expect(html).toContain("Warten auf Freigabe (1)");
    expect(html).toContain("Pull Requests (2)");
  });

  it("sagt, wenn nichts offen ist", () => {
    const html = konsoleZuHtml({ issues: [], prs: [] });

    expect(html.match(/Nichts offen/g)).toHaveLength(2);
  });

  it("verträgt fehlende Felder", () => {
    expect(() => konsoleZuHtml({})).not.toThrow();
  });
});

describe("maskiert", () => {
  it("behandelt Anführungszeichen, weil Werte in Attributen landen", () => {
    expect(maskiert('a"b')).toBe("a&quot;b");
  });
});
