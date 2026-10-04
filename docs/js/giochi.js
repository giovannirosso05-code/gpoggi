import { renderHeader, renderFooter, fetchJSON, esc, credito, erroreCaricamento } from "./common.js";

renderHeader("giochi");
renderFooter();

const N = 10;
const scelta = document.getElementById("scelta");
const box = document.getElementById("partita");

const mescola = (a) => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; };
const record = (g) => { try { return Number(localStorage.getItem("record-" + g)) || 0; } catch (e) { return 0; } };
const salvaRecord = (g, v) => { try { if (v > record(g)) localStorage.setItem("record-" + g, String(v)); } catch (e) {} };

let dati = null;
async function carica() {
  if (dati) return dati;
  const [eventi, roster, moto] = await Promise.all([fetchJSON("data/events.json"), fetchJSON("data/roster.json"), fetchJSON("data/motogp-classifica.json").catch(() => null)]);
  dati = { eventi: eventi.filter((e) => e.mappa), roster: roster.filter((p) => p.foto && p.nome), moto: moto ? moto.piloti : [] };
  return dati;
}

function domandeMoto() {
  const marche = [...new Set(dati.moto.map((p) => p.moto))];
  return mescola(dati.moto).slice(0, N).map((p) => {
    const altre = mescola(marche.filter((m) => m !== p.moto)).slice(0, 3);
    return { giusto: { nome: p.moto, rider: p.nome, team: p.team }, opzioni: mescola([{ nome: p.moto }, ...altre.map((m) => ({ nome: m }))]) };
  });
}

function domande(gioco) {
  if (gioco === "moto") return domandeMoto();
  const { eventi, roster } = dati;
  const pool = gioco === "circuito" ? eventi : roster;
  const etichetta = (x) => (gioco === "circuito" ? x.nome : x.nome);
  return mescola(pool).slice(0, N).map((giusto) => {
    const altri = mescola(pool.filter((x) => etichetta(x) !== etichetta(giusto))).slice(0, 3);
    return { giusto, opzioni: mescola([giusto, ...altri]) };
  });
}

function partita(gioco) {
  const qs = domande(gioco);
  let i = 0, punti = 0;
  scelta.classList.add("hidden");
  box.classList.remove("hidden");

  const mostra = () => {
    const q = qs[i];
    const immagine = gioco === "moto" ? `<div class="quiz-img foto-quiz" style="padding:28px"><div class="quiz-pilota"><b>${esc(q.giusto.rider)}</b><span>${esc(q.giusto.team)}</span></div></div>` : gioco === "circuito"
      ? `<div class="quiz-img mappa-quiz"><img src="${esc(q.giusto.mappa.file || q.giusto.mappa.url)}" alt="Tracciato da indovinare"></div>`
      : `<div class="quiz-img foto-quiz"><img src="${esc(q.giusto.foto.file || q.giusto.foto.url)}" alt="Pilota da indovinare"></div>`;
    box.innerHTML = `
      <div class="quiz-testa"><span>Domanda ${i + 1} di ${qs.length}</span><span>Punti: <b>${punti}</b></span></div>
      <h3 class="quiz-titolo">${gioco === "moto" ? "Che moto guida questo pilota?" : gioco === "circuito" ? "Di quale Gran Premio è questo tracciato?" : "Chi è questo pilota?"}</h3>
      ${immagine}
      <div class="quiz-opzioni">${q.opzioni.map((o, k) => `<button class="quiz-opz" data-k="${k}">${esc(o.nome)}</button>`).join("")}</div>
      <div class="quiz-esito" id="esito"></div>`;
    box.querySelectorAll(".quiz-opz").forEach((b) => b.addEventListener("click", () => rispondi(Number(b.dataset.k)), { once: true }));
  };

  const rispondi = (k) => {
    const q = qs[i];
    const ok = q.opzioni[k].nome === q.giusto.nome;
    if (ok) punti++;
    box.querySelectorAll(".quiz-opz").forEach((b, idx) => {
      b.disabled = true;
      if (q.opzioni[idx].nome === q.giusto.nome) b.classList.add("giusta");
      else if (idx === k) b.classList.add("sbagliata");
    });
    const cred = gioco === "moto" ? "" : gioco === "pilota" ? `<div class="credito">${credito(q.giusto.foto)}</div>` : `<div class="credito">${credito(q.giusto.mappa, "Mappa")}</div>`;
    document.getElementById("esito").innerHTML = `<b>${ok ? "Giusto!" : "Sbagliato."}</b> ${ok ? "" : "Era " + esc(q.giusto.nome) + "."}
      <button class="quiz-avanti" id="avanti">${i + 1 < qs.length ? "Avanti →" : "Vedi il risultato"}</button>${cred}`;
    document.getElementById("avanti").addEventListener("click", () => { i++; i < qs.length ? mostra() : fine(); });
  };

  const fine = () => {
    const prec = record(gioco);
    salvaRecord(gioco, punti);
    box.innerHTML = `<div class="quiz-fine"><div class="quiz-punteggio">${punti}<span>/${qs.length}</span></div>
      <p>${punti === qs.length ? "Perfetto!" : punti >= 7 ? "Ottimo risultato." : punti >= 4 ? "Non male, riprova." : "Si può fare meglio: riprova."}</p>
      <p class="muted">Record personale: <b>${Math.max(prec, punti)}</b>/${qs.length}</p>
      <div class="quiz-azioni"><button class="quiz-avanti" id="ancora">Rigioca</button><button class="quiz-avanti secondario" id="menu">Cambia gioco</button></div></div>`;
    document.getElementById("ancora").addEventListener("click", () => partita(gioco));
    document.getElementById("menu").addEventListener("click", () => { box.classList.add("hidden"); scelta.classList.remove("hidden"); aggiornaRecord(); });
  };
  mostra();
}

function aggiornaRecord() {
  scelta.querySelectorAll(".gioco-card").forEach((b) => {
    const r = record(b.dataset.gioco);
    let el = b.querySelector(".rec"); if (!el) { el = document.createElement("small"); el.className = "rec"; b.appendChild(el); }
    el.textContent = r ? `Record: ${r}/${N}` : "";
  });
}

try {
  await carica();
  aggiornaRecord();
  scelta.addEventListener("click", (e) => { const b = e.target.closest(".gioco-card"); if (b) partita(b.dataset.gioco); });
} catch (e) {
  erroreCaricamento(scelta);
}
