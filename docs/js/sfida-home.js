// Sfida del giorno in Home: stato di oggi (da fare / già fatta con il risultato). Indipendente dal resto della Home.
const giorno = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Rome" }).format(new Date());
const numero = Math.round((Date.parse(giorno) - Date.parse("2026-10-15")) / 864e5) + 1;
let fatta = null;
try { fatta = JSON.parse(localStorage.getItem("sfida-" + giorno) || "null"); } catch (e) {}
const nuova = document.getElementById("sfida-home-nuova"), k = document.getElementById("sfida-home-kicker"), n = document.getElementById("sfida-home-nota"), l = document.getElementById("sfida-home-link");
if (k) k.textContent = `Sfida del giorno #${numero}`;
if (fatta && Array.isArray(fatta.esiti) && n && l) {
  n.textContent = `Oggi hai fatto ${fatta.punti}/${fatta.esiti.length} ${fatta.esiti.map((e) => (e ? "🟩" : "🟥")).join("")}. Domani una nuova sfida.`;
  l.textContent = "Condividi il risultato →";
  if (nuova) nuova.hidden = true;
}
