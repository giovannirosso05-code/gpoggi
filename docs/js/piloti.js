import { renderHeader, renderFooter, fetchJSON, esc, punti, formattaData, intervalloWeekend, ND, ICON_SEARCH, erroreCaricamento } from "./common.js";

renderHeader("home");
renderFooter();
document.getElementById("search-icon").innerHTML = ICON_SEARCH;

let tutti = [];
let teamAttivi = new Set();

function disegna() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const lista = tutti.filter((p) =>
    (teamAttivi.size === 0 || teamAttivi.has(p.team)) &&
    (!q || (p.nome || "").toLowerCase().includes(q) || String(p.numero).includes(q) || (p.team || "").toLowerCase().includes(q)));
  document.getElementById("result-count").textContent = `(${lista.length})`;
  document.getElementById("piloti-grid").innerHTML = lista.length ? lista.map((p) => `
    <a class="driver-card" href="confronto.html?a=${p.numero}" style="--team:#${esc(p.colore || "6b6b78")}">
      <div class="driver-card-image"><span class="driver-number">${esc(p.numero)}</span></div>
      <div class="driver-card-info">
        <div class="name">${esc(p.nome || "Pilota #" + p.numero)}</div>
        <div class="numero">${p.posizione ? p.posizione + "° · " : ""}${p.punti != null ? p.punti + " pt" : "punti n.d."}</div>
        <div class="team">${esc(p.team || "Team n.d.")}</div>
      </div>
    </a>`).join("") : `<p class="muted" style="grid-column:1/-1">Nessun pilota trovato.</p>`;
}

try {
  const [roster, eventi, standings] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json"), fetchJSON("data/standings.json")]);
  tutti = roster;

  const teams = [...new Set(roster.map((p) => p.team).filter(Boolean))].sort();
  document.getElementById("stat-piloti").textContent = roster.length;
  document.getElementById("stat-team").textContent = teams.length;
  document.getElementById("stat-gare").textContent = eventi.length;
  document.getElementById("riassunto-nota").textContent = standings.dopo ? `Classifica dopo: ${standings.dopo}` : "";

  document.getElementById("category-pills").innerHTML = teams.map((t) => `<button class="pill" data-team="${esc(t)}">${esc(t)}</button>`).join("");
  document.getElementById("category-pills").addEventListener("click", (e) => {
    const b = e.target.closest(".pill");
    if (!b) return;
    teamAttivi.has(b.dataset.team) ? teamAttivi.delete(b.dataset.team) : teamAttivi.add(b.dataset.team);
    b.classList.toggle("active");
    disegna();
  });
  document.getElementById("search").addEventListener("input", disegna);

  const ora = new Date();
  const prossimi = eventi.filter((g) => new Date(g.fine) > ora).slice(0, 3);
  document.getElementById("prossimi-mini").innerHTML = prossimi.length ? prossimi.map((g) => `
    <a class="evento-widget-mini" href="gara.html?id=${g.id}" style="display:block">
      <div class="evento-widget-mini-nome">${esc(g.nome)}</div>
      <div class="evento-widget-mini-data">${esc(g.circuito)} · ${intervalloWeekend(g)}</div>
    </a>`).join("") : `<p class="muted" style="font-size:12px">Nessun weekend in programma.</p>`;

  disegna();
} catch (e) {
  erroreCaricamento(document.getElementById("piloti-grid"));
}
