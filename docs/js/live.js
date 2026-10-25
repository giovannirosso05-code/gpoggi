import { renderHeader, renderFooter, fetchJSON, esc, stemma } from "./common.js";

renderHeader("live");
renderFooter();

// Indirizzo del Worker del bot (rotta /live/motogp). Vuoto = MotoGP non collegato: si mostra solo il rimando al sito ufficiale.
const WORKER = "https://gpoggi-bot.giovannirosso05.workers.dev";
const ESPN = "https://site.api.espn.com/apis/site/v2/sports/racing/f1/scoreboard";
const SIGLE = { FP1: "Prove libere 1", FP2: "Prove libere 2", FP3: "Prove libere 3", SS: "Qualifiche sprint", SR: "Sprint", Qual: "Qualifiche", Race: "Gara" };

const box = document.getElementById("live-box"), nota = document.getElementById("live-nota");
const tab = document.querySelectorAll(".live-tab button");
let serie = new URLSearchParams(location.search).get("serie") === "moto" ? "moto" : "f1";
const norm = (t) => String(t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
let team = {};   // per nome senza accenti: ESPN scrive «Nico Hülkenberg», il roster «Nico Hulkenberg»
let timer = null;

const rosterP = fetchJSON("data/roster.json").then((r) => { for (const p of r) team[norm(p.nome)] = p; }).catch(() => {});

function tabella(righe, vuoto) {
  if (!righe.length) return `<p class="muted">${vuoto}</p>`;
  const conInfo = righe.some((r) => r.info), conPart = righe.some((r) => r.start != null);
  const diff = (r) => r.start == null ? "" : r.start - r.pos > 0 ? `<span class="su">▲ ${r.start - r.pos}</span>` : r.start - r.pos < 0 ? `<span class="giu">▼ ${r.pos - r.start}</span>` : `<span class="pari">=</span>`;
  return `<div class="tab-scroll"><table class="live-tab-ris"><thead><tr><th>Pos</th><th>Pilota</th>${conInfo ? '<th class="dx">Tempo</th>' : ""}${conPart ? '<th class="dx">Part.</th><th class="dx">+/−</th>' : ""}</tr></thead><tbody>${righe.map((r) =>
    `<tr><td class="pos">${esc(r.pos)}</td><td>${r.team ? stemma(r.team, r.colore) + " " : ""}<b>${esc(r.nome)}</b></td>${conInfo ? `<td class="dx">${esc(r.info || "")}</td>` : ""}${conPart ? `<td class="dx">${r.start == null ? "" : esc(r.start)}</td><td class="dx diff">${diff(r)}</td>` : ""}</tr>`).join("")}</tbody></table></div>`;
}

// Posizioni di partenza della gara in corso (ordine delle qualifiche: le penalità non sono conteggiate): nome senza accenti -> posizione
async function partenze(serie) {
  try {
    const mappa = {};
    if (serie === "moto") {
      const d = await fetchJSON("data/motogp-griglia.json");
      for (const r of (d && d.righe) || []) mappa[norm(r.nome)] = r.pos;
      return mappa;
    }
    const ev = await fetchJSON("data/events.json");
    const g = ev.filter((x) => new Date(x.fine).getTime() > Date.now() - 6 * 36e5).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
    if (!g) return mappa;
    const det = await fetchJSON(`data/gare/${g.id}.json`);
    const q = (det.sessioni || []).find((x) => x.tipo === "Qualifying");
    for (const r of (q && q.risultati) || []) if (r.pos) mappa[norm(r.nome)] = r.pos;
    return mappa;
  } catch (e) { return {}; }
}

async function caricaF1() {
  await rosterP;
  const d = await (await fetch(ESPN, { cache: "no-store" })).json();
  const ev = (d.events || [])[0];
  if (!ev) { await nessunaLive("f1"); return false; }
  const sess = ev.competitions || [];
  const stato = (c) => c.status && c.status.type && c.status.type.state;
  const attiva = sess.find((c) => stato(c) === "in") || [...sess].reverse().find((c) => stato(c) === "post" && (c.competitors || []).length) || sess.find((c) => stato(c) === "pre");
  if (!attiva) { await nessunaLive("f1"); return false; }
  const sigla = attiva.type && attiva.type.abbreviation;
  const live = stato(attiva) === "in";
  if (!live) { await nessunaLive("f1"); return false; }
  const finita = stato(attiva) === "post";
  const part = sigla === "Race" ? await partenze("f1") : {};
  const righe = (attiva.competitors || []).slice().sort((a, b) => a.order - b.order).map((c) => {
    const nome = c.athlete && (c.athlete.displayName || c.athlete.fullName) || "—";
    const r = team[norm(nome)];
    return { pos: c.order, nome, team: r && r.team, colore: r && r.colore, info: "", start: part[norm(nome)] ?? null };
  });
  const giro = live && attiva.status.period ? ` · giro ${attiva.status.period}` : "";
  box.innerHTML = `<div class="live-testa"><h2>${live ? '<i class="live-dot"></i>' : ""}${esc(SIGLE[sigla] || sigla || "Sessione")}</h2>
    <span class="muted">${esc(ev.name || "")}${giro}${finita ? " · terminata" : ""}</span></div>` +
    tabella(righe, "La sessione non è ancora iniziata: la classifica compare qui appena parte.");
  nota.innerHTML = "Ordine provvisorio, aggiornato ogni pochi secondi. Fonte: ESPN, non ufficiale e può avere ritardo; le penalità non sono conteggiate. Non sono qui i tempi sul giro." +
    (righe.some((r) => r.start != null) ? " Part. = posizione di partenza, presa dall'ordine delle qualifiche (penalità e partenze dai box non sono conteggiate); +/− = posizioni guadagnate (▲) o perse (▼)." : "");
  return live;
}

// Quando non c'è niente dal vivo: invece di un messaggio d'errore, si porta alla pagina dell'ultima gara
async function ultimaGara(serie) {
  try {
    if (serie === "moto") {
      const u = await fetchJSON("data/motogp-ultima.json");
      return u && u.nome ? { nome: u.nome, href: `gara-moto.html?gp=${encodeURIComponent(u.nome)}` } : null;
    }
    const ev = await fetchJSON("data/events.json");
    const finiti = ev.filter((g) => new Date(g.fine).getTime() < Date.now()).sort((a, b) => new Date(b.inizio) - new Date(a.inizio));
    return finiti[0] ? { nome: finiti[0].nome, href: `gara.html?id=${finiti[0].id}` } : null;
  } catch (e) { return null; }
}

// Subito dopo le qualifiche e fino alla partenza: la griglia di partenza. È l'ordine delle qualifiche (provvisoria: le penalità non sono ancora applicate).
async function grigliaProssima(serie) {
  try {
    await rosterP;
    if (serie === "moto") {
      const d = await fetchJSON("data/motogp-griglia.json");
      if (!d || !d.righe || !d.righe.length || new Date(d.gara_inizio).getTime() < Date.now()) return null;
      return { titolo: d.gp, inizio: d.gara_inizio, righe: d.righe.map((r) => ({ pos: r.pos, nome: r.nome, info: r.info || "" })),
               avviso: "Griglia provvisoria: è l'ordine delle qualifiche. Le penalità non sono ancora applicate: la griglia ufficiale la pubblica la MotoGP dopo le qualifiche." };
    }
    const ev = await fetchJSON("data/events.json");
    const adesso = Date.now();
    const g = ev.filter((x) => new Date(x.fine).getTime() > adesso).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
    if (!g) return null;
    const qual = g.sessioni.find((s) => s.nome === "Qualifiche"), gara = g.sessioni.find((s) => s.nome === "Gara");
    if (!qual || !gara || new Date(qual.fine).getTime() > adesso || new Date(gara.inizio).getTime() < adesso) return null;
    const det = await fetchJSON(`data/gare/${g.id}.json`);
    const q = (det.sessioni || []).find((s) => s.tipo === "Qualifying");
    const righe = ((q && q.risultati) || []).filter((r) => r.pos).sort((a, b) => a.pos - b.pos);
    if (!righe.length) return null;
    return { titolo: g.nome, inizio: gara.inizio, righe: righe.map((r) => { const t = team[norm(r.nome)]; return { pos: r.pos, nome: r.nome, team: t && t.team, colore: t && t.colore, info: r.tempo || "" }; }),
             avviso: "Griglia provvisoria: è l'ordine delle qualifiche. Penalità e partenze dai box non sono ancora applicate: la griglia ufficiale è il documento FIA «Final Starting Grid», che arriva dopo le qualifiche." };
  } catch (e) { return null; }
}

async function nessunaLive(serie) {
  const [g, gr] = await Promise.all([ultimaGara(serie), grigliaProssima(serie)]);
  nota.textContent = "";
  const quando = gr && new Date(gr.inizio).toLocaleString("it-IT", { weekday: "long", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Rome" });
  box.innerHTML = `<p class="live-vuoto">Al momento non c'è nessuna sessione dal vivo.</p>` +
    (gr ? `<div class="live-testa"><h2>Griglia di partenza · provvisoria</h2><span class="muted">${esc(gr.titolo)} · gara ${esc(quando)}</span></div>${tabella(gr.righe, "")}<p class="live-avviso">${esc(gr.avviso)}</p>` : "") +
    (g ? `<a class="live-ultima" href="${g.href}">Vuoi vedere l'ultima gara? ${esc(g.nome)} →</a>` : "");
}

async function caricaMoto() {
  if (!WORKER) { await nessunaLive("moto"); return false; }
  let d = null;
  try { d = await (await fetch(WORKER + "/live/motogp", { cache: "no-store" })).json(); } catch (e) {}
  if (!d || !d.ok || !d.piloti.length) { await nessunaLive("moto"); return false; }
  nota.innerHTML = "Fonte: MotoGP.com (non ufficiale qui, può avere ritardo). <a class='accent' href='https://www.motogp.com/en/live-timing' target='_blank' rel='noopener'>Apri il live timing ufficiale →</a>";
  const gara = /gara|race|rac/i.test(d.sessione || "") && !/sprint|spr/i.test(d.sessione || "");
  const part = gara ? await partenze("moto") : {};
  const righe = d.piloti.sort((a, b) => a.pos - b.pos).map((p) => ({ pos: p.pos, nome: p.nome || ("#" + p.numero), info: [p.tempo, p.distacco].filter(Boolean).join(" · "), start: part[norm(p.nome)] ?? null }));
  box.innerHTML = `<div class="live-testa"><h2><i class="live-dot"></i>${esc(d.sessione || "MotoGP")}</h2><span class="muted">${d.giri ? "giro " + esc(d.giri) : ""}</span></div>` + tabella(righe, "");
  return true;
}

async function aggiorna() {
  clearTimeout(timer);
  let live = false;
  try { live = await (serie === "f1" ? caricaF1() : caricaMoto()); }
  catch (e) { box.innerHTML = `<p class="muted">Impossibile leggere i dati dal vivo adesso. Riprova tra poco.</p>`; }
  timer = setTimeout(aggiorna, live ? 10000 : 60000);
}

function scegli(s) {
  serie = s;
  tab.forEach((b) => b.classList.toggle("on", b.dataset.s === s));
  document.body.classList.toggle("serie-moto", s === "moto");
  aggiorna();
}
tab.forEach((b) => b.addEventListener("click", () => scegli(b.dataset.s)));
document.addEventListener("visibilitychange", () => { if (!document.hidden) aggiorna(); });
scegli(serie);
