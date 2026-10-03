import { renderHeader, renderFooter, fetchJSON, esc, img, punti, ICON_SEARCH, erroreCaricamento } from "./common.js";

renderHeader("piloti");
renderFooter();
document.getElementById("search-icon").innerHTML = ICON_SEARCH;

let tutti = [];
const teamAttivi = new Set();

function card(p) {
  const nome = p.nome || "Pilota #" + p.numero;
  return `<a class="driver-card" href="pilota.html?n=${p.numero}" style="--team:#${esc(p.colore || "8b8a92")}">
    <div class="driver-card-image">
      ${img(p.foto, nome)}
      ${p.posizione ? `<span class="pos-badge">${p.posizione}°</span>` : ""}
      <span class="driver-number ${p.foto ? "" : "solo"}">${p.numero}</span>
    </div>
    <div class="driver-card-info">
      <div class="name">${esc(nome)}</div>
      <div class="team">${esc(p.team || "Team n.d.")}</div>
      <div class="numero"><b>${p.punti != null ? punti(p.punti) : "n.d."}</b> punti</div>
    </div>
  </a>`;
}

function disegna() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const lista = tutti.filter((p) =>
    (teamAttivi.size === 0 || teamAttivi.has(p.team)) &&
    (!q || (p.nome || "").toLowerCase().includes(q) || String(p.numero).includes(q) || (p.team || "").toLowerCase().includes(q)));
  document.getElementById("result-count").textContent = `(${lista.length})`;
  document.getElementById("piloti-grid").innerHTML = lista.length ? lista.map(card).join("") : `<p class="muted" style="grid-column:1/-1">Nessun pilota trovato.</p>`;
}

try {
  const roster = await fetchJSON("data/roster.json");
  tutti = roster;

  const teams = [...new Set(roster.map((p) => p.team).filter(Boolean))].sort();
  const pills = document.getElementById("category-pills");
  pills.innerHTML = teams.map((t) => `<button class="pill" data-team="${esc(t)}">${esc(t)}</button>`).join("");
  pills.addEventListener("click", (e) => {
    const b = e.target.closest(".pill");
    if (!b) return;
    teamAttivi.has(b.dataset.team) ? teamAttivi.delete(b.dataset.team) : teamAttivi.add(b.dataset.team);
    b.classList.toggle("active");
    disegna();
  });
  document.getElementById("search").addEventListener("input", disegna);
  disegna();
} catch (e) {
  erroreCaricamento(document.getElementById("piloti-grid"));
}
