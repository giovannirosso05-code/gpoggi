import { renderHeader, renderFooter, fetchJSON, traccia, formattaData } from './common.js';

let tutteGare = [];
let gareVisibili = [];

export async function inizializza() {
  await renderHeader('gare');
  await renderFooter();

  try {
    tutteGare = await fetchJSON('data/events.json');
    // Ordina per data, più prossime per prime
    tutteGare.sort((a, b) => {
      const dataA = new Date(a.data);
      const dataB = new Date(b.data);
      return dataA - dataB;
    });
    gareVisibili = [...tutteGare];
  } catch (e) {
    console.error('Errore caricando gare:', e);
    document.getElementById('gare-list').innerHTML = `
      <p style="text-align: center; color: var(--text-secondary);">
        Errore caricando le gare. Riprova più tardi.
      </p>
    `;
    return;
  }

  renderGare();
  traccia('pagina_gare', { totale: tutteGare.length });
}

function renderGare() {
  const list = document.getElementById('gare-list');

  if (gareVisibili.length === 0) {
    list.innerHTML = `<p style="text-align: center; color: var(--text-secondary);">Nessuna gara trovata.</p>`;
    return;
  }

  // Raggruppa per stato
  const oggi = new Date();
  const programmate = gareVisibili.filter(g => new Date(g.data) > oggi);
  const passate = gareVisibili.filter(g => new Date(g.data) <= oggi);

  let html = '';

  if (programmate.length > 0) {
    html += '<div class="gare-section"><h3 style="margin-bottom: 12px; color: var(--accent);">📅 Prossime</h3>';
    html += programmate.map(g => renderGaraCard(g, 'Programmato')).join('');
    html += '</div>';
  }

  if (passate.length > 0) {
    html += '<div class="gare-section"><h3 style="margin-bottom: 12px; margin-top: 28px;">✓ Passate</h3>';
    html += passate.map(g => renderGaraCard(g, 'Passato')).join('');
    html += '</div>';
  }

  list.innerHTML = html;

  document.querySelectorAll('.event-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.id;
      traccia('gara_cliccata', { gara: id });
      // TODO: apri scheda gara
    });
  });
}

function renderGaraCard(gara, stato) {
  const data = new Date(gara.data);
  const giorni = Math.ceil((data - new Date()) / (1000 * 60 * 60 * 24));
  const distanzaLabel = giorni > 0 ? `in ${giorni} giorni` : 'Completata';

  return `
    <div class="event-card" data-id="${gara.id}">
      <div class="event-date">${formattaData(gara.data)}</div>
      <div class="event-name">${gara.nome}</div>
      <div class="event-location">🏁 ${gara.circuito}, ${gara.paese}</div>
      <span class="event-status ${stato === 'Passato' ? 'passato' : ''}">${distanzaLabel}</span>
    </div>
  `;
}

document.addEventListener('DOMContentLoaded', inizializza);
