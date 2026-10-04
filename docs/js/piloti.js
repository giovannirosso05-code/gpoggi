import { renderHeader, renderFooter, fetchJSON, fotoMotoMap, esc, img, punti, ICON_SEARCH, erroreCaricamento } from "./common.js";

renderHeader("piloti");
renderFooter();
document.getElementById("search-icon").innerHTML = ICON_SEARCH;

const ANNI = 20;
const SERIE = [["f1", "Formula 1"], ["motogp", "MotoGP"], ["moto2", "Moto2"], ["moto3", "Moto3"], ["f2", "Formula 2"], ["f3", "Formula 3"]];
const tema = () => (document.documentElement.dataset.theme ? "&tema=" + document.documentElement.dataset.theme : "");
const norm = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
const iniziali = (n) => n.split(/\s+/).filter(Boolean).map((w) => w[0]).slice(0, 2).join("").toUpperCase();

const D = {};
let serie = new URLSearchParams(location.search).get("serie") || "f1";
if (!SERIE.some(([k]) => k === serie)) serie = "f1";
let modo = "oggi";
const teamAttivi = new Set();

function card(c) {
  const corpo = `<div class="driver-card-image">
      ${c.foto ? img(c.foto, c.nome) : ""}
      ${c.pos ? `<span class="pos-badge">${c.pos}°</span>` : ""}
      <span class="driver-number ${c.foto ? "" : "solo"}">${esc(c.grande ?? "")}</span>
    </div>
    <div class="driver-card-info">
      <div class="name">${esc(c.nome)}</div>
      <div class="team">${esc(c.team || "Team n.d.")}</div>
      <div class="numero">${c.riga}</div>
    </div>`;
  const stile = `style="--team:#${esc(c.colore || "8b8a92")}"`;
  return c.href ? `<a class="driver-card${c.foto ? "" : " nofoto"}" href="${esc(c.href)}" ${stile}>${corpo}</a>` : `<div class="driver-card senza-link${c.foto ? "" : " nofoto"}" ${stile}>${corpo}</div>`;
}

const pt = (v) => `<b>${v != null ? punti(v) : "n.d."}</b> punti`;

function elenco() {
  if (serie === "f1") {
    if (modo === "oggi") return D.roster.map((p) => ({ nome: p.nome || "Pilota #" + p.numero, team: p.team, colore: p.colore, foto: p.foto, pos: p.posizione, grande: p.numero, riga: pt(p.punti), href: `pilota.html?n=${p.numero}${tema()}` }));
    const attuali = new Set(D.roster.map((p) => norm(p.nome)));
    const da = D.anno - ANNI + 1;
    return [...D.roster.map((p) => ({ nome: p.nome, team: p.team, colore: p.colore, foto: p.foto, grande: p.numero, riga: `<b>${D.anno}</b> · in pista oggi`, href: `pilota.html?n=${p.numero}${tema()}`, ordine: 9999 })),
      ...D.storici.filter((p) => p.stagioni[p.stagioni.length - 1] >= da && !attuali.has(norm(p.nome))).map((p) => ({
        nome: p.nome, team: p.team[p.team.length - 1], foto: D.foto[norm(p.nome)], grande: iniziali(p.nome),
        riga: `<b>${p.stagioni[0]}–${p.stagioni[p.stagioni.length - 1]}</b>${p.titoli ? ` · ${p.titoli} ${p.titoli === 1 ? "titolo" : "titoli"}` : ""}${p.vittorie ? ` · ${p.vittorie} vitt.` : ""}`,
        href: `storico.html?id=${p.id}${tema()}`, ordine: p.stagioni[p.stagioni.length - 1] }))]
      .sort((a, b) => b.ordine - a.ordine || (a.pos ?? 999) - (b.pos ?? 999) || a.nome.localeCompare(b.nome));
  }
  if (serie === "motogp" || serie === "moto2" || serie === "moto3") {
    const cat = { motogp: "MotoGP", moto2: "Moto2", moto3: "Moto3" }[serie];
    const attuali = Object.values(D.motoPiloti).filter((p) => p.categoria === cat).sort((a, b) => (a.pos ?? 999) - (b.pos ?? 999));
    const lista = attuali.map((p) => ({ nome: p.nome, team: p.team, pos: p.pos, foto: D.fotoMoto[p.id], grande: p.numero ?? iniziali(p.nome), riga: pt(p.punti), href: `pilota-moto.html?id=${p.id}${tema()}`, ordine: 9999 }));
    if (serie !== "motogp" || modo === "oggi") return lista;
    const noti = new Set(attuali.map((p) => norm(p.nome)));
    const da = D.anno - ANNI;
    const vecchi = new Map();
    for (const s of D.motoArch.filter((s) => s.anno > da && s.anno <= D.anno)) {
      for (const r of s.classifica) {
        if (!r.nome || noti.has(norm(r.nome))) continue;
        const v = vecchi.get(norm(r.nome)) || { nome: r.nome, anni: [], titoli: 0, migliore: 99, team: "" };
        v.anni.push(s.anno); v.team = r.team || v.team; v.migliore = Math.min(v.migliore, r.pos || 99); if (r.pos === 1) v.titoli++;
        vecchi.set(norm(r.nome), v);
      }
    }
    return [...lista, ...[...vecchi.values()].map((v) => {
      const u = Math.max(...v.anni), pr = Math.min(...v.anni);
      return { nome: v.nome, team: v.team, grande: iniziali(v.nome), foto: D.foto[norm(v.nome)],
        riga: `<b>${pr}${u !== pr ? "–" + u : ""}</b>${v.titoli ? ` · ${v.titoli} ${v.titoli === 1 ? "titolo" : "titoli"}` : ""} · miglior pos. ${v.migliore}°`,
        href: `storico-moto.html?n=${encodeURIComponent(v.nome)}${tema()}`, ordine: u };
    })].sort((a, b) => b.ordine - a.ordine || (a.pos ?? 999) - (b.pos ?? 999) || a.nome.localeCompare(b.nome));
  }
  const f = D[serie];
  return f.piloti.map((p) => ({ nome: p.nome, team: p.team, pos: p.pos, grande: iniziali(p.nome), riga: pt(p.punti), href: `classifiche.html?serie=${serie}${tema()}` }));
}

function disegna() {
  const tutti = elenco();
  const pills = document.getElementById("category-pills");
  const teams = [...new Set(tutti.filter((p) => p.ordine == null || p.ordine === 9999).map((p) => p.team).filter(Boolean))].sort();
  pills.innerHTML = teams.map((t) => `<button class="pill ${teamAttivi.has(t) ? "active" : ""}" data-team="${esc(t)}">${esc(t)}</button>`).join("");
  const q = norm(document.getElementById("search").value);
  const lista = tutti.filter((p) => (teamAttivi.size === 0 || teamAttivi.has(p.team)) && (!q || norm(p.nome).includes(q) || norm(p.team).includes(q) || String(p.grande).toLowerCase() === q));
  document.getElementById("result-count").textContent = `(${lista.length})`;
  document.getElementById("piloti-grid").innerHTML = lista.length ? lista.map(card).join("") : `<p class="muted" style="grid-column:1/-1">Nessun pilota trovato.</p>`;
}

function barre() {
  document.getElementById("serie-pills").innerHTML = SERIE.map(([k, n]) => `<button class="pill ${k === serie ? "active" : ""}" data-serie="${k}">${n}</button>`).join("");
  const m = document.getElementById("modo-pills");
  m.hidden = !(serie === "f1" || serie === "motogp");
  m.innerHTML = [["oggi", "In pista oggi"], ["storici", `Ultimi ${ANNI} anni`]].map(([k, n]) => `<button class="pill ${k === modo ? "active" : ""}" data-modo="${k}">${n}</button>`).join("");
}

try {
  const [roster, storici, motoPiloti, motoArch, f2, f3, meta, foto, fotoMoto] = await Promise.all([
    fetchJSON("data/roster.json"), fetchJSON("data/storici.json"), fetchJSON("data/motogp-piloti.json"), fetchJSON("data/motogp-archivio.json"),
    fetchJSON("data/f2.json").catch(() => ({ piloti: [] })), fetchJSON("data/f3.json").catch(() => ({ piloti: [] })),
    fetchJSON("data/meta.json").catch(() => ({})), fetchJSON("data/foto-storici.json").catch(() => []), fotoMotoMap()]);
  Object.assign(D, { fotoMoto, roster, storici: storici.piloti, motoPiloti, motoArch: motoArch.anni, f2, f3 });
  D.foto = Object.fromEntries(foto.map((f) => [norm(f.nome), f.foto]));
  D.anno = Math.max(...storici.piloti.flatMap((p) => p.stagioni), new Date().getFullYear() - 1);
  barre();
  document.getElementById("serie-pills").addEventListener("click", (e) => {
    const b = e.target.closest("[data-serie]");
    if (!b) return;
    serie = b.dataset.serie; modo = "oggi"; teamAttivi.clear(); barre(); disegna();
  });
  document.getElementById("modo-pills").addEventListener("click", (e) => {
    const b = e.target.closest("[data-modo]");
    if (!b) return;
    modo = b.dataset.modo; teamAttivi.clear(); barre(); disegna();
  });
  document.getElementById("category-pills").addEventListener("click", (e) => {
    const b = e.target.closest(".pill");
    if (!b) return;
    teamAttivi.has(b.dataset.team) ? teamAttivi.delete(b.dataset.team) : teamAttivi.add(b.dataset.team);
    disegna();
  });
  document.getElementById("search").addEventListener("input", disegna);
  disegna();
} catch (e) {
  erroreCaricamento(document.getElementById("piloti-grid"));
}
