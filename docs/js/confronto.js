import { renderHeader, renderFooter, fetchJSON, traccia } from './common.js';

let tuttiPiloti = [];

export async function inizializza() {
  await renderHeader('confronto');
  await renderFooter();

  try {
    tuttiPiloti = await fetchJSON('data/roster.json');
  } catch (e) {
    console.error('Errore caricando piloti:', e);
    document.getElementById('confronto-container').innerHTML = `
      <p style="text-align: center; color: var(--text-secondary);">
        Errore caricando i dati. Riprova più tardi.
      </p>
    `;
    return;
  }

  impostaAutocomplete('pilota-1', (p) => selezionaPilota(1, p));
  impostaAutocomplete('pilota-2', (p) => selezionaPilota(2, p));
  traccia('pagina_confronto');
}

function impostaAutocomplete(inputId, onSelect) {
  const input = document.getElementById(inputId);
  const suggestionsId = inputId + '-suggestions';
  let suggestionsDiv = document.getElementById(suggestionsId);

  if (!suggestionsDiv) {
    suggestionsDiv = document.createElement('div');
    suggestionsDiv.id = suggestionsId;
    suggestionsDiv.className = 'autocomplete-suggestions';
    suggestionsDiv.style.cssText = `
      position: absolute;
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      max-height: 200px;
      overflow-y: auto;
      z-index: 100;
      width: 100%;
      display: none;
      margin-top: 4px;
    `;
    input.parentNode.style.position = 'relative';
    input.parentNode.appendChild(suggestionsDiv);
  }

  input.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();

    if (query.length < 2) {
      suggestionsDiv.style.display = 'none';
      return;
    }

    const filtered = tuttiPiloti.filter(p => p.nome.toLowerCase().includes(query)).slice(0, 8);

    if (filtered.length === 0) {
      suggestionsDiv.style.display = 'none';
      return;
    }

    suggestionsDiv.innerHTML = filtered.map(p => `
      <div class="autocomplete-item" style="
        padding: 8px 12px;
        cursor: pointer;
        border-bottom: 1px solid var(--border-soft);
      " data-id="${p.id}">
        <strong>${p.nome}</strong> <span style="color: var(--text-secondary);">#${p.numero}</span>
      </div>
    `).join('');

    suggestionsDiv.style.display = 'block';

    suggestionsDiv.querySelectorAll('.autocomplete-item').forEach(item => {
      item.addEventListener('click', () => {
        const pilotaId = item.dataset.id;
        const pilota = tuttiPiloti.find(p => p.id === pilotaId);
        if (pilota) {
          onSelect(pilota);
          input.value = pilota.nome;
          suggestionsDiv.style.display = 'none';
        }
      });
    });
  });

  document.addEventListener('click', (e) => {
    if (!input.parentNode.contains(e.target)) {
      suggestionsDiv.style.display = 'none';
    }
  });
}

function selezionaPilota(numero, pilota) {
  const container = document.getElementById(`pilota-${numero}`);

  container.innerHTML = `
    <div class="compare-col" style="grid-column: ${numero === 1 ? 1 : 2};">
      <h2>${pilota.nome}</h2>

      <div class="compare-stat">
        <div class="compare-stat-label">Team</div>
        <div></div>
        <div class="compare-stat-value">${pilota.team}</div>
      </div>

      <div class="compare-stat">
        <div class="compare-stat-label">Numero</div>
        <div></div>
        <div class="compare-stat-value">#${pilota.numero}</div>
      </div>

      <div class="compare-stat">
        <div class="compare-stat-label">Nazionalità</div>
        <div></div>
        <div class="compare-stat-value">${pilota.nazionalita || '-'}</div>
      </div>

      ${pilota.foto ? `
        <div style="margin-top: 16px;">
          <img src="${pilota.foto}" alt="${pilota.nome}" style="
            width: 100%;
            border-radius: var(--radius);
            max-height: 300px;
            object-fit: cover;
          " onerror="this.style.display='none'">
        </div>
      ` : ''}
    </div>
  `;

  traccia('pilota_confrontato', { pilota: pilota.id });
}

function pulisciCampo(inputId) {
  document.getElementById(inputId).value = '';
  document.getElementById(`pilota-${inputId.slice(-1)}`).innerHTML = '';
}

document.addEventListener('DOMContentLoaded', inizializza);
