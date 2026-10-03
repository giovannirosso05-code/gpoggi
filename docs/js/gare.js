import { renderHeader, renderFooter, fetchJSON, esc, intervalloWeekend, erroreCaricamento } from "./common.js";

renderHeader("gare");
renderFooter();

function card(g, passata) {
  return `<a class="event-card" href="gara.html?id=${g.id}" style="display:block">
    <div class="event-date">${intervalloWeekend(g)}</div>
    <div class="event-name">${esc(g.nome)}</div>
    <div class="event-location">${esc(g.circuito)}, ${esc(g.paese)}</div>
    <span class="event-status ${passata ? "passato" : ""}">${passata ? "Disputata" : g.sessioni.some((s) => s.tipo === "Sprint") ? "Con sprint" : "In programma"}</span>
  </a>`;
}

const lista = document.getElementById("gare-list");
try {
  const eventi = await fetchJSON("data/events.json");
  const ora = new Date();
  const prossime = eventi.filter((g) => new Date(g.fine) > ora);
  const passate = eventi.filter((g) => new Date(g.fine) <= ora).reverse();
  lista.innerHTML =
    (prossime.length ? `<div class="gare-section"><h3 class="accent">Prossime</h3>${prossime.map((g) => card(g, false)).join("")}</div>` : "") +
    (passate.length ? `<div class="gare-section"><h3>Disputate</h3>${passate.map((g) => card(g, true)).join("")}</div>` : "");
} catch (e) {
  erroreCaricamento(lista);
}
