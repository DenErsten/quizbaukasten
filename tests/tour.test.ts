import { describe, expect, it } from "vitest";
import {
  TourFehler,
  stoppHinzufuegen,
  tourAnlegen,
  tourLaden,
  tourSpeichern,
} from "../src/tour";

// Diese Tests liegen unter tests/ und sind damit ein geschützter Pfad:
// Die KI darf hier ergänzen, aber nichts entschärfen oder löschen, ohne
// dass ein Mensch den PR freigibt. Genau das wird an Tag 1 geprüft.

describe("tourAnlegen", () => {
  it("legt eine leere Tour mit Datum und Fahrzeug an", () => {
    const tour = tourAnlegen("2026-09-14", "HH-NL 412");
    expect(tour.datum).toBe("2026-09-14");
    expect(tour.fahrzeug).toBe("HH-NL 412");
    expect(tour.stopps).toEqual([]);
  });

  it("weist ein unplausibles Datum zurück", () => {
    expect(() => tourAnlegen("14.09.2026", "HH-NL 412")).toThrow(TourFehler);
  });

  it("weist eine Tour ohne Fahrzeug zurück", () => {
    expect(() => tourAnlegen("2026-09-14", "   ")).toThrow(TourFehler);
  });
});

describe("stoppHinzufuegen", () => {
  it("hängt Stopps in der Reihenfolge an, in der sie kommen", () => {
    let tour = tourAnlegen("2026-09-14", "HH-NL 412");
    tour = stoppHinzufuegen(tour, "Werftstraße 3, Kiel", "08:30");
    tour = stoppHinzufuegen(tour, "Am Kai 17, Rendsburg");

    expect(tour.stopps.map((s) => s.adresse)).toEqual([
      "Werftstraße 3, Kiel",
      "Am Kai 17, Rendsburg",
    ]);
    expect(tour.stopps[0].ankunft).toBe("08:30");
    expect(tour.stopps[1].ankunft).toBeUndefined();
  });

  it("lässt die ursprüngliche Tour unberührt", () => {
    const leer = tourAnlegen("2026-09-14", "HH-NL 412");
    stoppHinzufuegen(leer, "Werftstraße 3, Kiel");
    expect(leer.stopps).toHaveLength(0);
  });

  it("weist eine leere Adresse zurück", () => {
    const tour = tourAnlegen("2026-09-14", "HH-NL 412");
    expect(() => stoppHinzufuegen(tour, "  ")).toThrow(TourFehler);
  });

  it("weist eine unplausible Ankunftszeit zurück", () => {
    const tour = tourAnlegen("2026-09-14", "HH-NL 412");
    expect(() => stoppHinzufuegen(tour, "Am Kai 17", "halb neun")).toThrow(TourFehler);
  });
});

describe("speichern und laden", () => {
  it("überlebt den Weg durch JSON unverändert", () => {
    let tour = tourAnlegen("2026-09-14", "HH-NL 412");
    tour = stoppHinzufuegen(tour, "Werftstraße 3, Kiel", "08:30");
    expect(tourLaden(tourSpeichern(tour))).toEqual(tour);
  });

  it("weist kaputtes JSON zurück", () => {
    expect(() => tourLaden("{nicht wirklich json")).toThrow(TourFehler);
  });

  it("weist eine unvollständige Tour zurück", () => {
    expect(() => tourLaden('{"id":"x"}')).toThrow(TourFehler);
  });
});
