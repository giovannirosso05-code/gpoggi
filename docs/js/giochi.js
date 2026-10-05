import { renderHeader, renderFooter, fetchJSON, esc, credito, erroreCaricamento, VOTI_URL } from "./common.js";

renderHeader("giochi");
renderFooter();

const N = 10;
const scelta = document.getElementById("scelta");
const box = document.getElementById("partita");

const mescola = (a) => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; };
const scelgo = (a) => a[Math.floor(Math.random() * a.length)];
const leggi = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const scrivi = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const record = (g) => Number(leggi("record-" + g)) || 0;
const salvaRecord = (g, v) => { if (v > record(g)) scrivi("record-" + g, String(v)); };

const GIOCHI = {
  circuito: { titolo: "Indovina il circuito", testo: "Ti mostro il tracciato, tu scegli il Gran Premio." },
  pilota: { titolo: "Chi è il pilota?", testo: "Una foto, quattro nomi: piloti di oggi e leggende del passato, F1 e MotoGP." },
  moto: { titolo: "MotoGP: che moto guida?", testo: "Un pilota, quattro marche." },
  numero: { titolo: "Che numero ha?", testo: "Numeri di gara di piloti F1 e MotoGP." },
  campioni: { titolo: "Chi vinse il mondiale?", testo: "Campioni del mondo di F1 e MotoGP, dal passato a oggi." },
  vincitore: { titolo: "Chi vinse quel Gran Premio?", testo: "Vincitori di Gran Premi di F1 dal 1980." },
  punti: { titolo: "Più o meno punti", testo: "Chi ha più punti in classifica? Quanto riesci ad andare avanti?", serie: true },
  pronostico: { titolo: "Pronostico del podio", testo: "Scegli il podio del prossimo Gran Premio e guarda quanti punti fai.", speciale: true },
};

let dati = null;
async function carica() {
  if (dati) return dati;
  const [eventi, roster, moto, indice, motoArch, storiche] = await Promise.all([
    fetchJSON("data/events.json"), fetchJSON("data/roster.json"),
    fetchJSON("data/motogp-classifica.json").catch(() => null), fetchJSON("data/archivio/indice.json").catch(() => []), fetchJSON("data/motogp-archivio.json").catch(() => null), fetchJSON("data/foto-storici.json").catch(() => [])]);
  dati = { eventi, roster, moto: moto ? moto.piloti : [], indice, motoArch: motoArch ? motoArch.anni : [], storiche };
  return dati;
}

// ---- generatori di domande: ognuno restituisce { titolo, img, opzioni:[testo], giusto:testo, cred }
const quattro = (giusto, pool) => ({ opzioni: mescola([giusto, ...mescola([...new Set(pool.filter((x) => x !== giusto))]).slice(0, 3)]), giusto });

const GEN = {
  circuito() {
    const ev = dati.eventi.filter((e) => e.mappa);
    return mescola(ev).slice(0, N).map((g) => ({ titolo: "Di quale Gran Premio è questo tracciato?", img: `<div class="quiz-img mappa-quiz"><img src="${esc(g.mappa.file || g.mappa.url)}" alt="Tracciato da indovinare"></div>`,
      ...quattro(g.nome, ev.map((e) => e.nome)), cred: credito(g.mappa, "Mappa") }));
  },
  pilota(modo = "tutti") {
    const oggi = dati.roster.filter((p) => p.foto && p.nome).map((p) => ({ nome: p.nome, foto: p.foto, nota: `${p.team || ""}`.trim() }));
    const leggende = dati.storiche.map((p) => ({ nome: p.nome, foto: p.foto, nota: `${p.serie} · ${p.anni}`, serie: p.serie }));
    const pool = modo === "oggi" ? oggi : modo === "leggende" ? leggende : [...oggi, ...leggende];
    return mescola(pool).slice(0, N).map((p) => {
      // le alternative arrivano dalla stessa epoca/serie, cosi' non basta riconoscere una foto a colori o in bianco e nero
      const simili = modo === "tutti" ? pool.filter((x) => (x.serie || "Formula 1") === (p.serie || "Formula 1")) : pool;
      return { titolo: "Chi è questo pilota?", img: `<div class="quiz-img foto-quiz"><img src="${esc(p.foto.file || p.foto.url)}" alt="Pilota da indovinare"></div>`,
        ...quattro(p.nome, simili.map((x) => x.nome)), cred: `${p.nota ? "<b>" + esc(p.nota) + "</b> · " : ""}${credito(p.foto)}` };
    });
  },
  moto() {
    const marche = [...new Set(dati.moto.map((p) => p.moto))];
    return mescola(dati.moto).slice(0, N).map((p) => ({ titolo: "Che moto guida questo pilota?", img: `<div class="quiz-img foto-quiz" style="padding:28px"><div class="quiz-pilota"><b>${esc(p.nome)}</b><span>${esc(p.team)}</span></div></div>`,
      ...quattro(p.moto, marche), cred: "" }));
  },
  numero() {
    const tutti = [...dati.roster.filter((p) => p.numero != null).map((p) => ({ nome: p.nome, n: String(p.numero), serie: "Formula 1", sub: p.team })),
      ...dati.moto.filter((p) => p.numero != null).map((p) => ({ nome: p.nome, n: String(p.numero), serie: "MotoGP", sub: p.team }))];
    return mescola(tutti).slice(0, N).map((p) => ({ titolo: "Che numero di gara ha questo pilota?", img: `<div class="quiz-img foto-quiz" style="padding:28px"><div class="quiz-pilota"><b>${esc(p.nome)}</b><span>${esc(p.serie)} · ${esc(p.sub || "")}</span></div></div>`,
      ...quattro(p.n, tutti.filter((x) => x.serie === p.serie).map((x) => x.n)), cred: "" }));
  },
  campioni() {
    const f1 = dati.indice.filter((x) => x.campione).map((x) => ({ anno: x.anno, nome: x.campione, serie: "Formula 1" }));
    const mg = dati.motoArch.map((s) => ({ anno: s.anno, nome: (s.classifica.find((p) => p.pos === 1) || {}).nome, serie: "MotoGP" })).filter((x) => x.nome);
    const pool = [...f1, ...mg];
    return mescola(pool).slice(0, N).map((c) => ({ titolo: `Chi vinse il mondiale ${c.serie === "Formula 1" ? "di Formula 1" : "della classe regina MotoGP"} nel ${c.anno}?`,
      img: `<div class="quiz-img foto-quiz" style="padding:24px"><div class="quiz-pilota"><b>${c.anno}</b><span>${esc(c.serie)}</span></div></div>`,
      ...quattro(c.nome, pool.filter((x) => x.serie === c.serie).map((x) => x.nome)), cred: "" }));
  },
  async vincitore() {
    const anni = mescola(Array.from({ length: 2025 - 1980 + 1 }, (_, i) => 1980 + i)).slice(0, N);
    const stagioni = await Promise.all(anni.map((a) => fetchJSON(`data/archivio/${a}.json`).catch(() => null)));
    return stagioni.filter(Boolean).map((s) => {
      const g = scelgo(s.gare);
      return { titolo: `Chi vinse il ${g.nome} del ${s.anno}?`, img: `<div class="quiz-img foto-quiz" style="padding:24px"><div class="quiz-pilota"><b>${esc(g.nome)}</b><span>${s.anno}</span></div></div>`,
        ...quattro(g.vincitore, s.gare.map((x) => x.vincitore).concat(s.piloti.map((p) => p.nome))), cred: "" };
    });
  },
};

function partitaQuiz(chiave, qs) {
  let i = 0, punti = 0;
  scelta.classList.add("hidden"); box.classList.remove("hidden");
  const mostra = () => {
    const q = qs[i];
    box.innerHTML = `<div class="quiz-testa"><span>${esc(GIOCHI[chiave].titolo)} · ${i + 1} di ${qs.length}</span><span>Punti: <b>${punti}</b></span></div>
      <h3 class="quiz-titolo">${esc(q.titolo)}</h3>${q.img || ""}
      <div class="quiz-opzioni">${q.opzioni.map((o, k) => `<button class="quiz-opz" data-k="${k}">${esc(o)}</button>`).join("")}</div><div class="quiz-esito" id="esito"></div>`;
    box.querySelectorAll(".quiz-opz").forEach((b) => b.addEventListener("click", () => rispondi(Number(b.dataset.k)), { once: true }));
  };
  const rispondi = (k) => {
    const q = qs[i], ok = q.opzioni[k] === q.giusto;
    if (ok) punti++;
    box.querySelectorAll(".quiz-opz").forEach((b, idx) => { b.disabled = true; if (q.opzioni[idx] === q.giusto) b.classList.add("giusta"); else if (idx === k) b.classList.add("sbagliata"); });
    document.getElementById("esito").innerHTML = `<b>${ok ? "Giusto!" : "Sbagliato."}</b> ${ok ? "" : "Era " + esc(q.giusto) + "."}
      <button class="quiz-avanti" id="avanti">${i + 1 < qs.length ? "Avanti →" : "Vedi il risultato"}</button>${q.cred ? `<div class="credito">${q.cred}</div>` : ""}`;
    document.getElementById("avanti").addEventListener("click", () => { i++; i < qs.length ? mostra() : fine(); });
  };
  const fine = () => {
    const prec = record(chiave); salvaRecord(chiave, punti);
    schermataFine(chiave, punti, qs.length, prec, () => avvia(chiave));
  };
  mostra();
}

function schermataFine(chiave, punti, su, prec, ancora, extra = "") {
  box.innerHTML = `<div class="quiz-fine"><div class="quiz-punteggio">${punti}${su ? `<span>/${su}</span>` : ""}</div>
    <p>${su && punti === su ? "Perfetto!" : punti >= (su || 8) * 0.7 ? "Ottimo risultato." : punti >= (su || 8) * 0.4 ? "Non male, riprova." : "Si può fare meglio: riprova."}</p>${extra}
    <p class="muted">Record personale: <b>${Math.max(prec, punti)}</b>${su ? "/" + su : ""}</p>
    <div class="quiz-azioni"><button class="quiz-avanti" id="ancora">Rigioca</button><button class="quiz-avanti secondario" id="menu">Cambia gioco</button></div></div>`;
  document.getElementById("ancora").addEventListener("click", ancora);
  document.getElementById("menu").addEventListener("click", tornaMenu);
}

// ---- Più o meno punti: si va avanti finche' non si sbaglia
function partitaPunti() {
  const serie = { "Formula 1": dati.roster.filter((p) => p.punti != null && p.nome).map((p) => ({ nome: p.nome, team: p.team, punti: p.punti })),
    MotoGP: dati.moto.map((p) => ({ nome: p.nome, team: p.team, punti: p.punti })) };
  let streak = 0;
  scelta.classList.add("hidden"); box.classList.remove("hidden");
  const turno = () => {
    const nomeSerie = scelgo(Object.keys(serie).filter((k) => serie[k].length > 3));
    const pool = serie[nomeSerie];
    let a, b; do { [a, b] = mescola(pool).slice(0, 2); } while (a.punti === b.punti);
    box.innerHTML = `<div class="quiz-testa"><span>Più o meno punti · ${esc(nomeSerie)}</span><span>Serie: <b>${streak}</b></span></div>
      <h3 class="quiz-titolo">Chi ha più punti in classifica?</h3>
      <div class="quiz-opzioni">${[a, b].map((p, k) => `<button class="quiz-opz grande" data-k="${k}"><b>${esc(p.nome)}</b><span>${esc(p.team || "")}</span></button>`).join("")}</div><div class="quiz-esito" id="esito"></div>`;
    box.querySelectorAll(".quiz-opz").forEach((bt) => bt.addEventListener("click", () => {
      const k = Number(bt.dataset.k), ok = (k === 0) === (a.punti > b.punti);
      box.querySelectorAll(".quiz-opz").forEach((x, idx) => { x.disabled = true; const p = idx === 0 ? a : b; x.insertAdjacentHTML("beforeend", `<em>${p.punti} punti</em>`); if ((idx === 0) === (a.punti > b.punti)) x.classList.add("giusta"); else if (idx === k) x.classList.add("sbagliata"); });
      if (ok) { streak++; document.getElementById("esito").innerHTML = `<b>Giusto!</b> <button class="quiz-avanti" id="avanti">Avanti →</button>`; document.getElementById("avanti").addEventListener("click", turno); }
      else { const prec = record("punti"); salvaRecord("punti", streak); document.getElementById("esito").innerHTML = `<b>Sbagliato.</b> <button class="quiz-avanti" id="fine">Vedi il risultato</button>`; document.getElementById("fine").addEventListener("click", () => schermataFine("punti", streak, 0, prec, () => { streak = 0; partitaPunti(); }, `<p class="muted">Hai indovinato ${streak} di fila.</p>`)); }
    }, { once: true }));
  };
  turno();
}

// ---- Pronostico del podio: punti per posizione e classifica Gran Premio per Gran Premio
// 1° posto indovinato 5 punti, 2° 3 punti, 3° 2 punti; un pilota sul podio ma in un'altra posizione vale 1; podio completo esatto +5 (massimo 15).
const PUNTI_POSIZIONE = [5, 3, 2];
function punteggio(podio, vero) {
  let pt = 0, esatti = 0;
  podio.forEach((n, i) => { if (vero[i] === String(n)) { pt += PUNTI_POSIZIONE[i]; esatti++; } else if (vero.includes(String(n))) pt += 1; });
  return pt + (esatti === 3 ? 5 : 0);
}
const base = VOTI_URL.replace(/\/$/, "");
const idGiocatore = () => { let v = leggi("pron-id"); if (!v) { v = "g" + Math.random().toString(36).slice(2) + Date.now().toString(36); scrivi("pron-id", v); } return v; };
async function podioVero(id) {
  try {
    const g = await fetchJSON(`data/gare/${id}.json`);
    const sess = g.sessioni.find((x) => x.tipo === "Race" && x.risultati && x.risultati.length);
    if (!sess) return null;
    return { vero: sess.risultati.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos).map((r) => String(r.numero)), inizio: new Date(sess.inizio).getTime() };
  } catch (e) { return null; }
}

async function partitaPronostico() {
  scelta.classList.add("hidden"); box.classList.remove("hidden");
  const salvati = () => { try { return JSON.parse(leggi("pronostici") || "{}"); } catch (e) { return {}; } };
  const prossimo = dati.eventi.filter((g) => new Date(g.fine) > new Date()).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
  const piloti = dati.roster.filter((p) => p.nome).sort((a, b) => (a.posizione ?? 99) - (b.posizione ?? 99));
  const opz = (sel) => `<option value="">Scegli…</option>` + piloti.map((p) => `<option value="${p.numero}" ${String(sel) === String(p.numero) ? "selected" : ""}>${esc(p.nome)}</option>`).join("");
  const nomePil = (n) => (piloti.find((p) => String(p.numero) === String(n)) || {}).nome || "n.d.";
  const gara = prossimo && prossimo.sessioni.find((x) => x.nome === "Gara");
  const aperto = prossimo && gara && new Date(gara.inizio) > new Date();
  const tutti = salvati();
  let totale = 0, righe = "";
  for (const [id, pr] of Object.entries(tutti)) {
    const r = await podioVero(id);
    const pt = r ? punteggio(pr.podio, r.vero) : null;
    if (pt !== null) totale += pt;
    righe += `<tr><td><strong>${esc(pr.nome)}</strong></td><td>${pr.podio.map(nomePil).map(esc).join(", ")}</td><td>${r ? r.vero.map(nomePil).map(esc).join(", ") : "<span class='muted'>in attesa</span>"}</td><td><strong>${pt ?? "–"}</strong></td></tr>`;
  }
  box.innerHTML = `<div class="quiz-testa pron-testa"><span>Pronostico del podio</span><span>Punti totali: <b>${totale}</b></span></div>
    ${prossimo ? `<h3 class="quiz-titolo">${esc(prossimo.nome)}: chi sale sul podio?</h3>
    ${aperto ? `<div class="pron-form">${[1, 2, 3].map((i) => `<label>${i}° posto<select class="sel" id="p${i}">${opz((tutti[prossimo.id] || { podio: [] }).podio[i - 1])}</select></label>`).join("")}</div>
    ${base ? `<label class="pron-nome">Il tuo nome in classifica<input type="text" id="nome" maxlength="16" autocomplete="nickname" placeholder="Per esempio Giovanni" value="${esc(leggi("pron-nome") || "")}"></label>` : ""}
    <div class="quiz-esito"><button class="quiz-avanti pron-rosso" id="salva" style="margin:0">Salva il pronostico</button> <span id="msg" class="muted"></span></div>` : `<p class="muted">Le votazioni per questo Gran Premio sono chiuse: la gara è iniziata.</p>`}
    <div class="pron-punti"><b>Come si fanno i punti</b><ul><li>1° posto indovinato: <b>5</b> punti</li><li>2° posto indovinato: <b>3</b> punti</li><li>3° posto indovinato: <b>2</b> punti</li><li>Pilota sul podio ma in un'altra posizione: <b>1</b> punto</li><li>Podio completo esatto: <b>+5</b> (massimo 15)</li></ul>
    <span class="muted">Il pronostico si può cambiare fino all'inizio della gara.</span></div>` : `<p class="muted">Nessun Gran Premio in programma.</p>`}
    ${base ? `<h3 class="quiz-titolo" style="margin-top:24px">Classifica</h3><div id="classifica"><p class="muted">Carico la classifica…</p></div>` : ""}
    ${righe ? `<h3 class="quiz-titolo" style="margin-top:20px">I tuoi pronostici</h3><div class="table-wrap"><table class="results"><thead><tr><th>Gran Premio</th><th>Il tuo podio</th><th>Podio vero</th><th>Punti</th></tr></thead><tbody>${righe}</tbody></table></div>` : ""}
    <div class="quiz-azioni" style="margin-top:16px"><button class="quiz-avanti secondario" id="menu" style="margin:0">Cambia gioco</button></div>`;
  document.getElementById("menu").addEventListener("click", tornaMenu);
  const salva = document.getElementById("salva");
  if (salva) salva.addEventListener("click", async () => {
    const podio = [1, 2, 3].map((i) => document.getElementById("p" + i).value);
    const msg = document.getElementById("msg");
    if (podio.some((x) => !x) || new Set(podio).size < 3) { msg.textContent = "Scegli tre piloti diversi."; return; }
    const nomeEl = document.getElementById("nome"), nome = nomeEl ? nomeEl.value.trim().replace(/\s+/g, " ") : "";
    if (base && !/^[\p{L}\p{N} _.-]{3,16}$/u.test(nome)) { msg.textContent = "Scrivi un nome di 3-16 caratteri (lettere, numeri, spazi)."; return; }
    const t = salvati(); t[prossimo.id] = { nome: prossimo.nome, podio }; scrivi("pronostici", JSON.stringify(t));
    let testo = leggi("pronostici") ? "Salvato sul dispositivo." : "Salvato solo finché la pagina resta aperta (la memoria del browser è bloccata).";
    if (base) {
      scrivi("pron-nome", nome);
      try {
        const r = await fetch(base + "/pronostico", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ gp: String(prossimo.id), id: idGiocatore(), nick: nome, podio }) });
        if (r.status === 409) testo = "Questo nome è già usato da un altro giocatore: scegline un altro.";
        else if (r.status === 429) testo = "Troppi invii oggi: riprova domani.";
        else if (!r.ok) throw new Error();
        else testo = `Salvato! Sei in classifica come ${nome}.`;
      } catch (e) { testo += " Non sono riuscito a raggiungere la classifica: riprova più tardi."; }
    }
    msg.textContent = testo;
    if (base) mostraClassifica();
  });
  if (base) mostraClassifica();

  // Classifica Gran Premio per Gran Premio e generale: contano solo i pronostici arrivati prima della partenza della gara
  async function mostraClassifica() {
    const el = document.getElementById("classifica");
    if (!el) return;
    let lista = [];
    try { lista = (await fetch(base + "/pronostici").then((r) => r.json())).pronostici || []; } catch (e) { el.innerHTML = `<p class="muted">Classifica non disponibile al momento.</p>`; return; }
    const perGp = {};
    for (const x of lista) (perGp[x.gp] ||= []).push(x);
    const chiusi = [];
    for (const g of dati.eventi.slice().sort((a, b) => new Date(a.inizio) - new Date(b.inizio))) {
      if (!perGp[g.id]) continue;
      const r = await podioVero(g.id);
      if (r) chiusi.push({ g, r, voci: perGp[g.id].filter((x) => x.ts <= r.inizio).map((x) => ({ nick: x.nick, podio: x.podio, pt: punteggio(x.podio, r.vero) })).sort((a, b) => b.pt - a.pt || a.nick.localeCompare(b.nick)) });
    }
    const generale = {};
    for (const c of chiusi) for (const v of c.voci) { const o = (generale[v.nick] ||= { nick: v.nick, pt: 0, gare: 0 }); o.pt += v.pt; o.gare++; }
    const gen = Object.values(generale).sort((a, b) => b.pt - a.pt || b.gare - a.gare || a.nick.localeCompare(b.nick));
    const io = (leggi("pron-nome") || "").toLowerCase();
    const riga = (v, i, extra) => `<tr class="${v.nick.toLowerCase() === io ? "pron-io" : ""}"><td>${i + 1}</td><td><b>${esc(v.nick)}</b></td>${extra}<td><b>${v.pt}</b></td></tr>`;
    const inAttesa = prossimo && perGp[prossimo.id] ? `<p class="muted" style="font-size:13px">Per il ${esc(prossimo.nome)} hanno già giocato ${perGp[prossimo.id].length} ${perGp[prossimo.id].length === 1 ? "persona" : "persone"}: la classifica esce a fine gara.</p>` : "";
    if (!chiusi.length) { el.innerHTML = inAttesa + `<p class="muted">Ancora nessuna classifica: compare dopo la prima gara con dei pronostici.</p>`; return; }
    el.innerHTML = inAttesa + `<label class="pron-scegli">Gran Premio <select id="gp-class" class="sel">${chiusi.slice().reverse().map((c) => `<option value="${c.g.id}">${esc(c.g.nome)}</option>`).join("")}</select></label>
      <div class="table-wrap"><table class="results" id="tab-gp"></table></div>
      <h4 class="quiz-titolo" style="margin-top:18px;font-size:18px">Classifica generale</h4>
      <div class="table-wrap"><table class="results"><thead><tr><th>#</th><th>Nome</th><th>Gare</th><th>Punti</th></tr></thead><tbody>${gen.map((v, i) => riga(v, i, `<td>${v.gare}</td>`)).join("")}</tbody></table></div>`;
    const disegna = () => {
      const c = chiusi.find((x) => String(x.g.id) === document.getElementById("gp-class").value);
      document.getElementById("tab-gp").innerHTML = `<thead><tr><th>#</th><th>Nome</th><th>Il suo podio</th><th>Punti</th></tr></thead><tbody>${c.voci.map((v, i) => riga(v, i, `<td>${v.podio.map(nomePil).map(esc).join(", ")}</td>`)).join("")}</tbody>`;
    };
    document.getElementById("gp-class").addEventListener("change", disegna);
    disegna();
  }
}

function tornaMenu() { box.classList.add("hidden"); scelta.classList.remove("hidden"); aggiornaRecord(); }

async function avvia(chiave) {
  const g = GIOCHI[chiave];
  if (g.speciale) return partitaPronostico();
  if (g.serie) return partitaPunti();
  box.classList.remove("hidden"); scelta.classList.add("hidden"); box.innerHTML = `<p class="muted">Preparo le domande…</p>`;
  let modo;
  if (chiave === "pilota") modo = await scegliModo();
  const qs = await GEN[chiave](modo);
  if (!qs.length) { box.innerHTML = `<p class="muted">Non ci sono abbastanza dati per questo gioco.</p>`; return; }
  partitaQuiz(chiave, qs);
}

function scegliModo() {
  const n = dati.storiche.length;
  return new Promise((ris) => {
    if (!n) return ris("oggi");
    box.innerHTML = `<h3 class="quiz-titolo">Chi è il pilota? Scegli la difficoltà</h3><div class="quiz-opzioni">
      <button class="quiz-opz grande" data-m="oggi"><b>Piloti di oggi</b><span>La griglia della stagione in corso</span></button>
      <button class="quiz-opz grande" data-m="leggende"><b>Leggende</b><span>${n} piloti del passato: campioni e grandi vincitori di F1 e MotoGP</span></button>
      <button class="quiz-opz grande" data-m="tutti"><b>Tutti insieme</b><span>Oggi e passato mescolati</span></button></div>`;
    box.querySelectorAll("[data-m]").forEach((b) => b.addEventListener("click", () => ris(b.dataset.m), { once: true }));
  });
}

function aggiornaRecord() {
  scelta.querySelectorAll(".gioco-card").forEach((b) => {
    const r = record(b.dataset.gioco);
    let el = b.querySelector(".rec"); if (!el) { el = document.createElement("small"); el.className = "rec"; b.appendChild(el); }
    el.textContent = r ? (b.dataset.gioco === "punti" ? `Record: ${r} di fila` : `Record: ${r}/${N}`) : "";
  });
}

try {
  await carica();
  scelta.innerHTML = Object.entries(GIOCHI).map(([k, g]) => `<button class="gioco-card" data-gioco="${k}"><b>${esc(g.titolo)}</b><span>${esc(g.testo)}</span></button>`).join("");
  aggiornaRecord();
  scelta.addEventListener("click", (e) => { const b = e.target.closest(".gioco-card"); if (b) avvia(b.dataset.gioco); });
} catch (e) {
  erroreCaricamento(scelta);
}
