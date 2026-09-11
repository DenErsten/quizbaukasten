import { describe, expect, it } from "vitest";
import { HOECHSTENS, alsHtml, alsZeit, liste, sichtbare, type Hinweis } from "../src/anzeige";

function hinweis(zeit: number, zitat: string): Hinweis {
  return {
    zeit,
    zitat,
    art: "mengenwort",
    grund: "Mengenwort ohne Zahl: „schnell“",
    frage: "Schnell im Vergleich wozu?",
  };
}

describe("ein einzelner Hinweis", () => {
  it("zeigt Zitat, Grund und Frage", () => {
    const html = alsHtml(hinweis(83, "Das muss schnell gehen"));

    expect(html).toContain("Das muss schnell gehen");
    expect(html).toContain("Mengenwort ohne Zahl");
    expect(html).toContain("Schnell im Vergleich wozu?");
  });

  it("zeigt die Zeit als Minuten und Sekunden", () => {
    expect(alsZeit(83)).toBe("1:23");
    expect(alsZeit(5)).toBe("0:05");
  });

  it("maskiert spitze Klammern im Zitat", () => {
    // Gesprochenes wird falsch erkannt, und erkannter Text landet ungeprüft
    // im Fenster. Ohne Maskierung reicht ein "<" und die Anzeige bricht.
    const html = alsHtml(hinweis(10, 'er sagte <b>"jetzt"</b>'));

    expect(html).not.toContain("<b>");
    expect(html).toContain("&lt;b&gt;");
  });
});

describe("die Liste", () => {
  it("stellt den neuesten Hinweis oben dar", () => {
    const html = liste([hinweis(10, "zuerst gesagt"), hinweis(20, "zuletzt gesagt")]);

    expect(html.indexOf("zuletzt gesagt")).toBeLessThan(html.indexOf("zuerst gesagt"));
  });

  it("zeigt höchstens fünf und lässt die ältesten weg", () => {
    const viele = Array.from({ length: 8 }, (_, i) => hinweis(i * 10, `satz ${i}`));

    const gezeigt = sichtbare(viele);

    expect(gezeigt).toHaveLength(HOECHSTENS);
    expect(gezeigt[0].zitat).toBe("satz 7");
    expect(gezeigt.at(-1)?.zitat).toBe("satz 3");
    expect(liste(viele)).not.toContain("satz 2");
  });

  it("lässt das übergebene Feld unberührt", () => {
    const viele = [hinweis(10, "eins"), hinweis(20, "zwei")];

    sichtbare(viele);

    expect(viele.map((h) => h.zitat)).toEqual(["eins", "zwei"]);
  });

  it("ist bei keinem Hinweis leer statt kaputt", () => {
    expect(liste([])).toBe("");
  });
});
