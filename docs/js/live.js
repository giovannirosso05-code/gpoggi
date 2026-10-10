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
let team = {};
let timer = null;

const rosterP = fetchJSON("data/roster.json").then((r) => { for (const p of r) team[p.nome] = p; }).catch(() => {});

function tabella(righe, vuoto) {
  if (!righe.length) return `<p class="muted">${vuoto}</p>`;
  return `<div class="tab-scroll"><table class="live-tab-ris"><thead><tr><th>Pos</th><th>Pilota</th>${righe.some((r) => r.info) ? '<th class="dx">Tempo</th>' : ""}</tr></thead><tbody>${righe.map((r) =>
    `<tr><td class="pos">${esc(r.pos)}</td><td>${r.team ? stemma(r.team, r.colore) + " " : ""}<b>${esc(r.nome)}</b></td>${righe.some((x) => x.info) ? `<td class="dx">${esc(r.info || "")}</td>` : ""}</tr>`).join("")}</tbody></table></div>`;
}

async function caricaF1() {
  await rosterP;
  const d = await (await fetch(ESPN, { cache: "no-store" })).json();
  const ev = (d.events || [])[0];
  if (!ev) { box.innerHTML = `<p class="muted">Nessun weekend di Formula 1 in questo momento.</p>`; nota.textContent = ""; return false; }
  const sess = ev.competitions || [];
  const stato = (c) => c.status && c.status.type && c.status.type.state;
  const attiva = sess.find((c) => stato(c) === "in") || [...sess].reverse().find((c) => stato(c) === "post" && (c.competitors || []).length) || sess.find((c) => stato(c) === "pre");
  if (!attiva) { box.innerHTML = `<p class="muted">Nessuna sessione disponibile.</p>`; return false; }
  const sigla = attiva.type && attiva.type.abbreviation;
  const live = stato(attiva) === "in";
  const finita = stato(attiva) === "post";
  const righe = (attiva.competitors || []).slice().sort((a, b) => a.order - b.order).map((c) => {
    const nome = c.athlete && (c.athlete.displayName || c.athlete.fullName) || "—";
    const r = team[nome];
    return { pos: c.order, nome, team: r && r.team, colore: r && r.colore, info: "" };
  });
  const giro = live && attiva.status.period ? ` · giro ${attiva.status.period}` : "";
  box.innerHTML = `<div class="live-testa"><h2>${live ? '<i class="live-dot"></i>' : ""}${esc(SIGLE[sigla] || sigla || "Sessione")}</h2>
    <span class="muted">${esc(ev.name || "")}${giro}${finita ? " · terminata" : ""}</span></div>` +
    tabella(righe, "La sessione non è ancora iniziata: la classifica compare qui appena parte.");
  nota.innerHTML = "Ordine provvisorio, aggiornato ogni pochi secondi. Fonte: ESPN, non ufficiale e può avere ritardo; le penalità non sono conteggiate. Non sono qui i tempi sul giro.";
  return live;
}

async function caricaMoto() {
  nota.innerHTML = "Fonte: MotoGP.com (non ufficiale qui, può avere ritardo). <a class='accent' href='https://www.motogp.com/en/live-timing' target='_blank' rel='noopener'>Apri il live timing ufficiale →</a>";
  if (!WORKER) { box.innerHTML = `<p class="muted">I tempi dal vivo MotoGP non sono ancora collegati.</p>`; return false; }
  let d = null;
  try { d = await (await fetch(WORKER + "/live/motogp", { cache: "no-store" })).json(); } catch (e) {}
  if (!d || !d.ok || !d.piloti.length) {
    box.innerHTML = `<p class="muted">Nessuna sessione MotoGP in corso, o i tempi dal vivo non sono disponibili in questo momento. Controlla il <a class="accent" href="https://www.motogp.com/en/live-timing" target="_blank" rel="noopener">live timing ufficiale</a>.</p>`;
    return false;
  }
  const righe = d.piloti.sort((a, b) => a.pos - b.pos).map((p) => ({ pos: p.pos, nome: p.nome || ("#" + p.numero), info: [p.tempo, p.distacco].filter(Boolean).join(" · ") }));
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
