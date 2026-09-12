import { describe, expect, it } from "vitest";
import { interviewHtml } from "../werkzeuge/interview.js";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt.

const LAEUFT = {
  laeuft: true,
  fertig: false,
  nummer: 2,
  von: 5,
  titel: "Abnahme",
  frage: "Woran merkst du, dass es fertig ist?",
  nachgefragt: false,
  rueckfrage: "",
  beantwortet: [{ titel: "Ausgangslage", frage: "Wer?", antwort: "…", offen: false }],
  offene: [],
};

describe("Das geführte Gespräch", () => {
  it("zeigt die aktuelle Frage und wo man steht", () => {
    const html = interviewHtml(LAEUFT);

    expect(html).toContain("Woran merkst du, dass es fertig ist?");
    expect(html).toContain("Frage 2 von 5");
    expect(html).toContain("Abnahme");
  });

  it("zeigt die schon beantwortete Frage klein darunter", () => {
    expect(interviewHtml(LAEUFT)).toContain("Ausgangslage");
  });

  // Die Rückfrage ist etwas anderes als die Frage: ein Nachhaken, kein
  // neuer Punkt. Deshalb eigene Klasse, eigene Fläche.
  it("setzt die Rückfrage sichtbar ab", () => {
    const html = interviewHtml({ ...LAEUFT, nachgefragt: true, rueckfrage: "Woran würdest du es festmachen?" });

    expect(html).toContain('class="rueckfrage"');
    expect(html).toContain("Woran würdest du es festmachen?");
    expect(html).toContain("interview-nachgefragt");
  });

  it("zeigt keine Rückfrage, solange keine gestellt wurde", () => {
    expect(interviewHtml(LAEUFT)).not.toContain('class="rueckfrage"');
  });

  it("führt offen gebliebene Fragen als offen mit, statt sie wegzulassen", () => {
    const html = interviewHtml({
      ...LAEUFT,
      beantwortet: [{ titel: "Ausgangslage", antwort: "", offen: true }],
    });

    expect(html).toContain("Ausgangslage");
    expect(html).toContain("offen");
  });

  it("sagt am Ende, dass es aufhört — und was offen blieb", () => {
    const html = interviewHtml({ ...LAEUFT, fertig: true, offene: ["Größenordnung"] });

    expect(html).toContain("Das war alles");
    expect(html).toContain("Größenordnung");
    expect(html).toContain("Liste fürs nächste Mal");
  });

  it("sagt es auch, wenn nichts offen blieb", () => {
    const html = interviewHtml({ ...LAEUFT, fertig: true, offene: [] });

    expect(html).toContain("Alle fünf Fragen haben eine Antwort");
  });

  // Kein laufendes Gespräch heißt: nichts zeichnen. Die Seite zeigt dann den
  // stillen Leitfaden — eine leere Fläche sähe aus wie ein kaputtes Interview.
  it("gibt nichts zurück, wenn gerade kein Gespräch läuft", () => {
    expect(interviewHtml({ laeuft: false })).toBe("");
    expect(interviewHtml(null)).toBe("");
  });

  it("zeigt einen kaputten Leitfaden als Fehler an, statt stillzuschweigen", () => {
    const html = interviewHtml({ laeuft: false, fehler: "Punkt 'X' nennt die Prüfung 'hellsehen'" });

    expect(html).toContain("Kein Gespräch möglich");
    expect(html).toContain("hellsehen");
  });

  it("maskiert Text aus dem Leitfaden", () => {
    expect(interviewHtml({ ...LAEUFT, frage: "<script>x</script>" })).not.toContain("<script>");
  });
});

describe("Die Seite verschluckt den Fehlerfall nicht (Befund aus dem review zu #118)", () => {
  // interviewHtml wird für JEDEN Stand aufgerufen, den /interview liefert.
  // Die Seite entscheidet nicht vorher, ob sich das lohnt — genau diese
  // Vorentscheidung hat die Fehlermeldung unerreichbar gemacht.
  it("liefert für einen kaputten Leitfaden sichtbaren Text, nicht leer", () => {
    const html = interviewHtml({ laeuft: false, fehler: "Punkt 'X' nennt die Prüfung 'hellsehen'" });

    expect(html).not.toBe("");
    expect(html).toContain("Kein Gespräch möglich");
  });

  it("liefert nur dann leer, wenn wirklich nichts anliegt", () => {
    expect(interviewHtml({ laeuft: false, fehler: null })).toBe("");
  });
});
