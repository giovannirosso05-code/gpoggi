import { intervalloWeekend, iniz, renderHeader, renderFooter, fetchJSON, esc, stemma, stemmaMoto, formattaData, formattaDataOra, punti, erroreCaricamento, img, credito, fotoMotoMap, mappeMotoMap } from "./common.js";

import { montaPronostico, colonnaMoto } from "./prono.js";

renderHeader("motogp");
renderFooter();

const box = document.getElementById("moto-box");
const FM = await fotoMotoMap();
const MAPPE = await mappeMotoMap();
const dataIt = (iso) => new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short", timeZone: "Europe/Rome" });

let classifica = null, ultima = null, cat = "MotoGP";
const idDa = (nome) => (classifica.categorie[cat].find((p) => p.nome === nome) || {}).id;
const nomeLink = (nome, id) => {
  const f = FM["nome:" + nome], mini = f ? img(f, nome, "foto-mini") : iniz(nome);
  const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";
  return id ? `<a class="cella-pilota" href="pilota-moto.html?id=${esc(id)}${tema}">${mini}<strong>${esc(nome)}</strong></a>` : `<span class="cella-pilota">${mini}<strong>${esc(nome)}</strong></span>`;
};

function tabellaGara(ris) {
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Moto</th><th>Distacco</th><th>Punti</th></tr></thead><tbody>${ris.slice(0, 15).map((r) => `<tr class="${r.pos && r.pos <= 3 ? "podio" : ""}">
    <td>${r.pos ?? esc(r.stato || "–")}</td><td>${nomeLink(r.nome, idDa(r.nome))}</td>
    <td><span class="cella-team">${stemmaMoto(r.moto)}${esc(r.moto)}</span></td><td>${r.pos === 1 ? esc(r.tempo || "") : r.distacco && r.distacco !== "0.000" ? "+" + esc(r.distacco) : "–"}</td><td>${r.punti ?? "–"}</td></tr>`).join("")}</tbody></table></div>`;
}

function tabellaClassifica(pil) {
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead><tbody>${pil.slice(0, 20).map((p) => `<tr class="${p.pos <= 3 ? "podio" : ""}">
    <td>${p.pos}</td><td>${nomeLink(p.nome, p.id)}</td><td><span class="cella-team">${stemmaMoto(p.moto)}${esc(p.team)}</span></td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")}</tbody></table></div>`;
}

function disegnaCategoria() {
  document.querySelectorAll("#m-cat .pill").forEach((b) => b.classList.toggle("active", b.dataset.c === cat));
  const pil = classifica.categorie[cat] || [];
  document.getElementById("m-classifica").innerHTML = pil.length ? tabellaClassifica(pil) : `<p class="muted">Classifica non disponibile.</p>`;
  const squadre = {};
  pil.forEach((p) => { const t = (squadre[p.team] ||= { team: p.team, moto: p.moto, punti: 0 }); t.punti += p.punti; });
  document.getElementById("m-team").innerHTML = Object.values(squadre).sort((a, b) => b.punti - a.punti).slice(0, 5).map((t, i) => `<li><a href="classifiche.html?serie=${cat.toLowerCase()}"><span class="pos">${i + 1}</span>${stemmaMoto(t.moto)}<span>${esc(t.team)}</span><span class="pt">${punti(t.punti)}</span></a></li>`).join("");
}

try {
  const [calendario, cl, ul] = await Promise.all([fetchJSON("data/motogp.json"), fetchJSON("data/motogp-classifica.json"), fetchJSON("data/motogp-ultima.json")]);
  classifica = cl; ultima = ul;
  const weekend = calendario.weekend;
  const w = weekend[0];
  document.getElementById("m-agg").textContent = `Dati aggiornati al ${new Date(calendario.generato_il).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" })}`;
  document.getElementById("m-cat").addEventListener("click", (e) => { const b = e.target.closest(".pill"); if (b) { cat = b.dataset.c; disegnaCategoria(); } });
  disegnaCategoria();
  try {
    const rep = await fetchJSON("data/motogp-report.json");
    document.getElementById("m-report").innerHTML = rep.slice(0, 1).map((r) => `<article class="report-card"><div class="report-data">${dataIt(r.data)} · ${esc(r.circuito || "")}</div>
      <h3><a href="gara-moto.html?gp=${encodeURIComponent(r.gp)}">${esc(r.titolo)}</a></h3>${r.paragrafi.map((p) => `<p>${esc(p)}</p>`).join("")}<a class="accent" href="gara-moto.html?gp=${encodeURIComponent(r.gp)}">Vai ai risultati →</a></article>`).join("") || `<p class="muted">Nessuna gara ancora disputata.</p>`;
  } catch (e) {}
  // testata: prossimo GP con la foto del leader della classifica
  const ora = new Date();
  const sess = weekend.flatMap((g) => g.sessioni.map((s) => ({ ...s, g }))).filter((s) => new Date(s.fine) > ora).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
  const prono = await fetchJSON("data/pronostici.json").catch(() => null);
  const el = document.getElementById("pross-moto");
  if (sess) el.href = `gara-moto.html?gp=${encodeURIComponent(sess.g.nome)}${document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : ""}`;
  const leader = ((cl.categorie || {}).MotoGP || [])[0], fl = leader && FM["nome:" + leader.nome];
  if (sess) {
    const f = fl && (fl.file_grande || fl.file);
    if (f) el.style.setProperty("--foto", `url("${new URL(f, document.baseURI).href}")`);
    const conto = (d) => { const g = Math.floor(d / 864e5), h = Math.floor(d / 36e5) % 24, mi = Math.floor(d / 6e4) % 60, s = Math.floor(d / 1e3) % 60, p = (n) => String(n).padStart(2, "0"); return g > 0 ? `${g}g ${p(h)}h ${p(mi)}m ${p(s)}s` : `${p(h)}h ${p(mi)}m ${p(s)}s`; };
    el.innerHTML = `<span class="cd-sigla moto">MotoGP</span><span class="hero2-kicker">Prossimo GP</span><strong class="pross-gp">${esc(sess.g.nome)}</strong><span class="pross-circ">${esc(sess.g.circuito)}</span>
      <span class="pross-sess">${esc(sess.nome)} · ${formattaDataOra(sess.inizio)}</span><span class="pross-timer cd-tempo"></span>
      ${prono && prono.motogp ? `<span class="hero2-fav">Favorito: <b>${esc(prono.motogp.favoriti[0].nome)}</b></span>` : ""}${fl ? `<span class="hero2-credito">${credito(fl)}</span>` : ""}`;
    const t = el.querySelector(".pross-timer");
    const tick = () => { const d = new Date(sess.inizio) - Date.now(); t.textContent = d > 0 ? conto(d) : "In corso"; };
    tick(); setInterval(tick, 1000);
  }
  if (prono && prono.motogp) {
    montaPronostico(document.getElementById("prono-griglia"), [colonnaMoto(prono, cl, FM)]);
    document.getElementById("prono-nota").textContent = prono.metodo;
    document.getElementById("prono").hidden = false;
  }
  // gare: la prossima e le già disputate
  const gareMoto = await fetchJSON("data/motogp-gare.json").catch(() => ({}));
  const cardMoto = (nome, circuito, quando, passata) => `<a class="event-card ${passata ? "passata" : "prossima"}" href="gara-moto.html?gp=${encodeURIComponent(nome)}">
    <div class="event-map">${MAPPE[circuito] ? img(MAPPE[circuito], "Tracciato di " + circuito) : `<span class="senza-mappa">${esc(circuito || "")}</span>`}</div>
    <div class="event-body"><div class="event-date">${quando}</div><div class="event-name">${esc(nome)}</div><div class="event-location">${esc(circuito || "")}</div>
    <span class="event-status ${passata ? "passato" : ""}">${passata ? "Vai ai risultati →" : "Programma e orari →"}</span></div></a>`;
  const passateM = Object.values(gareMoto).sort((a, b) => b.data.localeCompare(a.data));
  const prossimo = weekend[0];
  document.getElementById("gare-moto").innerHTML = (prossimo ? `<h4 class="gare-sottotitolo prossima">Prossima gara</h4><div class="gare-grid">` + cardMoto(prossimo.nome, prossimo.circuito, `${dataIt(prossimo.sessioni[0].inizio)} – ${dataIt((prossimo.sessioni.find((s) => s.codice === "RAC") || prossimo.sessioni[prossimo.sessioni.length - 1]).inizio)}`, false) + `</div>` : "")
    + (passateM.length ? `<h4 class="gare-sottotitolo">Gare già disputate</h4><div class="gare-grid">` + passateM.map((g) => cardMoto(g.nome, g.circuito, (g.inizio ? intervalloWeekend({ inizio: g.inizio + "T00:00:00Z", fine: g.data + "T12:00:00Z" }) : new Date(g.data).toLocaleDateString("it-IT", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })), true)).join("") + `</div>` : "");
  const ras = await fetchJSON("data/rassegna.json").catch(() => null);
  document.getElementById("m-notizie").innerHTML = ras ? ras.articoli.filter((a) => a.serie === "MotoGP").slice(0, 5).map((a) => `<a class="evento-widget-mini" href="${esc(a.url)}" target="_blank" rel="noopener nofollow"><div><div class="evento-widget-mini-nome">${esc(a.titolo)}</div><div class="evento-widget-mini-data">${esc(a.fonte)}</div></div></a>`).join("") : "";
} catch (e) {
  erroreCaricamento(box);
}
