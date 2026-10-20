import { renderHeader, renderFooter, fetchJSON, esc, punti, erroreCaricamento, schedeMap, bioHtml, fotoStorica, testataStorica } from "./common.js";

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
  const titoli = righe.filter((r) => r.pos === 1).length;
  // le vittorie per stagione mancano nell'archivio fino al 2005 e nel 2022: se manca anche una sola stagione il totale sarebbe sbagliato (solo una parte), quindi non si mostra
  const vittCompleto = righe.every((r) => r.vittorie != null);
  const vitt = vittCompleto ? righe.reduce((t, r) => t + r.vittorie, 0) : "n.d.";
  const migliore = Math.min(...righe.map((r) => r.pos || 99));
  const foto = await fotoStorica(nome);
  const bio = (await schedeMap())[`nome:${nome}`];
  document.title = `${nome} — GP Oggi`;
  box.innerHTML = `
    ${testataStorica({ nome, kicker: `${righe[righe.length - 1].paese || "Pilota storico"} · classe regina`, sotto: `${righe.length} ${righe.length === 1 ? "stagione" : "stagioni"} in classifica (${righe[0].anno}${righe.length > 1 ? "–" + righe[righe.length - 1].anno : ""})`,
      stat: [[titoli, "Titoli in classe regina"], [vitt, vittCompleto ? "Vittorie" : "Vittorie (dato non disponibile)"], [righe.length, "Stagioni"], [`${migliore}°`, "Miglior piazzamento"]], foto })}
    ${bioHtml(bio)}
    <h3 class="section-title">Stagioni</h3>
    <div class="table-wrap"><table class="results"><thead><tr><th>Anno</th><th>Classe</th><th>Pos</th><th>Team</th><th>Moto</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${
      [...righe].reverse().map((r) => `<tr class="${r.pos === 1 ? "podio" : ""}"><td><a class="accent" href="motogp-archivio.html?anno=${r.anno}${tema}">${r.anno}</a></td><td>${esc(r.classe)}</td><td>${r.pos ?? "–"}</td><td>${esc(r.team || "")}</td><td>${esc(r.moto || "")}</td><td><strong>${punti(r.punti)}</strong></td><td>${r.vittorie ?? 0}</td></tr>`).join("")
    }</tbody></table></div>
    <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="piloti.html?serie=motogp${tema}">← Tutti i piloti</a> · dati: archivio del campionato (solo classe regina)${vittCompleto ? "" : ". Le vittorie per stagione non sono presenti nell'archivio fino al 2005 e nel 2022: il totale non è calcolabile qui, quindi non lo mostriamo."}</p>`;
} catch (e) {
  erroreCaricamento(box);
}
