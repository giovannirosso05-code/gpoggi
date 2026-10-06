import { renderHeader, renderFooter, fetchJSON, esc, img, punti, ND, erroreCaricamento } from "./common.js";

renderHeader("confronto");
renderFooter();

const box = document.getElementById("confronto-box");
const params = new URLSearchParams(location.search);

try {
  const [roster, eventi] = await Promise.all([fetchJSON("data/roster.json"), fetchJSON("data/events.json")]);
  const gare = await Promise.all(eventi.filter((g) => new Date(g.inizio) < new Date()).map((g) => fetchJSON(`data/gare/${g.id}.json`)));

  const selA = document.getElementById("sel-a");
  const selB = document.getElementById("sel-b");
  const opz = [...roster].sort((x, y) => x.numero - y.numero).map((p) => `<option value="${p.numero}">#${p.numero} · ${esc(p.nome || "Pilota #" + p.numero)}</option>`).join("");
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

  function numeri(p) {
    const valide = risultatiGara(p.numero).filter((r) => r && r.pos != null && !r.stato);
    return { punti: p.punti ?? -1, vittorie: valide.filter((r) => r.pos === 1).length, podi: valide.filter((r) => r.pos <= 3).length, arrivi: valide.length };
  }

  function colonna(p, altro) {
    if (!p) return `<div class="compare-col"><div class="compare-vuoto">Scegli un pilota dal menu.</div></div>`;
    const mio = numeri(p), suo = altro ? numeri(altro) : null;
    const riga = (label, val, chiave) => `<div class="compare-stat"><span class="compare-stat-label">${label}</span><span class="compare-stat-value ${suo && chiave && mio[chiave] > suo[chiave] ? "meglio" : ""}">${val}</span></div>`;
    return `<div class="compare-col" style="--team:#${esc(p.colore || "8b8a92")}">
      <div class="compare-foto">${img(p.foto, p.nome || "")}</div>
      <div class="compare-corpo">
        <h2><a href="pilota.html?n=${p.numero}">${esc(p.nome || "Pilota #" + p.numero)}</a></h2>
        ${riga("Team", esc(p.team || "n.d."))}
        ${riga("Numero", "#" + p.numero)}
        ${riga("Posizione", p.posizione ? p.posizione + "°" : ND)}
        ${riga("Punti", punti(p.punti), "punti")}
        ${riga("Vittorie in gara", mio.vittorie, "vittorie")}
        ${riga("Podi in gara", mio.podi, "podi")}
        ${riga("Gare concluse", mio.arrivi, "arrivi")}
      </div>
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
      `<div class="compare-layout">${colonna(a, b)}${colonna(b, a)}</div>${a && b ? testaATesta(a, b) : ""}`;
  }
  selA.addEventListener("change", aggiorna);
  selB.addEventListener("change", aggiorna);
  aggiorna();
} catch (e) {
  erroreCaricamento(box);
}
