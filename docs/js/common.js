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

export function renderHeader(paginaAttuale) {
  const voci = [
    ["home", "index.html", "Piloti"],
    ["classifiche", "classifiche.html", "Classifiche"],
    ["gare", "gare.html", "Gare"],
    ["confronto", "confronto.html", "Confronto"],
    ["chi-siamo", "chi-siamo.html", "Info"],
  ];
  document.getElementById("site-header").innerHTML = `
    <nav class="nav container">
      <a href="index.html" class="brand" aria-label="F1 Oggi, home"><img src="img/logo-wide.png" alt="" class="brand-logo" width="88" height="52"><span>F1<span class="dot">•</span>Oggi</span></a>
      <div class="nav-links">
        ${voci.map(([id, href, label]) => `<a href="${href}" class="${id === paginaAttuale ? "active" : ""}">${label}</a>`).join("")}
      </div>
    </nav>`;
}

export function renderFooter() {
  document.getElementById("site-footer").innerHTML = `
    <div class="footer-grid">
      <div class="footer-col">
        <h3>Sezioni</h3>
        <ul>
          <li><a href="index.html">Piloti</a></li>
          <li><a href="classifiche.html">Classifiche</a></li>
          <li><a href="gare.html">Calendario</a></li>
          <li><a href="confronto.html">Confronto</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Fonte dati</h3>
        <ul>
          <li><a href="https://openf1.org/" target="_blank" rel="noopener">OpenF1</a></li>
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
      <p>Sito non ufficiale, non affiliato a Formula 1, FIA o ai team. Foto e mappe da Wikimedia Commons con licenze libere.<br>
      <small>Formula 1 è un marchio di Formula 1 World Championship Limited.</small></p>
    </div>`;
  fetchJSON("data/meta.json").then((m) => {
    const el = document.getElementById("footer-aggiornato");
    if (el) el.textContent = "Dati aggiornati al " + new Date(m.aggiornato).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
  }).catch(() => {});
}

export function formattaData(iso) {
  return new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short", year: "numeric" });
}

export function formattaDataOra(iso) {
  return new Date(iso).toLocaleString("it-IT", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function intervalloWeekend(g) {
  const a = new Date(g.inizio), b = new Date(g.fine);
  const mese = (d) => d.toLocaleDateString("it-IT", { month: "short" });
  return a.getMonth() === b.getMonth() ? `${a.getDate()}–${b.getDate()} ${mese(b)} ${b.getFullYear()}` : `${a.getDate()} ${mese(a)} – ${b.getDate()} ${mese(b)} ${b.getFullYear()}`;
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
