import { renderHeader, renderFooter, fetchJSON, esc, stemma, formattaData, formattaDataOra, punti, erroreCaricamento, img, credito, fotoMotoMap, mappeMotoMap } from "./common.js";

renderHeader("motogp");
renderFooter();

const box = document.getElementById("moto-box");
const FM = await fotoMotoMap();
const MAPPE = await mappeMotoMap();
const dataIt = (iso) => new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short", timeZone: "Europe/Rome" });

let classifica = null, ultima = null, cat = "MotoGP";
const idDa = (nome) => (classifica.categorie[cat].find((p) => p.nome === nome) || {}).id;
const nomeLink = (nome, id) => {
  const f = FM["nome:" + nome], mini = f ? img(f, nome, "foto-mini") : '<span class="foto-mini"></span>';
  const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";
  return id ? `<a class="cella-pilota" href="pilota-moto.html?id=${esc(id)}${tema}">${mini}<strong>${esc(nome)}</strong></a>` : `<span class="cella-pilota">${mini}<strong>${esc(nome)}</strong></span>`;
};

function tabellaGara(ris) {
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Moto</th><th>Distacco</th><th>Punti</th></tr></thead><tbody>${ris.slice(0, 15).map((r) => `<tr class="${r.pos && r.pos <= 3 ? "podio" : ""}">
    <td>${r.pos ?? esc(r.stato || "–")}</td><td>${nomeLink(r.nome, idDa(r.nome))} <span class="muted">#${r.numero ?? ""}</span></td>
    <td><span class="cella-team">${stemma(r.moto)}${esc(r.moto)}</span></td><td>${r.pos === 1 ? esc(r.tempo || "") : r.distacco && r.distacco !== "0.000" ? "+" + esc(r.distacco) : "–"}</td><td>${r.punti ?? "–"}</td></tr>`).join("")}</tbody></table></div>`;
}

function tabellaClassifica(pil) {
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Moto</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${pil.slice(0, 20).map((p) => `<tr class="${p.pos <= 3 ? "podio" : ""}">
    <td>${p.pos}</td><td>${nomeLink(p.nome, p.id)} <span class="muted">#${p.numero ?? ""}</span></td><td><span class="cella-team">${stemma(p.moto)}${esc(p.moto)}</span></td><td><strong>${punti(p.punti)}</strong></td><td>${p.vittorie}</td></tr>`).join("")}</tbody></table></div>`;
}

function disegnaCategoria() {
  document.querySelectorAll("#m-cat .pill").forEach((b) => b.classList.toggle("active", b.dataset.c === cat));
  const u = ultima.categorie && ultima.categorie[cat];
  document.getElementById("m-ultima-nome").textContent = u ? `· ${u.nome}` : "";
  document.getElementById("m-ultima").innerHTML = u ? tabellaGara(u.risultati) : `<p class="muted">Risultati non disponibili.</p>`;
  const pil = classifica.categorie[cat] || [];
  document.getElementById("m-classifica").innerHTML = pil.length ? tabellaClassifica(pil) : `<p class="muted">Classifica non disponibile.</p>`;
}

try {
  const [calendario, cl, ul] = await Promise.all([fetchJSON("data/motogp.json"), fetchJSON("data/motogp-classifica.json"), fetchJSON("data/motogp-ultima.json")]);
  classifica = cl; ultima = ul;
  const weekend = calendario.weekend;
  const w = weekend[0];
  document.getElementById("m-prossimo").innerHTML = w ? `<article class="moto-prossimo"><span class="kicker">Prossimo weekend</span><h2>${esc(w.nome)}</h2>
      <p class="muted" style="margin:0 0 14px">${esc(w.circuito)} · ${esc(w.paese)} · ora italiana · programma della classe MotoGP</p>
      ${MAPPE[w.circuito] ? `<div class="mappa-circuito">${img(MAPPE[w.circuito], "Tracciato di " + w.circuito)}<p class="credito">${credito(MAPPE[w.circuito], "Mappa")}</p></div>` : ""}
      <div class="moto-sessioni">${w.sessioni.map((s) => `<div class="moto-sess"><b>${esc(s.nome)}</b><span>${formattaDataOra(s.inizio)}</span></div>`).join("")}</div></article>` : `<p class="muted">Nessun weekend in programma.</p>`;
  document.getElementById("m-agg").textContent = `Dati aggiornati al ${new Date(calendario.generato_il).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" })}`;
  document.getElementById("m-cat").addEventListener("click", (e) => { const b = e.target.closest(".pill"); if (b) { cat = b.dataset.c; disegnaCategoria(); } });
  disegnaCategoria();
  try {
    const rep = await fetchJSON("data/motogp-report.json");
    document.getElementById("m-report").innerHTML = rep.slice(0, 1).map((r) => `<article class="report-card"><div class="report-data">${dataIt(r.data)} · ${esc(r.circuito || "")}</div>
      <h3>${esc(r.titolo)}</h3>${r.paragrafi.map((p) => `<p>${esc(p)}</p>`).join("")}</article>`).join("") || `<p class="muted">Nessuna gara ancora disputata.</p>`;
  } catch (e) {}
  document.getElementById("m-calendario").innerHTML = `<div class="report-lista">${weekend.map((g) => {
    const gara = g.sessioni.find((s) => s.codice === "RAC") || g.sessioni[g.sessioni.length - 1];
    return `<article class="report-card"><div class="report-data">${dataIt(g.sessioni[0].inizio)} – ${dataIt(gara.inizio)}</div><h3 style="margin:6px 0 4px">${esc(g.nome)}</h3>${MAPPE[g.circuito] ? img(MAPPE[g.circuito], "Tracciato di " + g.circuito, "mappa-mini") : ""}
      <p style="margin:0">${esc(g.circuito)}<br><b>Gara MotoGP: ${formattaDataOra(gara.inizio)}</b></p></article>`;
  }).join("")}</div>`;
} catch (e) {
  erroreCaricamento(box);
}
