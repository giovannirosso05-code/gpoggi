"""Pagine statiche con la pagella di OGNI weekend concluso (F1 e MotoGP), per farsi trovare su Google e dalle IA.

pagella.html mostra solo l'ultimo weekend e si disegna con JavaScript (chi non lo esegue vede una pagina vuota). Qui il testo è già nell'HTML.
I voti sono gli stessi del sito: li ricalcola build_pagella (f1_tutti / moto_tutti), correzioni dichiarate comprese.
Scrive docs/pagella-f1-<paese>-<anno>.html, docs/pagella-motogp-<paese>-<anno>.html, docs/pagelle-gp.html e aggiorna docs/sitemap.xml.
Uso:  python build_pagine_pagella.py   (dopo build_pagella.py)
"""
import html
import re
from datetime import datetime

import build_pagella as BP
from build_pagine_gp import DOCS, SITO, GIORNI, MESI, breve, paese_chiave, pagina

esc = html.escape
NOTA = "Voti di GP Oggi, messi a scopo divertente e senza intenzione di offendere nessuno: non sono voti ufficiali."


def virgola(v):
    return str(v).replace(".", ",")


def pos(p):
    return "RIT" if p is None else str(p)


def data_it(iso):
    d = datetime.fromisoformat(str(iso)[:10])
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}", d


def tabella(w):
    s = w["sprint"]
    righe = []
    for r in w["righe"]:
        extra = f"<br><small class=\"muted\">{esc(' · '.join(r['perche']))}</small>" if r.get("perche") else ""
        if r.get("correzione"):
            extra += f"<br><small class=\"muted\">Calcolato {virgola(r['voto_calcolato'])}, correzione {'+' if r['correzione'] > 0 else '−'}{virgola(abs(r['correzione']))}: {esc(r['motivo'])}</small>"
        righe.append(f"<tr><td><strong>{virgola(r['voto'])}</strong></td><td><strong>{esc(r['nome'])}</strong>{extra}</td><td>{esc(r.get('team') or '')}</td>"
                     f"<td>{pos(r.get('q'))}</td>{'<td>' + pos(r.get('s')) + '</td>' if s else ''}<td>{pos(r.get('g'))}</td></tr>")
    return (f'<div class="table-wrap"><table class="results"><thead><tr><th>Voto</th><th>Pilota</th><th>Team</th><th>Qualifica</th>{"<th>Sprint</th>" if s else ""}<th>Gara</th></tr></thead>'
            f'<tbody>\n' + "\n".join(righe) + '\n</tbody></table></div>')


def costruisci(w, serie):
    etichetta = "F1" if serie == "f1" else "MotoGP"
    nome = breve(w["nome"], serie)
    if str(w.get("id")) == "1308":
        nome += " (in Malesia)"   # il GP del Bahrain 2026 si è corso a Sepang
    testo_data, d = data_it(w["data"])
    anno = d.year
    file = f"pagella-{serie}-{paese_chiave(w['nome'])}-{anno}.html"
    top = w["righe"][0]
    titolo = f"Pagella {etichetta} {nome} {anno}: i voti ai piloti | GP Oggi"
    descr = f"I voti ai piloti nel {nome} {anno} di {etichetta}: la pagella di GP Oggi con qualifica{', sprint' if w['sprint'] else ''} e gara. Uomo del weekend: {top['nome']} ({virgola(top['voto'])})."
    ultimi = sorted(w["righe"], key=lambda r: (r["voto_esatto"], r.get("griglia") or 99))[:3]
    corpo = [f"    <p>La pagella del <strong>{esc(nome)} {anno}</strong> di {etichetta} (gara di {testo_data}): un voto a ogni pilota, calcolato sui risultati ufficiali di qualifica{', sprint' if w['sprint'] else ''} e gara.</p>",
             f"    <p><strong>Uomo del weekend: {esc(top['nome'])}, voto {virgola(top['voto'])}</strong> ({esc(top.get('team') or '')}).{(' ' + esc('; '.join(top['perche'])).capitalize() + '.') if top.get('perche') else ''}</p>",
             "    <h2>Tutti i voti</h2>", "    " + tabella(w),
             f"    <p>I voti più bassi del weekend: {', '.join(esc(r['nome']) + ' (' + virgola(r['voto']) + ')' for r in ultimi)}.</p>",
             "    <h2>Come calcoliamo il voto</h2>",
             "    <p>Ogni sessione dà un voto in base alla posizione: 1° = 10, 2° = 8,5, 3° = 8, 4° = 7,5, 5° = 7, 6° = 6,5, poi si scende di poco a ogni posizione, fino a un minimo di 4. "
             "In gara si aggiunge 0,1 per ogni posizione guadagnata rispetto alla griglia di partenza ufficiale. Chi si ritira o non fa registrare un tempo prende 4,5 in quella sessione (nelle pagelle fino al 25 ottobre 2026 prendeva 3). "
             "Pesi: qualifica 20%, sprint 20%, gara 60% (senza sprint: 25% e 75%). Il voto finale è arrotondato al mezzo punto. "
             "Se la redazione ritiene che un voto non renda giustizia a una giornata lo corregge e scrive il motivo sotto il nome del pilota.</p>",
             f'    <p class="muted">{NOTA}</p>',
             f'    <p><a class="accent" href="pagella.html">Ultima pagella →</a> · <a class="accent" href="pagelle-gp.html">Tutte le pagelle →</a>'
             + (f' · <a class="accent" href="gara.html?id={w["id"]}">Risultati completi del GP →</a>' if serie == "f1" and w.get("id") else "") + "</p>"]
    h1 = f"Pagella {etichetta} {nome} {anno}: i voti ai piloti"
    return file, pagina(titolo, descr, h1, f"{etichetta} · pagella · {testo_data}", "\n".join(corpo), file, None), (d, etichetta, nome, file)


def main():
    voci = [costruisci(w, "f1") for w in BP.f1_tutti()] + [costruisci(w, "motogp") for w in BP.moto_tutti()]
    for file, testo, _ in voci:
        (DOCS / file).write_text(testo, encoding="utf-8")
    voci.sort(key=lambda v: v[2][0], reverse=True)
    elenco = "<ul>" + "".join(f'<li><a class="accent" href="{f}">Pagella {e} {esc(n)}</a> — {GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}</li>' for (_, _, (d, e, n, f)) in voci) + "</ul>"
    corpo = ["    <p>La pagella di GP Oggi dopo ogni weekend: un voto a ogni pilota di Formula 1 e MotoGP, calcolato sui risultati ufficiali. Scegli il Gran Premio:</p>", "    " + elenco,
             f'    <p class="muted">{NOTA}</p>', '    <p><a class="accent" href="pagella.html">Ultima pagella →</a> · <a class="accent" href="orari-gp.html">Orari dei GP →</a></p>']
    (DOCS / "pagelle-gp.html").write_text(pagina("Pagelle F1 e MotoGP: i voti ai piloti di ogni Gran Premio | GP Oggi",
                                                 "Tutte le pagelle di GP Oggi: i voti ai piloti di Formula 1 e MotoGP dopo ogni Gran Premio, con il metodo di calcolo.",
                                                 "Pagelle dei Gran Premi", "Formula 1 e MotoGP", "\n".join(corpo), "pagelle-gp.html", None), encoding="utf-8")
    sm = DOCS / "sitemap.xml"
    s = re.sub(r"\s*<url><loc>https://gpoggi\.it/pagell[ae]-[^<]*</loc></url>", "", sm.read_text(encoding="utf-8"))
    nuove = "".join(f"\n  <url><loc>{SITO}/{f}</loc></url>" for f in ["pagelle-gp.html"] + [v[0] for v in voci])
    sm.write_text(s.replace("</urlset>", nuove.lstrip("\n") + "\n</urlset>"), encoding="utf-8")
    print(f"Pagine pagella: {len(voci)} + indice")


if __name__ == "__main__":
    main()
