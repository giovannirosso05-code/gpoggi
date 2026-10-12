import { renderHeader, renderFooter, fetchJSON, esc, stemma, stemmaMoto, erroreCaricamento } from "./common.js";

renderHeader("statistiche");
renderFooter();

const box = document.getElementById("stat-box");
const n1 = (v) => String(Math.round(v * 10) / 10).replace(".", ",");
const segno = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v);

function carta(titolo, righe, fmt, nota) {
  if (!righe.length) return "";
  return `<div class="st-carta"><h4>${titolo}</h4><ol>${righe.map((p) => `<li><span>${esc(p.nome)}${nota ? `<small>${esc(nota(p))}</small>` : ""}</span><b>${fmt(p)}</b></li>`).join("")}</ol></div>`;
}
const top = (lista, f, n = 3) => lista.slice().sort((a, b) => f(b) - f(a) || a.nome.localeCompare(b.nome)).slice(0, n);

function carte(S, moto) {
  const P = S.piloti, minimo = Math.max(5, Math.round(S.gare / 2));   // per le percentuali servono abbastanza gare
  const regolari = P.filter((p) => p.gare >= minimo);
  const conGriglia = P.filter((p) => p.gare_griglia >= minimo);
  const rimonte = P.filter((p) => p.rimonta).map((p) => ({ nome: p.nome, v: p.rimonta.posizioni, d: p.rimonta }));
  const crolli = P.filter((p) => p.crollo).map((p) => ({ nome: p.nome, v: p.crollo.posizioni, d: p.crollo }));
  return `<div class="st-carte">
    ${carta("Più ritiri", top(P, (p) => p.ritiri), (p) => p.ritiri, (p) => `su ${p.gare} gare`)}
    ${carta("Meno ritiri", regolari.slice().sort((a, b) => a.ritiri / a.gare - b.ritiri / b.gare || b.gare - a.gare).slice(0, 3), (p) => p.ritiri, (p) => `su ${p.gare} gare`)}
    ${carta("Più giri percorsi", top(P, (p) => p.giri), (p) => p.giri, (p) => `in ${p.gare} gare`)}
    ${carta("Re delle rimonte", top(conGriglia, (p) => p.guadagno), (p) => segno(p.guadagno), (p) => `posizioni guadagnate in ${p.gare_griglia} gare`)}
    ${carta("Più in calo", conGriglia.slice().sort((a, b) => a.guadagno - b.guadagno).slice(0, 3), (p) => segno(p.guadagno), (p) => `posizioni perse in ${p.gare_griglia} gare`)}
    ${carta("Miglior rimonta singola", top(rimonte, (r) => r.v).map((r) => ({ nome: r.nome, v: r.v, d: r.d })), (r) => "+" + r.v, (r) => `${r.d.gara}: dal ${r.d.da}° al ${r.d.a}°`)}
    ${carta("Peggior crollo singolo", crolli.slice().sort((a, b) => a.v - b.v).slice(0, 3), (r) => segno(r.v), (r) => `${r.d.gara}: dal ${r.d.da}° al ${r.d.a}°`)}
    ${carta("Più spesso a punti", regolari.slice().sort((a, b) => b.a_punti / b.gare - a.a_punti / a.gare || b.gare - a.gare).slice(0, 3), (p) => Math.round((100 * p.a_punti) / p.gare) + "%", (p) => `${p.a_punti} gare su ${p.gare}`)}
  </div>`;
}

const COLONNE = [["nome", "Pilota"], ["gare", "Gare"], ["vittorie", "Vitt."], ["podi", "Podi"], ["pole", "Pole"], ["giri_veloci", "Giri veloci"], ["ritiri", "Ritiri"], ["giri", "Giri"], ["a_punti", "A punti"], ["media", "Pos. media"], ["guadagno", "Posiz. +/−"]];
function tabella(S, moto, chiave, dir) {
  const cols = COLONNE.filter(([k]) => k !== "giri_veloci" || S.piloti.some((p) => p.giri_veloci != null));
  const val = (p, k) => (k === "media" ? (p.classificati ? p.somma_pos / p.classificati : 99) : k === "nome" ? p.nome : p[k] ?? 0);
  const righe = S.piloti.slice().sort((a, b) => {
    const x = val(a, chiave), y = val(b, chiave);
    return (typeof x === "string" ? x.localeCompare(y) : x - y) * dir;
  });
  return `<div class="table-wrap"><table class="results st-tab"><thead><tr>${cols.map(([k, t]) => `<th class="${k === "nome" ? "" : "n"} ${k === chiave ? "ord" : ""}" data-k="${k}">${t}</th>`).join("")}</tr></thead><tbody>${righe.map((p) => `<tr>
    <td><span class="cella-team">${moto ? stemmaMoto(p.moto) : stemma(p.team, p.colore)}<strong>${esc(p.nome)}</strong></span></td>
    ${cols.slice(1).map(([k]) => `<td class="n">${k === "media" ? (p.classificati ? n1(p.somma_pos / p.classificati) : "–") : k === "guadagno" ? (p.gare_griglia ? segno(p.guadagno) : "–") : p[k]}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function compagni(S) {
  const H = S.compagni.filter((h) => h.q_a + h.q_b + h.g_a + h.g_b > 0).sort((a, b) => a.team.localeCompare(b.team));
  const cella = (x, y) => `<span class="${x > y ? "st-vinc" : ""}">${x}</span> – <span class="${y > x ? "st-vinc" : ""}">${y}</span>`;
  return `<div class="table-wrap"><table class="results st-h2h"><thead><tr><th>Squadra</th><th>Compagni</th><th class="n">Qualifica</th><th class="n">Gara</th></tr></thead><tbody>${H.map((h) => `<tr><td>${esc(h.team)}</td><td><strong>${esc(h.a)}</strong> – <strong>${esc(h.b)}</strong></td><td class="n">${cella(h.q_a, h.q_b)}</td><td class="n">${cella(h.g_a, h.g_b)}</td></tr>`).join("")}</tbody></table></div>`;
}

try {
  const d = await fetchJSON("data/statistiche.json");
  box.innerHTML = `
    <span class="kicker">Numeri da esperti</span>
    <h1>Statistiche di stagione</h1>
    <p class="muted">Calcolate da noi sui risultati ufficiali di ogni gara. Tocca l'intestazione di una colonna per ordinare la tabella.</p>
    <div class="category-pills" id="st-serie" style="margin-bottom:8px"><button class="pill active" data-k="f1">Formula 1</button><button class="pill" data-k="motogp">MotoGP</button></div>
    <div id="st-corpo"></div>
    <div class="st-nota muted"><h3 class="section-title" style="margin-top:24px">Come leggere i numeri</h3>
      <ul><li><b>Ritiri:</b> gare in cui il pilota si è fermato prima della fine (anche se è stato classificato) o non ha completato il primo giro. I non partiti non contano come gara.</li>
      <li><b>Posizioni guadagnate:</b> somma di (posizione in griglia − posizione all'arrivo) nelle gare con la griglia ufficiale in cui il pilota ha tagliato il traguardo. Una penalità in griglia fa salire il numero.</li>
      <li><b>A punti:</b> arrivo nei primi 10 in F1 e nei primi 15 in MotoGP.</li>
      <li><b>Testa a testa:</b> quante volte un compagno ha chiuso davanti all'altro in qualifica e in gara; chi si ritira perde contro chi arriva.</li>
      <li>Non ci sono ancora sorpassi, giri in testa e cadute: i dati ufficiali non li dicono in modo completo e non vogliamo mostrare numeri sbagliati.</li>
      <li>Il giro veloce di ogni gara per ora è disponibile solo per la MotoGP.</li></ul></div>`;
  let serie = "f1", chiave = "vittorie", dir = -1;
  const mostra = () => {
    const S = d[serie], moto = serie === "motogp";
    document.getElementById("st-corpo").innerHTML = `<div class="${moto ? "serie-moto" : ""}">
      <h3 class="section-title">${moto ? "MotoGP" : "Formula 1"} <span class="count">· ${S.gare} gare</span></h3>
      ${carte(S, moto)}
      <h3 class="section-title">Tutti i piloti</h3><div id="st-tab">${tabella(S, moto, chiave, dir)}</div>
      <h3 class="section-title" style="margin-top:26px">Testa a testa tra compagni</h3>${compagni(S)}</div>`;
    document.querySelector("#st-tab").addEventListener("click", (e) => {
      const th = e.target.closest("th[data-k]"); if (!th) return;
      const k = th.dataset.k; dir = k === chiave ? -dir : (k === "nome" || k === "ritiri" && false ? 1 : -1); if (k === "media") dir = 1; chiave = k;
      document.getElementById("st-tab").innerHTML = tabella(S, moto, chiave, dir);
    });
  };
  document.getElementById("st-serie").addEventListener("click", (e) => {
    const b = e.target.closest(".pill"); if (!b) return;
    document.querySelectorAll("#st-serie .pill").forEach((p) => p.classList.toggle("active", p === b));
    serie = b.dataset.k; chiave = "vittorie"; dir = -1; mostra();
  });
  mostra();
} catch (e) {
  erroreCaricamento(box);
}
