"""Pagine statiche per farsi trovare su Google, Bing e dalle IA, sulle ricerche più frequenti:
classifica mondiale F1 e MotoGP, calendario 2026, e una pagina per ogni pilota (F1 e MotoGP).

Il testo è già nell'HTML (non serve JavaScript) e viene solo dai dati del sito (docs/data): niente numeri scritti a mano.
Scrive docs/classifica-f1-<anno>.html, classifica-motogp-<anno>.html, calendario-f1-<anno>.html, calendario-motogp-<anno>.html,
pilota-f1-<nome>.html, pilota-motogp-<nome>.html, piloti-2026.html (indice) e aggiorna docs/sitemap.xml.
Uso:  python build_pagine_seo.py   (dopo build_pagella.py e build_pagine_pagella.py)
"""
import html
import json
import re
from datetime import datetime

from build_pagine_gp import DOCS, SITO, GIORNI, MESI, ROMA, data_it, pagina, paese_chiave, slug

DATA = DOCS / "data"
esc = html.escape
NAZ = {"Italian": "italiana", "British": "britannica", "Dutch": "olandese", "Monegasque": "monegasca", "Spanish": "spagnola", "French": "francese", "German": "tedesca",
       "Australian": "australiana", "Canadian": "canadese", "Finnish": "finlandese", "Thai": "thailandese", "Mexican": "messicana", "Japanese": "giapponese",
       "Argentine": "argentina", "Brazilian": "brasiliana", "New Zealander": "neozelandese", "Danish": "danese", "Chinese": "cinese", "American": "americana"}


def carica(nome, difetto=None):
    try:
        return json.load(open(DATA / nome, encoding="utf-8"))
    except (OSError, ValueError):
        return difetto


def pt(v):
    v = float(v)
    return str(int(v)) if v == int(v) else str(v).replace(".", ",")


def tabella(intest, righe):
    return ('<div class="table-wrap"><table class="results"><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in intest) + "</tr></thead><tbody>\n"
            + "\n".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in righe) + "\n</tbody></table></div>")


def dt(iso):
    return datetime.fromisoformat(str(iso)).astimezone(ROMA)


def foto_img(foto, alt):
    """Foto libera di Wikimedia Commons con il suo credito (stessa regola del resto del sito)."""
    if not foto:
        return ""
    src = foto.get("file") or foto.get("url") or ""
    if not src:
        return ""
    cred = ""
    if foto.get("autore"):
        autore = re.sub(r"Original:\s*", "", foto["autore"])
        cred = (f'<p class="credito">Foto: {esc(autore)} · '
                f'<a href="{esc(foto.get("pagina", ""))}" target="_blank" rel="noopener">{esc(foto.get("licenza", ""))}</a>, via Wikimedia Commons</p>')
    return f'<p><img src="{esc(src)}" alt="{esc(alt)}" width="320" loading="lazy" style="max-width:100%;height:auto;border-radius:12px"></p>{cred}'


def pagella_di(id_gp, nome_gp, anno, serie):
    f = f"pagella-{serie}-{paese_chiave(nome_gp)}-{anno}.html"
    return f if (DOCS / f).exists() else None


# ---------------------------------------------------------------- classifiche
def pagina_classifica_f1(st, anno):
    piloti, costr = st["piloti"], st["costruttori"]
    dopo = st.get("dopo") or ""
    p1, p2 = piloti[0], piloti[1]
    file = f"classifica-f1-{anno}.html"
    titolo = f"Classifica Mondiale F1 {anno}: piloti e costruttori" + (f", dopo il {dopo.replace('Gran Premio', 'GP')}" if dopo else "") + " | GP Oggi"
    descr = f"Classifica del Mondiale di Formula 1 {anno} aggiornata: punti di tutti i piloti e dei team. Comanda {p1['nome']} con {pt(p1['punti'])} punti, davanti a {p2['nome']}."
    corpo = [f"    <p>Classifica del Mondiale di Formula 1 {anno}{(' dopo il ' + esc(dopo)) if dopo else ''}. "
             f"Al comando c'è <strong>{esc(p1['nome'])}</strong> ({esc(p1['team'])}) con <strong>{pt(p1['punti'])} punti</strong>; "
             f"secondo {esc(p2['nome'])} ({esc(p2['team'])}) con {pt(p2['punti'])}, a {pt(p1['punti'] - p2['punti'])} punti dalla vetta. "
             f"Tra i costruttori guida <strong>{esc(costr[0]['team'])}</strong> con {pt(costr[0]['punti'])} punti.</p>",
             "    <h2>Classifica piloti</h2>",
             "    " + tabella(["Pos", "Pilota", "Team", "Punti"], [[p["posizione"], f'<a href="pilota-f1-{slug(p["nome"])}.html"><strong>{esc(p["nome"])}</strong></a>', esc(p["team"]), f"<strong>{pt(p['punti'])}</strong>"] for p in piloti]),
             "    <h2>Classifica costruttori</h2>",
             "    " + tabella(["Pos", "Team", "Punti"], [[c["posizione"], esc(c["team"]), f"<strong>{pt(c['punti'])}</strong>"] for c in costr]),
             '    <p class="muted">Punti dei risultati ufficiali (qualifiche sprint, sprint e gara), aggiornati dopo ogni Gran Premio.</p>',
             f'    <p><a class="accent" href="classifiche.html">Classifiche interattive →</a> · <a class="accent" href="calendario-f1-{anno}.html">Calendario F1 {anno} →</a> · <a class="accent" href="pagelle-gp.html">Pagelle →</a> · <a class="accent" href="classifica-motogp-{anno}.html">Classifica MotoGP →</a></p>']
    return file, pagina(titolo, descr, f"Classifica Mondiale F1 {anno}", f"Formula 1 · {anno}", "\n".join(corpo), file, None)


def pagina_classifica_moto(mc, anno):
    cat = mc.get("categorie", {})
    gp = cat.get("MotoGP", [])
    if not gp:
        return None
    p1, p2 = gp[0], gp[1]
    file = f"classifica-motogp-{anno}.html"
    titolo = f"Classifica Mondiale MotoGP {anno}: piloti, punti e vittorie | GP Oggi"
    descr = f"Classifica del Mondiale MotoGP {anno} aggiornata: punti e vittorie di tutti i piloti, più Moto2 e Moto3. Comanda {p1['nome']} con {pt(p1['punti'])} punti."
    corpo = [f"    <p>Classifica del Mondiale MotoGP {anno}. Al comando <strong>{esc(p1['nome'])}</strong> ({esc(p1['team'])}) con <strong>{pt(p1['punti'])} punti</strong>; "
             f"secondo {esc(p2['nome'])} ({esc(p2['team'])}) con {pt(p2['punti'])}, a {pt(p1['punti'] - p2['punti'])} punti.</p>",
             "    <h2>Classifica piloti MotoGP</h2>",
             "    " + tabella(["Pos", "Pilota", "Team", "Moto", "Vittorie", "Punti"], [[p["pos"], f'<a href="pilota-motogp-{slug(p["nome"])}.html"><strong>{esc(p["nome"])}</strong></a>', esc(p["team"]), esc(p.get("moto", "")), p.get("vittorie", 0), f"<strong>{pt(p['punti'])}</strong>"] for p in gp])]
    for classe in ("Moto2", "Moto3"):
        lista = cat.get(classe) or []
        if lista:
            corpo += [f"    <h2>Classifica {classe} (primi 10)</h2>", "    " + tabella(["Pos", "Pilota", "Team", "Punti"], [[p["pos"], esc(p["nome"]), esc(p["team"]), pt(p["punti"])] for p in lista[:10]])]
    corpo.append(f'    <p><a class="accent" href="motogp.html">MotoGP, risultati e notizie →</a> · <a class="accent" href="calendario-motogp-{anno}.html">Calendario MotoGP {anno} →</a> · <a class="accent" href="classifica-f1-{anno}.html">Classifica F1 →</a></p>')
    return file, pagina(titolo, descr, f"Classifica Mondiale MotoGP {anno}", f"MotoGP · {anno}", "\n".join(corpo), file, None)


# ---------------------------------------------------------------- calendari
def vincitore_f1(id_gp):
    try:
        g = json.load(open(DATA / "gare" / f"{id_gp}.json", encoding="utf-8"))
        gara = next(s for s in g["sessioni"] if s["nome"] == "Gara" and s.get("risultati"))
        return next(r["nome"] for r in gara["risultati"] if r.get("pos") == 1)
    except (OSError, StopIteration, ValueError, KeyError):
        return None


def pagina_calendario_f1(eventi, anno):
    file = f"calendario-f1-{anno}.html"
    ora = datetime.now(ROMA)
    righe = []
    for e in sorted(eventi, key=lambda x: x["inizio"]):
        sess = [s for s in e["sessioni"] if s.get("inizio")]
        gara = next((s for s in sess if s["nome"] == "Gara"), sess[-1])
        d = dt(gara["inizio"])
        nome = re.sub(r"^Gran Premio", "GP", e["nome"]) + (" (in Malesia)" if "Bahrain" in e["nome"] and e.get("paese") == "Malesia" else "")
        orari = f"orari-f1-{paese_chiave(e['nome'])}-{d.year}.html"
        vinc = vincitore_f1(e["id"]) if d < ora else None
        righe.append([f"{d.day} {MESI[d.month - 1]}", f'<a href="{orari}"><strong>{esc(nome)}</strong></a>', esc(e.get("circuito") or ""), f"{d:%H:%M}", esc(vinc) if vinc else '<span class="muted">–</span>'])
    prossimo = next((e for e in sorted(eventi, key=lambda x: x["inizio"]) if dt(next(s for s in e["sessioni"] if s["nome"] == "Gara")["inizio"]) >= ora), None)
    intro = f"    <p>Calendario completo della Formula 1 {anno}: {len(eventi)} Gran Premi, con data, circuito, ora di partenza della gara (ora italiana) e vincitore dei GP già corsi."
    if prossimo:
        g = dt(next(s for s in prossimo["sessioni"] if s["nome"] == "Gara")["inizio"])
        intro += f" Il prossimo è il <strong>{esc(re.sub('^Gran Premio', 'GP', prossimo['nome']))}</strong>, {GIORNI[g.weekday()]} {g.day} {MESI[g.month - 1]} alle {g:%H:%M}."
    intro += "</p>"
    corpo = [intro, "    " + tabella(["Data gara", "Gran Premio", "Circuito", "Ora gara", "Vincitore"], righe),
             '    <p class="muted">Orari in ora italiana. Tocca un Gran Premio per tutti gli orari del weekend e dove vederlo.</p>',
             f'    <p><a class="accent" href="classifica-f1-{anno}.html">Classifica Mondiale →</a> · <a class="accent" href="orari-gp.html">Orari di tutti i GP →</a> · <a class="accent" href="calendario-motogp-{anno}.html">Calendario MotoGP →</a></p>']
    return file, pagina(f"Calendario F1 {anno}: date, orari e vincitori dei Gran Premi | GP Oggi",
                        f"Calendario Formula 1 {anno}: tutti i Gran Premi con data, circuito, orario della gara in ora italiana e vincitore.",
                        f"Calendario F1 {anno}", f"Formula 1 · {anno}", "\n".join(corpo), file, None)


def pagina_calendario_moto(anno):
    gare = carica("motogp-gare.json", {}) or {}
    prossimi = (carica("motogp.json", {}) or {}).get("weekend", [])
    voci = {}
    for nome, g in gare.items():
        vinc = next(iter((g.get("classifiche", {}).get("MotoGP") or [])), {}).get("nome")
        voci[nome] = (g.get("data"), g.get("circuito") or "", vinc)
    for w in prossimi:
        gara = next((s for s in w.get("sessioni", []) if s.get("codice") in ("RAC", "GP") or s.get("nome") == "Gara"), None) or (w.get("sessioni") or [None])[-1]
        if gara and gara.get("inizio") and w["nome"] not in voci:
            voci[w["nome"]] = (dt(gara["inizio"]).strftime("%Y-%m-%d"), w.get("circuito") or "", None)
    if not voci:
        return None
    righe = []
    for nome, (d, circ, vinc) in sorted(voci.items(), key=lambda x: x[1][0] or ""):
        dd = datetime.fromisoformat(d)
        righe.append([f"{dd.day} {MESI[dd.month - 1]}", f"<strong>{esc(nome)}</strong>", esc(circ), esc(vinc) if vinc else '<span class="muted">–</span>'])
    file = f"calendario-motogp-{anno}.html"
    corpo = [f"    <p>Calendario della MotoGP {anno}: date dei Gran Premi, circuito e vincitore della gara dei GP già corsi.</p>",
             "    " + tabella(["Data", "Gran Premio", "Circuito", "Vincitore gara"], righe),
             '    <p class="muted">Date delle gare della domenica. Orari italiani di prove, qualifiche, sprint e gara nelle pagine «orari» dei prossimi weekend.</p>',
             f'    <p><a class="accent" href="classifica-motogp-{anno}.html">Classifica Mondiale MotoGP →</a> · <a class="accent" href="orari-gp.html">Orari di tutti i GP →</a> · <a class="accent" href="calendario-f1-{anno}.html">Calendario F1 →</a></p>']
    return file, pagina(f"Calendario MotoGP {anno}: date, circuiti e vincitori | GP Oggi",
                        f"Calendario MotoGP {anno}: tutti i Gran Premi con data, circuito e vincitore della gara.",
                        f"Calendario MotoGP {anno}", f"MotoGP · {anno}", "\n".join(corpo), file, None)


# ---------------------------------------------------------------- piloti
def pagina_pilota_f1(p, schede, anno):
    nome = p["nome"]
    file = f"pilota-f1-{slug(nome)}.html"
    sc = schede.get(f"f1:{p['numero']}") or {}
    gare = [w for w in p.get("weekend", []) if w.get("gara")]
    fatte = [w for w in gare if w["gara"].get("pos") or w["gara"].get("stato")]
    titolo = f"{nome}: classifica, risultati e statistiche {anno} | GP Oggi"
    descr = (f"{nome} ({p.get('acronimo', '')}), numero {p['numero']}, {p['team']}: {p.get('posizione', '?')}° nel Mondiale F1 {anno} con {pt(p.get('punti', 0))} punti. "
             f"Risultati gara per gara, vittorie, podi e pole.")
    frasi = [f"{esc(nome)} ({esc(p.get('acronimo', ''))}) corre in Formula 1 con il numero <strong>{p['numero']}</strong> per <strong>{esc(p['team'])}</strong>. "
             f"Nel Mondiale {anno} è <strong>{p.get('posizione', '?')}°</strong> con <strong>{pt(p.get('punti', 0))} punti</strong>"
             f": {p.get('vittorie', 0)} vittorie, {p.get('podi', 0)} podi, {p.get('pole', 0)} pole position"
             + (f", miglior risultato in gara {p['miglior_arrivo']}°" if p.get("miglior_arrivo") else "")
             + (f", {p['ritiri']} ritiri" if p.get("ritiri") is not None else "") + "."]
    if sc:
        bio = []
        if sc.get("nascita"):
            n = datetime.fromisoformat(sc["nascita"])
            bio.append(f"è nato il {n.day} {MESI[n.month - 1]} {n.year}")
        if sc.get("nazionalita"):
            bio.append(f"di nazionalità {NAZ.get(sc['nazionalita'], sc['nazionalita'])}")
        carr = []
        if sc.get("gare") is not None:
            carr.append(f"{sc['gare']} Gran Premi disputati")
        for k, lab in (("vittorie", "vittorie"), ("podi", "podi"), ("pole", "pole position"), ("giri_veloci", "giri veloci")):
            if sc.get(k) is not None:
                carr.append(f"{sc[k]} {lab}")
        if sc.get("titoli") is not None:
            carr.append(f"{sc['titoli']} " + ("titolo mondiale" if sc['titoli'] == 1 else "titoli mondiali"))
        if bio:
            frasi.append(f"{esc(nome)} " + ", ".join(bio) + ".")
        if carr:
            frasi.append("In carriera in Formula 1: " + ", ".join(carr) + ".")
    corpo = ["\n".join(f"    <p>{f}</p>" for f in frasi)]
    corpo.insert(0, "    " + foto_img(p.get("foto"), f"{nome}, pilota {p['team']}"))
    if gare:
        righe = []
        for w in gare:
            q, s, g = w.get("qualifiche") or {}, w.get("sprint") or {}, w.get("gara") or {}
            cella = lambda x: (f"{x['pos']}°" if x.get("pos") else esc(x.get("stato") or "–")) if x else "–"
            nome_gp = re.sub(r"^Gran Premio", "GP", w["nome"])
            pag = pagella_di(w["id"], w["nome"], dt(w["inizio"]).year, "f1")
            righe.append([f'<a href="gara.html?id={w["id"]}">{esc(nome_gp)}</a>', cella(q), cella(s) if w.get("sprint") else "–", f"<strong>{cella(g)}</strong>", f'<a href="{pag}">pagella</a>' if pag else "–"])
        corpo += [f"    <h2>Risultati {esc(nome)} nel {anno}</h2>", "    " + tabella(["Gran Premio", "Qualifica", "Sprint", "Gara", "Voto GP Oggi"], righe)]
    corpo.append(f'    <p><a class="accent" href="classifica-f1-{anno}.html">Classifica Mondiale F1 →</a> · <a class="accent" href="piloti-{anno}.html">Tutti i piloti →</a> · <a class="accent" href="pilota.html?n={p["numero"]}">Scheda interattiva →</a></p>')
    ld = {"@context": "https://schema.org", "@type": "Person", "name": nome, "jobTitle": "Pilota di Formula 1", "url": f"{SITO}/{file}", "memberOf": {"@type": "SportsTeam", "name": p["team"]}}
    return file, pagina(titolo, descr, f"{nome}: risultati e statistiche {anno}", f"Formula 1 · {p['team']} · #{p['numero']}", "\n".join(corpo), file, ld)


def pagina_pilota_moto(p, anno, schede, foto_moto):
    nome = p["nome"]
    file = f"pilota-motogp-{slug(nome)}.html"
    sc = schede.get(f"moto:{p['id']}") or {}
    gare = p.get("gare") or []
    titolo = f"{nome}: classifica, risultati e statistiche MotoGP {anno} | GP Oggi"
    descr = f"{nome}, numero {p['numero']}, {p['team']} ({p.get('moto', '')}): {p.get('pos', '?')}° nel Mondiale MotoGP {anno} con {pt(p.get('punti', 0))} punti. Risultati di ogni gara."
    frasi = [f"{esc(nome)} corre in {esc(p.get('categoria', 'MotoGP'))} con il numero <strong>{p['numero']}</strong> per <strong>{esc(p['team'])}</strong> ({esc(p.get('moto', ''))})"
             f"{', nazionalità ' + esc(p['paese']) if p.get('paese') else ''}. Nel Mondiale {anno} è <strong>{p.get('pos', '?')}°</strong> con "
             f"<strong>{pt(p.get('punti', 0))} punti</strong> e {p.get('vittorie', 0)} {'vittoria' if p.get('vittorie') == 1 else 'vittorie'}."]
    if sc.get("nascita"):
        n = datetime.fromisoformat(sc["nascita"])
        extra = f"è nato il {n.day} {MESI[n.month - 1]} {n.year}" + (f" a {esc(sc['luogo'])}" if sc.get("luogo") else "")
        if sc.get("debutto"):
            extra += f", ha debuttato nel Motomondiale nel {sc['debutto']}"
        frasi.append(f"{esc(nome)} {extra}.")
    corpo = ["    " + foto_img(foto_moto.get(f"nome:{nome}") or foto_moto.get(f"id:{p['id']}"), f"{nome}, pilota {p['team']}")]
    corpo += [f"    <p>{f}</p>" for f in frasi]
    if gare:
        righe = [[esc(g["gp"]), f"{g['sprint']}°" if g.get("sprint") else "–", f"<strong>{g['gara']}°</strong>" if g.get("gara") else esc(g.get("stato_gara") or "–"), pt(g.get("punti", 0))] for g in gare]
        corpo += [f"    <h2>Risultati {esc(nome)} nel {anno}</h2>", "    " + tabella(["Gran Premio", "Sprint", "Gara", "Punti"], righe)]
    corpo.append(f'    <p><a class="accent" href="classifica-motogp-{anno}.html">Classifica Mondiale MotoGP →</a> · <a class="accent" href="piloti-{anno}.html">Tutti i piloti →</a></p>')
    ld = {"@context": "https://schema.org", "@type": "Person", "name": nome, "jobTitle": f"Pilota di {p.get('categoria', 'MotoGP')}", "url": f"{SITO}/{file}", "memberOf": {"@type": "SportsTeam", "name": p["team"]}}
    return file, pagina(titolo, descr, f"{nome}: risultati e statistiche MotoGP {anno}", f"{p.get('categoria', 'MotoGP')} · {p['team']} · #{p['numero']}", "\n".join(corpo), file, ld)


def main():
    st = carica("standings.json")
    eventi = carica("events.json", [])
    mc = carica("motogp-classifica.json", {})
    mp = carica("motogp-piloti.json", {})
    schede = carica("schede.json", {})
    foto_moto = carica("foto-motogp.json", {})
    anno = dt(eventi[0]["inizio"]).year if eventi else datetime.now().year
    pagine = []
    if st:
        pagine.append(pagina_classifica_f1(st, anno))
    r = pagina_classifica_moto(mc, anno) if mc else None
    if r:
        pagine.append(r)
    if eventi:
        pagine.append(pagina_calendario_f1(eventi, anno))
    r = pagina_calendario_moto(anno)
    if r:
        pagine.append(r)
    f1_piloti, moto_piloti = [], []
    for f in sorted((DATA / "piloti").glob("*.json")):
        p = json.load(open(f, encoding="utf-8"))
        if p.get("nome"):
            fp = pagina_pilota_f1(p, schede, anno)
            pagine.append(fp)
            f1_piloti.append((p, fp[0]))
    for p in mp.values():
        if p.get("categoria") == "MotoGP" and p.get("nome"):
            fp = pagina_pilota_moto(p, anno, schede, foto_moto)
            pagine.append(fp)
            moto_piloti.append((p, fp[0]))
    for serie, nome_s, cosa in (("f1", "F1", "Formula 1"), ("motogp", "MotoGP", "MotoGP")):
        f = f"giochi-{serie}-online.html"
        quiz = ("indovinare il pilota dalla foto, il circuito dal tracciato, il numero di gara, chi ha vinto il Mondiale o un Gran Premio" if serie == "f1"
                else "indovinare che moto guida un pilota, il suo numero di gara, chi ha vinto il Mondiale o un Gran Premio")
        c = [f"    <p>Giochi {nome_s} gratis, in italiano e senza registrazione: quiz sulla {cosa} da fare dal telefono o dal computer. Puoi sfidare gli amici e vedere se superi il punteggio di ieri.</p>",
             "    <h2>Che giochi trovi</h2>",
             f"    <ul><li><b>Sfida del giorno</b>: 5 domande uguali per tutti, una nuova ogni giorno, con la serie dei giorni di fila.</li><li><b>Quiz {nome_s}</b>: {quiz}.</li><li><b>Più o meno punti</b> e altre sfide a risposta rapida.</li></ul>",
             '    <p><a class="accent" href="giochi.html">Gioca ora ai giochi di GP Oggi</a></p>',
             f'    <p>Per le classifiche aggiornate: <a class="accent" href="classifica-{serie}-{anno}.html">Classifica {nome_s} {anno}</a> · <a class="accent" href="calendario-{serie}-{anno}.html">Calendario {nome_s} {anno}</a>.</p>']
        pagine.append((f, pagina(f"Giochi {nome_s} online gratis: quiz e sfida del giorno | GP Oggi",
                                 f"Giochi {nome_s} gratuiti in italiano: sfida del giorno, quiz sui piloti, i circuiti e i Mondiali di {cosa}. Nessuna registrazione. Sito non ufficiale.",
                                 f"Giochi {nome_s} online gratis", f"{cosa} · Giochi", "\n".join(c), f, None)))
    # indice dei piloti
    f1_piloti.sort(key=lambda x: x[0].get("posizione") or 99)
    moto_piloti.sort(key=lambda x: x[0].get("pos") or 99)
    corpo = [f"    <p>Tutti i piloti della Formula 1 e della MotoGP {anno}, con posizione nel Mondiale, punti e risultati gara per gara.</p>",
             "    <h2>Formula 1</h2>", "    <ul>" + "".join(f'<li><a class="accent" href="{f}">{esc(p["nome"])}</a> · {esc(p["team"])} · {p.get("posizione", "?")}° con {pt(p.get("punti", 0))} punti</li>' for p, f in f1_piloti) + "</ul>",
             "    <h2>MotoGP</h2>", "    <ul>" + "".join(f'<li><a class="accent" href="{f}">{esc(p["nome"])}</a> · {esc(p["team"])} · {p.get("pos", "?")}° con {pt(p.get("punti", 0))} punti</li>' for p, f in moto_piloti) + "</ul>"]
    ind = f"piloti-{anno}.html"
    pagine.append((ind, pagina(f"Piloti F1 e MotoGP {anno}: classifica, risultati e statistiche | GP Oggi",
                               f"Tutti i piloti di Formula 1 e MotoGP {anno}: posizione nel Mondiale, punti, risultati di ogni gara e statistiche.",
                               f"Piloti F1 e MotoGP {anno}", "Formula 1 e MotoGP", "\n".join(corpo), ind, None)))
    mappa = {"f1": {str(p.get("numero")): f for p, f in f1_piloti}, "moto": {str(p.get("id")): f for p, f in moto_piloti}}
    (DATA / "slug-piloti.json").write_text(json.dumps(mappa, ensure_ascii=False), encoding="utf-8")
    for file, testo in pagine:
        (DOCS / file).write_text(testo, encoding="utf-8")
    sm = DOCS / "sitemap.xml"
    s = re.sub(r"\s*<url><loc>https://gpoggi\.it/(?:classifica-(?:f1|motogp)-|calendario-(?:f1|motogp)-|pilota-(?:f1|motogp)-|piloti-\d|giochi-(?:f1|motogp)-online)[^<]*</loc></url>", "", sm.read_text(encoding="utf-8"))
    nuove = "".join(f"\n  <url><loc>{SITO}/{f}</loc></url>" for f, _ in pagine)
    sm.write_text(s.replace("</urlset>", nuove.lstrip("\n") + "\n</urlset>"), encoding="utf-8")
    print(f"Pagine SEO: {len(pagine)} (piloti F1 {len(f1_piloti)}, piloti MotoGP {len(moto_piloti)})")


if __name__ == "__main__":
    main()
