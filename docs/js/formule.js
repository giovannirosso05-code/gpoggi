import { renderHeader, renderFooter, fetchJSON, esc, punti, erroreCaricamento } from "./common.js";

renderHeader("formule");
renderFooter();

const box = document.getElementById("f-box");
const cache = {};
let serie = (new URLSearchParams(location.search).get("serie") === "f3") ? "f3" : "f2";

async function mostra() {
  document.querySelectorAll("#f-serie .pill").forEach((b) => b.classList.toggle("active", b.dataset.s === serie));
  box.innerHTML = `<p class="muted">Caricamento…</p>`;
  try {
    const d = cache[serie] || (cache[serie] = await fetchJSON(`data/${serie}.json`));
    document.getElementById("f-agg").textContent = `Stagione ${d.anno} · dati aggiornati al ${new Date(d.aggiornato).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" })}`;
    document.getElementById("f-fonte").innerHTML = `Fonte: <a href="${esc(d.fonte)}" target="_blank" rel="noopener">Wikipedia</a>, testo con licenza ${esc(d.licenza)}. Sito non ufficiale, non affiliato a FIA, Formula 2 o Formula 3.`;
    box.innerHTML = `<div class="two-col">
      <div><h3 class="section-title" style="margin-top:0">Piloti</h3><div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead><tbody>${
        d.piloti.map((p) => `<tr class="${p.pos && p.pos <= 3 ? "podio" : ""}"><td>${p.pos ?? "NC"}</td><td><strong>${esc(p.nome)}</strong></td><td>${esc(p.team || "n.d.")}</td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")
      }</tbody></table></div></div>
      <div><h3 class="section-title" style="margin-top:0">Team</h3><div class="table-wrap"><table class="results"><thead><tr><th>Pos</th><th>Team</th><th>Punti</th></tr></thead><tbody>${
        d.team.map((t) => `<tr class="${t.pos <= 3 ? "podio" : ""}"><td>${t.pos}</td><td><strong>${esc(t.team)}</strong></td><td><strong>${punti(t.punti)}</strong></td></tr>`).join("")
      }</tbody></table></div></div></div>`;
  } catch (e) { erroreCaricamento(box); }
}

document.getElementById("f-serie").addEventListener("click", (e) => { const b = e.target.closest(".pill"); if (b) { serie = b.dataset.s; mostra(); } });
mostra();
