// Utility condivise tra le pagine del sito F1.

export function traccia(nome, props) {
  try {
    window.plausible = window.plausible || function () { (window.plausible.q = window.plausible.q || []).push(arguments); };
    const doppie = {};
    for (const [k, v] of Object.entries(props || {})) {
      doppie[k] = v;
      doppie[k.charAt(0).toUpperCase() + k.slice(1)] = v;
    }
    window.plausible(nome, { props: doppie });
  } catch (e) { /* le statistiche non devono mai rompere la pagina */ }
}

export async function fetchJSON(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`Errore caricando ${path}: ${res.status}`);
  return res.json();
}

const ICONS = {
  search: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  flag: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 5-1 5 1 5 1v-3c0 0-1-1-5-1s-5 1-5 1"/><path d="M4 21v-7"/></svg>`,
  trophy: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-2"/><path d="M6 5h12v2a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5z"/><path d="M12 9v8"/><path d="M8 22v-4h8v4"/></svg>`,
  link: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1.5 1.5"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1.5-1.5"/></svg>`,
};

export function icon(name) {
  return ICONS[name] || "";
}

export function impostaMetaPagina({ titolo, descrizione, jsonLd, canonical }) {
  const statica = Boolean(document.body.dataset.slug);
  if (titolo && !statica) document.title = titolo;
  if (canonical) {
    const link = document.querySelector('link[rel="canonical"]');
    if (link) link.setAttribute("href", canonical);
    const og = document.querySelector('meta[property="og:url"]');
    if (og) og.setAttribute("content", canonical);
  }
  if (descrizione && !statica) {
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute("content", descrizione);
  }
  if (jsonLd) {
    let script = document.querySelector('script[type="application/ld+json"]');
    if (!script) {
      script = document.createElement("script");
      script.type = "application/ld+json";
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify(jsonLd);
  }
}

// Header e Footer condivisi
export async function renderHeader(paginaAttuale) {
  const header = document.getElementById("site-header");
  const version = new Date().toISOString().slice(0, 10).replace(/-/g, "");

  header.innerHTML = `
    <nav class="nav container">
      <div class="brand">
        <a href="index.html">🏁 F1 <span class="accent">Stats</span></a>
      </div>
      <div class="nav-links">
        <a href="index.html" class="${paginaAttuale === 'home' ? 'active' : ''}">Piloti</a>
        <a href="gare.html" class="${paginaAttuale === 'gare' ? 'active' : ''}">Gare</a>
        <a href="confronto.html" class="${paginaAttuale === 'confronto' ? 'active' : ''}">Confronto</a>
        <a href="chi-siamo.html" class="${paginaAttuale === 'chi-siamo' ? 'active' : ''}">Info</a>
      </div>
    </nav>
  `;
}

export async function renderFooter() {
  const footer = document.getElementById("site-footer");
  const anno = new Date().getFullYear();

  footer.innerHTML = `
    <div class="footer-grid">
      <div class="footer-col">
        <h3>Fonte dati</h3>
        <ul>
          <li><a href="https://openf1.org/" target="_blank">OpenF1 API</a></li>
          <li>Aggiornamenti in tempo reale</li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Link</h3>
        <ul>
          <li><a href="https://www.fia.com/" target="_blank">FIA Ufficiale</a></li>
          <li><a href="https://www.formula1.com/" target="_blank">Formula 1</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Legale</h3>
        <ul>
          <li><a href="chi-siamo.html">Chi siamo</a></li>
          <li><a href="privacy.html">Privacy</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© ${anno} F1 Stats — Non ufficiale, non affiliato a Formula 1 o FIA.<br>
      <small>Sito non ufficiale realizzato con dati pubblici OpenF1. Formula 1 è un marchio registrato di Formula 1 World Championship Limited.</small></p>
    </div>
  `;
}

export function formattaData(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString('it-IT', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formattaOra(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit'
  });
}
