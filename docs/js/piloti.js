import { renderHeader, renderFooter, fetchJSON, traccia } from './common.js';

let tuttiPiloti = [];
let pilotiVisibili = [];

export async function inizializza() {
  await renderHeader('home');
  await renderFooter();

  try {
    tuttiPiloti = await fetchJSON('data/roster.json');
    pilotiVisibili = [...tuttiPiloti];
  } catch (e) {
    console.error('Errore caricando piloti:', e);
    document.getElementById('piloti-grid').innerHTML = `
      <p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">
        Errore caricando i piloti. Riprova più tardi.
      </p>
    `;
    return;
  }

  renderPiloti();
  impostaFiltri();
  traccia('pagina_piloti', { totale: tuttiPiloti.length });
}

function renderPiloti() {
  const grid = document.getElementById('piloti-grid');

  if (pilotiVisibili.length === 0) {
    grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">Nessun pilota trovato.</p>`;
    return;
  }

  grid.innerHTML = pilotiVisibili.map(p => `
    <div class="driver-card" data-id="${p.id}">
      <div class="driver-card-image">
        ${p.foto ? `<img src="${p.foto}" alt="${p.nome}" loading="lazy" onerror="this.style.display='none'">` : ''}
      </div>
      <div class="driver-card-info">
        <div class="name">${p.nome}</div>
        <div class="numero">#${p.numero}</div>
        <div class="team">${p.team}</div>
      </div>
    </div>
  `).join('');

  document.querySelectorAll('.driver-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.id;
      traccia('pilota_cliccato', { pilota: id });
      // TODO: apri scheda pilota
    });
  });
}

function impostaFiltri() {
  const searchInput = document.getElementById('search');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      pilotiVisibili = tuttiPiloti.filter(p =>
        p.nome.toLowerCase().includes(query) ||
        p.team.toLowerCase().includes(query) ||
        p.numero.toString().includes(query)
      );
      renderPiloti();
      document.getElementById('result-count').textContent = `(${pilotiVisibili.length})`;
    });
  }

  // Genera pills per team unici
  const teamUnici = [...new Set(tuttiPiloti.map(p => p.team).filter(Boolean))].sort();
  const categoryPills = document.getElementById('category-pills');

  if (categoryPills) {
    categoryPills.innerHTML = teamUnici.map(team => `
      <div class="pill" data-team="${team}">${team}</div>
    `).join('');

    categoryPills.querySelectorAll('.pill').forEach(pill => {
      pill.addEventListener('click', () => {
        pill.classList.toggle('active');
        filtraPiloti();
      });
    });
  }

  document.getElementById('result-count').textContent = `(${tuttiPiloti.length})`;
}

function filtraPiloti() {
  const pillActive = [...document.querySelectorAll('.pill.active')].map(p => p.dataset.team);
  const searchQuery = document.getElementById('search').value.toLowerCase();

  pilotiVisibili = tuttiPiloti.filter(p => {
    const matchSearch = p.nome.toLowerCase().includes(searchQuery) ||
                        p.team.toLowerCase().includes(searchQuery);
    const matchTeam = pillActive.length === 0 || pillActive.includes(p.team);
    return matchSearch && matchTeam;
  });

  renderPiloti();
  document.getElementById('result-count').textContent = `(${pilotiVisibili.length})`;
}

document.addEventListener('DOMContentLoaded', inizializza);
