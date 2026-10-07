// Utility condivise tra le pagine del sito.

export async function fetchJSON(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`Errore caricando ${path}: ${res.status}`);
  return res.json();
}

const ENT = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ENT[c]);
}

export const ND = '<span class="muted">n.d.</span>';

export const ICON_SEARCH = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;

const CODICI_TEAM = { "Red Bull Racing": "RBR", "Racing Bulls": "RB", "Haas F1 Team": "HAA", "Aston Martin": "AMR", McLaren: "MCL", Mercedes: "MER", Ferrari: "FER", Alpine: "ALP", Williams: "WIL", Audi: "AUD", Cadillac: "CAD" };

// Monogramma nel colore del team: non è il logo ufficiale della scuderia.
export function stemma(team, colore) {
  if (!team) return "";
  const parole = team.split(/\s+/).filter((w) => !/^(f1|team|racing)$/i.test(w));
  const codice = CODICI_TEAM[team] || (parole.length > 1 ? parole.map((w) => w[0]).join("").slice(0, 3) : (parole[0] || team).slice(0, 3)).toUpperCase();
  const hex = /^[0-9a-f]{6}$/i.test(colore || "") ? colore : "8b8a92";
  const lum = (parseInt(hex.slice(0, 2), 16) * 299 + parseInt(hex.slice(2, 4), 16) * 587 + parseInt(hex.slice(4, 6), 16) * 114) / 1000;
  return `<span class="stemma" style="--team:#${hex};--stemma-testo:${lum > 150 ? "#16161b" : "#fff"}" title="${esc(team)}">${esc(codice)}</span>`;
}

// Colori delle case motociclistiche (solo il colore, non i marchi) per le classifiche della MotoGP.
const MOTO_COLORI = { Ducati: "e1251b", Aprilia: "7b2c8f", KTM: "f26a1b", Yamaha: "1d4fa3", Honda: "dcdce2", Kalex: "0f9d8f", Boscoscuro: "c9a227", Forward: "6b7280", Suter: "8a5a2b", Husqvarna: "1e3a8a", Gas: "d6336c", CFMoto: "2aa84a" };
export const coloreMoto = (marca) => MOTO_COLORI[marca];
export const stemmaMoto = (marca) => stemma(marca, MOTO_COLORI[marca]);

const ICONA_LUNA = `<svg class="luna" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>`;
const ICONA_SOLE = `<svg class="sole" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`;

function temaCorrente() {
  const t = document.documentElement.dataset.theme;
  return t || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

// Il tema scelto viaggia anche nell'indirizzo (?tema=dark) quando si cambia pagina: funziona pure dove
// il browser blocca la memoria del sito (anteprime, finestre incorporate) e vale anche per una nuova scheda.
document.addEventListener("click", (e) => {
  const tema = document.documentElement.dataset.theme;
  const a = e.target.closest && e.target.closest("a[href]");
  if (!tema || !a || a.target === "_blank") return;
  try {
    const u = new URL(a.href, location.href);
    if (u.origin !== location.origin || !/\.html$|\/$/.test(u.pathname)) return;
    u.searchParams.set("tema", tema);
    a.href = u.href;
  } catch (err) {}
}, true);

// Barra in cima con il conto alla rovescia della prossima sessione di F1 e di MotoGP (orari in ora italiana).
function prossimaSessione(weekend) {
  const ora = Date.now();
  const tutte = weekend.flatMap((g) => g.sessioni.map((x) => ({ ...x, gp: g.nome }))).filter((x) => new Date(x.fine).getTime() > ora)
    .sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  return tutte[0] || null;
}

function testoConto(diff) {
  const g = Math.floor(diff / 864e5), h = Math.floor(diff / 36e5) % 24, m = Math.floor(diff / 6e4) % 60, sec = Math.floor(diff / 1e3) % 60;
  return g > 0 ? `${g}g ${String(h).padStart(2, "0")}h ${String(m).padStart(2, "0")}m ${String(sec).padStart(2, "0")}s` : `${String(h).padStart(2, "0")}h ${String(m).padStart(2, "0")}m ${String(sec).padStart(2, "0")}s`;
}

async function renderCountdown() {
  const header = document.getElementById("site-header");
  if (!header || document.getElementById("cd-barra")) return;
  header.insertAdjacentHTML(matchMedia("(max-width: 600px)").matches ? "afterend" : "beforebegin", `<div class="cd-barra" id="cd-barra"><div class="container cd-griglia">
    <div class="cd-voce" id="cd-f1"><span class="cd-sigla">F1</span><span class="cd-testo muted">Caricamento…</span></div>
    <div class="cd-voce" id="cd-moto"><span class="cd-sigla moto">MotoGP</span><span class="cd-testo muted">Caricamento…</span></div></div></div>`);
  const fonti = [["cd-f1", "data/events.json", (d) => d], ["cd-moto", "data/motogp.json", (d) => d.weekend]];
  const stati = await Promise.all(fonti.map(async ([id, url, estrai]) => {
    try { return { id, sess: prossimaSessione(estrai(await fetchJSON(url))) }; } catch (e) { return { id, sess: null }; }
  }));
  const tick = () => {
    for (const { id, sess } of stati) {
      const el = document.querySelector(`#${id} .cd-testo`);
      if (!el) continue;
      if (!sess) { el.textContent = "Nessuna sessione in programma"; continue; }
      const diff = new Date(sess.inizio).getTime() - Date.now();
      el.classList.remove("muted");
      el.innerHTML = `<b>${esc(sess.nome)}</b> · ${esc(sess.gp)} · ${formattaDataOra(sess.inizio)} · ` +
        (diff > 0 ? `<span class="cd-tempo">${testoConto(diff)}</span>` : `<span class="cd-tempo live">In corso</span>`);
    }
  };
  tick();
  setInterval(tick, 1000);
}

// Sbarretta sotto le schede del menu (solo telefono): la parte colorata mostra quanto si vede e dove ci si trova
function sbarrettaSchede() {
  const lista = document.querySelector("#site-header .nav-links"), barra = document.getElementById("nav-scrollbar");
  if (!lista || !barra) return;
  const thumb = barra.querySelector("i");
  const aggiorna = () => {
    const tot = lista.scrollWidth, vis = lista.clientWidth;
    barra.classList.toggle("tutto", tot <= vis + 2);
    thumb.style.width = Math.max(12, (vis / tot) * 100) + "%";
    thumb.style.left = (lista.scrollLeft / tot) * 100 + "%";
  };
  lista.addEventListener("scroll", aggiorna, { passive: true });
  addEventListener("resize", aggiorna);
  aggiorna();
  setTimeout(aggiorna, 400);
}

// Telefono: la testata (Home, Formula 1, Calendario, Giochi…) e' sempre fissa in alto. Si usa position: fixed, che funziona
// ovunque (sticky su alcuni iPhone non regge), e il corpo della pagina viene spostato giu' di quanto e' alta.
function fissaTestata() {
  const h = document.getElementById("site-header");
  if (!h) return;
  const misura = () => document.documentElement.style.setProperty("--hh", h.offsetHeight + "px");
  misura();
  addEventListener("resize", misura);
  addEventListener("load", misura);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(misura);
  setTimeout(misura, 500);
}

export function renderHeader(paginaAttuale) {
  const voci = [
    ["home", "index.html", "Home"],
    ["f1", "f1.html", "Formula 1"],
    ["motogp", "motogp.html", "MotoGP"],
    ["piloti", "piloti.html", "Piloti"],
    ["classifiche", "classifiche.html", "Classifiche"],
    ["gare", "calendario.html", "Calendario"],
    ["notizie", "notizie.html", "Notizie"],
    ["giochi", "giochi.html", "Giochi"],
    ["consigli", "consigli.html", "Consigli"],
    ["social", "social.html", "Social"],
  ];
  document.getElementById("site-header").innerHTML = `
    <nav class="nav container">
      <a href="index.html" class="brand" aria-label="GP Oggi, home"><img src="img/logo-wide.png" alt="" class="brand-logo chiaro" width="98" height="54"><img src="img/logo-wide-scuro.png" alt="" class="brand-logo scuro" width="98" height="54"><span class="brand-nome">GP <span class="brand-oggi">Oggi</span></span></a>
      <div class="nav-destra">
        <div class="nav-links">
          ${voci.map(([id, href, label]) => `<a href="${href}" class="${id === "giochi" ? "nav-giochi " : ""}${id === paginaAttuale ? "active" : ""}">${label}</a>`).join("")}
        </div>
        ${selettoreLingua()}
        <button type="button" class="tema-btn" id="tema-btn" aria-label="Cambia tema chiaro o scuro">${ICONA_LUNA}${ICONA_SOLE}</button>
      </div>
    </nav>`;
  fissaTestata();
  barraIndietro();
  const selLingua = document.getElementById("lingua");
  if (selLingua) selLingua.addEventListener("change", () => cambiaLingua(selLingua.value));
  if (!window.__traduzioneAvviata) { window.__traduzioneAvviata = true; avviaTraduzione(); }
  document.getElementById("tema-btn").addEventListener("click", () => {
    const nuovo = temaCorrente() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nuovo;
    try { localStorage.setItem("tema", nuovo); } catch (e) {}
    // riserva se il browser blocca localStorage (anteprime, finestre incorporate): window.name resta tra una pagina e l'altra
    window.name = window.name.replace(/(^|;)gpoggi-tema=[a-z]+/, "") + ";gpoggi-tema=" + nuovo;
  });
}

export function renderFooter() {
  document.getElementById("site-footer").innerHTML = `
    <div class="footer-grid">
      <div class="footer-col">
        <h3>Sezioni</h3>
        <ul>
          <li><a href="index.html">Home</a></li>
          <li><a href="piloti.html">Piloti</a></li>
          <li><a href="classifiche.html">Classifiche</a></li>
          <li><a href="archivio.html">Archivio storico</a></li>
          <li><a href="f1.html">Formula 1</a></li>
          <li><a href="motogp.html">MotoGP</a></li>
          <li><a href="motogp-archivio.html">Archivio MotoGP</a></li>
          <li><a href="calendario.html">Aggiungi al calendario</a></li>
          <li><a href="notizie.html">Notizie</a></li>
          <li><a href="confronto.html">Confronto piloti</a></li>
          <li><a href="giochi.html">Giochi</a></li>
          <li><a href="consigli.html">Consigli</a></li>
          <li><a href="social.html">Social</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Fonte dati</h3>
        <ul>
          <li><a href="https://openf1.org/" target="_blank" rel="noopener">OpenF1</a></li>
          <li class="muted">Progetto senza scopo di lucro</li>
          <li id="footer-aggiornato"></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Seguici</h3>
        <ul>
          <li><a href="https://www.instagram.com/gp.oggi/" target="_blank" rel="noopener">Instagram @gp.oggi</a></li>
          <li><a href="https://www.tiktok.com/@gp.oggi" target="_blank" rel="noopener">TikTok @gp.oggi</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Legale</h3>
        <ul>
          <li><a href="chi-siamo.html">Chi siamo</a></li>
          <li><a href="privacy.html">Privacy</a></li>
          <li><a href="crediti.html">Crediti foto</a></li>
          <li>Segnalazioni: <a href="mailto:info@gpoggi.it">info@gpoggi.it</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team. Foto e mappe da Wikimedia Commons con licenze libere.<br>
      <small>Formula 1 è un marchio di Formula One Licensing B.V.; MotoGP è un marchio di Dorna Sports. Nomi usati solo per descrivere i contenuti.</small></p>
    </div>`;
  fetchJSON("data/meta.json").then((m) => {
    const el = document.getElementById("footer-aggiornato");
    if (el) el.textContent = "Dati aggiornati al " + new Date(m.aggiornato).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" });
  }).catch(() => {});
}

export function formattaData(iso) {
  return new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short", year: "numeric", timeZone: "Europe/Rome" });
}

export function formattaDataOra(iso) {
  return new Date(iso).toLocaleString("it-IT", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Rome" });
}

export function intervalloWeekend(g) {
  const a = new Date(g.inizio), b = new Date(g.fine);
  const f = (d, o) => d.toLocaleDateString("it-IT", { ...o, timeZone: "Europe/Rome" });
  const mese = (d) => f(d, { month: "short" });
  return f(a, { month: "numeric" }) === f(b, { month: "numeric" })
    ? `${f(a, { day: "numeric" })}–${f(b, { day: "numeric" })} ${mese(b)} ${f(b, { year: "numeric" })}`
    : `${f(a, { day: "numeric" })} ${mese(a)} – ${f(b, { day: "numeric" })} ${mese(b)} ${f(b, { year: "numeric" })}`;
}

export function punti(v) {
  return v == null ? ND : String(v % 1 === 0 ? v : v.toFixed(1));
}

export function erroreCaricamento(el) {
  el.innerHTML = `<p class="muted center">Dati non disponibili al momento. Riprova più tardi.</p>`;
}

export function img(foto, alt, cls = "") {
  if (!foto) return "";
  return `<img src="${esc(foto.file || foto.url)}" alt="${esc(alt)}" class="${cls}" loading="lazy" title="${esc(foto.autore)} · ${esc(foto.licenza)}">`;
}

export function credito(foto, cosa = "Foto") {
  if (!foto) return "";
  return `${cosa}: ${esc(foto.autore)} · <a href="${esc(foto.pagina)}" target="_blank" rel="noopener">${esc(foto.licenza)}</a>, via Wikimedia Commons`;
}

// Mescola due serie in ordine di data, alternando quando possibile: nessuna delle due sommerge l'altra.
export function mischia(articoli, n) {
  const per = (s) => articoli.filter((a) => a.serie === s).sort((a, b) => new Date(b.pubblicato || 0) - new Date(a.pubblicato || 0));
  const f1 = per("F1"), moto = per("MotoGP"), altri = articoli.filter((a) => a.serie !== "F1" && a.serie !== "MotoGP");
  const out = [];
  while ((f1.length || moto.length) && out.length < n) {
    const prima = (new Date(f1[0]?.pubblicato || 0) >= new Date(moto[0]?.pubblicato || 0)) ? [f1, moto] : [moto, f1];
    for (const l of prima) if (l.length && out.length < n) out.push(l.shift());
  }
  return [...out, ...altri].slice(0, n);
}

// Foto dei piloti del motomondiale (id e nome -> foto con autore e licenza); vuota finché non sono state cercate.
let _fotoMoto;
export function fotoMotoMap() {
  return (_fotoMoto ||= fetchJSON("data/foto-motogp.json").catch(() => ({})));
}

// ---------- Lingue ----------
// Il sito resta in italiano. Le altre lingue usano il traduttore di Google DENTRO la pagina (stessa soluzione di MMA Oggi):
// la scelta vive nel cookie googtrans (/it/<lingua>) che il traduttore legge da solo. Nomi di piloti e del sito non si traducono.
const LINGUE = [
  ["it", "Italiano"], ["en", "English"], ["es", "Español"], ["fr", "Français"], ["de", "Deutsch"], ["pt", "Português"],
  ["pl", "Polski"], ["ro", "Română"], ["sq", "Shqip"], ["ar", "العربية"], ["ru", "Русский"], ["uk", "Українська"],
  ["tr", "Türkçe"], ["zh-CN", "中文"], ["ja", "日本語"],
];
function linguaAttuale() {
  const m = document.cookie.match(/(?:^|;\s*)googtrans=\/it\/([^;]+)/);
  return m && LINGUE.some(([c]) => c === m[1]) ? m[1] : "it";
}
function cambiaLingua(lingua) {
  const scadenza = lingua === "it" ? "; expires=Thu, 01 Jan 1970 00:00:00 GMT" : "; max-age=31536000";
  const valore = lingua === "it" ? "" : `/it/${lingua}`;
  for (const dominio of ["", `; domain=${location.hostname}`, `; domain=.${location.hostname}`]) {
    document.cookie = `googtrans=${valore}; path=/${dominio}${scadenza}`;
  }
  location.reload();
}
const SELETTORE_NOMI = ".brand, .name, .nome, .nome2, .cella-pilota strong, .link-nome, .pm-testa h1, .campione h1, .stemma, .cd-sigla, .pross-gp, .podio-home strong";
function proteggiNomi(radice) {
  const el = radice.matches && radice.matches(SELETTORE_NOMI) ? [radice] : [];
  for (const e of [...el, ...radice.querySelectorAll(SELETTORE_NOMI)]) { e.classList.add("notranslate"); e.setAttribute("translate", "no"); }
}
function avviaTraduzione() {
  const lingua = linguaAttuale();
  if (lingua === "it") return;
  document.documentElement.classList.add("tradotto");
  proteggiNomi(document.body);
  new MutationObserver((cambi) => {
    for (const c of cambi) for (const n of c.addedNodes) if (n.nodeType === 1 && !n.closest(".skiptranslate")) proteggiNomi(n);
  }).observe(document.body, { childList: true, subtree: true });
  const box = document.createElement("div");
  box.id = "google_translate_element";
  box.hidden = true;
  document.body.appendChild(box);
  window.googleTranslateElementInit = () => {
    new window.google.translate.TranslateElement({ pageLanguage: "it", autoDisplay: false }, "google_translate_element");
  };
  const s = document.createElement("script");
  s.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
  document.body.appendChild(s);
}
function selettoreLingua() {
  const attuale = linguaAttuale();
  const opzioni = LINGUE.map(([codice, nome]) => `<option value="${codice}"${codice === attuale ? " selected" : ""}>${nome}</option>`).join("");
  return `<label class="lingua notranslate" translate="no" title="Lingua / Language">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>
      <select id="lingua" aria-label="Lingua / Language">${opzioni}</select></label>`;
}

// Mappe dei circuiti della MotoGP (nome del circuito -> mappa con autore e licenza).
let _mappeMoto;
export function mappeMotoMap() {
  return (_mappeMoto ||= fetchJSON("data/mappe-motogp.json").catch(() => ({})));
}

// Schede carriera (numeri di carriera e biografia breve da Wikipedia in italiano); vuote se non ancora generate.
let _schede;
export function schedeMap() {
  return (_schede ||= fetchJSON("data/schede.json").catch(() => ({})));
}
export function bioHtml(w) {
  if (!w) return "";
  return `<h3 class="section-title">Chi è</h3><div class="bio"><p>${esc(w.testo)}</p>
    <p class="credito">Fonte: <a href="${esc(w.pagina)}" target="_blank" rel="noopener">Wikipedia in italiano</a>, testo con licenza CC BY-SA 4.0.</p></div>`;
}
export function dataIt(iso) {
  return iso ? new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }) : "";
}

// Votazioni del pronostico. Con VOTI_URL vuoto il voto resta nel browser; con l'indirizzo del Worker (vedi worker/voti.js)
// i voti si sommano tra tutti i visitatori e si vedono le percentuali.
export const VOTI_URL = "https://gpoggivotti.giovannirosso05.workers.dev";
export function votoSalvato(chiave) {
  try { return localStorage.getItem("voto:" + chiave); } catch (e) { return null; }
}
export async function inviaVoto(chiave, scelta) {
  try { localStorage.setItem("voto:" + chiave, scelta); } catch (e) {}
  if (!VOTI_URL) return null;
  try {
    const r = await fetch(VOTI_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ gp: chiave, scelta }) });
    return r.ok ? (await r.json()).voti : null;
  } catch (e) { return null; }
}
export async function leggiVoti(chiave) {
  if (!VOTI_URL) return null;
  try {
    const r = await fetch(`${VOTI_URL}?gp=${encodeURIComponent(chiave)}`);
    return r.ok ? (await r.json()).voti : null;
  } catch (e) { return null; }
}

// Cronaca giro per giro: elenco con filtri (tutto, safety car, incidenti e penalità, ritiri, box).
const CRON_FILTRI = [["", "Tutto"], ["safety", "Safety car"], ["incidente,penalita", "Incidenti e penalità"], ["ritiro", "Ritiri"], ["pit", "Box"], ["comando,sorpasso", "Sorpassi e comando"]];
export function montaCronaca(el, voci, giriTot) {
  if (!voci || !voci.length) { el.innerHTML = ""; return; }
  const tipi = new Set(voci.map((v) => v.tipo));
  const filtri = CRON_FILTRI.filter(([k]) => !k || k.split(",").some((t) => tipi.has(t)));
  el.innerHTML = `<div class="category-pills cron-filtri">${filtri.map(([k, n], i) => `<button type="button" class="pill ${i === 0 ? "active" : ""}" data-k="${k}">${n}</button>`).join("")}</div>
    <ol class="cronaca" id="cron-lista"></ol>`;
  const lista = el.querySelector("#cron-lista");
  const disegna = (k) => {
    const ok = k ? k.split(",") : null;
    lista.innerHTML = voci.filter((v) => !ok || ok.includes(v.tipo)).map((v) => `<li class="cron-${v.tipo}"><span class="cron-giro">Giro ${v.giro}${giriTot ? `<small>/${giriTot}</small>` : ""}</span><span class="cron-testo">${esc(v.testo).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")}</span></li>`).join("");
  };
  el.querySelector(".cron-filtri").addEventListener("click", (e) => {
    const b = e.target.closest(".pill");
    if (!b) return;
    el.querySelectorAll(".cron-filtri .pill").forEach((x) => x.classList.toggle("active", x === b));
    disegna(b.dataset.k);
  });
  disegna("");
}

// Cerchio con le iniziali, al posto della foto quando non ce n'è una libera.
export const iniz = (nome) => `<span class="foto-mini ini" aria-hidden="true">${esc((nome || "").split(/\s+/).filter(Boolean).map((w) => w[0]).slice(0, 2).join("").toUpperCase())}</span>`;

// Freccia "Indietro" sulle pagine di dettaglio (gara, pilota, storico): torna alla pagina da cui si arriva, o all'elenco di riferimento.
const PAGINA_MADRE = {
  "gara.html": ["f1.html", "Formula 1"], "gara-moto.html": ["motogp.html", "MotoGP"], "pilota.html": ["piloti.html?serie=f1", "Piloti"],
  "pilota-moto.html": ["piloti.html?serie=motogp", "Piloti"], "storico.html": ["piloti.html?serie=f1", "Piloti"], "storico-moto.html": ["piloti.html?serie=motogp", "Piloti"],
  "confronto.html": ["piloti.html", "Piloti"],
};
function barraIndietro() {
  const pagina = location.pathname.split("/").pop();
  const madre = PAGINA_MADRE[pagina];
  const header = document.getElementById("site-header");
  if (!madre || !header || document.getElementById("indietro-barra")) return;
  const tema = document.documentElement.dataset.theme;
  const href = madre[0] + (tema ? (madre[0].includes("?") ? "&" : "?") + "tema=" + tema : "");
  header.insertAdjacentHTML("afterend", `<div class="indietro-barra" id="indietro-barra"><div class="container"><a class="indietro" href="${href}" aria-label="Torna indietro"><span aria-hidden="true">←</span> Indietro<small> · ${madre[1]}</small></a></div></div>`);
  document.querySelector("#indietro-barra a").addEventListener("click", (e) => {
    let stessoSito = false;
    try { stessoSito = document.referrer && new URL(document.referrer).origin === location.origin; } catch (err) {}
    if (stessoSito && history.length > 1) { e.preventDefault(); history.back(); }
  });
}

// Programma del weekend in forma compatta: un riga per giorno con le sessioni e l'orario italiano.
export function programmaHtml(sessioni) {
  const TZ = "Europe/Rome";
  const giorno = (iso) => new Date(iso).toLocaleDateString("sv-SE", { timeZone: TZ });
  const per = {};
  for (const s of sessioni) (per[giorno(s.inizio)] ||= []).push(s);
  const ora = Date.now();
  return `<div class="programma" aria-label="Programma del weekend, ora italiana">
    <div class="programma-testa">Programma <span>· ora italiana</span></div>
    ${Object.keys(per).sort().map((k) => `<div class="programma-giorno"><b>${new Date(k + "T12:00:00").toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" })}</b>
      <div class="programma-sessioni">${per[k].sort((a, b) => new Date(a.inizio) - new Date(b.inizio)).map((s) => `<span class="programma-sess ${/^gara$/i.test(s.nome) ? "gara" : ""} ${new Date(s.fine) < ora ? "finita" : ""}">${esc(s.nome)} <b>${new Date(s.inizio).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit", timeZone: TZ })}</b></span>`).join("")}</div></div>`).join("")}
  </div>`;
}
