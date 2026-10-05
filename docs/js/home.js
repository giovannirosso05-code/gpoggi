import { iniz, renderHeader, renderFooter, fetchJSON, esc, img, credito, intervalloWeekend, formattaDataOra, punti, stemma, stemmaMoto, coloreMoto, ND, mischia, fotoMotoMap, mappeMotoMap } from "./common.js";

import { montaPronostico, colonnaF1, colonnaMoto } from "./prono.js";

renderHeader("home");
renderFooter();

const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";

// ---- Prossimo GP: due riquadri, F1 a sinistra e MotoGP a destra, ciascuno con il suo timer
function prossimaSessione(weekend) {
  const ora = Date.now();
  for (const g of weekend) {
    const s = g.sessioni.filter((x) => new Date(x.fine).getTime() > ora).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
    if (s) return { g, s };
  }
  return null;
}
const conto = (diff) => {
  const g = Math.floor(diff / 864e5), h = Math.floor(diff / 36e5) % 24, m = Math.floor(diff / 6e4) % 60, s = Math.floor(diff / 1e3) % 60, d = (n) => String(n).padStart(2, "0");
  return g > 0 ? `${g}g ${d(h)}h ${d(m)}m ${d(s)}s` : `${d(h)}h ${d(m)}m ${d(s)}s`;
};
const timer = [];
function riquadro(id, sigla, classe, trovata, link, foto, favorito) {
  const el = document.getElementById(id);
  if (!trovata) { el.innerHTML = `<span class="cd-sigla ${classe}">${sigla}</span><span class="muted">Nessun weekend in programma</span>`; return; }
  const { g, s } = trovata;
  el.href = link(g);
  const f = foto && (foto.file_grande || foto.grande || foto.file || foto.url);
  if (f) el.style.setProperty("--foto", `url("${new URL(f, document.baseURI).href}")`);
  el.innerHTML = `<span class="cd-sigla ${classe}">${sigla}</span>
    <span class="hero2-kicker">Prossimo GP</span>
    <strong class="pross-gp">${esc(g.nome)}</strong>
    <span class="pross-circ">${esc(g.circuito)}</span>
    <span class="pross-sess">${esc(s.nome)} · ${formattaDataOra(s.inizio)}</span>
    <span class="pross-timer cd-tempo"></span>
    ${favorito ? `<span class="hero2-fav">Favorito: <b>${esc(favorito)}</b></span>` : ""}
    ${foto ? `<span class="hero2-credito">${credito(foto)}</span>` : ""}`;
  const t = el.querySelector(".pross-timer");
  timer.push(() => {
    const diff = new Date(s.inizio).getTime() - Date.now();
    t.textContent = diff > 0 ? conto(diff) : "In corso";
    t.classList.toggle("live", diff <= 0);
  });
}
setInterval(() => timer.forEach((f) => f()), 1000);

// ---- Ultima gara
const coloreTeam = {};
function podioF1(g, foto) {
  const sess = [...g.sessioni].reverse().find((s) => s.tipo === "Race" && s.risultati && s.risultati.length);
  if (!sess) return "";
  const top = sess.risultati.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos);
  return blocco("F1", "", g.nome, `${g.circuito}, ${g.paese}`, `gara.html?id=${g.id}${tema}`, top.map((r) => `<a href="pilota.html?n=${r.numero}${tema}" style="--team:#${esc(coloreTeam[r.team] || "8b8a92")}">
      <div class="posto">${r.pos}°</div>${foto[r.numero] ? img(foto[r.numero], r.nome || "") : '<span class="vuota"></span>'}
      <strong>${esc(r.nome || "Pilota #" + r.numero)}</strong><div>${stemma(r.team, coloreTeam[r.team])}</div><div class="tempo">${r.tempo ? esc(r.tempo) : ND}</div></a>`).join(""));
}
const FM = await fotoMotoMap();
function podioMoto(u) {
  const top = u.risultati.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos);
  return blocco("MotoGP", "moto", u.nome, u.circuito, `gara-moto.html?gp=${encodeURIComponent(u.nome)}${tema}`, top.map((r) => `<a href="gara-moto.html?gp=${encodeURIComponent(u.nome)}${tema}" style="--team:#${esc(coloreMoto(r.moto) || "8b8a92")}">
      <div class="posto">${r.pos}°</div>${FM["nome:" + r.nome] ? img(FM["nome:" + r.nome], r.nome) : '<span class="vuota"></span>'}
      <strong>${esc(r.nome)}</strong><div>${stemmaMoto(r.moto)}</div><div class="tempo">${r.tempo ? esc(r.tempo) : ND}</div></a>`).join(""));
}
function blocco(sigla, classe, nome, sotto, link, podio) {
  return `<div class="ultima-gara serie-${classe || "f1"}">
    <div class="ultima-gara-testa"><div><span class="cd-sigla ${classe}">${sigla}</span><h3>${esc(nome)}</h3></div>
      <div class="muted">${esc(sotto)} · <a href="${link}" class="accent">Risultati</a></div></div>
    <div class="podio-home">${podio}</div>
    <a class="guarda-gara" href="${link}">Guarda il resto della gara →</a></div>`;
}

// ---- Classifica con scelta F1 / MotoGP
const classifica = {};
function tabellaF1() {
  const { standings: s, foto } = classifica;
  document.getElementById("riassunto-nota").textContent = s.dopo ? `Dopo il ${s.dopo}` : "";
  return s.piloti.length ? `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead>
    <tbody>${s.piloti.slice(0, 10).map((p) => `<tr class="${p.posizione <= 3 ? "podio" : ""}"><td>${p.posizione}</td>
      <td><a class="cella-pilota" href="pilota.html?n=${p.numero}${tema}">${foto[p.numero] ? img(foto[p.numero], p.nome || "", "foto-mini") : '<span class="foto-mini"></span>'}<strong>${esc(p.nome || "Pilota #" + p.numero)}</strong></a></td>
      <td><span class="cella-team">${stemma(p.team, p.colore)}${esc(p.team || "")}</span></td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">Classifica non ancora disponibile.</p>`;
}
function tabellaMoto() {
  const c = classifica.moto;
  document.getElementById("riassunto-nota").textContent = "Classe MotoGP";
  const lista = (c.categorie || {}).MotoGP || c.piloti || [];
  return lista.length ? `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead>
    <tbody>${lista.slice(0, 10).map((p) => `<tr class="${p.pos <= 3 ? "podio" : ""}"><td>${p.pos}</td>
      <td><a class="cella-pilota" href="pilota-moto.html?id=${esc(p.id)}${tema}">${FM["nome:" + p.nome] ? img(FM["nome:" + p.nome], p.nome, "foto-mini") : iniz(p.nome)}<strong>${esc(p.nome)}</strong></a></td>
      <td><span class="cella-team">${stemmaMoto(p.moto)}${esc(p.team)}</span></td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">Classifica non disponibile.</p>`;
}
function mostraClassifica(k) {
  document.querySelectorAll("#home-serie .pill").forEach((b) => b.classList.toggle("active", b.dataset.s === k));
  document.getElementById("top-classifica").innerHTML = k === "f1" ? tabellaF1() : tabellaMoto();
  document.getElementById("home-tutte").href = `classifiche.html?serie=${k}${tema}`;
}

const sicuro = (p) => p.catch(() => null);
const [roster, eventi, standings, cal, clMoto, ultMoto, ras] = await Promise.all([
  sicuro(fetchJSON("data/roster.json")), sicuro(fetchJSON("data/events.json")), sicuro(fetchJSON("data/standings.json")),
  sicuro(fetchJSON("data/motogp.json")), sicuro(fetchJSON("data/motogp-classifica.json")), sicuro(fetchJSON("data/motogp-ultima.json")), sicuro(fetchJSON("data/rassegna.json"))]);

const prono = await fetchJSON("data/pronostici.json").catch(() => null);
const leaderF1 = (roster || []).find((p) => p.posizione === 1 && p.foto) || (roster || []).find((p) => p.foto);
const leaderMoto = ((clMoto && (clMoto.categorie || {}).MotoGP) || [])[0];
riquadro("pross-f1", "F1", "", eventi && prossimaSessione(eventi), (g) => `gara.html?id=${g.id}${tema}`, leaderF1 && leaderF1.foto, prono && prono.f1 && prono.f1.favoriti[0].nome);
riquadro("pross-moto", "MotoGP", "moto", cal && prossimaSessione(cal.weekend), (g) => `gara-moto.html?gp=${encodeURIComponent(g.nome)}${tema}`, leaderMoto && FM["nome:" + leaderMoto.nome], prono && prono.motogp && prono.motogp.favoriti[0].nome);
timer.forEach((f) => f());

if (standings) standings.costruttori.forEach((c) => (coloreTeam[c.team] = c.colore));
const foto = Object.fromEntries((roster || []).filter((p) => p.foto).map((p) => [p.numero, p.foto]));
const ultime = document.getElementById("ultime-gare");
let html = "";
if (eventi) {
  const passati = eventi.filter((g) => new Date(g.fine) < new Date()).reverse();
  for (const ev of passati.slice(0, 3)) {
    try { const h = podioF1(await fetchJSON(`data/gare/${ev.id}.json`), foto); if (h) { html += h; break; } } catch (e) {}
  }
}
if (ultMoto && ultMoto.risultati) html += podioMoto(ultMoto);
ultime.innerHTML = html || `<p class="muted">Nessuna gara ancora disputata.</p>`;

Object.assign(classifica, { standings, foto, moto: clMoto });
if (standings && clMoto) {
  mostraClassifica("f1");
  document.getElementById("home-serie").addEventListener("click", (e) => { const b = e.target.closest("[data-s]"); if (b) mostraClassifica(b.dataset.s); });
} else if (standings) { document.getElementById("home-serie").hidden = true; mostraClassifica("f1"); }

if (ras) {
  document.getElementById("ultime-notizie").innerHTML = mischia(ras.articoli, 5).map((a) => `
    <a class="evento-widget-mini" href="${esc(a.url)}" target="_blank" rel="noopener nofollow"><div>
      <div class="evento-widget-mini-nome">${esc(a.titolo)}</div>
      <div class="evento-widget-mini-data"><b>${esc(a.serie || "")}</b> · ${esc(a.fonte)}</div></div></a>`).join("");
}

// prossimi weekend di entrambe le serie, in ordine di data
const prossimi = [...(eventi || []).filter((g) => new Date(g.fine) > new Date()).map((g) => ({ ...g, serie: "F1", link: `gara.html?id=${g.id}${tema}` })),
  ...((cal && cal.weekend) || []).filter((g) => new Date(g.fine || g.sessioni[g.sessioni.length - 1].fine) > new Date()).map((g) => ({ ...g, serie: "MotoGP", inizio: g.inizio || g.sessioni[0].inizio, fine: g.fine || g.sessioni[g.sessioni.length - 1].fine, link: `motogp.html${tema ? "?" + tema.slice(1) : ""}` }))]
  .sort((a, b) => new Date(a.inizio) - new Date(b.inizio)).slice(0, 5);
const MAPPE = await mappeMotoMap();
document.getElementById("prossimi-mini").innerHTML = prossimi.length ? prossimi.map((g) => `
  <a class="evento-widget-mini" href="${g.link}">
    ${g.serie === "F1" ? (g.mappa ? img(g.mappa, "Tracciato di " + g.circuito) : "") : (MAPPE[g.circuito] ? img(MAPPE[g.circuito], "Tracciato di " + g.circuito) : "")}
    <div><div class="evento-widget-mini-nome"><span class="cd-sigla ${g.serie === "MotoGP" ? "moto" : ""}">${g.serie}</span> ${esc(g.nome)}</div>
    <div class="evento-widget-mini-data">${esc(g.circuito)} · ${intervalloWeekend(g)}</div></div>
  </a>`).join("") : `<p class="muted" style="font-size:12px">Nessun weekend in programma.</p>`;

// ---- Pronostico: indice calcolato dai dati (forma, campionato, stesso circuito l'anno scorso) e voto dei visitatori
if (prono && (prono.f1 || prono.motogp)) {
  montaPronostico(document.getElementById("prono-griglia"), [colonnaF1(prono, roster), colonnaMoto(prono, clMoto, FM)]);
  document.getElementById("prono-nota").textContent = prono.metodo;
  document.getElementById("prono").hidden = false;
}
