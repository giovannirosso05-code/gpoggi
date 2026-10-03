import { renderHeader, renderFooter, fetchJSON, esc, punti, ND, erroreCaricamento } from "./common.js";

renderHeader("confronto");
renderFooter();

const box = document.getElementById("confronto-box");
const params = new URLSearchParams(location.search);

try {
  const [roster, eventi] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json")]);
  const gare = await Promise.all(eventi.filter((g) => new Date(g.inizio) < new Date()).map((g) => fetchJSON(`data/gare/${g.id}.json`)));

  const selA = document.getElementById("sel-a");
  const selB = document.getElementById("sel-b");
  const opz = roster.map((p) => `<option value="${p.numero}">${esc(p.nome || "Pilota #" + p.numero)} (#${p.numero})</option>`).join("");
  selA.innerHTML = `<option value="">Primo pilota…</option>${opz}`;
  selB.innerHTML = `<option value="">Secondo pilota…</option>${opz}`;
  selA.value = params.get("a") || "";
  selB.value = params.get("b") || "";

  function risultatiGara(num) {
    return gare.map((g) => {
      const gara = g.sessioni.find((s) => s.tipo === "Race" && s.risultati);
      const r = gara && gara.risultati.find((x) => x.numero === num);
      return r ? { id: g.id, pos: r.pos, stato: r.stato } : null;
    });
  }

  function colonna(p, mio, altro) {
    if (!p) return `<div class="compare-col"><p class="muted">Seleziona un pilota.</p></div>`;
    const tutte = risultatiGara(p.numero);
    const valide = tutte.filter((r) => r && r.pos != null && !r.stato);
    const vittorie = valide.filter((r) => r.pos === 1).length;
    const podi = valide.filter((r) => r.pos <= 3).length;
    const punta = (r) => r && r.pos != null ? r.pos : null;
    const riga = (label, val) => `<div class="compare-stat"><div class="compare-stat-label">${label}</div><div></div><div class="compare-stat-value">${val}</div></div>`;
    return `<div class="compare-col" style="border-top:3px solid #${esc(p.colore || "2a2a33")}">
      <h2>${esc(p.nome || "Pilota #" + p.numero)}</h2>
      ${riga("Team", esc(p.team || "n.d."))}
      ${riga("Numero", "#" + p.numero)}
      ${riga("Posizione", p.posizione ? p.posizione + "°" : ND)}
      ${riga("Punti", punti(p.punti))}
      ${riga("Vittorie in gara", vittorie)}
      ${riga("Podi in gara", podi)}
      ${riga("Gare con risultato", valide.length)}
    </div>`;
  }

  function testaATesta(a, b) {
    const ra = risultatiGara(a.numero), rb = risultatiGara(b.numero);
    let ahead = 0, behind = 0;
    ra.forEach((x, i) => {
      const y = rb[i];
      if (x && y && x.pos != null && y.pos != null && !x.stato && !y.stato) x.pos < y.pos ? ahead++ : behind++;
    });
    const tot = ahead + behind;
    return tot ? `<p class="center muted" style="margin-top:20px">Nelle gare in cui hanno entrambi concluso (${tot}): ${esc(a.nome)} davanti ${ahead} volte, ${esc(b.nome)} davanti ${behind}.</p>` : `<p class="center muted" style="margin-top:20px">Nessuna gara conclusa da entrambi.</p>`;
  }

  function aggiorna() {
    const a = roster.find((p) => String(p.numero) === selA.value);
    const b = roster.find((p) => String(p.numero) === selB.value);
    document.getElementById("confronto-out").innerHTML =
      `<div class="compare-layout">${colonna(a)}${colonna(b)}</div>${a && b ? testaATesta(a, b) : ""}`;
  }
  selA.addEventListener("change", aggiorna);
  selB.addEventListener("change", aggiorna);
  aggiorna();
} catch (e) {
  erroreCaricamento(box);
}
