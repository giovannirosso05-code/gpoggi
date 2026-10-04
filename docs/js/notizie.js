import { renderHeader, renderFooter, fetchJSON, esc, formattaData, formattaDataOra, erroreCaricamento, mischia } from "./common.js";

renderHeader("notizie");
renderFooter();

const box = document.getElementById("notizie-box");
let serie = "tutte";
try {
  const [report, news, rassegna] = await Promise.all([fetchJSON("data/report.json"), fetchJSON("data/news.json").catch(() => []), fetchJSON("data/rassegna.json").catch(() => ({ articoli: [] }))]);

  const redazione = document.getElementById("redazione");
  redazione.innerHTML = news.length ? news.map((n) => `
    <article class="report-card in-evidenza">
      <div class="report-data">${formattaData(n.data)}${n.fonte ? ` · ${esc(n.fonte)}` : ""}</div>
      <h3>${esc(n.titolo)}</h3>
      ${n.testo ? `<p>${esc(n.testo)}</p>` : ""}
      ${n.link ? `<a class="accent" href="${esc(n.link)}" target="_blank" rel="noopener">Leggi la fonte →</a>` : ""}
    </article>`).join("") : "";

  const ras = document.getElementById("rassegna");
  const disegnaRassegna = () => {
  const lista = serie === "tutte" ? mischia(rassegna.articoli, 16) : rassegna.articoli.filter((a) => a.serie === serie).slice(0, 16);
  ras.innerHTML = lista.length ? lista.map((a) => `
    <article class="rassegna-voce">
      <div class="report-data"><b>${esc(a.serie || "F1")}</b> · ${esc(a.fonte)}${a.pubblicato ? " · " + formattaDataOra(a.pubblicato) : ""}</div>
      <h3><a href="${esc(a.url)}" target="_blank" rel="noopener nofollow">${esc(a.titolo)}</a></h3>
      ${a.estratto ? `<p>${esc(a.estratto)}</p>` : ""}
      <a class="accent" href="${esc(a.url)}" target="_blank" rel="noopener nofollow">Leggi su ${esc(a.fonte)} →</a>
    </article>`).join("") : `<p class="muted" style="font-size:13px">Nessuna notizia al momento.</p>`;
  };
  document.getElementById("filtro-serie").addEventListener("click", (e) => { const b = e.target.closest(".pill"); if (!b) return; serie = b.dataset.s; document.querySelectorAll("#filtro-serie .pill").forEach((x) => x.classList.toggle("active", x === b)); disegnaRassegna(); });
  disegnaRassegna();

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
