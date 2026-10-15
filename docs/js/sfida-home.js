// Sfida del giorno in Home: stato di oggi (da fare / già fatta con il risultato). Indipendente dal resto della Home.
const giorno = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Rome" }).format(new Date());
const numero = Math.round((Date.parse(giorno) - Date.parse("2026-10-15")) / 864e5) + 1;
const ieri = new Date(Date.parse(giorno) - 864e5).toISOString().slice(0, 10);
let serie = { ultimo: null, serie: 0 };
try { serie = JSON.parse(localStorage.getItem("sfida-serie") || "null") || serie; } catch (e) {}
const giorni = (x) => `${x} ${x === 1 ? "giorno" : "giorni"} di fila`;
let fatta = null;
try { fatta = JSON.parse(localStorage.getItem("sfida-" + giorno) || "null"); } catch (e) {}
const nuova = document.getElementById("sfida-home-nuova"), k = document.getElementById("sfida-home-kicker"), n = document.getElementById("sfida-home-nota"), l = document.getElementById("sfida-home-link");
if (k) k.textContent = `Sfida del giorno #${numero}`;
if (fatta && Array.isArray(fatta.esiti) && n && l) {
  n.textContent = `Oggi hai fatto ${fatta.punti}/${fatta.esiti.length} ${fatta.esiti.map((e) => (e ? "🟩" : "🟥")).join("")}.${serie.ultimo === giorno && serie.serie >= 2 ? ` 🔥 ${giorni(serie.serie)}!` : ""} Domani una nuova sfida.`;
  l.textContent = "Condividi il risultato →";
  if (nuova) nuova.hidden = true;
}
else if (n && serie.ultimo === ieri && serie.serie >= 1) {
  n.textContent = `🔥 Hai ${giorni(serie.serie)}: gioca oggi per non perdere la serie.`;   // ieri l'ha fatta, oggi no
}
