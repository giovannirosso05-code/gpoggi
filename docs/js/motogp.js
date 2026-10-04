import { renderHeader, renderFooter, fetchJSON, esc, stemma, formattaData, formattaDataOra, punti, erroreCaricamento } from "./common.js";

renderHeader("motogp");
renderFooter();

const box = document.getElementById("moto-box");
const dataIt = (iso) => new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short", timeZone: "Europe/Rome" });

function tabellaGara(ris) {
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Moto</th><th>Distacco</th><th>Punti</th></tr></thead><tbody>${ris.slice(0, 15).map((r) => `<tr class="${r.pos && r.pos <= 3 ? "podio" : ""}">
    <td>${r.pos ?? esc(r.stato || "–")}</td><td><strong>${esc(r.nome)}</strong> <span class="muted">#${r.numero ?? ""}</span></td>
    <td><span class="cella-team">${stemma(r.moto)}${esc(r.moto)}</span></td><td>${r.pos === 1 ? esc(r.tempo || "") : r.distacco && r.distacco !== "0.000" ? "+" + esc(r.distacco) : "–"}</td><td>${r.punti ?? "–"}</td></tr>`).join("")}</tbody></table></div>`;
}

function tabellaClassifica(pil) {
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Moto</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${pil.slice(0, 20).map((p) => `<tr class="${p.pos <= 3 ? "podio" : ""}">
    <td>${p.pos}</td><td><strong>${esc(p.nome)}</strong> <span class="muted">#${p.numero ?? ""}</span></td><td><span class="cell-team cella-team">${stemma(p.moto)}${esc(p.moto)}</span></td><td><strong>${punti(p.punti)}</strong></td><td>${p.vittorie}</td></tr>`).join("")}</tbody></table></div>`;
}

try {
  const [calendario, classifica, ultima] = await Promise.all([fetchJSON("data/motogp.json"), fetchJSON("data/motogp-classifica.json").catch(() => null), fetchJSON("data/motogp-ultima.json").catch(() => null)]);
  const weekend = calendario.weekend;
  const w = weekend[0];
  document.getElementById("m-prossimo").innerHTML = w ? `<article class="moto-prossimo"><span class="kicker">Prossimo weekend</span><h2>${esc(w.nome)}</h2>
      <p class="muted" style="margin:0 0 14px">${esc(w.circuito)} · ${esc(w.paese)} · ora italiana</p>
      <div class="moto-sessioni">${w.sessioni.map((s) => `<div class="moto-sess"><b>${esc(s.nome)}</b><span>${formattaDataOra(s.inizio)}</span></div>`).join("")}</div></article>` : `<p class="muted">Nessun weekend in programma.</p>`;
  if (ultima) {
    document.getElementById("m-ultima-nome").textContent = `· ${ultima.nome}`;
    document.getElementById("m-ultima").innerHTML = tabellaGara(ultima.risultati);
  } else document.getElementById("m-ultima").innerHTML = `<p class="muted">Risultati non disponibili.</p>`;
  if (classifica) {
    document.getElementById("m-agg").textContent = `Dati aggiornati al ${new Date(calendario.generato_il).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" })}`;
    document.getElementById("m-classifica").innerHTML = tabellaClassifica(classifica.piloti);
  } else document.getElementById("m-classifica").innerHTML = `<p class="muted">Classifica non disponibile.</p>`;
  document.getElementById("m-calendario").innerHTML = `<div class="report-lista">${weekend.map((g) => {
    const gara = g.sessioni.find((s) => s.codice === "RAC") || g.sessioni[g.sessioni.length - 1];
    return `<article class="report-card"><div class="report-data">${dataIt(g.sessioni[0].inizio)} – ${dataIt(gara.inizio)}</div><h3 style="margin:6px 0 4px">${esc(g.nome)}</h3>
      <p style="margin:0">${esc(g.circuito)}<br><b>Gara: ${formattaDataOra(gara.inizio)}</b></p></article>`;
  }).join("")}</div>`;
} catch (e) {
  erroreCaricamento(box);
}
