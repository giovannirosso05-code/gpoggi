// Pronostico e votazione, usati dalla home e dalle pagine Formula 1 e MotoGP.
import { esc, img, formattaDataOra, votoSalvato, inviaVoto, leggiVoti, VOTI_URL } from "./common.js";

const chiaveVoto = (s, d) => `${s}:${d.gp}`;

function votoHtml(s, d, tutti) {
  const mio = votoSalvato(chiaveVoto(s, d));
  return `<div class="vota" data-s="${s}">
    <button type="button" class="vota-apri">${mio ? `Il tuo voto: ${esc(mio)} · cambia` : "Vota il tuo vincitore"}</button>
    <div class="vota-box" hidden>
      <p class="muted" style="margin:6px 0 10px;font-size:12px">Scegli chi vince ${esc(d.gp)}. Puoi cambiare idea fino alla gara.</p>
      <div class="vota-griglia">${tutti.map((p) => `<button type="button" class="vota-pilota ${mio === p.nome ? "scelto" : ""}" data-n="${esc(p.nome)}">
        ${p.foto ? img(p.foto, p.nome, "foto-mini") : '<span class="foto-mini"></span>'}<span><b>${esc(p.nome)}</b><small>${esc(p.sotto || "")}</small></span></button>`).join("")}</div>
    </div>
    <div class="vota-esito"></div></div>`;
}

function mostraEsito(box, voti, mio) {
  const el = box.querySelector(".vota-esito");
  if (!voti) { el.innerHTML = mio ? `<p class="muted" style="font-size:12px">Voto salvato su questo dispositivo.${VOTI_URL ? "" : " Le percentuali di tutti i visitatori compariranno quando le votazioni saranno attive."}</p>` : ""; return; }
  const tot = Object.values(voti).reduce((a, b) => a + b, 0) || 1;
  el.innerHTML = Object.entries(voti).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([n, v]) => `<div class="vota-riga"><span>${esc(n)}</span><div class="prono-barra"><i style="width:${Math.round(100 * v / tot)}%"></i></div><b>${Math.round(100 * v / tot)}%</b></div>`).join("")
    + `<p class="muted" style="font-size:11px;margin:4px 0 0">${tot} ${tot === 1 ? "voto" : "voti"}</p>`;
}

/** colonne: [{ s: "f1"|"motogp", sigla, classe, d (dati del pronostico), fotoDi(favorito), tutti: [{nome, sotto, foto}] }] */
export function montaPronostico(griglia, colonne) {
  griglia.innerHTML = colonne.filter((c) => c.d).map((c) => `<div class="prono-col" data-serie="${c.s}">
    <div class="prono-testa"><span class="cd-sigla ${c.classe}">${c.sigla}</span><b>${esc(c.d.gp)}</b><span class="muted">gara ${formattaDataOra(c.d.gara)}</span></div>
    ${c.d.favoriti.slice(0, 3).map((r, i) => `<div class="prono-riga ${i === 0 ? "primo" : ""}">
      <span class="prono-pos">${i + 1}</span>${c.fotoDi(r) ? img(c.fotoDi(r), r.nome, "foto-mini") : '<span class="foto-mini"></span>'}
      <div class="prono-info"><strong>${esc(r.nome)}</strong><span class="muted">${esc(r.motivi.join(" · "))}</span>
        <div class="prono-barra"><i style="width:${r.indice}%"></i></div></div><span class="prono-ind">${r.indice}</span></div>`).join("")}
    ${votoHtml(c.s, c.d, c.tutti)}</div>`).join("");
  for (const c of colonne.filter((x) => x.d)) {
    const box = griglia.querySelector(`.prono-col[data-serie="${c.s}"] .vota`), chiave = chiaveVoto(c.s, c.d);
    mostraEsito(box, null, votoSalvato(chiave));
    leggiVoti(chiave).then((v) => v && mostraEsito(box, v, votoSalvato(chiave)));
    box.querySelector(".vota-apri").addEventListener("click", () => { const b = box.querySelector(".vota-box"); b.hidden = !b.hidden; });
    box.querySelector(".vota-griglia").addEventListener("click", async (e) => {
      const b = e.target.closest(".vota-pilota");
      if (!b) return;
      const nome = b.dataset.n;
      box.querySelectorAll(".vota-pilota").forEach((x) => x.classList.toggle("scelto", x === b));
      box.querySelector(".vota-apri").textContent = `Il tuo voto: ${nome} · cambia`;
      box.querySelector(".vota-box").hidden = true;
      mostraEsito(box, await inviaVoto(chiave, nome), nome);
    });
  }
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
