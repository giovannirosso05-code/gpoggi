import { renderHeader, renderFooter, fetchJSON, esc, stemma, stemmaMoto, formattaData, erroreCaricamento } from "./common.js";

renderHeader("pagella");
renderFooter();

const box = document.getElementById("pagella-box");
const pos = (p) => (p == null ? '<span class="muted">RIT</span>' : p);

function tabella(w, moto) {
  const righe = w.righe;
  return `<div class="table-wrap"><table class="results">
    <thead><tr><th>Voto</th><th>Pilota</th><th>Team</th><th>Qualifica</th>${w.sprint ? "<th>Sprint</th>" : ""}<th>Gara</th><th></th></tr></thead>
    <tbody>${righe.map((r) => `<tr class="${r === righe[0] ? "podio" : ""}">
      <td><span class="pg-num">${String(r.voto).replace(".", ",")}</span></td>
      <td><strong>${esc(r.nome)}</strong>${r.perche && r.perche.length ? `<br><small class="muted">${esc(r.perche.join(" · "))}</small>` : ""}${r.correzione ? `<br><small class="muted">Calcolato ${String(r.voto_calcolato).replace(".", ",")}, correzione ${r.correzione > 0 ? "+" : "−"}${String(Math.abs(r.correzione)).replace(".", ",")}: ${esc(r.motivo)}</small>` : ""}</td>
      <td><span class="cella-team">${moto ? stemmaMoto(r.moto) : stemma(r.team, r.colore)}${esc(r.team || "")}</span></td>
      <td>${pos(r.q)}</td>${w.sprint ? `<td>${pos(r.s)}</td>` : ""}<td>${pos(r.g)}${r.griglia && r.g != null ? ` <span class="muted">(da P${r.griglia})</span>` : ""}</td>
      <td><span class="pg-barra" style="width:${r.voto * 9}px"></span></td></tr>`).join("")}</tbody></table></div>`;
}

try {
  const d = await fetchJSON("data/pagella.json");
  const serie = [["f1", "Formula 1"], ["motogp", "MotoGP"]].filter(([k]) => d[k]);
  if (!serie.length) throw new Error("nessuna pagella");
  box.innerHTML = `
    <span class="kicker">Il voto di GP Oggi</span>
    <h1>Pagella del weekend</h1>
    <p class="muted">I voti sono nostri: partono da un calcolo sui risultati ufficiali di qualifica, sprint e gara e dicono la nostra su ogni pilota. Il metodo è in fondo alla pagina.</p>
    <div class="category-pills" id="pg-serie" style="margin-bottom:8px">${serie.map(([k, n], i) => `<button class="pill ${i === 0 ? "active" : ""}" data-k="${k}">${n}</button>`).join("")}</div>
    <div id="pg-corpo"></div>
    <div class="pg-metodo muted"><h3 class="section-title" style="margin-top:0">Come calcoliamo il voto</h3>
      <ol><li>Ogni sessione dà un voto in base alla posizione: 1° = 10, 2° = 8,5, 3° = 8, 4° = 7,5, 5° = 7, 6° = 6,5, poi si scende di poco a ogni posizione, fino a un minimo di 4.</li>
      <li>In gara si aggiunge 0,1 per ogni posizione guadagnata rispetto alla griglia di partenza ufficiale (da −1 a +1,5, mai oltre 10).</li>
      <li>Chi si ritira, o non fa registrare un tempo, prende 3 in quella sessione.</li>
      <li>Pesi: qualifica 20%, sprint 20%, gara 60%. Senza sprint: qualifica 25%, gara 75%. Il voto finale è arrotondato al mezzo punto.</li></ol>
      <p>Il calcolo è il punto di partenza: se la redazione ritiene che un voto non renda giustizia a una giornata, lo corregge e lo scrive sotto il nome del pilota, con il motivo.</p><p>Sono i voti di GP Oggi, non quelli di un ente ufficiale: il calcolo non conosce strategie o incidenti subiti, per questo possono esserci correzioni. Si aggiorna dopo ogni gara.</p></div>`;
  const mostra = (k) => {
    const w = d[k], moto = k === "motogp", top = w.righe[0];
    document.getElementById("pg-corpo").innerHTML = `
      <div class="${moto ? "serie-moto" : ""}">
      <h3 class="section-title">${esc(w.nome)} <span class="count">· ${formattaData(w.data)}</span></h3>
      <div class="pg-hero"><div class="pg-voto">${String(top.voto).replace(".", ",")}</div><div><small>Uomo del weekend</small><strong>${esc(top.nome)}</strong></div></div>
      ${tabella(w, moto)}</div>`;
  };
  document.getElementById("pg-serie").addEventListener("click", (e) => {
    const b = e.target.closest(".pill"); if (!b) return;
    document.querySelectorAll("#pg-serie .pill").forEach((p) => p.classList.toggle("active", p === b));
    mostra(b.dataset.k);
  });
  mostra(serie[0][0]);
} catch (e) {
  erroreCaricamento(box);
}
