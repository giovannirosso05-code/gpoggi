import { renderHeader, renderFooter, fetchJSON, esc, punti, erroreCaricamento } from "./common.js";

renderHeader("motogp");
renderFooter();

const box = document.getElementById("ma-box");
const sel = document.getElementById("anno");
let anni = [];

function mostra(anno) {
  const s = anni.find((x) => x.anno === Number(anno));
  const c = s.classifica.find((p) => p.pos === 1) || s.classifica[0];
  box.innerHTML = `
    <section class="campione"><span class="kicker">Campione ${s.anno} · ${esc(s.classe)}</span><h1>${esc(c.nome || "n.d.")}</h1>
      <p class="muted" style="margin:0">${[c.moto, c.team].filter(Boolean).map(esc).join(" · ")}${c.punti != null ? " · " + punti(c.punti) + " punti" : ""}${c.vittorie != null ? " · " + c.vittorie + " vittorie" : ""}</p></section>
    <div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Moto</th><th>Team</th><th>Punti</th><th>Vitt.</th></tr></thead><tbody>${s.classifica.map((p) => `<tr class="${p.pos && p.pos <= 3 ? "podio" : ""}">
      <td>${p.pos ?? "–"}</td><td><strong>${esc(p.nome || "n.d.")}</strong> <span class="muted">${esc(p.paese || "")}</span></td><td>${esc(p.moto || "n.d.")}</td><td>${esc(p.team || "n.d.")}</td><td><strong>${p.punti != null ? punti(p.punti) : "n.d."}</strong></td><td>${p.vittorie ?? "n.d."}</td></tr>`).join("")}</tbody></table></div>`;
}

try {
  anni = (await fetchJSON("data/motogp-archivio.json")).anni;
  sel.innerHTML = anni.map((s) => { const c = s.classifica.find((p) => p.pos === 1); return `<option value="${s.anno}">${s.anno}${c ? " · " + esc(c.nome) : ""}</option>`; }).join("");
  const p = Number(new URLSearchParams(location.search).get("anno"));
  sel.value = anni.some((s) => s.anno === p) ? p : anni[0].anno;
  sel.addEventListener("change", () => mostra(sel.value));
  mostra(sel.value);
} catch (e) { erroreCaricamento(box); }
