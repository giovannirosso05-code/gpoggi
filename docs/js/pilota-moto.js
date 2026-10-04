import { renderHeader, renderFooter, fetchJSON, esc, stemma, stemmaMoto, formattaData, punti, erroreCaricamento, img, credito, fotoMotoMap, schedeMap, bioHtml, dataIt } from "./common.js";

renderHeader("motogp");
renderFooter();

const box = document.getElementById("pm-box");
const id = new URLSearchParams(location.search).get("id") || "";
const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";

try {
  const dati = await fetchJSON("data/motogp-piloti.json");
  const FM = await fotoMotoMap();
  const p = dati[id];
  const foto = FM[id];
  const SC = await schedeMap();
  const sm = SC[`moto:${id}`], bio = SC[`nome:${p.nome}`];
  if (!p) throw new Error("pilota non trovato");
  document.title = `${p.nome} — GP Oggi`;
  const gare = p.gare;
  const podi = gare.filter((g) => g.gara && g.gara <= 3).length;
  const migliore = gare.map((g) => g.gara).filter(Boolean).sort((a, b) => a - b)[0];
  const esito = (g) => (g.gara ? `${g.gara}°` : g.stato_gara && g.stato_gara !== "INSTND" ? "Ritirato" : "–");
  box.innerHTML = `
    <section class="campione" style="margin-top:32px"><span class="kicker">${esc(p.categoria)} · #${p.numero ?? "n.d."}</span><div class="pm-testa">${foto ? img(foto, p.nome, "pm-foto") : ""}<div><h1>${esc(p.nome)}</h1>
      <p class="muted" style="margin:0"><span class="cella-team">${stemmaMoto(p.moto)}${esc(p.team)}</span> · ${esc(p.paese || "")}</p></div></div>
      ${foto ? `<p class="credito" style="margin:10px 0 0">${credito(foto)}</p>` : ""}</section>
    <div class="stat-strip">
      <div class="stat"><div class="stat-number">${p.pos ?? "n.d."}${p.pos ? "°" : ""}</div><div class="stat-label">In classifica</div></div>
      <div class="stat"><div class="stat-number">${punti(p.punti)}</div><div class="stat-label">Punti</div></div>
      <div class="stat"><div class="stat-number">${p.vittorie}</div><div class="stat-label">Vittorie</div></div>
      <div class="stat"><div class="stat-number">${podi}</div><div class="stat-label">Podi in gara</div></div>
    </div>
    ${sm ? `<h3 class="section-title">Scheda</h3>
    <div class="stat-strip">${sm.nascita ? `<div class="stat"><div class="stat-number" style="font-size:22px">${dataIt(sm.nascita)}</div><div class="stat-label">Nato${sm.luogo ? " · " + esc(sm.luogo) : ""}</div></div>` : ""}
      ${sm.debutto ? `<div class="stat"><div class="stat-number">${sm.debutto}</div><div class="stat-label">Debutto nel mondiale</div></div>` : ""}
      ${sm.altezza ? `<div class="stat"><div class="stat-number">${sm.altezza} cm</div><div class="stat-label">Altezza</div></div>` : ""}
      ${sm.peso ? `<div class="stat"><div class="stat-number">${sm.peso} kg</div><div class="stat-label">Peso</div></div>` : ""}</div>
    ${sm.carriera.length ? `<h3 class="section-title">Carriera nel mondiale</h3><div class="table-wrap"><table class="results"><thead><tr><th>Anno</th><th>Classe</th><th>Team</th><th>N.</th></tr></thead><tbody>${[...sm.carriera].reverse().map((a) => a.classi.map((c) => `<tr><td>${a.anno}</td><td>${esc(c.categoria)}</td><td>${esc(c.team || "")}</td><td>${c.numero ?? ""}</td></tr>`).join("")).join("")}</tbody></table></div><p class="muted" style="font-size:12px;margin-top:8px">Dati dal servizio pubblico del campionato.</p>` : ""}` : ""}
    ${bioHtml(bio)}
    <h3 class="section-title">Gara per gara${migliore ? ` <span class="count">· miglior risultato ${migliore}°</span>` : ""}</h3>
    <div class="table-wrap"><table class="results"><thead><tr><th>Gran Premio</th><th>Data</th><th>Sprint</th><th>Gara</th><th>Punti</th></tr></thead><tbody>${
      [...gare].reverse().map((g) => `<tr class="${g.gara === 1 ? "podio" : ""}"><td><strong>${esc(g.gp)}</strong></td><td>${formattaData(g.data)}</td><td>${g.sprint ? g.sprint + "°" : "–"}</td><td>${esito(g)}</td><td><strong>${g.punti}</strong></td></tr>`).join("")
    }</tbody></table></div>
    <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="motogp.html${tema ? "?" + tema.slice(1) : ""}">← Torna alla MotoGP</a></p>`;
} catch (e) {
  erroreCaricamento(box);
}
