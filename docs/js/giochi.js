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
  pronostico: { titolo: "Pronostico del podio", testo: "Scegli il podio di F1 e MotoGP, scegli il tuo nickname ed entra in classifica: a fine anno chi è primo vince 50 € in carta Amazon.", speciale: true },
  circuito: { titolo: "Indovina il circuito", testo: "Ti mostro il tracciato, tu scegli il Gran Premio." },
  pilota: { titolo: "Chi è il pilota?", testo: "Una foto, quattro nomi: piloti di oggi e leggende del passato, F1 e MotoGP." },
  pixel: { titolo: "Chi è? Foto pixelata", testo: "La foto si schiarisce a poco a poco: prima indovini, più punti fai. Tutti i piloti dell'archivio.", pixel: true },
  moto: { titolo: "MotoGP: che moto guida?", testo: "Un pilota, quattro marche." },
  numero: { titolo: "Che numero ha?", testo: "Numeri di gara di piloti F1 e MotoGP." },
  campioni: { titolo: "Chi vinse il mondiale?", testo: "Campioni del mondo di F1 e MotoGP, dal passato a oggi." },
  vincitore: { titolo: "Chi vinse quel Gran Premio?", testo: "Vincitori di Gran Premi di F1 dal 1980." },
  punti: { titolo: "Più o meno punti", testo: "Chi ha più punti in classifica? Quanto riesci ad andare avanti?", serie: true },
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
  // Nel quiz del circuito la mappa non deve contenere scritte (titolo, nomi delle curve): sarebbero la risposta.
  // Le mappe vettoriali si ripuliscono qui, togliendo ogni testo; quelle che sono già immagini con le scritte dentro restano fuori dal gioco.
  async circuito() {
    const pulita = async (g) => {
      const u = g.mappa.file || g.mappa.url;
      if (!/\.svg(\?|$)/i.test(u)) return null;
      try {
        const doc = new DOMParser().parseFromString(await (await fetch(u)).text(), "image/svg+xml");
        if (doc.querySelector("parsererror") || doc.querySelector("image")) return null;
        doc.querySelectorAll("text, title, desc, metadata").forEach((el) => { if (el.localName === "text" && /^\s*\d{1,2}\s*$/.test(el.textContent)) return; el.remove(); });   // restano solo i numeri delle curve
        return URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(doc)], { type: "image/svg+xml" }));
      } catch (e) { return null; }
    };
    const ev = (await Promise.all(dati.eventi.filter((e) => e.mappa).map(async (e) => ({ e, src: await pulita(e) })))).filter((x) => x.src);
    return mescola(ev).slice(0, N).map(({ e: g, src }) => ({ titolo: "Di quale Gran Premio è questo tracciato?", img: `<div class="quiz-img mappa-quiz"><img src="${src}" alt="Tracciato da indovinare"></div>`,
      ...quattro(g.nome, ev.map((x) => x.e.nome)), cred: credito(g.mappa, "Mappa") }));
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
    document.getElementById("esito").innerHTML = `<span class="esito-testo"><b>${ok ? "Giusto!" : "Sbagliato."}</b> ${ok ? "" : "Era " + (/^Gran Premio/.test(q.giusto) ? "il " : "") + esc(q.giusto) + "."}</span>
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

// ---- Pronostico del podio (F1 e MotoGP): punti per posizione e classifica con il nome dei giocatori
// 1° posto indovinato 10 punti, 2° 5 punti, 3° 2 punti; un pilota sul podio ma in un'altra posizione vale 1; podio completo esatto +5 (massimo 22).
const PUNTI_POSIZIONE = [10, 5, 2];
function punteggio(podio, vero) {
  let pt = 0, esatti = 0;
  podio.forEach((n, i) => { if (vero[i] === String(n)) { pt += PUNTI_POSIZIONE[i]; esatti++; } else if (vero.includes(String(n))) pt += 1; });
  return pt + (esatti === 3 ? 5 : 0);
}
// pole indovinata +7 (vale solo se scelta prima delle qualifiche), giro più veloce in gara +1
function punti(v, r) {
  let pt = punteggio(v.podio, r.vero);
  if (v.pole && r.pole && String(v.pole) === String(r.pole) && (!r.qInizio || (v.tp || v.ts || 0) <= r.qInizio)) pt += 7;
  if (v.giro && r.giro && String(v.giro) === String(r.giro)) pt += 1;
  return pt;
}
const base = VOTI_URL.replace(/\/$/, "");
// Il giocatore si riconosce da un id. Alla prima partita si crea un codice di recupero (8 caratteri) e l'id si ricava da nickname + codice:
// su un altro telefono basta rimettere gli stessi nickname e codice per riavere lo stesso id, quindi gli stessi punti. Nessuna email, nessuna registrazione.
const ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
const nuovoCodice = () => Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) => ALFABETO[b % 32]).join("");
async function idDa(nick, codice) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(nick.trim().toLowerCase() + ":" + codice.trim().toUpperCase()));
  return "g" + [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 24);
}
async function idGiocatore(nick) {
  let id = leggi("pron-id");
  if (id) return id;
  const codice = nuovoCodice();
  id = await idDa(nick, codice);
  scrivi("pron-id", id); scrivi("pron-codice", codice); scrivi("pron-nick0", nick);
  return id;
}
function boxRecupero() {
  const cod = leggi("pron-codice"), nick0 = leggi("pron-nick0");
  return `<div class="pron-recupero">
    ${cod ? `<p><b>Il tuo codice di recupero</b><br>Nickname <b>${esc(nick0)}</b> · codice <b class="pron-cod">${esc(cod)}</b><br><span class="muted">Fai uno screenshot e gioca sempre da questo dispositivo: se cambi telefono, browser o cancelli i dati, ti servono nickname e codice per riprendere i tuoi punti.</span></p>` : ""}
    <details><summary>Hai già giocato da un altro telefono? Riprendi il tuo nickname</summary>
      <label class="pron-nome">Nickname<input type="text" id="rec-nick" maxlength="16" autocomplete="off" value="${esc(leggi("pron-nome") || "")}"></label>
      <label class="pron-nome">Codice di recupero<input type="text" id="rec-cod" maxlength="8" autocomplete="off" autocapitalize="characters" placeholder="8 caratteri"></label>
      <button class="quiz-avanti secondario" id="rec-vai" style="margin:0">Riprendi</button> <span id="rec-msg" class="muted"></span>
      <p class="muted" style="font-size:13px;margin:12px 0 0"><b>Hai dimenticato nickname o codice?</b> <a class="accent" href="mailto:info@gpoggi.it?subject=${encodeURIComponent("Recupero nickname GP Oggi")}&body=${encodeURIComponent("Ciao, ho dimenticato il nickname o il codice di recupero del Pronostico di GP Oggi.\n\nEmail che ho inserito nel pronostico (scrivi da questo indirizzo):\nNickname, se lo ricordo:\n")}">Scrivi all'amministrazione</a>: se hai inserito l'email nel pronostico ti rispondiamo con un nuovo codice, come per la password dimenticata. Senza email non possiamo verificare che sei tu.</p>
    </details></div>`;
}
const chiaveMoto = (nome) => "m" + nome.replace(/\W/g, "").slice(0, 38);
async function podioVeroF1(id) {
  try {
    const g = await fetchJSON(`data/gare/${id}.json`);
    const sess = g.sessioni.find((x) => x.tipo === "Race" && x.risultati && x.risultati.length);
    if (!sess) return null;
    const quali = g.sessioni.find((x) => x.tipo === "Qualifying");
    const primoQ = quali && (quali.risultati || []).find((r) => r.pos === 1);
    const cron = await fetchJSON(`data/cronaca/${id}.json`).catch(() => null);
    return { vero: sess.risultati.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos).map((r) => String(r.numero)), inizio: new Date(sess.inizio).getTime(),
      pole: primoQ ? String(primoQ.numero) : null, qInizio: quali ? new Date(quali.inizio).getTime() : null, giro: cron && cron.giro_veloce != null ? String(cron.giro_veloce) : null };
  } catch (e) { return null; }
}
let garePassateMoto = null, orariGara = null;
const caricaOrari = async () => orariGara || (orariGara = await fetchJSON("data/gara-orari.json").catch(() => ({})));
async function podioVeroMoto(chiave) {
  if (!garePassateMoto) garePassateMoto = await fetchJSON("data/motogp-gare.json").catch(() => ({}));
  const nome = Object.keys(garePassateMoto).find((n) => chiaveMoto(n) === chiave);
  const g = nome && garePassateMoto[nome], righe = g && (g.classifiche || {}).MotoGP;
  if (!righe || !righe.length) return null;
  // ora di partenza esatta se salvata; per le gare più vecchie (senza pronostici) vale la fine del giorno
  const orari = await caricaOrari();
  return { nome, pole: g.pole != null ? String(g.pole) : null, giro: g.giro_veloce != null ? String(g.giro_veloce) : null, qInizio: orari["q:" + chiave] ? new Date(orari["q:" + chiave]).getTime() : null,
    vero: righe.filter((r) => r.pos && r.pos <= 3).sort((a, b) => a.pos - b.pos).map((r) => String(r.numero)), inizio: orari[chiave] ? new Date(orari[chiave]).getTime() : new Date(g.data + "T23:59:59Z").getTime() };
}

// per ogni serie: piloti tra cui scegliere, prossimo Gran Premio e Gran Premi già disputati
async function serieDati(serie) {
  if (serie === "moto") {
    const cal = await fetchJSON("data/motogp.json").catch(() => ({ weekend: [] }));
    const piloti = dati.moto.map((p) => ({ n: String(p.numero), nome: p.nome }));
    const gareOrd = cal.weekend.map((w) => ({ w, gara: w.sessioni.find((x) => x.nome === "Gara") })).filter((x) => x.gara).sort((a, b) => new Date(a.gara.inizio) - new Date(b.gara.inizio));
    const pross = gareOrd.find((x) => new Date(x.gara.inizio).getTime() + 45 * 60000 > Date.now());   // il calendario MotoGP non ha la fine della gara: la si conta 45 minuti dopo il via
    if (!garePassateMoto) garePassateMoto = await fetchJSON("data/motogp-gare.json").catch(() => ({}));
    return { serie, etichetta: "MotoGP", piloti, prossimo: pross && { chiave: chiaveMoto(pross.w.nome), nome: pross.w.nome, inizio: pross.gara.inizio },
      vero: podioVeroMoto, passate: Object.keys(garePassateMoto).map((n) => ({ chiave: chiaveMoto(n), nome: n, data: garePassateMoto[n].data })), appartiene: (c) => c.startsWith("m") };
  }
  const piloti = dati.roster.filter((p) => p.nome).sort((a, b) => (a.posizione ?? 99) - (b.posizione ?? 99)).map((p) => ({ n: String(p.numero), nome: p.nome }));
  const pross = dati.eventi.filter((g) => new Date(g.fine) > new Date()).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
  const gara = pross && pross.sessioni.find((x) => x.nome === "Gara");
  return { serie, etichetta: "F1", piloti, prossimo: pross && { chiave: String(pross.id), nome: pross.nome, inizio: gara ? gara.inizio : null },
    vero: podioVeroF1, passate: dati.eventi.map((g) => ({ chiave: String(g.id), nome: g.nome, data: g.inizio })), appartiene: (c) => !c.startsWith("m") };
}

async function partitaPronostico(serie = "f1", vista = "voto") {
  scelta.classList.add("hidden"); box.classList.remove("hidden");
  box.classList.toggle("serie-moto", serie === "moto");
  const [S, altra] = await Promise.all([serieDati(serie), serieDati(serie === "f1" ? "moto" : "f1")]);
  const F1 = serie === "f1" ? S : altra, MO = serie === "moto" ? S : altra;
  const salvati = () => { try { return JSON.parse(leggi("pronostici") || "{}"); } catch (e) { return {}; } };
  const opz = (sel) => `<option value="">Scegli…</option>` + S.piloti.map((p) => `<option value="${p.n}" ${String(sel) === p.n ? "selected" : ""}>${esc(p.nome)}</option>`).join("");
  const nomeDi = (s, n) => (s.piloti.find((p) => p.n === String(n)) || {}).nome || "n.d.";
  const pr = S.prossimo;
  const quando = (d) => new Date(d).toLocaleString("it-IT", { weekday: "long", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Rome" });
  const orariG = await caricaOrari();
  const qInizio = pr && orariG["q:" + pr.chiave];
  // tutto il pronostico (podio, pole, giro veloce) si chiude all'inizio delle qualifiche, così nessuno copia dalla griglia
  const chiusura = pr && (qInizio || pr.inizio);
  const aperto = !!chiusura && new Date(chiusura) > new Date();
  const poleAperta = aperto;
  const tutti = salvati();
  let totale = 0, righe = "";
  for (const [id, mio] of Object.entries(tutti)) {
    if (!S.appartiene(id)) continue;
    const r = await S.vero(id);
    const pt = r ? punti({ ...mio, tp: 0 }, r) : null;
    if (pt !== null) totale += pt;
    righe += `<tr><td><strong>${esc(mio.nome)}</strong></td><td>${mio.podio.map((n) => nomeDi(S, n)).map(esc).join(", ")}</td><td>${r ? r.vero.map((n) => nomeDi(S, n)).map(esc).join(", ") : "<span class='muted'>in attesa</span>"}</td><td><strong>${pt ?? "–"}</strong></td></tr>`;
  }
  box.innerHTML = `<div class="quiz-testa pron-testa"><span>Pronostico del podio</span><span>I tuoi punti ${S.etichetta}: <b>${totale}</b></span></div>
    <div class="pron-premio"><b>Premio di fine anno</b><span>Chi è primo nella classifica generale (F1 + MotoGP) il 31 dicembre 2026 vince una <b>carta regalo Amazon da 50 €</b>. Per vincere bisogna seguire <b>@gp.oggi su TikTok</b>. Gratis, senza registrazione. Premi in aggiornamento.</span>
      <details class="pron-reg"><summary>Regolamento</summary><ol>
        <li><b>Chi organizza:</b> GP Oggi, sito indipendente. Contatti: info@gpoggi.it.</li>
        <li><b>Durata:</b> dall'8 ottobre al 31 dicembre 2026. Contano i pronostici di Formula 1 e MotoGP inviati prima dell'inizio delle qualifiche di ogni Gran Premio (per la MotoGP la Q1): da quel momento podio, pole e giro veloce non si possono più cambiare.</li>
        <li><b>Email:</b> per concorrere al premio serve inserire un'email valida al momento del pronostico. Una stessa email può essere collegata a un solo giocatore (un solo nickname e un solo codice di recupero). L'email non è pubblica, serve solo a consegnare il premio e viene cancellata dopo la consegna. Senza email si gioca e si va in classifica, ma non si può vincere.</li>
        <li><b>Partecipazione:</b> gratuita, senza acquisti né registrazione. Un solo nickname a persona. Prima di consegnare il premio GP Oggi controlla i nickname collegati tra loro (stesso dispositivo o stessa connessione) e può chiedere al vincitore di dimostrare che il nickname è il suo: chi usa più nickname o trucchi viene escluso, con tutti i suoi nickname.</li>
        <li><b>Seguirci per vincere:</b> per ricevere il premio il vincitore deve seguire il profilo TikTok <b>@gp.oggi</b> e lo dimostra con uno screenshot al momento del ritiro. In futuro potremo chiedere di seguire anche il nostro profilo Instagram: se cambia, lo scriviamo qui prima che l'iniziativa finisca.</li>
        <li><b>Chi vince:</b> chi ha più punti nella classifica generale a fine anno. A parità di punti vince chi ha giocato più gare; se ancora pari, il premio viene sorteggiato tra i pari merito.</li>
        <li><b>Premi in aggiornamento:</b> il premio indicato qui è garantito e non viene ridotto. Se il sito inizia a generare ricavi potremo aggiungere altri premi (per esempio più carte regalo da 50 euro per i primi classificati): l'elenco aggiornato è sempre in questo regolamento e gli eventuali premi in più vengono annunciati sul sito e sui profili social.</li>
        <li><b>Premio:</b> una carta regalo Amazon da 50 euro, non convertibile in denaro. Amazon non sponsorizza e non partecipa all'iniziativa.</li>
        <li><b>Gioca sempre dallo stesso dispositivo:</b> il sito ti riconosce dal telefono o dal computer su cui hai votato la prima volta. Dopo il primo voto ricevi un codice di recupero di 8 caratteri: fai uno screenshot e conservalo. Se cambi dispositivo, browser o cancelli i dati di navigazione, ti serve il codice per riprendere il tuo nickname e i tuoi punti.</li>
        <li><b>Nickname o codice dimenticato:</b> chi ha inserito l'email nel pronostico può scrivere a info@gpoggi.it dall'indirizzo che ha usato e riceve un nuovo codice di recupero; i punti restano. Senza email non è possibile verificare l'identità.</li>
        <li><b>Come si ritira:</b> il nickname vincitore sarà pubblicato sul sito e sui profili social. Il premio viene mandato all'email indicata dal vincitore. GP Oggi lo contatta; se non risponde o non dimostra di essere il titolare del nickname entro 30 giorni, il premio passa al secondo in classifica.</li>
        <li><b>Minorenni:</b> possono partecipare solo con il consenso di un genitore.</li>
        <li><b>Modifiche:</b> l'organizzatore può cambiare o annullare l'iniziativa per cause tecniche, avvisando sul sito.</li>
      </ol></details></div>
    <div class="pron-doppio">Vota <span class="pd-f1">F1</span> + <span class="pd-moto">MotoGP</span><small>i punti si sommano nella stessa classifica</small></div>
    <div class="chip-serie-riga" style="display:flex;gap:8px;margin:14px 0 4px"><button class="chip-serie grande f1 ${serie === "f1" ? "attivo" : ""}" data-s="f1">Formula 1${F1.prossimo && tutti[F1.prossimo.chiave] ? " ✓" : ""}</button><button class="chip-serie grande moto ${serie === "moto" ? "attivo" : ""}" data-s="moto">MotoGP${MO.prossimo && tutti[MO.prossimo.chiave] ? " ✓" : ""}</button>${base ? `<button class="chip-serie chip-class" data-vai="classifica">Classifica</button>` : ""}</div>
    <div id="vista-voto">${pr ? `<h3 class="quiz-titolo">${esc(pr.nome)}: chi sale sul podio?</h3>
    ${aperto ? `<p class="pron-chiusure">⏱ Si vota fino a <b>${quando(chiusura)}</b> (${qInizio ? "inizio delle qualifiche" : "partenza della gara"}): dopo non si cambia più niente</p>` : ""}
    ${aperto ? `<div class="pron-form">${[1, 2, 3].map((i) => `<label>${i}° posto<select class="sel" id="p${i}">${opz((tutti[pr.chiave] || { podio: [] }).podio[i - 1])}</select></label>`).join("")}</div>
    ${tutti[pr.chiave] && !tutti[pr.chiave].pole && !tutti[pr.chiave].giro ? `<div class="pron-nuovo"><b>Novità:</b> hai già votato, ora puoi aggiungere pole${poleAperta ? "" : " (chiusa: qualifiche iniziate)"} e giro veloce. Scegli qui sotto e premi «Salva le modifiche».</div>` : ""}
    <div class="pron-form pron-extra"><label>Pole position · <b>7 punti</b><select class="sel" id="pole" ${poleAperta ? "" : "disabled"}>${opz((tutti[pr.chiave] || {}).pole)}</select>${poleAperta ? "" : `<small class="muted" style="text-transform:none;letter-spacing:0">Chiusa: le qualifiche sono iniziate</small>`}</label>
      <label>Giro più veloce in gara · <b>1 punto</b><select class="sel" id="giro">${opz((tutti[pr.chiave] || {}).giro)}</select></label></div>
    ${base ? `<label class="pron-nome">Il tuo nickname in classifica<input type="text" id="nome" maxlength="16" autocomplete="nickname" placeholder="Per esempio Giovanni_F1" value="${esc(leggi("pron-nome") || "")}"></label>` : ""}
    ${base ? `<label class="pron-nome">Email per il premio (facoltativa)<input type="email" id="email" maxlength="80" autocomplete="email" placeholder="nome@esempio.it" value="${esc(leggi("pron-email") || "")}"></label>
    <p class="muted" style="font-size:13px;margin:-6px 0 12px">Serve solo per mandarti il premio se vinci: senza email giochi lo stesso ma non puoi vincere. Non è mai pubblica e la cancelliamo dopo la consegna. <a href="privacy.html" class="accent">Privacy</a></p>` : ""}
    <div class="quiz-esito"><button class="quiz-avanti pron-rosso" id="salva" style="margin:0">${tutti[pr.chiave] ? "Aggiorna il pronostico" : "Salva il pronostico"}</button> <span id="msg" class="muted"></span></div><div id="poi"></div>` : `<p class="muted">Le votazioni per questo Gran Premio sono chiuse: sono iniziate le qualifiche.</p>`}
    <div class="pron-punti"><b>Come si fanno i punti</b><ul><li>1° posto indovinato: <b>10</b> punti</li><li>2° posto indovinato: <b>5</b> punti</li><li>3° posto indovinato: <b>2</b> punti</li><li>Pilota sul podio ma in un'altra posizione: <b>1</b> punto</li><li>Podio completo esatto: <b>+5</b></li><li>Pole position indovinata: <b>7</b> punti </li><li>Giro più veloce in gara indovinato: <b>1</b> punto</li></ul><span class="muted">Massimo 30 punti per Gran Premio. </span>
    <span class="muted">Il pronostico si può cambiare fino all'inizio delle qualifiche: da quel momento è chiuso tutto, podio compreso. La classifica si aggiorna dopo ogni gara.</span></div>` : `<p class="muted">Nessun Gran Premio ${S.etichetta} in programma.</p>`}
    ${base ? `<div class="pron-invito"><b>La classifica è appena partita: tutti da zero.</b> Ogni Gran Premio vale fino a 30 punti e ogni weekend ci sono due gare, una di Formula 1 e una di MotoGP. Chi le vota tutte e due fa punti il doppio più in fretta.</div>` : ""}
    ${righe ? `<h3 class="quiz-titolo" style="margin-top:20px">I tuoi pronostici ${S.etichetta}</h3><div class="table-wrap"><table class="results"><thead><tr><th>Gran Premio</th><th>Il tuo podio</th><th>Podio vero</th><th>Punti</th></tr></thead><tbody>${righe}</tbody></table></div>` : ""}
    ${base ? boxRecupero() : ""}</div>
    ${base ? `<div id="vista-class" class="hidden"><h3 class="quiz-titolo" id="titolo-classifica">Classifica</h3><div id="classifica"><p class="muted">Carico la classifica…</p></div></div>` : ""}
    <div class="quiz-azioni" style="margin-top:16px"><button class="quiz-avanti secondario" id="menu" style="margin:0">Cambia gioco</button></div>`;
  const recVai = document.getElementById("rec-vai");
  if (recVai) recVai.addEventListener("click", async () => {
    const n = document.getElementById("rec-nick").value.trim().replace(/\s+/g, " "), c = document.getElementById("rec-cod").value.trim().toUpperCase(), m = document.getElementById("rec-msg");
    if (!/^[\p{L}\p{N} _.-]{3,16}$/u.test(n) || !/^[A-Z2-9]{8}$/.test(c)) { m.textContent = "Scrivi il nickname e il codice di 8 caratteri."; return; }
    scrivi("pron-id", await idDa(n, c)); scrivi("pron-codice", c); scrivi("pron-nick0", n); scrivi("pron-nome", n);
    m.textContent = "Fatto: da ora giochi come " + n + ". Se il codice è sbagliato, al prossimo salvataggio ti dirà che il nickname è già usato.";
    setTimeout(() => partitaPronostico(serie), 1800);
  });
  document.getElementById("menu").addEventListener("click", () => { box.classList.remove("serie-moto"); tornaMenu(); });
  // Classifica: scheda a parte, al posto del modulo di voto
  const vaiClass = box.querySelector("[data-vai]");
  const mostraVista = (classifica) => {
    document.getElementById("vista-voto").classList.toggle("hidden", classifica);
    const vc = document.getElementById("vista-class"); if (vc) vc.classList.toggle("hidden", !classifica);
    box.querySelectorAll(".chip-serie[data-s]").forEach((b) => b.classList.toggle("attivo", !classifica && b.dataset.s === serie));
    if (vaiClass) vaiClass.classList.toggle("attivo", classifica);
  };
  box.querySelectorAll(".chip-serie[data-s]").forEach((b) => b.addEventListener("click", () => { if (b.dataset.s !== serie) partitaPronostico(b.dataset.s); else mostraVista(false); }));
  if (vaiClass) vaiClass.addEventListener("click", () => mostraVista(true));
  if (vista === "classifica") mostraVista(true);
  const salva = document.getElementById("salva");
  // dopo il voto il modulo resta bloccato: per cambiarlo (fino all'inizio delle qualifiche) si tocca «Cambia il voto»
  const campi = () => box.querySelectorAll("#vista-voto .pron-form select, #nome, #email");
  const blocca = () => {
    campi().forEach((el) => { el.disabled = true; });
    salva.disabled = true; salva.textContent = "✓ Votato";
    if (!document.getElementById("cambia")) {
      salva.insertAdjacentHTML("afterend", ` <button class="quiz-avanti secondario" id="cambia" style="margin:0">✏️ Cambia il voto</button>`);
      document.getElementById("cambia").addEventListener("click", sblocca);
    }
  };
  function sblocca() {
    campi().forEach((el) => { el.disabled = el.id === "pole" && !poleAperta; });
    salva.disabled = false; salva.textContent = "Salva le modifiche";
    const c = document.getElementById("cambia"); if (c) c.remove();
    const m = document.getElementById("msg"); m.textContent = poleAperta ? "Cambia quello che vuoi e premi «Salva le modifiche»." : "Cambia il podio o il giro veloce e premi «Salva le modifiche» (la pole è chiusa: le qualifiche sono iniziate)."; m.className = "pron-msg";
  }
  if (salva && tutti[pr && pr.chiave]) {
    blocca();
    // chi ha votato prima che esistessero pole e giro veloce trova il modulo già aperto
    if (!tutti[pr.chiave].pole && !tutti[pr.chiave].giro) sblocca();
  }
  if (salva) salva.addEventListener("click", async () => {
    const podio = [1, 2, 3].map((i) => document.getElementById("p" + i).value);
    const msg = document.getElementById("msg");
    if (new Date(chiusura) <= new Date()) { msg.textContent = "Le votazioni sono chiuse: sono iniziate le qualifiche."; setTimeout(() => partitaPronostico(serie), 1500); return; }
    if (podio.some((x) => !x) || new Set(podio).size < 3) { msg.textContent = "Scegli tre piloti diversi."; return; }
    const nomeEl = document.getElementById("nome"), nome = nomeEl ? nomeEl.value.trim().replace(/\s+/g, " ") : "";
    if (base && !/^[\p{L}\p{N} _.-]{3,16}$/u.test(nome)) { msg.textContent = "Scrivi un nickname di 3-16 caratteri (lettere, numeri, spazi)."; return; }
    const emailEl = document.getElementById("email"), email = emailEl ? emailEl.value.trim() : "";
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { msg.textContent = "L'email non sembra valida: correggila o lasciala vuota."; return; }
    const pole = (document.getElementById("pole") || {}).value || "", giro = (document.getElementById("giro") || {}).value || "";
    // sul dispositivo si salva solo se il voto è arrivato davvero (altrimenti comparirebbe "votato" anche quando non lo è)
    const salvaQui = () => { const t = salvati(); t[pr.chiave] = { nome: pr.nome, podio, pole, giro }; scrivi("pronostici", JSON.stringify(t)); };
    let testo = "Salvato sul dispositivo.", ok = !base;
    if (!base) salvaQui();
    if (base) {
      scrivi("pron-nome", nome); if (email) scrivi("pron-email", email);
      try {
        const r = await fetch(base + "/pronostico", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ gp: pr.chiave, id: await idGiocatore(nome), nick: nome, podio, pole, giro, ...(email ? { email } : {}) }) });
        if (r.status === 409) {
          const j = await r.json().catch(() => ({}));
          testo = /email/.test(j.errore || "") ? "Questa email è già collegata a un altro giocatore: in fondo alla pagina tocca «Hai già giocato da un altro telefono?» e inserisci nickname e codice di recupero. Se non hai più il codice, scrivi a info@gpoggi.it." : `Il nickname ${nome} è già usato. Se sei tu e hai votato da un altro telefono, in fondo alla pagina tocca «Hai già giocato da un altro telefono?» e inserisci nickname e codice di recupero. Altrimenti scegline un altro.`;
        }
        else if (r.status === 429) testo = "Troppi invii oggi: riprova domani.";
        else if (r.status === 403) testo = "Le votazioni sono chiuse: sono iniziate le qualifiche.";
        else if (!r.ok) throw new Error();
        else { ok = true; salvaQui(); testo = `Salvato! Sei in classifica come ${nome}.`; if (leggi("pron-codice")) testo += ` Il tuo codice di recupero è ${leggi("pron-codice")}: fai uno screenshot.`; }
      } catch (e) { testo = "Non sono riuscito a salvare il voto: controlla la connessione e riprova."; }
    }
    msg.textContent = testo;
    msg.className = ok ? "pron-msg ok" : "pron-msg errore";
    if (ok) blocca();
    // subito dopo, l'invito a fare anche l'altra serie
    const altraS = serie === "f1" ? MO : F1, ap = altraS.prossimo && altraS.prossimo.inizio && new Date(altraS.prossimo.inizio) > new Date();
    if (ap && !salvati()[altraS.prossimo.chiave] && /Salvato/.test(testo)) {
      const poi = document.getElementById("poi");
      poi.innerHTML = `<button class="pron-poi ${serie === "f1" ? "moto" : "f1"}">Ora fai il podio ${altraS.etichetta}: ${esc(altraS.prossimo.nome)} →</button>`;
      poi.querySelector("button").addEventListener("click", () => { partitaPronostico(serie === "f1" ? "moto" : "f1").then(() => box.scrollIntoView({ behavior: "smooth" })); });
    }
    if (base) mostraClassifica();
  });
  if (base) mostraClassifica();

  // Classifica generale (F1 + MotoGP), dell'ultimo weekend e Gran Premio per Gran Premio: contano solo i pronostici arrivati prima della gara
  async function mostraClassifica() {
    const el = document.getElementById("classifica");
    if (!el) return;
    let lista = [];
    try { lista = (await fetch(base + "/pronostici").then((r) => r.json())).pronostici || []; } catch (e) { el.innerHTML = `<p class="muted">Classifica non disponibile al momento.</p>`; return; }
    const perGp = {};
    for (const x of lista) (perGp[x.gp] ||= []).push(x);
    const chiusi = [];
    for (const s of [F1, MO]) {
      for (const g of s.passate.slice().sort((a, b) => new Date(a.data) - new Date(b.data))) {
        if (!perGp[g.chiave]) continue;
        const r = await s.vero(g.chiave);
        if (r) chiusi.push({ s, g, r, voci: perGp[g.chiave].filter((x) => x.podio && x.ts <= (r.qInizio || r.inizio)).map((x) => ({ nick: x.nick, podio: x.podio, pt: punti(x, r) })).sort((a, b) => b.pt - a.pt || a.nick.localeCompare(b.nick)) });
      }
    }
    chiusi.sort((a, b) => a.r.inizio - b.r.inizio);
    const somma = (gruppo) => {
      const m = {};
      for (const c of gruppo) for (const v of c.voci) { const o = (m[v.nick] ||= { nick: v.nick, pt: 0, gare: 0, f1: 0, mo: 0 }); o.pt += v.pt; o.gare++; o[c.s.etichetta === "F1" ? "f1" : "mo"] += v.pt; }
      return Object.values(m).sort((a, b) => b.pt - a.pt || b.gare - a.gare || a.nick.localeCompare(b.nick));
    };
    const io = (leggi("pron-nome") || "").toLowerCase();
    const riga = (v, i, extra) => `<tr class="${v.nick.toLowerCase() === io ? "pron-io" : ""}"><td>${i + 1}</td><td><b>${esc(v.nick)}</b></td>${extra}<td><b>${v.pt}</b></td></tr>`;
    const nota = `<p class="muted" style="font-size:13px">La classifica si aggiorna dopo ogni gara, quando i risultati sono ufficiali.</p>`;
    const ultimo = chiusi.length ? chiusi[chiusi.length - 1].r.inizio : 0;
    const weekend = chiusi.filter((c) => ultimo - c.r.inizio < 4 * 864e5);
    el.innerHTML = nota + `<label class="pron-scegli">Classifica <select id="gp-class" class="sel"><optgroup label="Classifiche"><option value="gen">Generale · premio di fine anno (F1 + MotoGP)</option><option value="f1">Solo Formula 1</option><option value="mo">Solo MotoGP</option><option value="wk">Ultimo weekend</option></optgroup><optgroup label="Per Gran Premio" ${chiusi.length ? "" : "hidden"}>${chiusi.slice().reverse().map((c, i) => `<option value="${chiusi.length - 1 - i}">${esc(c.g.nome)} (${c.s.etichetta})</option>`).join("")}</optgroup></select></label>
      <p class="muted" id="nota-class" style="font-size:13px;margin:0 0 8px"></p>
      <div class="table-wrap"><table class="results" id="tab-gp"></table></div>`;
    const disegna = () => {
      const val = document.getElementById("gp-class").value, t = document.getElementById("tab-gp");
      const nota = document.getElementById("nota-class");
      nota.textContent = val === "gen" ? "È la classifica del premio di fine anno: somma dei punti di Formula 1 e MotoGP." : val === "f1" ? "Statistiche: solo i pronostici di Formula 1." : val === "mo" ? "Statistiche: solo i pronostici di MotoGP." : "";
      if (!chiusi.length) { t.innerHTML = `<tbody><tr><td class="muted" style="white-space:normal">Ancora nessuna gara disputata con pronostici: i punteggi compaiono qui dopo la prima gara, quando i risultati sono ufficiali.</td></tr></tbody>`; return; }
      if (val === "gen") {
        t.innerHTML = `<thead><tr><th>#</th><th>Nickname</th><th>F1</th><th>MotoGP</th><th>Gare</th><th>Totale</th></tr></thead><tbody>${somma(chiusi).map((v, i) => riga(v, i, `<td>${v.f1}</td><td>${v.mo}</td><td>${v.gare}</td>`)).join("")}</tbody>`;
      } else if (val === "f1" || val === "mo" || val === "wk") {
        const gr = val === "wk" ? weekend : chiusi.filter((c) => c.s.etichetta === (val === "f1" ? "F1" : "MotoGP")), lista = somma(gr);
        t.innerHTML = lista.length ? `<thead><tr><th>#</th><th>Nickname</th><th>Gare</th><th>Punti</th></tr></thead><tbody>${lista.map((v, i) => riga(v, i, `<td>${v.gare}</td>`)).join("")}</tbody>` : `<tbody><tr><td class="muted">Ancora nessuna gara disputata con pronostici.</td></tr></tbody>`;
      } else {
        const c = chiusi[Number(val)];
        t.innerHTML = `<thead><tr><th>#</th><th>Nome</th><th>Il suo podio</th><th>Punti</th></tr></thead><tbody>${c.voci.map((v, i) => riga(v, i, `<td>${v.podio.map((n) => nomeDi(c.s, n)).map(esc).join(", ")}</td>`)).join("")}</tbody>`;
      }
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
  if (g.pixel) return partitaPixel();
  box.classList.remove("hidden"); scelta.classList.add("hidden"); box.innerHTML = `<p class="muted">Preparo le domande…</p>`;
  let modo;
  if (chiave === "pilota") modo = await scegliModo();
  const qs = await GEN[chiave](modo);
  if (!qs.length) { box.innerHTML = `<p class="muted">Non ci sono abbastanza dati per questo gioco.</p>`; return; }
  partitaQuiz(chiave, qs);
}

// ---- Chi è? Foto pixelata: la foto parte sgranata e si schiarisce ogni due secondi; i punti calano a ogni passo (5, 4, 3, 2, 1)
const BLOCCHI_PIXEL = [5, 7, 10, 14, 22, 36], PUNTI_PIXEL = [5, 4, 3, 2, 1, 1], PASSO_PIXEL = 2200;
let timerPixel = null;
function pixelata(img, blocchi, canvas) {
  const w = img.naturalWidth, h = img.naturalHeight, scala = Math.min(1, 700 / Math.max(w, h));
  canvas.width = Math.round(w * scala); canvas.height = Math.round(h * scala);
  const piccolo = document.createElement("canvas"), lato = Math.max(w, h);
  piccolo.width = Math.max(1, Math.round(blocchi * w / lato)); piccolo.height = Math.max(1, Math.round(blocchi * h / lato));
  piccolo.getContext("2d").drawImage(img, 0, 0, piccolo.width, piccolo.height);
  const c = canvas.getContext("2d"); c.imageSmoothingEnabled = false; c.drawImage(piccolo, 0, 0, piccolo.width, piccolo.height, 0, 0, canvas.width, canvas.height);
}
async function partitaPixel() {
  box.classList.remove("hidden"); scelta.classList.add("hidden"); box.innerHTML = `<p class="muted">Preparo le foto…</p>`;
  const oggi = dati.roster.filter((p) => p.foto && p.nome).map((p) => ({ nome: p.nome, foto: p.foto, serie: "Formula 1", indizio: `${p.team || ""}`.trim() }));
  const passato = dati.storiche.map((p) => ({ nome: p.nome, foto: p.foto, serie: p.serie, indizio: `Anni in pista: ${p.anni}` }));
  const pool = [...oggi, ...passato];
  const domande = mescola(pool).slice(0, N);
  let i = 0, punti = 0;
  const carica = (p) => new Promise((ok, no) => { const im = new Image(); im.onload = () => ok(im); im.onerror = no; im.src = p.foto.file || p.foto.url; });
  const fine = () => { clearInterval(timerPixel); const prec = record("pixel"); salvaRecord("pixel", punti); schermataFine("pixel", punti, N * PUNTI_PIXEL[0], prec, () => avvia("pixel")); };
  const mostra = async () => {
    clearInterval(timerPixel);
    const p = domande[i];
    let im; try { im = await carica(p); } catch (e) { i++; return i < domande.length ? mostra() : fine(); }
    const stessi = pool.filter((x) => x.serie === p.serie && x.nome !== p.nome);
    const opzioni = mescola([p.nome, ...mescola([...new Set(stessi.map((x) => x.nome))]).slice(0, 3)]);
    let livello = 0, risposto = false;
    box.innerHTML = `<div class="quiz-testa"><span>${esc(GIOCHI.pixel.titolo)} · ${i + 1} di ${domande.length}</span><span>Punti: <b>${punti}</b></span></div>
      <h3 class="quiz-titolo">Chi è questo pilota?</h3>
      <div class="quiz-img foto-quiz pixel-quiz"><canvas id="px" aria-label="Foto pixelata del pilota da indovinare" role="img"></canvas><span class="pixel-punti" id="pxp"></span></div>
      <div class="pixel-indizi" id="pxi"><span>${esc(p.serie)}</span></div>
      <div class="quiz-opzioni">${opzioni.map((o, k) => `<button class="quiz-opz" data-k="${k}">${esc(o)}</button>`).join("")}</div><div class="quiz-esito" id="esito"></div>`;
    const canvas = document.getElementById("px"), ptxt = document.getElementById("pxp"), indizi = document.getElementById("pxi");
    const disegna = () => {
      pixelata(im, BLOCCHI_PIXEL[livello], canvas); ptxt.textContent = `+${PUNTI_PIXEL[livello]}`;
      if (livello >= 2 && p.indizio) indizi.innerHTML = `<span>${esc(p.serie)}</span><span>${esc(p.indizio)}</span>`;
    };
    disegna();
    window.__px = { giusto: p.nome, opzioni, avanza: () => { if (livello < BLOCCHI_PIXEL.length - 1) { livello++; disegna(); } } };   // serve solo a registrare i video dimostrativi
    timerPixel = setInterval(() => { if (livello < BLOCCHI_PIXEL.length - 1) { livello++; disegna(); } else clearInterval(timerPixel); }, PASSO_PIXEL);
    box.querySelectorAll(".quiz-opz").forEach((b) => b.addEventListener("click", () => {
      if (risposto) return; risposto = true; clearInterval(timerPixel);
      const ok = opzioni[Number(b.dataset.k)] === p.nome, guadagno = ok ? PUNTI_PIXEL[livello] : 0;
      punti += guadagno;
      pixelata(im, Math.max(im.naturalWidth, im.naturalHeight), canvas); ptxt.textContent = "";
      box.querySelectorAll(".quiz-opz").forEach((x, idx) => { x.disabled = true; if (opzioni[idx] === p.nome) x.classList.add("giusta"); else if (x === b) x.classList.add("sbagliata"); });
      document.getElementById("esito").innerHTML = `<span class="esito-testo"><b>${ok ? `Giusto! +${guadagno}` : "Sbagliato."}</b> ${ok ? "" : "Era " + esc(p.nome) + "."}</span>
        <button class="quiz-avanti" id="avanti">${i + 1 < domande.length ? "Avanti →" : "Vedi il risultato"}</button><div class="credito">${credito(p.foto)}</div>`;
      document.getElementById("avanti").addEventListener("click", () => { i++; i < domande.length ? mostra() : fine(); });
    }));
  };
  mostra();
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
    el.textContent = r ? (b.dataset.gioco === "punti" ? `Record: ${r} di fila` : b.dataset.gioco === "pixel" ? `Record: ${r}/${N * PUNTI_PIXEL[0]}` : `Record: ${r}/${N}`) : "";
  });
}

try {
  await carica();
  scelta.innerHTML = Object.entries(GIOCHI).map(([k, g]) => `<button class="gioco-card" data-gioco="${k}"><b>${esc(g.titolo)}</b><span>${esc(g.testo)}</span></button>`).join("");
  aggiornaRecord();
  scelta.addEventListener("click", (e) => { const b = e.target.closest(".gioco-card"); if (b) avvia(b.dataset.gioco); });
  const q = new URLSearchParams(location.search);
  if (q.get("gioco") === "pronostico") partitaPronostico(q.get("serie") === "moto" ? "moto" : "f1", q.get("vista") === "classifica" ? "classifica" : "voto");
} catch (e) {
  erroreCaricamento(scelta);
}
