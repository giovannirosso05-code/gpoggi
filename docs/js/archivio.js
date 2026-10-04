import { renderHeader, renderFooter, fetchJSON, esc, punti, formattaData, erroreCaricamento } from "./common.js";

renderHeader("classifiche");
renderFooter();

const box = document.getElementById("archivio-box");
const sel = document.getElementById("anno");

function riga(p) { return `<tr class="${p.pos && p.pos <= 3 ? "podio" : ""}"><td>${p.pos ?? "–"}</td><td><strong>${esc(p.nome)}</strong> <span class="muted">${esc(p.naz || "")}</span></td><td>${esc(p.team)}</td><td><strong>${punti(p.punti)}</strong></td><td>${p.vittorie}</td></tr>`; }

async function mostra(anno) {
  box.innerHTML = `<p class="muted">Caricamento…</p>`;
  try {
    const s = await fetchJSON(`data/archivio/${anno}.json`);
    const c = s.campione;
    const cost = s.costruttori.find((x) => x.pos === 1);
    box.innerHTML = `
      <section class="campione"><span class="kicker">Campione ${anno}</span><h1>${c ? esc(c.nome) : "n.d."}</h1>
        <p class="muted" style="margin:0">${c ? esc(c.team) + " · " + c.vittorie + (c.vittorie === 1 ? " vittoria" : " vittorie") + " · " + punti(c.punti) + " punti" : ""}${cost ? " · Costruttori: " + esc(cost.team) : ""}</p></section>
      <div class="two-col">
        <div><h3 class="section-title" style="margin-top:0">Piloti</h3><div class="table-wrap"><table class="results">
          <thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${s.piloti.map(riga).join("")}</tbody></table></div></div>
        <div>${s.costruttori.length ? `<h3 class="section-title" style="margin-top:0">Costruttori</h3><div class="table-wrap"><table class="results">
          <thead><tr><th>Pos</th><th>Team</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${s.costruttori.map((x) => `<tr class="${x.pos && x.pos <= 3 ? "podio" : ""}"><td>${x.pos ?? "–"}</td><td><strong>${esc(x.team)}</strong></td><td><strong>${punti(x.punti)}</strong></td><td>${x.vittorie}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">Il campionato costruttori è stato introdotto nel 1958.</p>`}
        </div>
      </div>
      <h3 class="section-title">Vincitori delle gare</h3><div class="table-wrap"><table class="results">
        <thead><tr><th>Gara</th><th>Data</th><th>Gran Premio</th><th>Vincitore</th><th>Team</th></tr></thead>
        <tbody>${s.gare.map((g) => `<tr><td>${g.round}</td><td>${formattaData(g.data)}</td><td>${esc(g.nome)}</td><td><strong>${esc(g.vincitore)}</strong></td><td>${esc(g.team)}</td></tr>`).join("")}</tbody></table></div>`;
  } catch (e) { erroreCaricamento(box); }
}

try {
  const indice = await fetchJSON("data/archivio/indice.json");
  const anni = indice.map((x) => x.anno).sort((a, b) => b - a);
  sel.innerHTML = anni.map((a) => { const i = indice.find((x) => x.anno === a); return `<option value="${a}">${a}${i.campione ? " · " + esc(i.campione) : ""}</option>`; }).join("");
  const p = Number(new URLSearchParams(location.search).get("anno"));
  sel.value = anni.includes(p) ? p : anni[0];
  sel.addEventListener("change", () => { history.replaceState(null, "", `?anno=${sel.value}${document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : ""}`); mostra(sel.value); });
  mostra(sel.value);
} catch (e) { erroreCaricamento(box); }
