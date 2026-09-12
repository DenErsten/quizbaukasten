import { describe, expect, it } from "vitest";
import { ZUSTAND, naechsterZustand, zustandZuHtml } from "../werkzeuge/aufnahme.js";

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

describe("Knopf-Zustand", () => {
  it("Fall 1: im Zustand bereit ist der Stoppknopf nicht bedienbar, der Startknopf schon", () => {
    const html = zustandZuHtml({ art: ZUSTAND.BEREIT });

    expect(html).toMatch(/id="stop"[^>]*disabled/);
    expect(html).not.toMatch(/id="start"[^>]*disabled/);
  });

  it("Fall 1: im Zustand läuft ist der Startknopf nicht bedienbar, der Stoppknopf schon", () => {
    const html = zustandZuHtml({ art: ZUSTAND.LAEUFT, sekunden: 0, hinweise: [] });

    expect(html).toMatch(/id="start"[^>]*disabled/);
    expect(html).not.toMatch(/id="stop"[^>]*disabled/);
  });
});

describe("laufende Zeit", () => {
  it("Fall 2: wird im Zustand läuft als mm:ss dargestellt", () => {
    const html = zustandZuHtml({ art: ZUSTAND.LAEUFT, sekunden: 11 * 60 + 3, hinweise: [] });

    expect(html).toContain("11:03");
  });

  it("Fall 2: rundet und füllt mit führenden Nullen auf", () => {
    const html = zustandZuHtml({ art: ZUSTAND.LAEUFT, sekunden: 9.6, hinweise: [] });

    expect(html).toContain("00:10");
  });
});

describe("Hinweise im Zustand läuft", () => {
  it("Fall 3: höchstens fünf, neuester oben — wie in #37", () => {
    const hinweise = [0, 1, 2, 3, 4, 5, 6].map(hinweis);
    const html = zustandZuHtml({ art: ZUSTAND.LAEUFT, sekunden: 0, hinweise });

    const eintraege = html.match(/class="hinweis"/g) ?? [];
    expect(eintraege).toHaveLength(5);
    expect(html.indexOf("Zitat 6")).toBeLessThan(html.indexOf("Zitat 5"));
    expect(html).not.toContain("Zitat 0");
  });

  it("Fall 3: im Zustand bereit werden keine Hinweise angezeigt", () => {
    const html = zustandZuHtml({ art: ZUSTAND.BEREIT });

    expect(html).not.toContain("class=\"hinweis\"");
  });
});

describe("Verbindungsverlust", () => {
  it("Fall 4: der letzte Stand bleibt stehen und wird als veraltet gekennzeichnet", () => {
    const laufend = { art: ZUSTAND.LAEUFT, sekunden: 42, hinweise: [hinweis(1)] };

    const zustand = naechsterZustand(laufend, null);

    expect(zustand).toEqual({ ...laufend, veraltet: true });

    const html = zustandZuHtml(zustand);
    expect(html).toContain("veraltet");
    expect(html).toContain("Zitat 1");
  });

  it("Fall 4: ohne vorherigen Stand bleibt die Ansicht leer statt zu raten", () => {
    expect(naechsterZustand(null, null)).toBeNull();
  });

  it("ein neuer Stand vom Server hebt die Veraltet-Markierung wieder auf", () => {
    const veraltet = { art: ZUSTAND.LAEUFT, sekunden: 42, hinweise: [], veraltet: true };

    const frisch = naechsterZustand(veraltet, { art: ZUSTAND.LAEUFT, sekunden: 45, hinweise: [] });

    expect(frisch.veraltet).toBe(false);
  });
});

describe("Zustand beendet", () => {
  it("zeigt, wie viele Hinweise kamen, und den Weg zur Anforderungs-Ansicht", () => {
    const html = zustandZuHtml({
      art: ZUSTAND.BEENDET,
      anzahlHinweise: 3,
      anforderungenUrl: "/anforderungen",
    });

    expect(html).toContain("3 Hinweise");
    expect(html).toContain('href="/anforderungen"');
  });

  it("keine Knöpfe mehr im Zustand beendet", () => {
    const html = zustandZuHtml({ art: ZUSTAND.BEENDET, anzahlHinweise: 0 });

    expect(html).not.toContain("<button");
  });
});

describe("gescheiterter Start (#76)", () => {
  it("wird ein eigener Zustand, nicht 'bereit'", () => {
    const zustand = naechsterZustand(null, {
      art: "bereit",
      laeuft: false,
      fehler: "ModuleNotFoundError: No module named 'sounddevice'",
    });

    expect(zustand?.art).toBe("gescheitert");
  });

  it("zeigt die Meldung, statt sie zu verschlucken", () => {
    const html = zustandZuHtml({
      art: "gescheitert",
      fehler: "ModuleNotFoundError: No module named 'sounddevice'",
    });

    expect(html).toContain("sounddevice");
    expect(html).toContain("nicht starten");
  });

  it("maskiert Sonderzeichen in der Meldung", () => {
    const html = zustandZuHtml({ art: "gescheitert", fehler: "Fehler in <modul>" });

    expect(html).not.toContain("<modul>");
    expect(html).toContain("&lt;modul&gt;");
  });

  it("ohne Fehler bleibt es beim gemeldeten Zustand", () => {
    const zustand = naechsterZustand(null, { art: "bereit", laeuft: false, fehler: null });

    expect(zustand?.art).toBe("bereit");
  });
});
