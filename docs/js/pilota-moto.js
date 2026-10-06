import { renderHeader, renderFooter, fetchJSON, esc, ND, coloreMoto, stemma, stemmaMoto, formattaData, punti, erroreCaricamento, img, credito, fotoMotoMap, schedeMap, bioHtml, dataIt } from "./common.js";

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
  // Stessa struttura della scheda F1: foto grande a sinistra col numero, a destra nome, team e sei riquadri; poi scheda carriera con sei riquadri
  const statBox = (v, label) => `<div class="stat"><div class="stat-number">${v}</div><div class="stat-label">${label}</div></div>`;
  const colore = (coloreMoto(p.moto) || "#8b8a92").replace("#", "");
  const ritiri = gare.filter((g) => !g.gara && g.stato_gara && g.stato_gara !== "INSTND").length;
  const tot = sm && sm.totali, num = (v) => (v == null ? ND : v);
  box.innerHTML = `
    <section class="pilota-testata" style="--team:#${esc(colore)}">
      <div class="pilota-foto">${foto ? img(foto, p.nome) : ""}<span class="driver-number">${p.numero ?? ""}</span></div>
      <div class="pilota-dati">
        <span class="kicker">${p.pos ? `${p.pos}° in ${esc(p.categoria)}` : esc(p.categoria)}</span>
        <h1>${esc(p.nome)}</h1>
        <p class="muted" style="margin:0;font-size:16px">${esc(p.team || "Team n.d.")}${p.paese ? " · " + esc(p.paese) : ""}</p>
        <div class="stat-strip six">
          ${statBox(punti(p.punti), "Punti")}${statBox(p.vittorie, "Vittorie")}${statBox(podi, "Podi")}${statBox(gare.length, "Gare")}${statBox(migliore ? migliore + "°" : ND, "Miglior arrivo")}${statBox(ritiri, "Ritiri")}
        </div>
        <label class="confronta">Confronta con <select id="conf-sel"><option value="">scegli un pilota…</option>${Object.entries(dati).filter(([k, x]) => k !== id && x.categoria === p.categoria).sort((a, b) => (a[1].numero ?? 999) - (b[1].numero ?? 999)).map(([k, x]) => `<option value="${esc(k)}">${x.numero != null ? "#" + x.numero + " · " : ""}${esc(x.nome)}</option>`).join("")}</select></label>
        ${foto ? `<p class="credito">${credito(foto)}</p>` : ""}
      </div>
    </section>
    <div id="conf-risultato"></div>
    ${sm ? `<h3 class="section-title">Scheda carriera nel mondiale</h3>
    <div class="stat-strip six">${statBox(num(tot && tot.gare), "Gran Premi")}${statBox(num(tot && tot.vittorie), "Vittorie")}${statBox(num(tot && tot.podi), "Podi")}${statBox(num(tot && tot.pole), "Pole")}${statBox(num(tot && tot.giri_veloci), "Giri veloci")}${statBox(num(tot && tot.titoli), "Titoli")}</div>
    <p class="muted" style="font-size:13px;margin-top:8px">${sm.nascita ? `Nato il ${dataIt(sm.nascita)}` : ""}${sm.luogo ? ` · ${esc(sm.luogo)}` : ""}${sm.debutto ? ` · debutto nel mondiale ${sm.debutto}` : ""}${sm.altezza ? ` · ${sm.altezza} cm` : ""}${sm.peso ? ` · ${sm.peso} kg` : ""}${tot ? ` · totali di tutte le classi (in MotoGP: ${tot.motogp.gare} GP, ${tot.motogp.vittorie} vittorie, ${tot.motogp.titoli} titoli), da <a href="${esc(tot.fonte)}" target="_blank" rel="noopener">Wikipedia</a>` : " · totali di carriera non ancora disponibili"}</p>
    ${sm.carriera.length ? `<h3 class="section-title">Carriera nel mondiale</h3><div class="table-wrap"><table class="results"><thead><tr><th>Anno</th><th>Classe</th><th>Team</th><th>N.</th></tr></thead><tbody>${[...sm.carriera].reverse().map((a) => a.classi.map((c) => `<tr><td>${a.anno}</td><td>${esc(c.categoria)}</td><td>${esc(c.team || "")}</td><td>${c.numero ?? ""}</td></tr>`).join("")).join("")}</tbody></table></div><p class="muted" style="font-size:12px;margin-top:8px">Dati dal servizio pubblico del campionato.</p>` : ""}` : ""}
    ${bioHtml(bio)}
    <h3 class="section-title">Gara per gara${migliore ? ` <span class="count">· miglior risultato ${migliore}°</span>` : ""}</h3>
    <div class="table-wrap"><table class="results"><thead><tr><th>Gran Premio</th><th>Data</th><th>Sprint</th><th>Gara</th><th>Punti</th></tr></thead><tbody>${
      [...gare].reverse().map((g) => `<tr class="${g.gara === 1 ? "podio" : ""}"><td><strong>${esc(g.gp)}</strong></td><td>${formattaData(g.data)}</td><td>${g.sprint ? g.sprint + "°" : "–"}</td><td>${esito(g)}</td><td><strong>${g.punti}</strong></td></tr>`).join("")
    }</tbody></table></div>
    <p class="muted" style="margin-top:18px;font-size:13px"><a class="accent" href="motogp.html${tema ? "?" + tema.slice(1) : ""}">← Torna alla MotoGP</a></p>`;
  const stat = (x) => {
    const g = x.gare, pod = g.filter((r) => r.gara && r.gara <= 3).length, best = g.map((r) => r.gara).filter(Boolean).sort((a, b) => a - b)[0];
    return { pos: x.pos, punti: x.punti ?? 0, vitt: x.vittorie ?? 0, podi: pod, best: best ?? null, gare: g.length };
  };
  const riga = (et, a, b, modo) => {   // modo: omesso = vince il valore più alto, "basso" = vince il più basso, "no" = nessuna evidenza
    const va = a ?? null, vb = b ?? null;
    const meglio = modo === "no" || va == null || vb == null || va === vb ? 0 : (modo === "basso" ? (va < vb ? 1 : 2) : (va > vb ? 1 : 2));
    const f = (v) => (v == null ? "n.d." : v);
    const suf = modo === "basso" ? "°" : "";
    return `<tr><td class="${meglio === 1 ? "conf-vince" : ""}">${f(va)}${va != null ? suf : ""}</td><td class="conf-et">${et}</td><td class="${meglio === 2 ? "conf-vince" : ""}">${f(vb)}${vb != null ? suf : ""}</td></tr>`;
  };
  const carr = (k, x) => {
    const c = SC[`moto:${k}`]; if (!c) return null;
    const anni = (c.carriera || []).length, inGp = (c.carriera || []).filter((r) => r.classi.some((q) => q.categoria === "MotoGP")).length;
    const eta = c.nascita ? Math.floor((Date.now() - new Date(c.nascita)) / 31557600000) : null;
    const classi = [...new Set((c.carriera || []).flatMap((r) => r.classi.map((q) => q.categoria)))].join(" → ");
    return { tot: c.totali || null, debutto: c.debutto ?? null, anni: anni || null, inGp: anni ? inGp : null, eta, altezza: c.altezza ?? null, peso: c.peso ?? null, classi };
  };
  document.getElementById("conf-sel").addEventListener("change", (e) => {
    const out = document.getElementById("conf-risultato");
    const q = dati[e.target.value]; if (!q) { out.innerHTML = ""; return; }
    const A = stat(p), B = stat(q), fq = FM[e.target.value], CA = carr(id, p), CB = carr(e.target.value, q);
    const gps = [...new Set([...p.gare, ...q.gare].map((r) => r.gp))];
    const get = (x, gp) => x.gare.find((r) => r.gp === gp);
    const es = (r) => (!r ? "–" : r.gara ? `${r.gara}°` : r.stato_gara && r.stato_gara !== "INSTND" ? "Rit." : "–");
    const testa = (x, ft, nome) => `<div class="conf-pil">${ft ? img(ft, nome, "foto-mini") : ""}<strong>${esc(nome)}</strong><span class="muted">${esc(x.team || "")}</span></div>`;
    out.innerHTML = `<div class="conf-testa">${testa(p, foto, p.nome)}<span class="conf-vs">VS</span>${testa(q, fq, q.nome)}</div>
      <table class="conf-tab"><tbody>${riga("Posizione", A.pos, B.pos, "basso")}${riga("Punti", A.punti, B.punti)}${riga("Vittorie", A.vitt, B.vitt)}${riga("Podi in gara", A.podi, B.podi)}${riga("Miglior risultato", A.best, B.best, "basso")}${riga("Gare disputate", A.gare, B.gare)}<tr><td colspan="3" class="conf-sub">In carriera</td></tr>${CA && CB ? `${CA.tot && CB.tot ? `${riga("Gran Premi", CA.tot.gare, CB.tot.gare)}${riga("Vittorie", CA.tot.vittorie, CB.tot.vittorie)}${riga("Podi", CA.tot.podi, CB.tot.podi)}${riga("Pole", CA.tot.pole, CB.tot.pole)}${riga("Giri veloci", CA.tot.giri_veloci, CB.tot.giri_veloci)}${riga("Titoli", CA.tot.titoli, CB.tot.titoli)}` : ""}${riga("Debutto nel mondiale", CA.debutto, CB.debutto, "no")}${riga("Stagioni nel mondiale", CA.anni, CB.anni)}${riga("Stagioni in MotoGP", CA.inGp, CB.inGp)}${riga("Età", CA.eta, CB.eta, "no")}${riga("Altezza (cm)", CA.altezza, CB.altezza, "no")}${riga("Peso (kg)", CA.peso, CB.peso, "no")}<tr><td class="conf-testo">${esc(CA.classi || "n.d.")}</td><td class="conf-et">Classi disputate</td><td class="conf-testo">${esc(CB.classi || "n.d.")}</td></tr>` : `<tr><td colspan="3" class="conf-et">Dati di carriera non disponibili per uno dei due piloti.</td></tr>`}</tbody></table><p class="muted" style="font-size:12px;margin:-8px 0 16px">Totali di carriera da Wikipedia, dove disponibili; sopra ci sono i dati della stagione.</p>
      <div class="table-wrap"><table class="results"><thead><tr><th>Gran Premio</th><th>${esc(p.nome.split(" ").slice(-1)[0])}</th><th>${esc(q.nome.split(" ").slice(-1)[0])}</th></tr></thead><tbody>${[...gps].reverse().map((gp) => `<tr><td>${esc(gp)}</td><td>${es(get(p, gp))}</td><td>${es(get(q, gp))}</td></tr>`).join("")}</tbody></table></div>`;
  });
} catch (e) {
  erroreCaricamento(box);
}
