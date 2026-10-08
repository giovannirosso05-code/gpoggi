import { fetchJSON, esc, VOTI_URL } from "./common.js";

const base = VOTI_URL.replace(/\/$/, "");
const $ = (id) => document.getElementById(id);
let chiave = "";
try { chiave = sessionStorage.getItem("adm-k") || ""; } catch (e) {}

async function api(percorso, params = {}) {
  const u = new URL(base + percorso);
  u.searchParams.set("k", chiave);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  let r;
  try { r = await fetch(u); } catch (e) { throw new Error("Chiave non valida, oppure il Worker non è ancora aggiornato."); }
  if (!r.ok) {
    // il Worker risponde 404 anche quando il nickname non esiste: in quel caso c'è il motivo nel testo
    const j = await r.json().catch(() => null);
    throw new Error(j && j.errore ? "Errore: " + j.errore : r.status === 404 ? "Chiave non valida, oppure il Worker non è ancora aggiornato." : "Errore " + r.status);
  }
  return r.json();
}

const PUNTI_POSIZIONE = [10, 5, 2];
function punteggio(podio, vero) {
  let pt = 0, esatti = 0;
  podio.forEach((n, i) => { if (vero[i] === String(n)) { pt += PUNTI_POSIZIONE[i]; esatti++; } else if (vero.includes(String(n))) pt += 1; });
  return pt + (esatti === 3 ? 5 : 0);
}
function punti(v, r) {
  let pt = punteggio(v.podio, r.vero);
  if (v.pole && r.pole && String(v.pole) === String(r.pole) && (!r.qInizio || (v.tp || v.ts || 0) <= r.qInizio)) pt += 7;
  if (v.giro && r.giro && String(v.giro) === String(r.giro)) pt += 1;
  return pt;
}
const chiaveMoto = (nome) => "m" + nome.replace(/\W/g, "").slice(0, 38);
const quando = (ts) => new Date(ts).toLocaleString("it-IT", { timeZone: "Europe/Rome", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

async function carica() {
  const [eventi, roster, motoCl, motoGare, orari, motoCal] = await Promise.all([
    fetchJSON("data/events.json"), fetchJSON("data/roster.json"), fetchJSON("data/motogp-classifica.json").catch(() => ({ piloti: [] })),
    fetchJSON("data/motogp-gare.json").catch(() => ({})), fetchJSON("data/gara-orari.json").catch(() => ({})), fetchJSON("data/motogp.json").catch(() => ({ weekend: [] }))]);
  const nomiF1 = Object.fromEntries(roster.filter((p) => p.nome).map((p) => [String(p.numero), p.nome]));
  const nomiMoto = Object.fromEntries((motoCl.piloti || []).map((p) => [String(p.numero), p.nome]));
  const gare = {};
  for (const g of eventi) gare[String(g.id)] = { serie: "F1", nome: g.nome, ev: g };
  for (const w of motoCal.weekend || []) gare[chiaveMoto(w.nome)] = { serie: "MotoGP", nome: w.nome, moto: null };
  for (const n of Object.keys(motoGare)) gare[chiaveMoto(n)] = { serie: "MotoGP", nome: n, moto: motoGare[n] };
  return { nomiF1, nomiMoto, gare, orari };
}

async function podioVero(d, chiaveGara) {
  const g = d.gare[chiaveGara];
  if (!g) return null;
  if (g.serie === "F1") {
    try {
      const dett = await fetchJSON(`data/gare/${chiaveGara}.json`);
      const sess = dett.sessioni.find((x) => x.tipo === "Race" && x.risultati && x.risultati.length);
      if (!sess) return null;
      const quali = dett.sessioni.find((x) => x.tipo === "Qualifying"), primoQ = quali && (quali.risultati || []).find((r) => r.pos === 1);
      const cron = await fetchJSON(`data/cronaca/${chiaveGara}.json`).catch(() => null);
      return { vero: sess.risultati.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos).map((r) => String(r.numero)), inizio: new Date(sess.inizio).getTime(),
        pole: primoQ ? String(primoQ.numero) : null, qInizio: quali ? new Date(quali.inizio).getTime() : null, giro: cron && cron.giro_veloce != null ? String(cron.giro_veloce) : null };
    } catch (e) { return null; }
  }
  const righe = g.moto && (g.moto.classifiche || {}).MotoGP;
  if (!righe || !righe.length) return null;
  return { pole: g.moto.pole != null ? String(g.moto.pole) : null, giro: g.moto.giro_veloce != null ? String(g.moto.giro_veloce) : null, qInizio: d.orari["q:" + chiaveGara] ? new Date(d.orari["q:" + chiaveGara]).getTime() : null,
    vero: righe.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos).map((r) => String(r.numero)), inizio: d.orari[chiaveGara] ? new Date(d.orari[chiaveGara]).getTime() : new Date(g.moto.data + "T23:59:59Z").getTime() };
}

async function mostra() {
  const d = await carica();
  const [pub, tutti, sosp] = await Promise.all([
    fetch(base + "/pronostici").then((r) => r.json()).then((j) => j.pronostici || []),
    api("/voti-admin").then((j) => j.voti), api("/sospetti").then((j) => j.sospetti).catch(() => [])]);
  const sospetti = new Set();
  for (const s of sosp) for (const n of s.nickname) sospetti.add(n.nick.toLowerCase());

  // classifica del premio, calcolata come sul sito
  const perGp = {};
  for (const x of pub) (perGp[x.gp] ||= []).push(x);
  const classifica = {};
  for (const k of Object.keys(perGp)) {
    const r = await podioVero(d, k);
    if (!r) continue;
    for (const x of perGp[k]) {
      if (!x.podio || x.ts > (r.qInizio || r.inizio)) continue;
      const o = (classifica[x.nick] ||= { nick: x.nick, f1: 0, mo: 0, gare: 0 });
      o[d.gare[k].serie === "F1" ? "f1" : "mo"] += punti(x, r);
      o.gare++;
    }
  }
  const lista = Object.values(classifica).map((o) => ({ ...o, tot: o.f1 + o.mo })).sort((a, b) => b.tot - a.tot || b.gare - a.gare || a.nick.localeCompare(b.nick)).slice(0, 10);
  let primo = false;
  const righe = [];
  for (const v of lista) {
    let email = null;
    try { email = ((await api("/vincitore", { nick: v.nick })).email || []).map((e) => e.email).find(Boolean) || null; } catch (e) {}
    const sosp = sospetti.has(v.nick.toLowerCase());
    let nota = "";
    if (email && !sosp && !primo) { nota = `<span class="ok">IDONEO: primo con email</span>`; primo = true; }
    else if (!email) nota = `<span class="muted">senza email</span>`;
    else if (sosp) nota = `<span class="no">controlla: nickname collegati</span>`;
    righe.push(`<tr><td>${righe.length + 1}</td><td><b>${esc(v.nick)}</b></td><td>${v.f1}</td><td>${v.mo}</td><td>${v.gare}</td><td><b>${v.tot}</b></td><td>${email ? esc(email) : "—"}</td><td>${nota}</td></tr>`);
  }
  $("n-premio").textContent = lista.length ? "Primi 10 nella classifica generale (F1 + MotoGP). Vince il primo idoneo: ha l'email e non ha nickname collegati." : "Ancora nessuna gara disputata con pronostici.";
  $("t-premio").innerHTML = lista.length ? `<thead><tr><th>#</th><th>Nickname</th><th>F1</th><th>MotoGP</th><th>Gare</th><th>Tot</th><th>Email</th><th>Esito</th></tr></thead><tbody>${righe.join("")}</tbody>` : "";

  // tutti i voti dei Gran Premi non ancora disputati, con il podio
  const nomeGara = (k) => (d.gare[k] ? `${d.gare[k].nome} (${d.gare[k].serie})` : k.startsWith("m") ? k.slice(1) + " (MotoGP)" : "Gran Premio " + k);
  const nomePil = (k, n) => (k.startsWith("m") ? d.nomiMoto : d.nomiF1)[String(n)] || "n." + n;
  const futuri = [];
  for (const v of tutti) { if (!(await podioVero(d, v.gp))) futuri.push(v); }
  futuri.sort((a, b) => a.gp.localeCompare(b.gp) || a.ts - b.ts);
  const emailDi = {};
  await Promise.all([...new Set(futuri.map((v) => v.nick))].map(async (n) => {
    try { emailDi[n] = ((await api("/vincitore", { nick: n })).email || []).map((e) => e.email).find(Boolean) || null; } catch (e) { emailDi[n] = null; }
  }));
  const tabellaVoti = (lista) => lista.length ? `<thead><tr><th>Gara</th><th>Nickname</th><th>Email</th><th>Podio</th><th>Ora</th></tr></thead><tbody>${lista.map((v) => `<tr><td>${esc(nomeGara(v.gp))}</td><td><b>${esc(v.nick)}</b></td><td>${emailDi[v.nick] ? esc(emailDi[v.nick]) : '<span class="muted">nessuna</span>'}</td><td>${v.podio.map((n) => esc(nomePil(v.gp, n))).join(", ")}${v.pole ? ` <span class="muted">· pole ${esc(nomePil(v.gp, v.pole))}</span>` : ""}${v.giro ? ` <span class="muted">· giro ${esc(nomePil(v.gp, v.giro))}</span>` : ""}</td><td>${quando(v.ts)}</td></tr>`).join("")}</tbody>` : `<tbody><tr><td class="muted">Nessun voto per le prossime gare.</td></tr></tbody>`;
  $("t-voti-f1").innerHTML = tabellaVoti(futuri.filter((v) => !v.gp.startsWith("m")));
  $("t-voti-moto").innerHTML = tabellaVoti(futuri.filter((v) => v.gp.startsWith("m")));
}

// Consigli lasciati dai visitatori con "Aiutaci a migliorare" e nella pagina Consigli
async function mostraConsigli() {
  try {
    const j = await api("/consigli-admin");
    const tipi = { funzione: "Funzione nuova", errore: "Errore", altro: "Altro" };
    $("n-consigli").textContent = j.totale ? `${j.totale} ${j.totale === 1 ? "consiglio" : "consigli"} (si cancellano da soli dopo 90 giorni). Qui gli ultimi ${j.consigli.length}.` : "Ancora nessun consiglio.";
    $("t-consigli").innerHTML = j.consigli.length ? `<thead><tr><th>Quando</th><th>Tipo</th><th>Pagina</th><th>Testo</th></tr></thead><tbody>${j.consigli.map((c) => {
      const m = /^\[([^\]]+)\]\s*/.exec(c.testo || ""), pagina = m ? m[1] : "consigli.html", testo = m ? c.testo.slice(m[0].length) : c.testo || "";
      return `<tr><td style="white-space:nowrap">${esc(new Date(c.quando).toLocaleString("it-IT", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }))}</td><td>${esc(tipi[c.tipo] || c.tipo || "")}</td><td>${esc(pagina)}</td><td style="white-space:normal">${esc(testo)}</td></tr>`;
    }).join("")}</tbody>` : "";
  } catch (e) { $("n-consigli").textContent = "Per vedere i consigli reincolla il Worker aggiornato in Cloudflare."; }
}

async function entra() {
  $("err").textContent = "";
  chiave = $("chiave").value.trim() || chiave;
  try {
    await api("/sospetti");
    try { sessionStorage.setItem("adm-k", chiave); } catch (e) {}
    $("login").hidden = true; $("pannello").hidden = false;
    mostraConsigli();
    await mostra();
  } catch (e) { $("err").textContent = e.message; $("login").hidden = false; $("pannello").hidden = true; }
}
const scrivi = (id, testo) => { const el = $(id); el.hidden = false; el.textContent = testo; };
$("entra").addEventListener("click", entra);
$("chiave").addEventListener("keydown", (e) => { if (e.key === "Enter") entra(); });
$("esci").addEventListener("click", () => { try { sessionStorage.removeItem("adm-k"); } catch (e) {} location.reload(); });
$("b-email").addEventListener("click", async () => {
  try { const j = await api("/vincitore", { email: $("q-email").value.trim() }); scrivi("o-email", j.nota || `Nickname: ${j.nickname}\nEmail: ${(j.email || []).map((e) => e.email).join(", ")}`); } catch (e) { scrivi("o-email", e.message); }
});
$("b-rip").addEventListener("click", async () => {
  const n = $("q-nick").value.trim();
  if (!n || !confirm(`Creare un nuovo codice per "${n}"? Il vecchio codice smette di funzionare.`)) return;
  try { const j = await api("/ripristina", { nick: n }); scrivi("o-rip", `Nickname: ${j.nickname}\nNuovo codice: ${j.codice}\n\nScrivi questo codice all'email salvata. Lui lo inserisce in "Riprendi il tuo nickname" con il nickname.`); } catch (e) { scrivi("o-rip", e.message); }
});
$("b-svin").addEventListener("click", async () => {
  const em = $("q-svin").value.trim();
  if (!em || !confirm(`Liberare l'email ${em} dal giocatore a cui è collegata?`)) return;
  try { const j = await api("/svincola", { email: em }); scrivi("o-svin", `Fatto: ${j.email} non è più collegata a nessun giocatore.`); } catch (e) { scrivi("o-svin", e.message); }
});
if (chiave) entra();
