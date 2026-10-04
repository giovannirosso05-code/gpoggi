import { renderHeader, renderFooter, fetchJSON, esc, img, punti, stemma, erroreCaricamento } from "./common.js";

renderHeader("classifiche");
renderFooter();

const box = document.getElementById("classifiche-box");
const barra = document.getElementById("serie-barra");
const SERIE = {
  f1: { archivio: "archivio.html", etichetta: "Archivio storico F1 →" },
  f2: { archivio: "archivio.html", etichetta: "Archivio storico F1 →" },
  f3: { archivio: "archivio.html", etichetta: "Archivio storico F1 →" },
  motogp: { archivio: "motogp-archivio.html", etichetta: "Archivio storico MotoGP →" },
  moto2: { archivio: "motogp-archivio.html", etichetta: "Archivio storico MotoGP →" },
  moto3: { archivio: "motogp-archivio.html", etichetta: "Archivio storico MotoGP →" },
};
const dati = {};
const carica = async (k, url) => dati[k] || (dati[k] = await fetchJSON(url));
const colonne = (a, b) => `<div class="two-col"><div><h3 class="section-title" style="margin-top:0">${a.titolo}</h3>${a.html}</div><div><h3 class="section-title" style="margin-top:0">${b.titolo}</h3>${b.html}</div></div>`;
const tab = (intest, righe) => `<div class="table-wrap"><table class="results"><thead><tr>${intest.map((x) => `<th>${x}</th>`).join("")}</tr></thead><tbody>${righe}</tbody></table></div>`;

async function f1() {
  const [s, roster] = await Promise.all([carica("f1", "data/standings.json"), carica("roster", "data/roster.json")]);
  const foto = Object.fromEntries(roster.filter((p) => p.foto).map((p) => [p.numero, p.foto]));
  if (!s.piloti.length) return { html: `<p class="muted center">Classifiche non ancora disponibili: nessuna gara disputata.</p>` };
  return {
    sotto: s.dopo ? `Stagione ${new Date().getFullYear()} · aggiornate dopo il ${s.dopo}` : "",
    fonte: `Dati: <a href="https://openf1.org/" target="_blank" rel="noopener">OpenF1</a> (uso non commerciale). Foto: Wikimedia Commons, vedi i <a href="crediti.html">crediti</a>.`,
    html: colonne(
      { titolo: "Piloti", html: tab(["Pos", "Pilota", "Team", "Punti"], s.piloti.map((p) => `<tr class="${p.posizione <= 3 ? "podio" : ""}"><td>${p.posizione}</td>
        <td><a class="cella-pilota" href="pilota.html?n=${p.numero}">${foto[p.numero] ? img(foto[p.numero], p.nome || "", "foto-mini") : '<span class="foto-mini"></span>'}<strong>${esc(p.nome || "Pilota #" + p.numero)}</strong></a></td>
        <td><span class="cella-team">${stemma(p.team, p.colore)}${esc(p.team || "")}</span></td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")) },
      { titolo: "Costruttori", html: tab(["Pos", "Team", "Punti"], s.costruttori.map((c) => `<tr class="${c.posizione <= 3 ? "podio" : ""}"><td>${c.posizione}</td><td><span class="cella-team">${stemma(c.team, c.colore)}<strong>${esc(c.team)}</strong></span></td><td><strong>${punti(c.punti)}</strong></td></tr>`).join("")) }),
  };
}

async function moto(cat) {
  const [c, cal] = await Promise.all([carica("motogp", "data/motogp-classifica.json"), carica("motogp-cal", "data/motogp.json")]);
  const piloti = (c.categorie || {})[cat] || [];
  if (!piloti.length) return { html: `<p class="muted center">Classifica non disponibile.</p>` };
  const team = {};
  piloti.forEach((p) => { const t = (team[p.team] ||= { team: p.team, moto: p.moto, punti: 0 }); t.punti += p.punti; });
  const squadre = Object.values(team).sort((a, b) => b.punti - a.punti);
  const tema = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";
  return {
    sotto: `Stagione ${new Date().getFullYear()} · dati aggiornati al ${new Date(cal.generato_il).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" })}`,
    fonte: `Dati dal servizio pubblico del campionato, per uso non commerciale. Sito non ufficiale, non affiliato a MotoGP o Dorna. Schede dei piloti nella <a href="motogp.html">pagina MotoGP</a>.`,
    html: colonne(
      { titolo: "Piloti", html: tab(["Pos", "Pilota", "Moto", "Punti", "Vitt."], piloti.map((p) => `<tr class="${p.pos <= 3 ? "podio" : ""}"><td>${p.pos}</td>
        <td><a class="link-nome" href="pilota-moto.html?id=${esc(p.id)}${tema}"><strong>${esc(p.nome)}</strong></a> <span class="muted">#${p.numero ?? ""}</span></td>
        <td><span class="cella-team">${stemma(p.moto)}${esc(p.moto)}</span></td><td><strong>${punti(p.punti)}</strong></td><td>${p.vittorie}</td></tr>`).join("")) },
      { titolo: "Team", html: tab(["Pos", "Team", "Punti"], squadre.map((t, i) => `<tr class="${i < 3 ? "podio" : ""}"><td>${i + 1}</td><td><span class="cella-team">${stemma(t.moto)}<strong>${esc(t.team)}</strong></span></td><td><strong>${punti(t.punti)}</strong></td></tr>`).join("")) + `<p class="muted" style="font-size:12px;margin-top:8px">Punti dei team: somma dei punti dei loro piloti.</p>` }),
  };
}

async function formula(k) {
  const d = await carica(k, `data/${k}.json`);
  return {
    sotto: `Stagione ${d.anno} · dati aggiornati al ${new Date(d.aggiornato).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" })}`,
    fonte: `Fonte: <a href="${esc(d.fonte)}" target="_blank" rel="noopener">Wikipedia</a>, testo con licenza ${esc(d.licenza)}. Sito non ufficiale, non affiliato a FIA, Formula 2 o Formula 3.`,
    html: colonne(
      { titolo: "Piloti", html: tab(["Pos", "Pilota", "Team", "Punti"], d.piloti.map((p) => `<tr class="${p.pos && p.pos <= 3 ? "podio" : ""}"><td>${p.pos ?? "NC"}</td><td><strong>${esc(p.nome)}</strong></td><td>${esc(p.team || "n.d.")}</td><td><strong>${punti(p.punti)}</strong></td></tr>`).join("")) },
      { titolo: "Team", html: tab(["Pos", "Team", "Punti"], d.team.map((t) => `<tr class="${t.pos <= 3 ? "podio" : ""}"><td>${t.pos}</td><td><strong>${esc(t.team)}</strong></td><td><strong>${punti(t.punti)}</strong></td></tr>`).join("")) }),
  };
}

async function mostra(k) {
  const info = SERIE[k] || SERIE.f1;
  document.getElementById("link-archivio").href = info.archivio;
  document.getElementById("link-archivio").textContent = info.etichetta;
  box.innerHTML = `<p class="muted">Caricamento…</p>`;
  try {
    const r = k === "f1" ? await f1() : k.startsWith("moto") ? await moto({ motogp: "MotoGP", moto2: "Moto2", moto3: "Moto3" }[k]) : await formula(k);
    document.getElementById("dopo").textContent = r.sotto || "";
    document.getElementById("fonte").innerHTML = r.fonte || "";
    box.innerHTML = r.html;
  } catch (e) { erroreCaricamento(box); }
}

const richiesta = (new URLSearchParams(location.search).get("serie") || "").toLowerCase();
let corrente = SERIE[richiesta] ? richiesta : "f1";
function scegli(k) {
  corrente = k;
  barra.querySelectorAll("[data-s]").forEach((b) => b.classList.toggle("active", b.dataset.s === k));
  mostra(k);
}
barra.addEventListener("click", (e) => {
  const b = e.target.closest("[data-s]");
  if (!b) return;
  const t = document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "";
  history.replaceState(null, "", `?serie=${b.dataset.s}${t}`);
  scegli(b.dataset.s);
});
scegli(corrente);
