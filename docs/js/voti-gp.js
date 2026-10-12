import { esc } from "./common.js";


// Scheda "Voti GP Oggi" di una gara: top 3 (il primo e' l'MVP), flop 3 e sorpresa, ognuno con la sua frase. I voti vengono da data/pagelle.json (stessi dei video).
export function votiGpOggi(r) {
  if (!r || !r.top || !r.top.length) return "";
  const riga = (x, chip) => `<li><b class="vg-voto">${String(x.voto).replace(".0", "").replace(".", ",")}</b><span class="vg-testo"><strong>${esc(x.nome)}</strong>${chip ? ` <em class="vg-chip">${chip}</em>` : ""}<small>${esc(x.perche)}</small></span></li>`;
  const gruppo = (titolo, lista, primoChip) => lista && lista.length ? `<div class="vg-gruppo"><h4>${titolo}</h4><ul>${lista.map((x, i) => riga(x, i === 0 ? primoChip : "")).join("")}</ul></div>` : "";
  return `<aside class="voti-gp" aria-label="Voti GP Oggi">
    <div class="voti-gp-titolo"><span>Voti GP Oggi</span><a href="pagella.html">Pagella completa →</a></div>
    ${gruppo("Top 3", r.top, "MVP")}${r.sorpresa ? gruppo("Sorpresa", [r.sorpresa], "") : ""}${gruppo("Flop 3", r.flop, "")}
    <p class="vg-nota">Voti nostri, a scopo divertente: nessuno si offenda.</p></aside>`;
}
