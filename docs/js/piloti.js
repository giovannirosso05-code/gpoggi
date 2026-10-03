import { renderHeader, renderFooter, fetchJSON, esc, img, credito, intervalloWeekend, formattaDataOra, punti, ICON_SEARCH, erroreCaricamento } from "./common.js";

renderHeader("home");
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

function hero(eventi, roster) {
  const ora = Date.now();
  const sessioni = eventi.flatMap((g) => g.sessioni.map((s) => ({ ...s, gp: g })))
    .filter((s) => new Date(s.fine).getTime() > ora)
    .sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  const leader = roster.find((p) => p.posizione === 1 && p.foto) || roster.find((p) => p.foto);
  if (leader) {
    document.getElementById("hero").style.setProperty("--foto", `url("${new URL(leader.foto.file_grande || leader.foto.grande || leader.foto.file || leader.foto.url, document.baseURI).href}")`);
    document.getElementById("hero-credito").innerHTML = `${esc(leader.nome)} · ` + credito(leader.foto);
  }
  const s = sessioni[0];
  if (!s) {
    document.getElementById("hero-kicker").textContent = "Stagione conclusa";
    return;
  }
  document.getElementById("hero-kicker").textContent = s.nome;
  document.getElementById("hero-titolo").textContent = s.gp.nome;
  document.getElementById("hero-sotto").innerHTML = `${esc(s.gp.circuito)}, ${esc(s.gp.paese)} · ${formattaDataOra(s.inizio)} · <a href="gara.html?id=${s.gp.id}">Programma del weekend</a>`;
  const inizio = new Date(s.inizio).getTime();
  const box = document.getElementById("hero-countdown");
  const tick = () => {
    const diff = inizio - Date.now();
    if (diff <= 0) {
      box.innerHTML = `<div><b>${Date.now() < new Date(s.fine).getTime() ? "In corso" : "Conclusa"}</b><span>${esc(s.nome)}</span></div>`;
      return;
    }
    const parti = [[Math.floor(diff / 864e5), "giorni"], [Math.floor(diff / 36e5) % 24, "ore"], [Math.floor(diff / 6e4) % 60, "minuti"], [Math.floor(diff / 1e3) % 60, "secondi"]];
    box.innerHTML = parti.map(([v, l]) => `<div><b>${String(v).padStart(2, "0")}</b><span>${l}</span></div>`).join("");
    setTimeout(tick, 1000);
  };
  tick();
}

try {
  const [roster, eventi, standings] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json"), fetchJSON("data/standings.json")]);
  tutti = roster;
  hero(eventi, roster);

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

  document.getElementById("riassunto-nota").textContent = standings.dopo ? `Dopo il ${standings.dopo}` : "";
  document.getElementById("mini-classifica").innerHTML = roster.filter((p) => p.posizione).slice(0, 5).map((p) => `
    <li><a href="pilota.html?n=${p.numero}">
      <span class="pos">${p.posizione}</span>${p.foto ? img(p.foto, p.nome) : '<span class="vuota"></span>'}
      <span>${esc(p.nome || "Pilota #" + p.numero)}</span><span class="pt">${punti(p.punti)}</span>
    </a></li>`).join("");

  const ora = new Date();
  const prossimi = eventi.filter((g) => new Date(g.fine) > ora).slice(0, 3);
  document.getElementById("prossimi-mini").innerHTML = prossimi.length ? prossimi.map((g) => `
    <a class="evento-widget-mini" href="gara.html?id=${g.id}">
      ${g.mappa ? img(g.mappa, "Tracciato di " + g.circuito) : ""}
      <div><div class="evento-widget-mini-nome">${esc(g.nome)}</div>
      <div class="evento-widget-mini-data">${esc(g.circuito)} · ${intervalloWeekend(g)}</div></div>
    </a>`).join("") : `<p class="muted" style="font-size:12px">Nessun weekend in programma.</p>`;

  disegna();
} catch (e) {
  erroreCaricamento(document.getElementById("piloti-grid"));
}
