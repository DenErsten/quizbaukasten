/*
  Meldet, wenn das Modul dieser Seite nicht anlaeuft (#122).

  KEIN MODUL. Das ist der ganze Trick: Ein Modul, das einen Ladefehler melden
  soll, teilt dessen Schicksal — schlaegt der Import fehl, laeuft auch der
  Melder nicht. Deshalb ein gewoehnliches Skript, das vorher laeuft und nichts
  importiert.

  Firat am 2026-09-12: "Screen Freigabe bleibt im 'Wird geladen' haengen."
  Genau das: Der Platzhalter stand, das Modul war nie angelaufen, und nichts
  auf der Seite sagte es. Dasselbe Muster wie #99 und #119, nur an der Stelle,
  an die weder ein Test noch ein Check reicht.
*/
(function () {
  "use strict";

  var WARTEZEIT = 8000;
  var gemeldet = false;

  function feld() {
    return document.querySelector("[data-anlauf]");
  }

  function melden(titel, einzelheit) {
    if (gemeldet) return;
    var ziel = feld();
    if (!ziel) return;
    gemeldet = true;
    ziel.setAttribute("data-anlauf", "gescheitert");
    var p = document.createElement("p");
    p.className = "anlauf-fehler";
    p.setAttribute("role", "alert");
    p.textContent = titel;
    var pre = document.createElement("pre");
    pre.className = "anlauf-einzelheit";
    // textContent, nicht innerHTML: Der Text kommt vom Browser, nicht von uns.
    pre.textContent = einzelheit;
    ziel.textContent = "";
    ziel.appendChild(p);
    if (einzelheit) ziel.appendChild(pre);
  }

  // true = auch Ladefehler von <script> und <link>. Die steigen nicht auf,
  // sie sind nur in der Erfassungsphase zu sehen — genau der Fall hier.
  window.addEventListener(
    "error",
    function (e) {
      if (e && e.target && e.target !== window && e.target.src) {
        melden("Diese Seite konnte nicht starten.", "Nicht geladen: " + e.target.src);
        return;
      }
      var wo = e && e.filename ? e.filename + ":" + e.lineno : "";
      melden("Diese Seite konnte nicht starten.", ((e && e.message) || "Unbekannter Fehler") + (wo ? "\n" + wo : ""));
    },
    true,
  );

  window.addEventListener("unhandledrejection", function (e) {
    melden("Diese Seite konnte nicht starten.", String((e && e.reason) || "Abgelehntes Versprechen"));
  });

  // Der Fall ohne Fehlerereignis: eine alte Datei aus dem Zwischenspeicher,
  // ein Modul, das still nichts tut. Dann steht nach acht Sekunden immer noch
  // der Platzhalter — und das ist Aussage genug.
  window.setTimeout(function () {
    var ziel = feld();
    if (!ziel) return;
    if (ziel.getAttribute("data-anlauf") === "gescheitert") return;
    if (ziel.textContent.trim() !== ziel.getAttribute("data-anlauf")) return;
    melden(
      "Diese Seite ist seit acht Sekunden nicht weitergekommen.",
      "Das Modul hat nichts gezeichnet. Läuft werkzeuge/server.py? " +
        "Ein Neuladen mit gedrückter Umschalttaste umgeht den Zwischenspeicher.",
    );
  }, WARTEZEIT);
})();
