import { renderHeader, renderFooter, fetchJSON, esc, img, credito, intervalloWeekend, formattaDataOra, punti, stemma, mischia, erroreCaricamento } from "./common.js";
import { montaPronostico, colonnaF1 } from "./prono.js";

renderHeader("f1");
renderFooter();
const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";

const conto = (diff) => {
  const g = Math.floor(diff / 864e5), h = Math.floor(diff / 36e5) % 24, m = Math.floor(diff / 6e4) % 60, s = Math.floor(diff / 1e3) % 60, d = (n) => String(n).padStart(2, "0");
  return g > 0 ? `${g}g ${d(h)}h ${d(m)}m ${d(s)}s` : `${d(h)}h ${d(m)}m ${d(s)}s`;
};

function card(g, passata, prossima) {
  const sprint = g.sessioni.some((s) => s.tipo === "Sprint");
  return `<a class="event-card ${passata ? "passata" : "prossima"}" href="gara.html?id=${g.id}${tema}">
    <div class="event-map">${g.mappa ? img(g.mappa, "Tracciato di " + g.circuito) : `<span class="senza-mappa">${esc(g.circuito)}</span>`}</div>
    <div class="event-body">
      <div class="event-date">${intervalloWeekend(g)}</div>
      <div class="event-name">${esc(g.nome)}</div>
      <div class="event-location">${esc(g.circuito)}, ${esc(g.paese)}</div>
      <span class="event-status ${passata ? "passato" : ""}">${passata ? "Vai ai risultati →" : prossima ? (sprint ? "Prossima · weekend con sprint" : "Prossima gara") : "In programma"}</span>
    </div>
  </a>`;
}

try {
  const sicuro = (p) => p.catch(() => null);
  const [roster, eventi, standings, prono, ras, report] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json"), fetchJSON("data/standings.json"),
    sicuro(fetchJSON("data/pronostici.json")), sicuro(fetchJSON("data/rassegna.json")), sicuro(fetchJSON("data/report.json"))]);
  const ora = new Date();
  // testata: prossimo GP con la foto del leader
  const sessioni = eventi.flatMap((g) => g.sessioni.map((s) => ({ ...s, gp: g }))).filter((s) => new Date(s.fine) > ora).sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  const el = document.getElementById("pross-f1");
  const leader = roster.find((p) => p.posizione === 1 && p.foto) || roster.find((p) => p.foto);
  if (sessioni[0]) {
    const { gp, ...s } = sessioni[0];
    el.href = `gara.html?id=${gp.id}${tema}`;
    const f = leader && leader.foto && (leader.foto.file_grande || leader.foto.file);
    if (f) el.style.setProperty("--foto", `url("${new URL(f, document.baseURI).href}")`);
    el.innerHTML = `<span class="cd-sigla">F1</span><span class="hero2-kicker">Prossimo GP</span><strong class="pross-gp">${esc(gp.nome)}</strong><span class="pross-circ">${esc(gp.circuito)}, ${esc(gp.paese)}</span>
      <span class="pross-sess">${esc(s.nome)} · ${formattaDataOra(s.inizio)}</span><span class="pross-timer cd-tempo"></span>
      ${prono && prono.f1 ? `<span class="hero2-fav">Favorito: <b>${esc(prono.f1.favoriti[0].nome)}</b></span>` : ""}${leader && leader.foto ? `<span class="hero2-credito">${credito(leader.foto)}</span>` : ""}`;
    const t = el.querySelector(".pross-timer");
    const tick = () => { const d = new Date(s.inizio) - Date.now(); t.textContent = d > 0 ? conto(d) : "In corso"; };
    tick(); setInterval(tick, 1000);
  } else el.innerHTML = `<span class="cd-sigla">F1</span><span class="hero2-kicker">Stagione conclusa</span>`;

  if (prono && prono.f1) {
    montaPronostico(document.getElementById("prono-griglia"), [colonnaF1(prono, roster)]);
    document.getElementById("prono-nota").textContent = prono.metodo;
    document.getElementById("prono").hidden = false;
  }

  // gare: la prossima e le già disputate (le altre future stanno nel calendario)
  const prossime = eventi.filter((g) => new Date(g.fine) > ora), passate = eventi.filter((g) => new Date(g.fine) <= ora).reverse();
  document.getElementById("gare-f1").innerHTML = (prossime[0] ? `<h4 class="gare-sottotitolo prossima">Prossima gara</h4><div class="gare-grid">${card(prossime[0], false, true)}</div>` : "")
    + (passate.length ? `<h4 class="gare-sottotitolo">Gare già disputate</h4><div class="gare-grid">${passate.map((g) => card(g, true)).join("")}</div>` : "");
  document.getElementById("report-f1").innerHTML = (report || []).slice(0, 2).map((r) => `<article class="report-card"><div class="report-data">${esc(r.circuito)}, ${esc(r.paese)}</div><h3><a href="gara.html?id=${r.id}${tema}">${esc(r.titolo)}</a></h3>${r.paragrafi.map((p) => `<p>${esc(p)}</p>`).join("")}<a class="accent" href="gara.html?id=${r.id}${tema}">Vai ai risultati →</a></article>`).join("") || `<p class="muted">Nessuna gara ancora disputata.</p>`;

  const foto = Object.fromEntries(roster.filter((p) => p.foto).map((p) => [p.numero, p.foto]));
  document.getElementById("f1-nota").textContent = standings.dopo ? `Dopo il ${standings.dopo}` : "";
  document.getElementById("top-classifica").innerHTML = `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead><tbody>${standings.piloti.slice(0, 10).map((p) => `<tr class="${p.posizione <= 3 ? "podio" : ""}"><td>${p.posizione}</td>
    <td><a class="cella-pilota" href="pilota.html?n=${p.numero}${tema}">${foto[p.numero] ? img(foto[p.numero], p.nome || "", "foto-mini") : '<span class="foto-mini"></span>'}<strong>${esc(p.nome || "Pilota #" + p.numero)}</strong></a></td>
    <td><span class="cella-team">${stemma(p.team, p.colore)}${esc(p.team || "")}</span></td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")}</tbody></table></div>`;
  document.getElementById("mini-costruttori").innerHTML = standings.costruttori.slice(0, 5).map((c) => `<li><a href="classifiche.html?serie=f1${tema}"><span class="pos">${c.posizione}</span>${stemma(c.team, c.colore)}<span>${esc(c.team)}</span><span class="pt">${punti(c.punti)}</span></a></li>`).join("");
  document.getElementById("notizie-f1").innerHTML = ras ? ras.articoli.filter((a) => a.serie === "F1").slice(0, 5).map((a) => `<a class="evento-widget-mini" href="${esc(a.url)}" target="_blank" rel="noopener nofollow"><div><div class="evento-widget-mini-nome">${esc(a.titolo)}</div><div class="evento-widget-mini-data">${esc(a.fonte)}</div></div></a>`).join("") : "";
} catch (e) {
  erroreCaricamento(document.getElementById("gare-f1"));
}
