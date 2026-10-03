import { renderHeader, renderFooter, fetchJSON, esc, img, intervalloWeekend, erroreCaricamento } from "./common.js";

renderHeader("gare");
renderFooter();

function card(g, passata) {
  const sprint = g.sessioni.some((s) => s.tipo === "Sprint");
  return `<a class="event-card ${passata ? "passata" : ""}" href="gara.html?id=${g.id}">
    <div class="event-map">${g.mappa ? img(g.mappa, "Tracciato di " + g.circuito) : `<span class="senza-mappa">${esc(g.circuito)}</span>`}</div>
    <div class="event-body">
      <div class="event-date">${intervalloWeekend(g)}</div>
      <div class="event-name">${esc(g.nome)}</div>
      <div class="event-location">${esc(g.circuito)}, ${esc(g.paese)}</div>
      <span class="event-status ${passata ? "passato" : ""}">${passata ? "Disputata" : sprint ? "Weekend con sprint" : "In programma"}</span>
    </div>
  </a>`;
}

const lista = document.getElementById("gare-list");
try {
  const eventi = await fetchJSON("data/events.json");
  const ora = new Date();
  const prossime = eventi.filter((g) => new Date(g.fine) > ora);
  const passate = eventi.filter((g) => new Date(g.fine) <= ora).reverse();
  lista.innerHTML =
    (prossime.length ? `<div class="gare-section"><h3 class="section-title">Prossimi weekend</h3><div class="gare-grid">${prossime.map((g) => card(g, false)).join("")}</div></div>` : "") +
    (passate.length ? `<div class="gare-section"><h3 class="section-title">Già disputati</h3><div class="gare-grid">${passate.map((g) => card(g, true)).join("")}</div></div>` : "");
} catch (e) {
  erroreCaricamento(lista);
}
