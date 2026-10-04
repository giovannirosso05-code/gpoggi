import { renderHeader, renderFooter, fetchJSON, esc, img, credito, stemma, ND, formattaDataOra, intervalloWeekend, erroreCaricamento, montaCronaca } from "./common.js";

renderHeader("gare");
renderFooter();

const box = document.getElementById("gara-box");
const id = new URLSearchParams(location.search).get("id");

function tabella(risultati, foto, colori, griglia) {
  if (!risultati || !risultati.length) return `<p class="muted">Risultati non disponibili.</p>`;
  return `<div class="table-wrap"><table class="results">
    <thead><tr><th>Pos</th>${griglia ? "<th>Griglia</th>" : ""}<th>Pilota</th><th>Team</th><th>Giri</th><th>Tempo</th><th>Distacco</th></tr></thead>
    <tbody>${risultati.map((r) => `<tr class="${r.pos && r.pos <= 3 ? "podio" : ""}">
      <td>${r.pos ?? esc(r.stato || "–")}</td>
      ${griglia ? `<td class="muted">${griglia[r.numero] ? "P" + griglia[r.numero] + (r.pos && !r.stato && griglia[r.numero] !== r.pos ? ` <span class="${r.pos < griglia[r.numero] ? "su" : "giu"}">${r.pos < griglia[r.numero] ? "▲" : "▼"}${Math.abs(r.pos - griglia[r.numero])}</span>` : "") : "–"}</td>` : ""}
      <td><a class="cella-pilota" href="pilota.html?n=${r.numero}">${foto[r.numero] ? img(foto[r.numero], r.nome || "", "foto-mini") : '<span class="foto-mini"></span>'}<strong>${esc(r.nome || "Pilota #" + r.numero)}</strong></a></td>
      <td><span class="cella-team">${stemma(r.team, colori[r.team])}${esc(r.team || "")}</span></td>
      <td>${r.giri ?? ND}</td>
      <td>${r.tempo ? esc(r.tempo) : ND}${r.stato && r.pos ? ` <span class="muted">${esc(r.stato)}</span>` : ""}</td>
      <td>${r.distacco ? esc(r.distacco) : "–"}</td>
    </tr>`).join("")}</tbody></table></div>`;
}

try {
  if (!/^\d+$/.test(id || "")) throw new Error("id non valido");
  const [g, roster, st, reports] = await Promise.all([fetchJSON(`data/gare/${id}.json`), fetchJSON("data/roster.json"), fetchJSON("data/standings.json"), fetchJSON("data/report.json").catch(() => [])]);
  const rep = reports.find((r) => String(r.id) === String(id));
  const colori = Object.fromEntries(st.costruttori.map((c) => [c.team, c.colore]));
  const foto = Object.fromEntries(roster.filter((p) => p.foto).map((p) => [p.numero, p.foto]));
  document.title = `${g.nome} — GP Oggi`;
  const ora = new Date();
  const sessioni = g.sessioni;
  const predefinita = [...sessioni].reverse().find((s) => s.risultati) || sessioni[0];

  box.innerHTML = `
    <section class="gara-testata">
      <div>
        <span class="kicker">${intervalloWeekend(g)}</span>
        <h1>${esc(g.nome)}</h1>
        <p class="muted" style="margin:0">${esc(g.circuito)} · ${esc(g.localita)}, ${esc(g.paese)}</p>
      </div>
      <div>${g.mappa ? img(g.mappa, "Tracciato di " + g.circuito, "mappa") + `<p class="credito center">${credito(g.mappa, "Mappa")}</p>` : ""}</div>
    </section>
    ${rep ? `<h3 class="section-title">Com'è andata</h3><article class="report-card"><h3 style="margin-top:0">${esc(rep.titolo)}</h3>${rep.paragrafi.map((p) => `<p>${esc(p)}</p>`).join("")}</article>` : ""}
    <h3 class="section-title">Cronaca giro per giro</h3><div id="cronaca-box"><p class="muted">Cronaca non disponibile per questa gara.</p></div>
    <div id="tabs" class="category-pills" style="margin-bottom:8px">
      ${sessioni.map((s) => `<button class="pill ${s.key === predefinita.key ? "active" : ""}" data-key="${s.key}">${esc(s.nome)}</button>`).join("")}
    </div>
    <div id="sessione"></div>`;

  let griglia = null, sessioneCorrente = null;
  const mostra = (key) => {
    const s = sessioni.find((x) => String(x.key) === String(key));
    document.getElementById("sessione").innerHTML = `
      <h3 class="section-title" style="margin-top:20px">${esc(s.nome)} <span class="count">· ${formattaDataOra(s.inizio)}</span></h3>
      ${new Date(s.fine) > ora && !s.risultati ? `<p class="muted">Sessione non ancora disputata.</p>` : tabella(s.risultati, foto, colori, s.tipo === "Race" ? griglia : null)}`;
    sessioneCorrente = key;
  };
  document.getElementById("tabs").addEventListener("click", (e) => {
    const b = e.target.closest(".pill");
    if (!b) return;
    document.querySelectorAll("#tabs .pill").forEach((p) => p.classList.toggle("active", p === b));
    mostra(b.dataset.key);
  });
  mostra(predefinita.key);
  fetchJSON(`data/cronaca/${id}.json`).then((c) => { montaCronaca(document.getElementById("cronaca-box"), c.voci, c.giri); griglia = c.griglia && Object.keys(c.griglia).length ? c.griglia : null; if (griglia && sessioneCorrente != null) mostra(sessioneCorrente); }).catch(() => {});
} catch (e) {
  erroreCaricamento(box);
}
