import { stoppHinzufuegen, tourAnlegen, type Tour } from "./tour";

// Absichtlich roh. Der erste echte PR im Planspiel macht hieraus etwas,
// das Timo aus der Disposition benutzen würde.

const beispiel: Tour = stoppHinzufuegen(
  stoppHinzufuegen(tourAnlegen("2026-09-14", "HH-NL 412"), "Werftstraße 3, Kiel", "08:30"),
  "Am Kai 17, Rendsburg",
  "10:15",
);

const app = document.querySelector<HTMLElement>("#app");
if (app) {
  app.innerHTML = `
    <h1>Tour ${beispiel.datum} — ${beispiel.fahrzeug}</h1>
    <ol>
      ${beispiel.stopps
        .map((s) => `<li>${s.ankunft ?? "--:--"} &nbsp; ${s.adresse}</li>`)
        .join("")}
    </ol>
  `;
}
