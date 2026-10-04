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
  header.insertAdjacentHTML("beforebegin", `<div class="cd-barra" id="cd-barra"><div class="container cd-griglia">
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

export function renderHeader(paginaAttuale) {
  const voci = [
    ["home", "index.html", "Home"],
    ["piloti", "piloti.html", "Piloti"],
    ["classifiche", "classifiche.html", "Classifiche"],
    ["gare", "gare.html", "Gare"],
    ["notizie", "notizie.html", "Notizie"],
    ["giochi", "giochi.html", "Giochi"],
  ];
  document.getElementById("site-header").innerHTML = `
    <nav class="nav container">
      <a href="index.html" class="brand" aria-label="GP Oggi, home"><img src="img/logo-wide.png" alt="" class="brand-logo chiaro" width="98" height="54"><img src="img/logo-wide-scuro.png" alt="" class="brand-logo scuro" width="98" height="54"><span>GP<span class="dot">•</span>Oggi</span></a>
      <div class="nav-destra">
        <div class="nav-links">
          ${voci.map(([id, href, label]) => `<a href="${href}" class="${id === paginaAttuale ? "active" : ""}">${label}</a>`).join("")}
        </div>
        <button type="button" class="tema-btn" id="tema-btn" aria-label="Cambia tema chiaro o scuro">${ICONA_LUNA}${ICONA_SOLE}</button>
      </div>
    </nav>`;
  renderCountdown();
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
          <li><a href="gare.html">Calendario</a></li>
          <li><a href="calendario.html">Aggiungi al calendario</a></li>
          <li><a href="notizie.html">Notizie</a></li>
          <li><a href="confronto.html">Confronto piloti</a></li>
          <li><a href="giochi.html">Giochi</a></li>
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
        <h3>Legale</h3>
        <ul>
          <li><a href="chi-siamo.html">Chi siamo</a></li>
          <li><a href="privacy.html">Privacy</a></li>
          <li><a href="crediti.html">Crediti foto</a></li>
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
