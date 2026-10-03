import { renderHeader, renderFooter, fetchJSON, esc, punti, erroreCaricamento } from "./common.js";

renderHeader("classifiche");
renderFooter();

const box = document.getElementById("classifiche-box");
try {
  const s = await fetchJSON("data/standings.json");
  if (!s.piloti.length) {
    box.innerHTML = `<p class="muted center">Classifiche non ancora disponibili: nessuna gara disputata.</p>`;
  } else {
    const dot = (c) => `<span class="dot" style="background:#${esc(c || "6b6b78")}"></span>`;
    document.getElementById("dopo").textContent = `Dopo: ${s.dopo}`;
    box.innerHTML = `
      <div class="two-col">
        <div><h3 class="section-title" style="margin-top:0">Piloti</h3><div class="table-wrap"><table class="results">
          <thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead>
          <tbody>${s.piloti.map((p) => `<tr><td>${p.posizione}</td><td>${dot(p.colore)}<a href="pilota.html?n=${p.numero}"><strong>${esc(p.nome || "Pilota #" + p.numero)}</strong></a></td><td>${esc(p.team || "")}</td><td>${punti(p.punti)}</td></tr>`).join("")}</tbody>
        </table></div></div>
        <div><h3 class="section-title" style="margin-top:0">Costruttori</h3><div class="table-wrap"><table class="results">
          <thead><tr><th>Pos</th><th>Team</th><th>Punti</th></tr></thead>
          <tbody>${s.costruttori.map((c) => `<tr><td>${c.posizione}</td><td>${dot(c.colore)}<strong>${esc(c.team)}</strong></td><td>${punti(c.punti)}</td></tr>`).join("")}</tbody>
        </table></div></div>
      </div>`;
  }
} catch (e) {
  erroreCaricamento(box);
}
