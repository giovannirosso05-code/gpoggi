import { renderHeader, renderFooter, fetchJSON, esc, intervalloWeekend, formattaDataOra, ICON_SEARCH, erroreCaricamento } from "./common.js";

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
    <a class="driver-card" href="pilota.html?n=${p.numero}" style="--team:#${esc(p.colore || "6b6b78")}">
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

  mostraProssimaSessione(eventi);
  disegna();
} catch (e) {
  erroreCaricamento(document.getElementById("piloti-grid"));
}

function mostraProssimaSessione(eventi) {
  const ora = Date.now();
  const prossime = eventi.flatMap((g) => g.sessioni.map((s) => ({ ...s, gp: g })))
    .filter((s) => new Date(s.fine).getTime() > ora)
    .sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  const s = prossime[0];
  if (!s) return;
  const box = document.getElementById("prossima-sessione");
  box.hidden = false;
  document.getElementById("ps-nome").textContent = s.nome;
  document.getElementById("ps-gp").innerHTML = `<a href="gara.html?id=${s.gp.id}">${esc(s.gp.nome)}</a> · ${esc(s.gp.circuito)}`;
  document.getElementById("ps-ora").textContent = formattaDataOra(s.inizio) + " (ora locale)";
  const inizio = new Date(s.inizio).getTime();
  const tick = () => {
    const diff = inizio - Date.now();
    if (diff <= 0) {
      document.getElementById("ps-countdown").textContent = Date.now() < new Date(s.fine).getTime() ? "In corso" : "Conclusa";
      return;
    }
    const g = Math.floor(diff / 864e5), h = Math.floor(diff / 36e5) % 24, m = Math.floor(diff / 6e4) % 60, sec = Math.floor(diff / 1e3) % 60;
    document.getElementById("ps-countdown").textContent = (g ? `${g}g ` : "") + `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
    setTimeout(tick, 1000);
  };
  tick();
}
