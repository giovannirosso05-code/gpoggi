import { renderHeader, renderFooter, fetchJSON, esc, punti, erroreCaricamento, schedeMap, bioHtml, fotoStorica, testataStorica } from "./common.js";

renderHeader("classifiche");
renderFooter();

const box = document.getElementById("storico-box");
const id = new URLSearchParams(location.search).get("id") || "";

try {
  const [storici, dett] = await Promise.all([fetchJSON("data/storici.json"), fetchJSON("data/storici-stagioni.json")]);
  const p = storici.piloti.find((x) => x.id === id);
  if (!p || !dett[id]) throw new Error("pilota non trovato");
  const foto = await fotoStorica(p.nome);
  const bio = (await schedeMap())[`nome:${p.nome}`];
  const stagioni = dett[id].s, gare = dett[id].v;
  document.title = `${p.nome} — GP Oggi`;
  const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";
  box.innerHTML = `
    ${testataStorica({ nome: p.nome, kicker: p.naz || "Pilota storico", sotto: `${p.stagioni.length} ${p.stagioni.length === 1 ? "stagione" : "stagioni"} in classifica (${p.stagioni[0]}${p.stagioni.length > 1 ? "–" + p.stagioni[p.stagioni.length - 1] : ""})`,
      stat: [[p.titoli, "Titoli mondiali"], [p.vittorie, "Vittorie"], [p.stagioni.length, "Stagioni"], [`${p.migliore ?? "n.d."}${p.migliore ? "°" : ""}`, "Miglior piazzamento"]], foto })}
    ${bioHtml(bio)}
    <h3 class="section-title">Stagioni</h3>
    <div class="table-wrap"><table class="results"><thead><tr><th>Anno</th><th>Pos</th><th>Team</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${
      [...stagioni].reverse().map(([a, pos, team, pt, v]) => `<tr class="${pos === 1 ? "podio" : ""}"><td><a class="accent" href="archivio.html?anno=${a}${tema}">${a}</a></td><td>${pos ?? "–"}</td><td>${esc(team)}</td><td><strong>${punti(pt)}</strong></td><td>${v}</td></tr>`).join("")
    }</tbody></table></div>
    ${gare.length ? `<h3 class="section-title">Gran Premi vinti <span class="count">(${gare.length})</span></h3>
      <div class="table-wrap"><table class="results"><thead><tr><th>Anno</th><th>Gran Premio</th></tr></thead><tbody>${[...gare].reverse().map(([a, n]) => `<tr><td>${a}</td><td>${esc(n)}</td></tr>`).join("")}</tbody></table></div>` : ""}
    <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="storici.html">← Tutti i piloti storici</a></p>`;
} catch (e) {
  erroreCaricamento(box);
}
