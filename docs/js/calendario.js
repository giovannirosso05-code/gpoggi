import { renderHeader, renderFooter, fetchJSON, esc } from "./common.js";

renderHeader("gare");
renderFooter();

const TZ = "Europe/Rome";
const giorno = (iso) => new Date(iso).toLocaleDateString("sv-SE", { timeZone: TZ });          // AAAA-MM-GG in ora italiana
const ora = (iso) => new Date(iso).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit", timeZone: TZ });
const MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"];
const GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];
const PESO = { gara: 5, sprint: 4, qualifiche: 3, altro: 1 };

let weekend = [];            // {serie, id, nome, circuito, paese, sessioni:[{nome, inizio, fine, peso}]}
let attive = { f1: true, moto: true };
let mese = null, scelto = null;

function peso(nome) {
  const n = nome.toLowerCase();
  if (n === "gara") return PESO.gara;
  if (n.startsWith("sprint") && !n.includes("qualifiche")) return PESO.sprint;
  if (n.includes("qualifiche")) return PESO.qualifiche;
  return PESO.altro;
}

const ab = (n) => n.replace("Qualifiche sprint", "Q.Sprint").replace("Qualifiche", "Quali").replace(/^Prove libere\s*(\d)?$/, (m, d) => "PL" + (d || "")).replace("Warm up", "Warm-up");

function costruisci(eventi, moto) {
  const f1 = eventi.map((g) => ({ serie: "f1", id: g.id, nome: g.nome, circuito: g.circuito, paese: g.paese, sessioni: g.sessioni.map((s) => ({ nome: s.nome, inizio: s.inizio, fine: s.fine, peso: peso(s.nome) })) }));
  const m = moto.weekend.map((w) => ({ serie: "moto", id: w.nome, nome: w.nome, circuito: w.circuito, paese: w.paese, sessioni: w.sessioni.map((s) => ({ nome: s.nome, inizio: s.inizio, fine: s.fine, peso: peso(s.nome) })) }));
  return [...f1, ...m];
}

function perGiorno() {
  const mappa = {};
  for (const w of weekend) {
    if (!attive[w.serie]) continue;
    for (const s of w.sessioni) (mappa[giorno(s.inizio)] ||= []).push({ ...s, w });
  }
  for (const k of Object.keys(mappa)) mappa[k].sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  return mappa;
}

function disegnaMese() {
  const [anno, m] = mese;
  document.getElementById("mese-titolo").textContent = `${MESI[m]} ${anno}`;
  const primo = new Date(Date.UTC(anno, m, 1));
  const offset = (primo.getUTCDay() + 6) % 7;                     // lunedì = 0
  const giorni = new Date(Date.UTC(anno, m + 1, 0)).getUTCDate();
  const oggi = giorno(new Date().toISOString());
  const mappa = perGiorno();
  const tinta = {};
  for (const w of weekend) { if (!attive[w.serie]) continue; const ks = w.sessioni.map((s) => giorno(s.inizio)).sort(); for (const k of ks) (tinta[k] ||= new Set()).add(w.serie); }
  let html = GIORNI.map((g) => `<div class="ag-sett">${g}</div>`).join("");
  for (let i = 0; i < offset; i++) html += `<div class="ag-giorno vuoto"></div>`;
  for (let d = 1; d <= giorni; d++) {
    const k = `${anno}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const ev = mappa[k] || [];
    // per ogni serie si mostra la sessione piu' importante del giorno
    const principali = ["f1", "moto"].map((serie) => {
      const l = ev.filter((e) => e.w.serie === serie);
      if (!l.length) return "";
      const top = l.reduce((a, b) => (b.peso > a.peso ? b : a));
      return `<span class="ag-chip ${serie}" title="${esc(top.w.nome)} · ${esc(top.nome)}">${esc(ab(top.nome))} <b>${ora(top.inizio)}</b></span>`;
    }).join("");
    const punti = ["f1", "moto"].map((s) => (ev.some((e) => e.w.serie === s) ? `<i class="ag-punto ${s}"></i>` : "")).join("");
    const tn = tinta[k] ? " wk-" + [...tinta[k]].join(" wk-") : "";
    html += `<button class="ag-giorno${ev.length ? " con-eventi" : ""}${tn}${k === oggi ? " oggi" : ""}${k === scelto ? " scelto" : ""}" data-k="${k}" aria-label="${d} ${MESI[m]}${ev.length ? ", con sessioni" : ""}">
      <span class="ag-num">${d}</span><span class="ag-chips">${principali}</span><span class="ag-punti">${punti}</span></button>`;
  }
  document.getElementById("agenda").innerHTML = `<div class="ag-griglia">${html}</div>`;
}

function icsWeekend(w) {
  const z = (iso) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d+/, "");
  const righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GP Oggi//Calendario//IT", "CALSCALE:GREGORIAN"];
  for (const s of w.sessioni) {
    const fine = new Date(s.fine) > new Date(s.inizio) ? s.fine : new Date(new Date(s.inizio).getTime() + 36e5).toISOString();
    righe.push("BEGIN:VEVENT", `UID:${w.serie}-${w.id}-${s.nome}@gpoggi.it`.replace(/\s+/g, ""), `DTSTAMP:${z(new Date().toISOString())}`, `DTSTART:${z(s.inizio)}`, `DTEND:${z(fine)}`,
      `SUMMARY:${w.serie === "f1" ? "F1" : "MotoGP"} · ${s.nome} · ${w.nome}`, `LOCATION:${(w.circuito || "") + (w.paese ? ", " + w.paese : "")}`.replace(/,/g, "\\,"),
      "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Tra 15 minuti", "TRIGGER:-PT15M", "END:VALARM", "END:VEVENT");
  }
  righe.push("END:VCALENDAR");
  return righe.join("\r\n") + "\r\n";
}

function dettaglio() {
  const box = document.getElementById("dettaglio");
  const mappa = perGiorno();
  const ev = mappa[scelto] || [];
  if (!scelto) { box.innerHTML = `<p class="muted">Tocca un giorno per vedere il programma.</p>`; return; }
  if (!ev.length) {
    const d = new Date(scelto + "T12:00:00");
    box.innerHTML = `<h3>${d.toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long" })}</h3><p class="muted">Nessuna sessione in questo giorno.</p>`;
    return;
  }
  const weekends = [...new Map(ev.map((e) => [e.w.serie + e.w.id, e.w])).values()];
  box.innerHTML = weekends.map((w) => {
    const giorni = {};
    for (const s of w.sessioni) (giorni[giorno(s.inizio)] ||= []).push(s);
    return `<article class="ag-wk ${w.serie}">
      <div class="ag-wk-testa"><span class="cd-sigla ${w.serie === "moto" ? "moto" : ""}">${w.serie === "f1" ? "F1" : "MotoGP"}</span><h3>${esc(w.nome)}</h3></div>
      <p class="muted" style="margin:0 0 10px;font-size:13px">${esc(w.circuito || "")}${w.paese ? " · " + esc(w.paese) : ""}</p>
      ${Object.keys(giorni).sort().map((k) => `<div class="ag-wk-giorno${k === scelto ? " evid" : ""}"><b>${new Date(k + "T12:00:00").toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" })}</b>
        ${giorni[k].map((s) => `<div class="ag-sessione"><span>${esc(s.nome)}</span><span>${ora(s.inizio)}</span></div>`).join("")}</div>`).join("")}
      <div class="ag-wk-azioni"><button class="quiz-avanti ag-scarica" data-w="${esc(w.serie + "|" + w.id)}">Aggiungi al calendario</button>${w.serie === "f1" ? `<a class="accent" href="gara.html?id=${w.id}">Pagina del weekend →</a>` : `<a class="accent" href="motogp.html">Pagina MotoGP →</a>`}</div>
    </article>`;
  }).join("");
}

function cambiaMese(delta) {
  const d = new Date(Date.UTC(mese[0], mese[1] + delta, 1));
  mese = [d.getUTCFullYear(), d.getUTCMonth()];
  disegnaMese();
}

try {
  const [eventi, moto] = await Promise.all([fetchJSON("data/events.json"), fetchJSON("data/motogp.json")]);
  weekend = costruisci(eventi, moto);
  const nf = eventi.reduce((n, g) => n + g.sessioni.length, 0), nm = moto.weekend.reduce((n, w) => n + w.sessioni.length, 0);
  document.getElementById("n-f1").textContent = `${eventi.length} weekend, ${nf} sessioni.`;
  document.getElementById("n-moto").textContent = `${moto.weekend.length} weekend da disputare, ${nm} sessioni.`;
  document.getElementById("n-tutto").textContent = `${nf + nm} sessioni in un solo calendario.`;
  // mese iniziale: quello della prossima sessione (o di oggi)
  const prossima = weekend.flatMap((w) => w.sessioni).filter((s) => new Date(s.fine) > new Date()).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
  const base = prossima ? giorno(prossima.inizio) : giorno(new Date().toISOString());
  mese = [Number(base.slice(0, 4)), Number(base.slice(5, 7)) - 1];
  scelto = base;
  disegnaMese(); dettaglio();
  document.getElementById("mese-prec").addEventListener("click", () => cambiaMese(-1));
  document.getElementById("mese-succ").addEventListener("click", () => cambiaMese(1));
  document.getElementById("mese-oggi").addEventListener("click", () => { const o = giorno(new Date().toISOString()); mese = [Number(o.slice(0, 4)), Number(o.slice(5, 7)) - 1]; scelto = o; disegnaMese(); dettaglio(); });
  document.getElementById("agenda").addEventListener("click", (e) => { const b = e.target.closest(".ag-giorno[data-k]"); if (!b) return; scelto = b.dataset.k; disegnaMese(); dettaglio(); if (matchMedia("(max-width: 900px)").matches) document.getElementById("dettaglio").scrollIntoView({ behavior: "smooth", block: "nearest" }); });
  document.getElementById("filtri").addEventListener("click", (e) => { const b = e.target.closest(".chip-serie"); if (!b) return; attive[b.dataset.s] = !attive[b.dataset.s]; b.classList.toggle("attivo", attive[b.dataset.s]); b.setAttribute("aria-pressed", attive[b.dataset.s]); disegnaMese(); dettaglio(); });
  document.getElementById("dettaglio").addEventListener("click", (e) => {
    const b = e.target.closest(".ag-scarica"); if (!b) return;
    const [serie, id] = b.dataset.w.split("|");
    const w = weekend.find((x) => x.serie === serie && String(x.id) === id);
    const url = URL.createObjectURL(new Blob([icsWeekend(w)], { type: "text/calendar" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `${serie}-${w.nome.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.ics` });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
} catch (e) {
  document.getElementById("agenda").innerHTML = `<p class="muted center">Calendario non disponibile al momento.</p>`;
}
