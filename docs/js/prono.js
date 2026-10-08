// Pronostico e votazione, usati dalla home e dalle pagine Formula 1 e MotoGP.
import { esc, img, formattaDataOra } from "./common.js";

function inviti(s, d) {
  return `<div class="vota" data-s="${s}">
    <a class="vota-apri vota-cta" href="giochi.html?gioco=pronostico&serie=${s === "motogp" ? "moto" : "f1"}">Fai il tuo pronostico · carta Amazon 50 €</a>
    <p class="muted" style="font-size:12px;margin:8px 0 0;text-align:center">Scegli il podio di ${esc(d.gp)}: gratis, il primo in classifica a fine anno vince.</p></div>`;
}

/** colonne: [{ s: "f1"|"motogp", sigla, classe, d (dati del pronostico), fotoDi(favorito), tutti: [{nome, sotto, foto}] }] */
export function montaPronostico(griglia, colonne) {
  griglia.innerHTML = colonne.filter((c) => c.d).map((c) => `<div class="prono-col" data-serie="${c.s}">
    <div class="prono-testa"><span class="cd-sigla ${c.classe}">${c.sigla}</span><b>${esc(c.d.gp)}</b><span class="muted">gara ${formattaDataOra(c.d.gara)}</span></div>
    ${c.d.favoriti.slice(0, 3).map((r, i) => `<div class="prono-riga ${i === 0 ? "primo" : ""}">
      <span class="prono-pos">${i + 1}</span>${c.fotoDi(r) ? img(c.fotoDi(r), r.nome, "foto-mini") : '<span class="foto-mini"></span>'}
      <div class="prono-info"><strong>${esc(r.nome)}</strong><span class="muted">${esc(r.motivi.join(" · "))}</span>
        <div class="prono-barra"><i style="width:${r.indice}%"></i></div></div><span class="prono-ind">${r.indice}</span></div>`).join("")}
    ${inviti(c.s, c.d)}</div>`).join("");
}

/** Dati comuni per costruire le colonne a partire dai file del sito. */
export function colonnaF1(pr, roster) {
  const fotoF1 = Object.fromEntries((roster || []).filter((p) => p.foto).map((p) => [p.numero, p.foto]));
  return { s: "f1", sigla: "F1", classe: "", d: pr && pr.f1, fotoDi: (r) => fotoF1[r.numero], tutti: (roster || []).filter((p) => p.nome).map((p) => ({ nome: p.nome, sotto: p.team, foto: p.foto })) };
}
export function colonnaMoto(pr, clMoto, FM) {
  const lista = (clMoto && (clMoto.categorie || {}).MotoGP) || [];
  return { s: "motogp", sigla: "MotoGP", classe: "moto", d: pr && pr.motogp, fotoDi: (r) => FM[r.id], tutti: lista.map((p) => ({ nome: p.nome, sotto: p.moto, foto: FM[p.id] })) };
}
