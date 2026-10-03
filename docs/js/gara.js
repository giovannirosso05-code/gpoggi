import { renderHeader, renderFooter, fetchJSON, esc, ND, formattaDataOra, intervalloWeekend, erroreCaricamento } from "./common.js";

renderHeader("gare");
renderFooter();

const box = document.getElementById("gara-box");
const id = new URLSearchParams(location.search).get("id");

function tabella(risultati) {
  if (!risultati || !risultati.length) return `<p class="muted">Risultati non disponibili.</p>`;
  return `<div class="table-wrap"><table class="results">
    <thead><tr><th>Pos</th><th>Pilota</th><th>Team</th><th>Giri</th><th>Tempo</th><th>Distacco</th></tr></thead>
    <tbody>${risultati.map((r) => `<tr>
      <td>${r.pos ?? esc(r.stato || "–")}</td>
      <td><a href="pilota.html?n=${r.numero}"><strong>${esc(r.nome || "Pilota #" + r.numero)}</strong></a> <span class="muted">${esc(r.acronimo || "")}</span></td>
      <td>${esc(r.team || "")}</td>
      <td>${r.giri ?? ND}</td>
      <td>${r.tempo ? esc(r.tempo) : ND}${r.stato && r.pos ? ` <span class="muted">${esc(r.stato)}</span>` : ""}</td>
      <td>${r.distacco ? esc(r.distacco) : "–"}</td>
    </tr>`).join("")}</tbody></table></div>`;
}

try {
  if (!/^\d+$/.test(id || "")) throw new Error("id non valido");
  const g = await fetchJSON(`data/gare/${id}.json`);
  document.title = `${g.nome} — F1 Oggi`;
  const ora = new Date();
  const sessioni = g.sessioni;
  const predefinita = [...sessioni].reverse().find((s) => s.risultati) || sessioni[0];

  box.innerHTML = `
    <section class="hero" style="padding:32px 0 12px">
      <h1>${esc(g.nome)}</h1>
      <p class="muted">${esc(g.circuito)}, ${esc(g.paese)} · ${intervalloWeekend(g)}</p>
    </section>
    <div id="tabs" class="category-pills" style="justify-content:center;margin-bottom:20px">
      ${sessioni.map((s) => `<button class="pill ${s.key === predefinita.key ? "active" : ""}" data-key="${s.key}">${esc(s.nome)}</button>`).join("")}
    </div>
    <div id="sessione"></div>`;

  const mostra = (key) => {
    const s = sessioni.find((x) => String(x.key) === String(key));
    document.getElementById("sessione").innerHTML = `
      <h3 class="section-title" style="margin-top:0">${esc(s.nome)} <span class="count">· ${formattaDataOra(s.inizio)}</span></h3>
      ${new Date(s.fine) > ora && !s.risultati ? `<p class="muted">Sessione non ancora disputata.</p>` : tabella(s.risultati)}`;
  };
  document.getElementById("tabs").addEventListener("click", (e) => {
    const b = e.target.closest(".pill");
    if (!b) return;
    document.querySelectorAll("#tabs .pill").forEach((p) => p.classList.toggle("active", p === b));
    mostra(b.dataset.key);
  });
  mostra(predefinita.key);
} catch (e) {
  erroreCaricamento(box);
}
