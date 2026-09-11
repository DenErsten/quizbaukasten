import { frageHinzufuegen, punkteGesamt, quizAnlegen, rundeHinzufuegen } from "./quiz";

// Absichtlich roh. Der erste echte PR im Planspiel macht hieraus etwas,
// mit dem Marek am Donnerstagabend tatsächlich ein Quiz zusammenstellen würde.

let quiz = quizAnlegen("Sudhaus Monatsquiz");
quiz = rundeHinzufuegen(quiz, "Musik der Neunziger");
quiz = frageHinzufuegen(quiz, quiz.runden[0].id, {
  typ: "auswahl",
  text: "Wer sang „Wonderwall“?",
  optionen: ["Blur", "Oasis", "Pulp"],
  loesung: "Oasis",
  punkte: 1,
});
quiz = frageHinzufuegen(quiz, quiz.runden[0].id, {
  typ: "schaetzen",
  text: "In welchem Jahr erschien „Nevermind“?",
  loesung: 1991,
  punkte: 2,
});

const app = document.querySelector<HTMLElement>("#app");
if (app) {
  app.innerHTML = `
    <h1>${quiz.titel}</h1>
    <p>${punkteGesamt(quiz)} Punkte zu holen</p>
    ${quiz.runden
      .map(
        (r) => `
      <section>
        <h2>${r.titel}</h2>
        <ol>
          ${r.fragen.map((f) => `<li>${f.text} <small>(${f.punkte})</small></li>`).join("")}
        </ol>
      </section>`,
      )
      .join("")}
  `;
}
