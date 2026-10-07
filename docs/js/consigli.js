import { renderHeader, renderFooter, fetchJSON, esc, VOTI_URL } from "./common.js";

renderHeader("consigli");
renderFooter();

// Il fuso scelto nel Calendario vale anche qui (all'inizio: Italia)
let TZ = "Europe/Rome";
try { TZ = localStorage.getItem("cal-fuso") || TZ; } catch (e) {}
const NOME_FUSO = { "Europe/Rome": "ora italiana" };
document.getElementById("cons-fuso").innerHTML = `Orari in ${NOME_FUSO[TZ] || "fuso " + esc(TZ.replace("_", " ").split("/").pop())}. Puoi cambiarli nel <a class="accent" href="calendario.html">Calendario</a>.`;

const quando = (iso) => new Date(iso).toLocaleString("it-IT", { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", timeZone: TZ });
const tipo = (n) => { const x = n.toLowerCase(); return x === "gara" ? "gara" : x.startsWith("sprint") && !x.includes("qualifiche") ? "sprint" : x.includes("qualifiche") ? "quali" : "altro"; };
const PERCHE = {
  gara: "L'appuntamento principale: se ne guardi una sola, guarda questa.",
  sprint: "Gara breve del sabato, con punti in palio.",
  quali: "Decidono la griglia di partenza della gara.",
};

function scheda(serie, sigla, classe, pron, sessioni, href) {
  const gara = sessioni.find((s) => s.nome === "Gara");
  const utili = sessioni.filter((s) => tipo(s.nome) !== "altro" && new Date(s.fine) > new Date()).sort((a, b) => new Date(a.inizio) - new Date(b.inizio));
  const fav = pron.favoriti.slice(0, 3);
  return `<article class="cons-card ${serie}">
    <div class="pe-testa"><span class="cd-sigla ${classe}">${sigla}</span><b>${esc(pron.gp)}</b></div>
    <p class="muted" style="margin:0 0 10px;font-size:13px">${esc(pron.circuito || "")}</p>
    <h3 class="cons-sotto">Da non perdere</h3>
    ${utili.length ? utili.map((s) => `<div class="cons-sess"><b>${esc(s.nome)}</b><span>${quando(s.inizio)}</span><small>${PERCHE[tipo(s.nome)]}</small></div>`).join("") : `<p class="muted">Le sessioni principali sono già passate.</p>`}
    <p class="muted" style="font-size:12px;margin:8px 0 0">Le prove libere servono ai team per provare l'assetto: si possono saltare.</p>
    <h3 class="cons-sotto">Chi tenere d'occhio</h3>
    ${fav.map((f, i) => `<div class="cons-fav"><b>${i + 1}. ${esc(f.nome)}</b><small>${esc(f.team || "")} · ${esc((f.motivi || []).slice(0, 2).join(" · "))}</small></div>`).join("")}
    <p class="muted" style="font-size:12px;margin:8px 0 12px">È un'opinione di GP Oggi basata sui numeri, non una certezza.</p>
    <a class="quiz-avanti" style="text-align:center;text-decoration:none" href="${href}">Programma e orari completi</a>
  </article>`;
}

try {
  const [pron, eventi, moto] = await Promise.all([fetchJSON("data/pronostici.json"), fetchJSON("data/events.json"), fetchJSON("data/motogp.json")]);
  const trova = (lista, gara) => lista.find((w) => w.sessioni.some((s) => s.nome === "Gara" && new Date(s.inizio).getTime() === new Date(gara).getTime()));
  const f1 = pron.f1 && trova(eventi, pron.f1.gara), mg = pron.motogp && trova(moto.weekend, pron.motogp.gara);
  const out = [];
  if (f1) out.push(scheda("f1", "F1", "", pron.f1, f1.sessioni, "gara.html?id=" + f1.id));
  if (mg) out.push(scheda("moto", "MotoGP", "moto", pron.motogp, mg.sessioni, "gara-moto.html?gp=" + encodeURIComponent(mg.nome)));
  document.getElementById("cons-weekend").innerHTML = out.join("") || `<p class="muted">Nessun weekend in programma al momento.</p>`;
} catch (e) {
  document.getElementById("cons-weekend").innerHTML = `<p class="muted">Consigli non disponibili al momento.</p>`;
}

// Modulo: attivo solo quando il servizio dei voti (Cloudflare Worker) è collegato, altrimenti restano i messaggi privati
const form = document.getElementById("cons-form");
const base = VOTI_URL.replace(/\/$/, "");
const attivo = VOTI_URL ? await fetch(base + "/consiglio").then((r) => r.json()).then((d) => !!d.consigli).catch(() => false) : false;
if (attivo) {
  form.hidden = false;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const esito = document.getElementById("cons-esito"), d = Object.fromEntries(new FormData(form));
    esito.textContent = "Invio…";
    try {
      const r = await fetch(base + "/consiglio", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d) });
      if (r.status === 429) { esito.textContent = "Hai già mandato qualche consiglio oggi: riprova domani."; return; }
      if (!r.ok) throw new Error();
      form.reset(); esito.textContent = "Grazie! Il consiglio è arrivato.";
    } catch (err) { esito.textContent = "Non sono riuscito a inviarlo. Riprova più tardi o scrivici in messaggio privato."; }
  });
}


// Stelle: un voto per dispositivo, la media la tiene il servizio dei voti (Cloudflare Worker)
const stelle = document.getElementById("cons-stelle"), media = document.getElementById("cons-media");
let miaId = "", mioVoto = 0;
try { miaId = localStorage.getItem("val-id") || ""; if (!miaId) { miaId = (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now()); localStorage.setItem("val-id", miaId); } mioVoto = Number(localStorage.getItem("val-voto") || 0); } catch (e) { miaId = String(Math.random()).slice(2) + Date.now(); }
const disegna = (n) => stelle.querySelectorAll("button").forEach((b) => { const on = Number(b.dataset.s) <= n; b.classList.toggle("on", on); b.setAttribute("aria-checked", String(Number(b.dataset.s) === mioVoto)); });
const testoMedia = (d) => (d && d.voti ? `Voto medio ${String(d.media).replace(".", ",")} su 5 · ${d.voti} ${d.voti === 1 ? "voto" : "voti"}` : "Sii il primo a votare.");
const servizio = VOTI_URL ? await fetch(base + "/valutazione").then((r) => r.json()).then((d) => (d && "media" in d ? d : null)).catch(() => null) : null;
disegna(mioVoto);
media.textContent = servizio ? testoMedia(servizio) + (mioVoto ? ` · il tuo voto: ${mioVoto}` : "") : "Le valutazioni si attivano a breve.";
stelle.querySelectorAll("button").forEach((b) => {
  b.addEventListener("mouseenter", () => disegna(Number(b.dataset.s)));
  b.addEventListener("mouseleave", () => disegna(mioVoto));
  b.addEventListener("click", async () => {
    if (!servizio) { media.textContent = "Le valutazioni si attivano a breve: riprova tra poco."; return; }
    const v = Number(b.dataset.s); media.textContent = "Invio…";
    try {
      const r = await fetch(base + "/valutazione", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: miaId, stelle: v }) });
      if (r.status === 429) { media.textContent = "Troppi voti oggi da questa rete: riprova domani."; return; }
      if (!r.ok) throw new Error();
      const d = await r.json(); mioVoto = v; try { localStorage.setItem("val-voto", String(v)); } catch (e) {}
      disegna(v); media.textContent = "Grazie! " + testoMedia(d);
    } catch (err) { media.textContent = "Non sono riuscito a registrare il voto. Riprova più tardi."; disegna(mioVoto); }
  });
});
