import { renderHeader, renderFooter, fetchJSON, esc, formattaData, erroreCaricamento } from "./common.js";

renderHeader("notizie");
renderFooter();

const box = document.getElementById("notizie-box");
try {
  const [report, news] = await Promise.all([fetchJSON("data/report.json"), fetchJSON("data/news.json").catch(() => [])]);

  const redazione = document.getElementById("redazione");
  redazione.innerHTML = news.length ? news.map((n) => `
    <article class="report-card in-evidenza">
      <div class="report-data">${formattaData(n.data)}${n.fonte ? ` · ${esc(n.fonte)}` : ""}</div>
      <h3>${esc(n.titolo)}</h3>
      ${n.testo ? `<p>${esc(n.testo)}</p>` : ""}
      ${n.link ? `<a class="accent" href="${esc(n.link)}" target="_blank" rel="noopener">Leggi la fonte →</a>` : ""}
    </article>`).join("") : `<p class="muted" style="font-size:13px">Qui compaiono le notizie scritte dalla redazione. Per ora ci sono solo i report di gara.</p>`;

  document.getElementById("report-lista").innerHTML = report.length ? report.map((r) => `
    <article class="report-card">
      <div class="report-data">${formattaData(r.data)} · ${esc(r.circuito)}, ${esc(r.paese)}</div>
      <h3><a href="gara.html?id=${r.id}">${esc(r.titolo)}</a></h3>
      ${r.paragrafi.map((p) => `<p>${esc(p)}</p>`).join("")}
      <a class="accent" href="gara.html?id=${r.id}">Tutti i risultati →</a>
    </article>`).join("") : `<p class="muted">Nessuna gara ancora disputata.</p>`;
} catch (e) {
  erroreCaricamento(box);
}
