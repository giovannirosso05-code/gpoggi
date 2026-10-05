import { renderHeader, renderFooter, fetchJSON, esc, img, credito, mappeMotoMap } from "./common.js";

renderHeader("gare");
renderFooter();

// Fuso orario scelto dal visitatore: all'inizio sempre quello italiano. Le sessioni mostrate si scelgono con i tasti sopra il calendario.
const FUSI = [["Europe/Rome", "Italia"], ["Europe/London", "Regno Unito / Portogallo"], ["Europe/Athens", "Grecia / Finlandia"], ["Europe/Moscow", "Mosca"], ["America/Sao_Paulo", "Brasile (San Paolo)"],
  ["America/New_York", "USA costa est"], ["America/Chicago", "USA centro"], ["America/Los_Angeles", "USA costa ovest"], ["America/Mexico_City", "Messico"], ["Asia/Dubai", "Emirati / Oman"],
  ["Asia/Kolkata", "India"], ["Asia/Bangkok", "Thailandia / Indonesia (Giava)"], ["Asia/Singapore", "Singapore / Malesia"], ["Asia/Tokyo", "Giappone"], ["Australia/Sydney", "Australia (Sydney)"], ["Pacific/Auckland", "Nuova Zelanda"]];
const memo = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; };
let TZ = memo("cal-fuso");
if (!FUSI.some(([z]) => z === TZ)) TZ = "Europe/Rome";
const TIPI = [["gara", "Gara"], ["sprint", "Sprint"], ["quali", "Qualifiche"], ["libere", "Prove libere"], ["altro", "Altro (warm-up)"]];
function tipo(nome) {
  const n = nome.toLowerCase();
  if (n === "gara") return "gara";
  if (n.startsWith("sprint") && !n.includes("qualifiche")) return "sprint";
  if (n.includes("qualifiche")) return "quali";
  if (n.startsWith("prove libere")) return "libere";
  return "altro";
}
const mostra = () => true;   // il calendario mostra sempre tutte le sessioni: la scelta si fa solo al momento di scaricare
// Cosa mettere nel file del calendario: scelta a parte, fatta solo nella sezione dei download (non dipende dai tasti dell'agenda)
let nelFile = { gara: true, sprint: true, quali: true, libere: false, altro: false };
try { const sf = JSON.parse(memo("cal-scarica") || "null"); if (sf) nelFile = { ...nelFile, ...sf }; } catch (e) {}
const nelCal = (sess) => nelFile[tipo(sess.nome)] !== false;
const visibiliDi = (w) => { const l = w.sessioni.filter(mostra); return l.length ? l : w.sessioni; };
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

let INFO = { report: {}, mappe: {}, f1: {} };   // commenti (report) e mappe per i riquadri
const finito = (w) => w.sessioni.every((s) => new Date(s.fine) < new Date());

function costruisci(eventi, moto, gareMoto) {
  const f1 = eventi.map((g) => ({ serie: "f1", id: g.id, nome: g.nome, circuito: g.circuito, paese: g.paese, sessioni: g.sessioni.map((s) => ({ nome: s.nome, inizio: s.inizio, fine: s.fine, peso: peso(s.nome) })) }));
  const m = moto.weekend.map((w) => ({ serie: "moto", id: w.nome, nome: w.nome, circuito: w.circuito, paese: w.paese, sessioni: w.sessioni.map((s) => ({ nome: s.nome, inizio: s.inizio, fine: s.fine, peso: peso(s.nome) })) }));
  const passati = Object.values(gareMoto || {}).filter((g) => !m.some((w) => w.nome === g.nome)).map((g) => ({ serie: "moto", id: g.nome, nome: g.nome, circuito: g.circuito, paese: "", passato: true,
    sessioni: [{ nome: "Gara", inizio: g.data + "T12:00:00+00:00", fine: g.data + "T13:00:00+00:00", peso: PESO.gara, senzaOra: true }] }));
  return [...f1, ...m, ...passati];
}

function perGiorno() {
  const mappa = {};
  for (const w of weekend) {
    if (!attive[w.serie]) continue;
    for (const s of w.sessioni.filter(mostra)) (mappa[giorno(s.inizio)] ||= []).push({ ...s, w });
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
  for (const w of weekend) { if (!attive[w.serie]) continue; const ks = w.sessioni.filter(mostra).map((s) => giorno(s.inizio)).sort(); for (const k of ks) (tinta[k] ||= new Set()).add(w.serie); }
  let html = GIORNI.map((g) => `<div class="ag-sett">${g}</div>`).join("");
  for (let i = 0; i < offset; i++) html += `<div class="ag-giorno vuoto"></div>`;
  for (let d = 1; d <= giorni; d++) {
    const k = `${anno}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const ev = mappa[k] || [];
    // per ogni serie si mostrano tutte le sessioni del giorno, in ordine di orario
    const principali = ["f1", "moto"].map((serie) => ev.filter((e) => e.w.serie === serie).map((x) => `<span class="ag-chip ${serie}" title="${esc(x.w.nome)} · ${esc(x.nome)}">${esc(ab(x.nome))} <b>${ora(x.inizio)}</b></span>`).join("")).join("");
    const punti = ["f1", "moto"].map((s) => (ev.some((e) => e.w.serie === s) ? `<i class="ag-punto ${s}"></i>` : "")).join("");
    const tn = tinta[k] ? " wk-" + [...tinta[k]].join(" wk-") : "";
    html += `<button class="ag-giorno${ev.length ? " con-eventi" : ""}${tn}${k === oggi ? " oggi" : ""}${k === scelto ? " scelto" : ""}" data-k="${k}" aria-label="${d} ${MESI[m]}${ev.length ? ", con sessioni" : ""}">
      <span class="ag-num">${d}</span><span class="ag-chips">${principali}</span><span class="ag-punti">${punti}</span></button>`;
  }
  document.getElementById("agenda").innerHTML = `<div class="ag-griglia">${html}</div>`;
}

function icsWeekend(w, tutti = false) { return icsDi([w], tutti); }

// Calendario da scaricare con le sole sessioni scelte (gli orari sono in UTC: l'app calendario li mostra nel fuso del telefono)
function icsDi(lista, tutti = false) {
  const z = (iso) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d+/, "");
  const righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GP Oggi//Calendario//IT", "CALSCALE:GREGORIAN"];
  for (const w of lista) for (const s of tutti ? w.sessioni : w.sessioni.filter(nelCal)) {
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
    for (const s of w.sessioni.filter(mostra)) (giorni[giorno(s.inizio)] ||= []).push(s);
    return `<article class="ag-wk ${w.serie}">
      <div class="ag-wk-testa"><span class="cd-sigla ${w.serie === "moto" ? "moto" : ""}">${w.serie === "f1" ? "F1" : "MotoGP"}</span><h3>${esc(w.nome)}</h3></div>
      <p class="muted" style="margin:0 0 10px;font-size:13px">${esc(w.circuito || "")}${w.paese ? " · " + esc(w.paese) : ""}</p>
      ${Object.keys(giorni).sort().map((k) => `<div class="ag-wk-giorno${k === scelto ? " evid" : ""}"><b>${new Date(k + "T12:00:00").toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" })}</b>
        ${giorni[k].map((s) => `<div class="ag-sessione"><span>${esc(s.nome)}</span><span>${s.senzaOra ? "" : ora(s.inizio)}</span></div>`).join("")}</div>`).join("")}${finito(w) && INFO.report[w.serie + "|" + w.id] ? `<div class="ag-commento"><b>Com'è andata</b><p>${esc(INFO.report[w.serie + "|" + w.id])}</p></div>` : ""}
      <div class="ag-wk-azioni">${finito(w) ? "" : `<button class="quiz-avanti ag-scarica" data-w="${esc(w.serie + "|" + w.id)}">Aggiungi al calendario</button>`}${
        w.serie === "f1" ? `<a class="${finito(w) ? "quiz-avanti ag-risultati" : "accent"}" href="gara.html?id=${w.id}">${finito(w) ? "Vai ai risultati" : "Pagina del weekend →"}</a>`
        : `<a class="${finito(w) ? "quiz-avanti ag-risultati" : "accent"}" href="${finito(w) ? "gara-moto.html?gp=" + encodeURIComponent(w.id) : "gara-moto.html?gp=" + encodeURIComponent(w.id)}">${finito(w) ? "Vai ai risultati" : "Pagina del weekend →"}</a>`}</div>
    </article>`;
  }).join("");
}

function cambiaMese(delta) {
  const d = new Date(Date.UTC(mese[0], mese[1] + delta, 1));
  mese = [d.getUTCFullYear(), d.getUTCMonth()];
  disegnaMese();
}

// "Prossimi eventi": i prossimi weekend di F1 e MotoGP in ordine di data, con mappa e conto alla rovescia
function prossimiEventi() {
  const el = document.getElementById("prossimi-eventi");
  if (!el) return;
  const lista = weekend.filter((w) => !finito(w)).sort((a, b) => new Date(a.sessioni[0].inizio) - new Date(b.sessioni[0].inizio)).slice(0, 6);
  const giorniA = (w) => Math.max(0, Math.ceil((new Date(w.sessioni[0].inizio) - Date.now()) / 864e5));
  const periodo = (w) => { const vs = visibiliDi(w); const a = vs[0].inizio, b = vs[vs.length - 1].fine; const f = (x) => new Date(x).toLocaleDateString("it-IT", { day: "numeric", month: "short", timeZone: TZ }); return `${f(a)} – ${f(b)}`; };
  el.innerHTML = lista.map((w) => {
    const mappa = w.serie === "f1" ? (INFO.f1[w.id] || {}).mappa : INFO.mappe[w.circuito];
    const gara = w.sessioni[w.sessioni.length - 1];
    return `<article class="pe-card ${w.serie}">
      <div class="pe-testa"><span class="cd-sigla ${w.serie === "moto" ? "moto" : ""}">${w.serie === "f1" ? "F1" : "MotoGP"}</span><span class="pe-giorni">${giorniA(w) === 0 ? "Questo weekend" : "tra " + giorniA(w) + (giorniA(w) === 1 ? " giorno" : " giorni")}</span></div>
      <h3>${esc(w.nome)}</h3>
      <p class="muted">${esc(w.circuito || "")}${w.paese ? " · " + esc(w.paese) : ""}</p>
      ${mappa ? `<div class="pe-mappa">${img(mappa, "Tracciato di " + w.circuito)}</div>` : ""}
      <p class="pe-data"><b>${periodo(w)}</b><br><span class="muted">Gara: ${new Date(gara.inizio).toLocaleString("it-IT", { weekday: "long", hour: "2-digit", minute: "2-digit", timeZone: TZ })}</span></p>
      <a class="quiz-avanti" href="${w.serie === "f1" ? "gara.html?id=" + w.id : "gara-moto.html?gp=" + encodeURIComponent(w.id)}">Programma e orari</a>
    </article>`;
  }).join("") || `<p class="muted">Nessun evento in programma.</p>`;
}

// Prima di ogni download si chiede quali sessioni mettere nel file (la scelta resta memorizzata per la volta dopo)
function chiediSessioni() {
  return new Promise((risolvi) => {
    const dlg = document.createElement("dialog");
    dlg.className = "dlg-sessioni";
    dlg.innerHTML = `<form method="dialog"><h3>Quali sessioni vuoi nel calendario?</h3>
      <p class="muted" style="margin:0 0 12px;font-size:13px">Per la maggior parte delle persone bastano gara, sprint e qualifiche.</p>
      <div class="dlg-lista">${TIPI.map(([k, nome]) => `<label class="scarica-tipo"><input type="checkbox" data-t="${k}"${nelFile[k] ? " checked" : ""}><span>${nome}</span></label>`).join("")}</div>
      <div class="dlg-azioni"><button value="annulla" class="quiz-avanti secondario" formnovalidate>Annulla</button><button value="ok" class="quiz-avanti" id="dlg-ok">Scarica</button></div></form>`;
    document.body.appendChild(dlg);
    const ok = dlg.querySelector("#dlg-ok");
    const controlla = () => { ok.disabled = !dlg.querySelector("input:checked"); };
    dlg.addEventListener("change", controlla);
    controlla();
    dlg.addEventListener("close", () => {
      const sel = dlg.returnValue === "ok" ? Object.fromEntries(TIPI.map(([k]) => [k, !!dlg.querySelector(`input[data-t="${k}"]`).checked])) : null;
      dlg.remove();
      if (sel) { nelFile = sel; memo("cal-scarica", JSON.stringify(sel)); }
      risolvi(sel);
    });
    dlg.showModal();
  });
}

function conteggi() {
  const da = (serie) => weekend.filter((w) => !finito(w) && !w.passato && (!serie || w.serie === serie));
  const n = (l) => l.reduce((t, w) => t + w.sessioni.length, 0);
  document.getElementById("n-f1").textContent = `${da("f1").length} weekend, ${n(da("f1"))} sessioni.`;
  document.getElementById("n-moto").textContent = `${da("moto").length} weekend da disputare, ${n(da("moto"))} sessioni.`;
  document.getElementById("n-tutto").textContent = `${n(da())} sessioni in un solo calendario.`;
}

function controlli() {
  document.getElementById("fuso").innerHTML = FUSI.map(([z, nome]) => `<option value="${z}"${z === TZ ? " selected" : ""}>${nome}${z === "Europe/Rome" ? " (predefinito)" : ""}</option>`).join("");
}
function ridisegna() { disegnaMese(); dettaglio(); prossimiEventi(); conteggi(); }

try {
  const [eventi, moto, gareMoto, repF1, repMoto, mappeMoto] = await Promise.all([fetchJSON("data/events.json"), fetchJSON("data/motogp.json"), fetchJSON("data/motogp-gare.json").catch(() => ({})),
    fetchJSON("data/report.json").catch(() => []), fetchJSON("data/motogp-report.json").catch(() => []), mappeMotoMap()]);
  for (const r of repF1) INFO.report["f1|" + r.id] = r.paragrafi[0];
  for (const r of repMoto) INFO.report["moto|" + r.gp] = r.paragrafi[0];
  INFO.mappe = mappeMoto; INFO.f1 = Object.fromEntries(eventi.map((g) => [g.id, g]));
  weekend = costruisci(eventi, moto, gareMoto);
  prossimiEventi();
  controlli(); conteggi();
  document.getElementById("fuso").addEventListener("change", (e) => { TZ = e.target.value; memo("cal-fuso", TZ); ridisegna(); });
  document.getElementById("scarica").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-ics]"); if (!b) return;
    if (!(await chiediSessioni())) return;
    const serie = b.dataset.ics;
    const lista = weekend.filter((w) => !finito(w) && !w.passato && (serie === "tutto" || w.serie === serie));
    const url = URL.createObjectURL(new Blob([icsDi(lista)], { type: "text/calendar" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `gp-oggi-${serie}.ics` });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
  // mese iniziale: quello della prossima sessione (o di oggi)
  const prossima = weekend.flatMap((w) => w.sessioni).filter((s) => new Date(s.fine) > new Date()).sort((a, b) => new Date(a.inizio) - new Date(b.inizio))[0];
  const base = prossima ? giorno(prossima.inizio) : giorno(new Date().toISOString());
  mese = [Number(base.slice(0, 4)), Number(base.slice(5, 7)) - 1];
  scelto = null; // nessun giorno aperto di default: il programma si apre solo toccando un giorno
  disegnaMese(); dettaglio();
  document.getElementById("vai-scarica").addEventListener("click", () => document.getElementById("scarica").scrollIntoView({ behavior: "smooth", block: "start" }));
  document.getElementById("mese-prec").addEventListener("click", () => cambiaMese(-1));
  document.getElementById("mese-succ").addEventListener("click", () => cambiaMese(1));
  document.getElementById("mese-oggi").addEventListener("click", () => { const o = giorno(new Date().toISOString()); mese = [Number(o.slice(0, 4)), Number(o.slice(5, 7)) - 1]; scelto = o; disegnaMese(); dettaglio(); });
  document.getElementById("agenda").addEventListener("click", (e) => { const b = e.target.closest(".ag-giorno[data-k]"); if (!b) return; scelto = scelto === b.dataset.k ? null : b.dataset.k; disegnaMese(); dettaglio(); if (scelto && matchMedia("(max-width: 900px)").matches) document.getElementById("dettaglio").scrollIntoView({ behavior: "smooth", block: "nearest" }); });
  document.getElementById("filtri").addEventListener("click", (e) => { const b = e.target.closest(".chip-serie"); if (!b) return; attive[b.dataset.s] = !attive[b.dataset.s]; b.classList.toggle("attivo", attive[b.dataset.s]); b.setAttribute("aria-pressed", attive[b.dataset.s]); disegnaMese(); dettaglio(); });
  document.getElementById("dettaglio").addEventListener("click", async (e) => {
    const b = e.target.closest(".ag-scarica"); if (!b) return;
    if (!(await chiediSessioni())) return;
    const [serie, id] = b.dataset.w.split("|");
    const w = weekend.find((x) => x.serie === serie && String(x.id) === id);
    const url = URL.createObjectURL(new Blob([icsWeekend(w)], { type: "text/calendar" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `${serie}-${w.nome.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.ics` });
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
} catch (e) {
  document.getElementById("agenda").innerHTML = `<p class="muted center">Calendario non disponibile al momento.</p>`;
}
