import { renderHeader, renderFooter, fetchJSON, esc, punti, ND, formattaData, erroreCaricamento } from "./common.js";

renderHeader("home");
renderFooter();

const box = document.getElementById("pilota-box");
const n = new URLSearchParams(location.search).get("n");

const cella = (e) => !e ? '<span class="muted">–</span>' : e.stato ? `<span class="muted">${esc(e.stato)}</span>` : e.pos == null ? ND : `<span class="${e.pos === 1 ? "accent" : ""}">${e.pos}°</span>`;

try {
  if (!/^\d+$/.test(n || "")) throw new Error("numero non valido");
  const p = await fetchJSON(`data/piloti/${n}.json`);
  const nome = p.nome || `Pilota #${p.numero}`;
  document.title = `${nome} — F1 Oggi`;
  const stat = (v, label) => `<div class="stat"><div class="stat-number">${v}</div><div class="stat-label">${label}</div></div>`;

  box.innerHTML = `
    <section class="hero" style="padding:32px 0 8px">
      <div class="driver-number" style="--team:#${esc(p.colore || "6b6b78")};font-size:64px;line-height:1">${p.numero}</div>
      <h1>${esc(nome)}</h1>
      <p class="muted">${esc(p.team || "Team n.d.")}${p.posizione ? ` · ${p.posizione}° in classifica` : ""}</p>
      <div class="stat-strip six" style="max-width:900px;margin:24px auto 0">
        ${stat(punti(p.punti), "Punti")}${stat(p.vittorie, "Vittorie")}${stat(p.podi, "Podi")}${stat(p.pole, "Pole")}${stat(p.miglior_arrivo ? p.miglior_arrivo + "°" : ND, "Miglior arrivo")}${stat(p.ritiri, "Ritiri")}
      </div>
    </section>
    <div style="display:flex;justify-content:center;margin:16px 0 8px">
      <a class="pill" href="confronto.html?a=${p.numero}">Confronta con un altro pilota →</a>
    </div>
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
