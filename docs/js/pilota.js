import { renderHeader, renderFooter, fetchJSON, esc, img, credito, punti, ND, formattaData, erroreCaricamento, schedeMap, bioHtml, dataIt } from "./common.js";

renderHeader("home");
renderFooter();

const box = document.getElementById("pilota-box");
const n = new URLSearchParams(location.search).get("n");

const cella = (e) => !e ? '<span class="muted">–</span>' : e.stato ? `<span class="muted">${esc(e.stato)}</span>` : e.pos == null ? ND : `<span class="${e.pos === 1 ? "accent" : ""}" style="font-weight:600">${e.pos}°</span>`;

try {
  if (!/^\d+$/.test(n || "")) throw new Error("numero non valido");
  const p = await fetchJSON(`data/piloti/${n}.json`);
  const nome = p.nome || `Pilota #${p.numero}`;
  document.title = `${nome} — GP Oggi`;
  const SC = await schedeMap();
  const sf = SC[`f1:${n}`], bio = SC[`nome:${p.nome}`];
  const stat = (v, label) => `<div class="stat"><div class="stat-number">${v}</div><div class="stat-label">${label}</div></div>`;

  box.innerHTML = `
    <section class="pilota-testata" style="--team:#${esc(p.colore || "8b8a92")}">
      <div class="pilota-foto">${img(p.foto, nome)}<span class="driver-number">${p.numero}</span></div>
      <div class="pilota-dati">
        <span class="kicker">${p.posizione ? `${p.posizione}° nel mondiale` : "Stagione in corso"}</span>
        <h1>${esc(nome)}</h1>
        <p class="muted" style="margin:0;font-size:16px">${esc(p.team || "Team n.d.")}</p>
        <div class="stat-strip six">
          ${stat(punti(p.punti), "Punti")}${stat(p.vittorie, "Vittorie")}${stat(p.podi, "Podi")}${stat(p.pole, "Pole")}${stat(p.miglior_arrivo ? p.miglior_arrivo + "°" : ND, "Miglior arrivo")}${stat(p.ritiri, "Ritiri")}
        </div>
        <p style="margin:20px 0 0"><a class="pill" href="confronto.html?a=${p.numero}">Confronta con un altro pilota →</a></p>
        ${p.foto ? `<p class="credito">${credito(p.foto)}</p>` : ""}
      </div>
    </section>
    ${sf ? `<h3 class="section-title">Scheda carriera in Formula 1</h3>
    <div class="stat-strip six">${stat(sf.gare, "Gran Premi")}${stat(sf.vittorie, "Vittorie")}${stat(sf.podi, "Podi")}${stat(sf.pole, "Pole")}${stat(sf.giri_veloci, "Giri veloci")}${stat(sf.titoli ?? ND, "Titoli")}</div>
    <p class="muted" style="font-size:13px;margin-top:8px">${sf.nascita ? `Nato il ${dataIt(sf.nascita)}` : ""}${sf.nazionalita ? ` · ${esc(sf.nazionalita)}` : ""} · numeri di carriera da Jolpica (Ergast)</p>` : ""}
    ${bioHtml(bio)}
    <h3 class="section-title">Stagione weekend per weekend</h3>
    ${p.weekend.length ? `<div class="table-wrap"><table class="results">
      <thead><tr><th>Weekend</th><th>Data</th><th>Qualifiche</th><th>Sprint</th><th>Gara</th></tr></thead>
      <tbody>${[...p.weekend].reverse().map((w) => `<tr>
        <td><a href="gara.html?id=${w.id}"><strong>${esc(w.nome)}</strong></a></td>
        <td class="muted">${formattaData(w.inizio)}</td>
        <td>${cella(w.qualifiche)}</td><td>${cella(w.sprint)}</td><td>${cella(w.gara)}</td>
      </tr>`).join("")}</tbody></table></div>
      <p class="muted" style="font-size:12px;margin-top:8px">RIT = ritirato · NP = non partito · SQ = squalificato · – = non presente o sessione non prevista</p>` : `<p class="muted">Nessun risultato disponibile.</p>`}`;
} catch (e) {
  erroreCaricamento(box);
}
