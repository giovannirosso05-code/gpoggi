import { renderHeader, renderFooter, fetchJSON, esc, img, punti, erroreCaricamento } from "./common.js";

renderHeader("classifiche");
renderFooter();

const box = document.getElementById("classifiche-box");
try {
  const [s, roster] = await Promise.all([fetchJSON("data/standings.json"), fetchJSON("data/roster.json")]);
  const foto = Object.fromEntries(roster.filter((p) => p.foto).map((p) => [p.numero, p.foto]));
  if (!s.piloti.length) {
    box.innerHTML = `<p class="muted center">Classifiche non ancora disponibili: nessuna gara disputata.</p>`;
  } else {
    const dot = (c) => `<span class="dot" style="background:#${esc(c || "8b8a92")}"></span>`;
    document.getElementById("dopo").textContent = `Aggiornate dopo il ${s.dopo}`;
    box.innerHTML = `
      <div class="two-col">
        <div><h3 class="section-title" style="margin-top:0">Piloti</h3><div class="table-wrap"><table class="results">
          <thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Punti</th></tr></thead>
          <tbody>${s.piloti.map((p) => `<tr class="${p.posizione <= 3 ? "podio" : ""}"><td>${p.posizione}</td>
            <td><a class="cella-pilota" href="pilota.html?n=${p.numero}">${foto[p.numero] ? img(foto[p.numero], p.nome || "", "foto-mini") : '<span class="foto-mini"></span>'}<strong>${esc(p.nome || "Pilota #" + p.numero)}</strong></a></td>
            <td>${dot(p.colore)}${esc(p.team || "")}</td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")}</tbody>
        </table></div></div>
        <div><h3 class="section-title" style="margin-top:0">Costruttori</h3><div class="table-wrap"><table class="results">
          <thead><tr><th>Pos</th><th>Team</th><th>Punti</th></tr></thead>
          <tbody>${s.costruttori.map((c) => `<tr class="${c.posizione <= 3 ? "podio" : ""}"><td>${c.posizione}</td><td>${dot(c.colore)}<strong>${esc(c.team)}</strong></td><td><strong>${punti(c.punti)}</strong></td></tr>`).join("")}</tbody>
        </table></div></div>
      </div>`;
  }
} catch (e) {
  erroreCaricamento(box);
}
