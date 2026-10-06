import { iniz, renderHeader, renderFooter, fetchJSON, esc, img, credito, stemma, stemmaMoto, ND, formattaData, punti, erroreCaricamento, fotoMotoMap, mappeMotoMap, montaCronaca, programmaHtml, intervalloWeekend } from "./common.js";

renderHeader("gare");
renderFooter();

const box = document.getElementById("gara-moto-box");
const gp = new URLSearchParams(location.search).get("gp") || "";
const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";

function tabella(righe, FM) {
  if (!righe || !righe.length) return `<p class="muted">Risultati non disponibili.</p>`;
  return `<div class="table-wrap"><table class="results"><thead><tr><th>Pos</th>${righe.some((r) => r.griglia) ? "<th>Griglia</th>" : ""}<th>Pilota</th><th>Team</th><th>Giri</th><th>Tempo</th><th>Distacco</th></tr></thead>
    <tbody>${righe.map((r) => `<tr class="${r.pos && r.pos <= 3 ? "podio" : ""}"><td>${r.pos ?? esc(r.stato === "OUTSTND" ? "RIT" : r.stato || "–")}</td>${righe.some((x) => x.griglia) ? `<td class="muted">${r.griglia ? "P" + r.griglia + (r.pos && r.griglia !== r.pos ? ` <span class="${r.pos < r.griglia ? "su" : "giu"}">${r.pos < r.griglia ? "▲" : "▼"}${Math.abs(r.pos - r.griglia)}</span>` : "") : "–"}</td>` : ""}
      <td><span class="cella-pilota">${FM["nome:" + r.nome] ? img(FM["nome:" + r.nome], r.nome, "foto-mini") : iniz(r.nome)}<strong>${esc(r.nome)}</strong></span></td>
      <td><span class="cella-team">${stemmaMoto(r.moto)}${esc(r.team)}</span></td><td>${r.giri ?? ND}</td>
      <td>${r.pos ? (r.tempo ? esc(r.tempo) : ND) : "–"}${r.stato && r.pos && r.stato !== "INSTND" ? ` <span class="muted">${esc(r.stato)}</span>` : ""}</td><td>${r.distacco && r.distacco !== "0.000" ? "+" + esc(r.distacco) : "–"}</td></tr>`).join("")}</tbody></table></div>`;
}

try {
  const [gare, rep, FM, MAPPE] = await Promise.all([fetchJSON("data/motogp-gare.json"), fetchJSON("data/motogp-report.json").catch(() => []), fotoMotoMap(), mappeMotoMap()]);
  const g = gare[gp];
  if (!g) {
    // weekend non ancora disputato: intestazione, mappa e programma con gli orari
    const cal = await fetchJSON("data/motogp.json");
    const w = cal.weekend.find((x) => x.nome === gp);
    if (!w) throw new Error("gara non trovata");
    document.title = `${gp} — GP Oggi`;
    const mp = MAPPE[w.circuito];
    box.innerHTML = `
      <section class="campione" style="margin-top:32px"><span class="kicker">MotoGP · ${intervalloWeekend({ inizio: w.sessioni[0].inizio, fine: w.sessioni[w.sessioni.length - 1].fine })}</span><h1>${esc(gp)}</h1>
        <p class="muted" style="margin:0">${esc(w.circuito || "")}${w.paese ? " · " + esc(w.paese) : ""}</p></section>
      ${programmaHtml(w.sessioni)}
      ${mp ? `<div class="mappa-circuito">${img(mp, "Tracciato di " + w.circuito)}<p class="credito">${credito(mp, "Mappa")}</p></div>` : ""}
      <p class="muted">Programma della classe MotoGP. I risultati compariranno dopo la gara.</p>
      <h3 class="section-title">Cronaca giro per giro</h3><p class="muted">Cronaca disponibile dopo la gara: compare qui poche ore dopo l'arrivo.</p>
      <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="calendario.html${tema ? "?" + tema.slice(1) : ""}">← Torna al calendario</a></p>`;
  } else {
  const r = rep.find((x) => x.gp === gp);
  document.title = `${gp} — GP Oggi`;
  const mappa = MAPPE[g.circuito];
  const chiavi = Object.keys(g.classifiche);
  box.innerHTML = `
    <section class="campione" style="margin-top:32px"><span class="kicker">MotoGP · ${formattaData(g.data)}</span><h1>${esc(gp)}</h1>
      <p class="muted" style="margin:0">${esc(g.circuito || "")}</p></section>
    ${mappa ? `<div class="mappa-circuito">${img(mappa, "Tracciato di " + g.circuito)}<p class="credito">${credito(mappa, "Mappa")}</p></div>` : ""}
    ${r ? `<h3 class="section-title">Com'è andata</h3><article class="report-card">${r.paragrafi.map((p) => `<p>${esc(p)}</p>`).join("")}</article>` : ""}
    <h3 class="section-title">Risultati</h3>
    <div class="category-pills" id="gm-cat" style="margin-bottom:12px">${chiavi.map((k, i) => `<button class="pill ${i === 0 ? "active" : ""}" data-k="${esc(k)}">${esc(k.replace(" sprint", " · sprint"))}</button>`).join("")}</div>
    <div id="gm-tab"></div>
    ${g.cronaca ? `<h3 class="section-title">Cronaca giro per giro</h3><div id="cronaca-box"></div>` : ""}
    <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="calendario.html${tema ? "?" + tema.slice(1) : ""}">← Torna al calendario</a></p>`;
  const mostra = (k) => {
    document.querySelectorAll("#gm-cat .pill").forEach((b) => b.classList.toggle("active", b.dataset.k === k));
    document.getElementById("gm-tab").innerHTML = tabella(g.classifiche[k], FM);
  };
  document.getElementById("gm-cat").addEventListener("click", (e) => { const b = e.target.closest(".pill"); if (b) mostra(b.dataset.k); });
  mostra(chiavi[0]);
  if (g.cronaca) montaCronaca(document.getElementById("cronaca-box"), g.cronaca, g.cronaca[g.cronaca.length - 1].giro);
  }
} catch (e) {
  erroreCaricamento(box);
}
