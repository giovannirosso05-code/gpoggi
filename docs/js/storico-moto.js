import { renderHeader, renderFooter, fetchJSON, esc, punti, erroreCaricamento, schedeMap, bioHtml } from "./common.js";

renderHeader("piloti");
renderFooter();

const box = document.getElementById("storico-box");
const nome = new URLSearchParams(location.search).get("n") || "";
const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";

try {
  const arch = (await fetchJSON("data/motogp-archivio.json")).anni;
  const righe = [];
  for (const s of arch) for (const r of s.classifica) if (r.nome === nome) righe.push({ anno: s.anno, classe: s.classe, ...r });
  if (!righe.length) throw new Error("pilota non trovato");
  righe.sort((a, b) => a.anno - b.anno);
  const titoli = righe.filter((r) => r.pos === 1).length, vitt = righe.reduce((t, r) => t + (r.vittorie || 0), 0);
  const migliore = Math.min(...righe.map((r) => r.pos || 99));
  const bio = (await schedeMap())[`nome:${nome}`];
  document.title = `${nome} — GP Oggi`;
  box.innerHTML = `
    <section class="campione" style="margin-top:32px"><span class="kicker">${esc(righe[righe.length - 1].paese || "Pilota storico")} · classe regina</span><h1>${esc(nome)}</h1>
      <p class="muted" style="margin:0">${righe.length} ${righe.length === 1 ? "stagione" : "stagioni"} in classifica (${righe[0].anno}${righe.length > 1 ? "–" + righe[righe.length - 1].anno : ""})</p></section>
    <div class="stat-strip">
      <div class="stat"><div class="stat-number">${titoli}</div><div class="stat-label">Titoli mondiali</div></div>
      <div class="stat"><div class="stat-number">${vitt}</div><div class="stat-label">Vittorie</div></div>
      <div class="stat"><div class="stat-number">${righe.length}</div><div class="stat-label">Stagioni</div></div>
      <div class="stat"><div class="stat-number">${migliore}°</div><div class="stat-label">Miglior piazzamento</div></div>
    </div>
    ${bioHtml(bio)}
    <h3 class="section-title">Stagioni</h3>
    <div class="table-wrap"><table class="results"><thead><tr><th>Anno</th><th>Classe</th><th>Pos</th><th>Team</th><th>Moto</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${
      [...righe].reverse().map((r) => `<tr class="${r.pos === 1 ? "podio" : ""}"><td><a class="accent" href="motogp-archivio.html?anno=${r.anno}${tema}">${r.anno}</a></td><td>${esc(r.classe)}</td><td>${r.pos ?? "–"}</td><td>${esc(r.team || "")}</td><td>${esc(r.moto || "")}</td><td><strong>${punti(r.punti)}</strong></td><td>${r.vittorie ?? 0}</td></tr>`).join("")
    }</tbody></table></div>
    <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="piloti.html?serie=motogp${tema}">← Tutti i piloti</a> · dati: archivio del campionato (solo classe regina)</p>`;
} catch (e) {
  erroreCaricamento(box);
}
