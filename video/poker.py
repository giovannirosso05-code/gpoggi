"""Video lezione «Quando chiamare: la matematica del Texas Hold'em» (16 scene, ~15 minuti), nell'ambiente del gioco: tavolo visto dall'alto,
carte, fiches e lavagna dei calcoli. Il testo del parlato è quello della sceneggiatura (video/poker_testi.json, estratta dal documento).
Uso:  python3 poker.py [--prova N] [--uscita FILE] [--invia]
Una voce, schermate 1920x1080; a ogni frase corrisponde uno stato del tavolo (carte, pot, bet) e righe sulla lavagna che compaiono in sincronia."""
import argparse, asyncio, hashlib, html, json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notizia_sub as NS  # noqa: E402

QUI = Path(__file__).parent
W, H = 1920, 1080
NS.RALLENTA = 1.0
NS.VOCE = "it-IT-IsabellaNeural"
VELOCITA = "+8%"
TESTI = json.load(open(QUI / "poker_testi.json"))

# ---------------------------------------------------------------- parlato
NOMI = {"A": "asso", "K": "re", "Q": "donna", "J": "fante", "T": "dieci", "10": "dieci", "9": "nove", "8": "otto", "7": "sette", "6": "sei", "5": "cinque", "4": "quattro", "3": "tre", "2": "due"}
SEMI = {"♠": "picche", "♥": "cuori", "♦": "quadri", "♣": "fiori"}
TERMINI = [("preflop", "prìflop"), ("river", "rìver"), ("turn", "tern"), ("board", "bòrd"), ("pot", "pòt"), ("bet", "bèt"), ("check", "cèk"), ("call", "còl"), ("raise", "rèiz"),
           ("fold", "fòld"), ("all-in", "òl in"), ("hero", "ìro"), ("villain", "vìllen"), ("draw", "drò"), ("flush", "flàsh"), ("straight", "strèit"), ("open-ended", "òpen èndid"),
           ("gutshot", "gàtscot"), ("outs", "àuts"), ("dirty", "dèrti"), ("equity", "èquiti"), ("odds", "òds"), ("implied", "implàid"), ("overcard", "òvercàrd"),
           ("overpair", "òverpèr"), ("mining", "màining"), ("kicker", "chìcker"), ("dominated", "dòmineitid"), ("hand", "hend"), ("range", "rèinj"), ("showdown", "sciòudaun"),
           ("screenshot", "scrinsciòt"), ("bluff", "blàf"), ("value", "vàliu"), ("pair", "pèr"), ("out", "àut"), ("set", "sèt")]
_RE_CARTA = re.compile(r"(10|[2-9TJQKA])([♠♥♦♣])")
_RE_TERM = re.compile(r"(?<![\w-])(" + "|".join(re.escape(a) for a, _ in sorted(TERMINI, key=lambda x: -len(x[0]))) + r")(?![\w-])", re.I)
_MAP_T = dict(TERMINI)


def parla(t):
    t = re.sub(r"((?:10|[2-9TJQKA])[♠♥♦♣])(?=(?:10|[2-9TJQKA])[♠♥♦♣])", r"\1, ", t)
    t = _RE_CARTA.sub(lambda m: f"{NOMI[m.group(1)]} di {SEMI[m.group(2)]}", t)
    t = re.sub(r"\b([AKQJT2-9])-([AKQJT2-9])\b", lambda m: f"{NOMI[m.group(1)]} {NOMI[m.group(2)]}", t)
    t = re.sub(r"\b(Q|K)\b", lambda m: NOMI[m.group(1)], t)
    t = t.replace("×", " per ").replace("÷", " diviso ").replace("−", " meno ").replace("%", " per cento").replace("≈", " circa ")
    t = re.sub(r"(\d+)-(\d+)", r"\1 o \2", t)
    t = _RE_TERM.sub(lambda m: _MAP_T[m.group(1).lower()], t)
    return re.sub(r"\s+", " ", t).replace(" ,", ",").replace(", .", ".").strip()


# ---------------------------------------------------------------- grafica
SVG_SEME = {
    "h": '<path d="M50 92 C8 60 0 34 18 17 C32 4 46 12 50 28 C54 12 68 4 82 17 C100 34 92 60 50 92Z"/>',
    "d": '<path d="M50 4 L90 50 L50 96 L10 50Z"/>',
    "s": '<path d="M50 6 C10 44 4 68 24 78 C37 84 47 78 50 70 C48 86 42 92 33 96 L67 96 C58 92 52 86 50 70 C53 78 63 84 76 78 C96 68 90 44 50 6Z"/>',
    "c": '<circle cx="50" cy="27" r="22"/><circle cx="28" cy="60" r="22"/><circle cx="72" cy="60" r="22"/><path d="M50 50 C50 78 46 88 36 96 L64 96 C54 88 50 78 50 50Z"/>',
}
SIGLA = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}
COL = {"h": "#d62828", "d": "#d62828", "s": "#16181d", "c": "#16181d"}
COL_SCURO = {"h": "#ff6b6b", "d": "#ff6b6b", "s": "#e9ecf2", "c": "#e9ecf2"}


def seme(s, px=30, col=None):
    return f'<svg viewBox="0 0 100 100" width="{px}" height="{px}" style="vertical-align:-.12em;fill:{col or COL_SCURO[s]}">{SVG_SEME[s]}</svg>'


def rich(t):
    """Testo con le carte come rango + simbolo disegnato (non dipende dai font del computer)."""
    t = html.escape(t, quote=False)
    return _RE_CARTA.sub(lambda m: f'<span class=cs>{m.group(1).replace("T", "10")}{seme(SIGLA[m.group(2)], 26)}</span>', t)


def carta(c, grande=True, evid=False, ipotesi=False, coperta=False, w=120):
    h = int(w * 1.4)
    if coperta:
        return f'<div class="car dorso" style="width:{w}px;height:{h}px"></div>'
    r, s = c[0], c[1]
    rr = "10" if r == "T" else r
    cl = "car" + (" ev" if evid else "") + (" ip" if ipotesi else "")
    return (f'<div class="{cl}" style="width:{w}px;height:{h}px;color:{COL[s]}"><b style="font-size:{int(w * .36)}px">{rr}</b>'
            f'<div class=sm>{seme(s, int(w * .3), COL[s])}</div><div class=gr>{seme(s, int(w * .55), COL[s])}</div></div>')


def fiches(n, col="#c0392b"):
    k = max(1, min(6, n // 25 if n else 1))
    return '<div class=pila>' + "".join(f'<i style="bottom:{i * 9}px;background:{col}"></i>' for i in range(k)) + '</div>'


CSS = f"""{NS.CSS_FONT}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#08130e;color:#f2f4f8;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.top{{position:absolute;left:60px;top:28px;font:700 30px Oswald;letter-spacing:.08em;text-transform:uppercase;color:#9fd8b5}}
.top span{{color:#f5b301}}
.bar{{position:absolute;left:0;bottom:0;height:8px;background:#f5b301}}
.cs{{display:inline-block;white-space:nowrap;font-weight:700}}
.tav{{position:absolute;left:50px;top:90px;width:1240px;height:740px}}
.felt{{position:absolute;left:0;top:30px;width:1240px;height:680px;border-radius:340px;border:16px solid #5a3a1e;background:radial-gradient(ellipse at center,#14794a 0%,#0d5a37 70%,#0a4a2d 100%);box-shadow:0 20px 60px rgba(0,0,0,.6) inset}}
.car{{position:absolute;background:#fbfbf6;border-radius:12px;box-shadow:0 6px 16px rgba(0,0,0,.5);font-family:Oswald;padding:8px 10px}}
.car b{{display:block;line-height:1}} .car .sm{{margin-top:2px}} .car .gr{{position:absolute;right:10px;bottom:8px;opacity:.9}}
.dorso{{background:repeating-linear-gradient(45deg,#1b3a8a 0 8px,#274bb0 8px 16px);border:5px solid #fbfbf6}}
.ev{{outline:5px solid #f5b301;box-shadow:0 0 28px #f5b301}} .ip{{border:4px dashed #f5b301;opacity:.95}}
.slot{{position:absolute;border:3px dashed rgba(255,255,255,.25);border-radius:12px}}
.eti{{position:absolute;font:700 30px Oswald;letter-spacing:.12em;color:rgba(255,255,255,.75)}}
.pila{{position:relative;width:70px;height:60px;display:inline-block}} .pila i{{position:absolute;left:0;width:70px;height:18px;border-radius:50%;border:4px dashed #fff;box-shadow:0 3px 0 rgba(0,0,0,.4)}}
.pot,.bet{{position:absolute;text-align:center;font:700 40px Oswald}} .pot small,.bet small{{display:block;font:700 24px Oswald;letter-spacing:.12em;color:#ffe9a8}}
.lav{{position:absolute;left:1330px;top:100px;width:540px;height:730px;background:#17292b;border:14px solid #5a3a1e;border-radius:10px;padding:22px 26px;box-shadow:0 8px 30px rgba(0,0,0,.5)}}
.lav h3{{margin:0 0 14px;font:700 24px Oswald;letter-spacing:.18em;color:#8fb7b0;text-transform:uppercase}}
.lav p{{margin:0 0 14px;font:700 38px/1.15 Oswald;letter-spacing:.01em}}
.w{{color:#f2f4f8}} .g{{color:#52e08a}} .r{{color:#ff6b6b}} .y{{color:#ffd24a}} .b{{color:#7fb8ff}}
.sov{{position:absolute;left:60px;right:60px;bottom:50px;min-height:150px;display:flex;flex-direction:column;justify-content:flex-end;gap:8px}}
.sov div{{font:700 46px/1.1 Oswald;color:#ffd24a;background:rgba(0,0,0,.55);padding:6px 18px;border-radius:10px;width:fit-content;max-width:100%}}
.sov div em{{font-style:normal;color:#fff}}
.tab{{position:absolute;left:120px;right:120px;top:100px}}
.tab h2{{margin:0 0 14px;font:700 50px Oswald;color:#f5b301;text-transform:uppercase}}
.tab table{{border-collapse:collapse;width:100%;font:500 30px Inter}} .tab th{{text-align:left;font:700 26px Oswald;letter-spacing:.1em;color:#9fd8b5;text-transform:uppercase;padding:8px 16px;border-bottom:3px solid #2a4a3a}}
.tab td{{padding:9px 16px;border-bottom:2px solid #1f3a2d}} .tab td.n{{font:700 40px Oswald;color:#ffd24a}} .tab tr.nuova td{{background:rgba(245,179,1,.14)}}
.glos{{position:absolute;left:100px;right:100px;top:110px;display:grid;grid-template-columns:1fr 1fr;gap:12px 28px}}
.glos.cp{{gap:6px 24px;top:100px}} .glos.cp div{{padding:3px 12px;border-left-width:6px}} .glos.cp b{{font-size:21px;line-height:1.05}} .glos.cp span{{font-size:16px;line-height:1.1}}
.glos div{{background:#10281d;border-left:8px solid #2a8a5a;border-radius:10px;padding:10px 18px}} .glos div.nuova{{border-left-color:#f5b301;background:#1a3a28}}
.glos b{{display:block;font:700 34px Oswald;color:#ffd24a;letter-spacing:.04em;text-transform:uppercase}} .glos span{{font:500 25px/1.2 Inter;color:#dfe8e2}}
.bil{{position:absolute;left:0;right:0;top:140px;text-align:center}}
.verdetto{{font:700 150px Oswald;letter-spacing:.06em;margin-top:10px}}
.barre{{position:absolute;left:120px;right:120px;top:140px}} .riga{{margin-bottom:46px}}
.riga .mani{{display:flex;align-items:center;gap:30px;font:700 40px Oswald}} .riga .mani .car{{position:relative}} .riga .mani>div{{position:relative;width:84px;height:118px}}
.barra{{display:flex;height:56px;border-radius:12px;overflow:hidden;margin-top:14px;font:700 36px Oswald}} .barra i{{display:flex;align-items:center;justify-content:center;font-style:normal}}
.cart{{position:absolute;left:120px;right:120px;top:130px;display:grid;grid-template-columns:1fr 1fr;gap:28px}}
.cart div{{background:#8a1c1c;border-radius:18px;padding:30px 34px;font:700 56px/1.1 Oswald;display:flex;gap:26px;align-items:center;min-height:270px}} .cart div i{{font-style:normal;background:#fff;color:#8a1c1c;border-radius:50%;width:84px;height:84px;display:flex;align-items:center;justify-content:center;font-size:56px;flex:none}}
.sch{{position:absolute;left:100px;right:100px;top:100px}} .sch ol{{margin:0 0 18px;padding-left:46px;font:700 46px/1.25 Oswald}} .sch li{{margin-bottom:6px}}
.dos{{display:flex;gap:30px}} .dos table{{flex:1;border-collapse:collapse;font:500 30px Inter}} .dos th{{font:700 22px Oswald;letter-spacing:.1em;color:#9fd8b5;text-align:left;padding:5px 10px;border-bottom:2px solid #2a4a3a}} .dos td{{padding:6px 10px;border-bottom:1px solid #1f3a2d}} .dos td:last-child{{font:700 32px Oswald;color:#ffd24a}}
.fin{{position:absolute;inset:0;background:#000;text-align:center;padding-top:130px}} .fin .d18{{font:700 220px Oswald;color:#ff6b6b;line-height:1}}
.fin h1{{font:700 74px Oswald;margin:10px 0 28px;color:#fff;letter-spacing:.05em}} .fin p{{font:500 40px/1.3 Inter;margin:0 140px 20px;color:#dfe8e2}} .fin .num{{font:700 100px Oswald;color:#ffd24a;margin-top:26px}}
.mazzo{{position:absolute;left:50px;top:100px;width:1240px;display:grid;grid-template-columns:repeat(13,1fr);gap:7px}}
.mazzo div{{background:#fbfbf6;border-radius:8px;height:128px;padding:6px 4px;text-align:center;font:700 34px Oswald}} .mazzo div svg{{display:block;margin:6px auto 0}}
.mazzo div.k{{opacity:.18;filter:grayscale(1)}} .mazzo div.o{{outline:5px solid #f5b301;box-shadow:0 0 22px #f5b301;transform:translateY(-6px)}}
.comb{{position:absolute;left:60px;right:60px;top:90px;display:grid;grid-template-columns:1fr 1fr;gap:6px 40px}} .comb>div{{display:flex;align-items:center;gap:18px;height:146px;background:#0f2419;border-radius:12px;padding:0 16px}}
.comb>div.nuova{{background:#1a3a28;outline:3px solid #f5b301}} .comb .c5{{display:flex;gap:6px;width:390px;height:98px}}
.comb>div>b{{font:700 34px/1.05 Oswald;color:#ffd24a;text-transform:uppercase}} .comb>div>b>span{{display:block;font:500 22px Inter;color:#cfe0d6;text-transform:none;margin-top:4px}}
.pausa{{position:absolute;left:1330px;top:100px;width:540px;height:730px;background:#222;border:14px solid #5a3a1e;border-radius:10px;display:flex;align-items:center;justify-content:center;font:700 120px Oswald;color:#ff6b6b;letter-spacing:.1em}}
"""


def pagina(st, titolo, prog):
    """Pagina HTML 1920x1080 per lo stato `st` (dizionario)."""
    modo = st.get("modo", "tavolo")
    corpo = ""
    if modo == "tavolo":
        felt = '<div class=felt></div>'
        vil = st.get("vil", "x")
        if vil == "x":
            c = "".join(f'<div style="position:absolute;left:{i * 105}px;top:0">{carta("", coperta=True, w=100)}</div>' for i in range(2))
            felt += f'<div style="position:absolute;left:545px;top:8px">{c}</div>'
        elif vil:
            c = "".join(f'<div style="position:absolute;left:{i * 105}px;top:0">{carta(x, ipotesi=True, w=100)}</div>' for i, x in enumerate(vil))
            felt += f'<div style="position:absolute;left:545px;top:8px">{c}</div>'
        felt += '<div class=eti style="left:380px;top:50px">VILLAIN</div><div class=eti style="left:380px;top:620px">HERO</div>'
        board = st.get("board", [])
        ev = set(st.get("ev", []))
        for i in range(5):
            x = 290 + i * 135
            felt += (f'<div style="position:absolute;left:{x}px;top:240px">{carta(board[i], evid=board[i] in ev)}</div>' if i < len(board)
                     else f'<div class=slot style="left:{x}px;top:240px;width:120px;height:168px"></div>')
        felt += "".join(f'<div style="position:absolute;left:{500 + i * 135}px;top:520px">{carta(c, evid=c in ev, w=125)}</div>' for i, c in enumerate(st.get("hero", [])))
        if st.get("pot") is not None:
            felt += f'<div class=pot style="left:250px;top:470px;width:200px">{fiches(st["pot"], "#1d6fb8")}<small>POT</small>{st["pot"]}</div>'
        elif st.get("pot_t"):
            felt += f'<div class=pot style="left:250px;top:470px;width:200px"><small>POT</small>{html.escape(st["pot_t"])}</div>'
        if st.get("bet") is not None:
            felt += f'<div class=bet style="left:830px;top:110px;width:200px">{fiches(st["bet"], "#c0392b")}<small>{st.get("bet_t", "BET")}</small>{st["bet"]}</div>'
        if st.get("stack"):
            felt += f'<div class=bet style="left:830px;top:330px;width:240px"><small>STACK VILLAIN</small>{st["stack"]}</div>'
        corpo += f'<div class=tav>{felt}</div>'
        if st.get("pausa"):
            corpo += '<div class=pausa>PAUSA</div>'
        else:
            righe = "".join(f'<p class="{c}">{rich(t)}</p>' for t, c in st.get("lav", []))
            corpo += f'<div class=lav><h3>Lavagna</h3>{righe}</div>'
    elif modo == "mazzo":
        known = set(st.get("known", [])); outs = set(st.get("outs", []))
        g = ""
        for se in "hdsc":
            for r in "AKQJT98765432":
                c = r + se
                cl = "k" if c in known else ("o" if c in outs else "")
                g += f'<div class="{cl}" style="color:{COL[se]}">{"10" if r == "T" else r}{seme(se, 34, COL[se])}</div>'
        corpo += f'<div class=mazzo>{g}</div>'
        righe = "".join(f'<p class="{c}">{rich(t)}</p>' for t, c in st.get("lav", []))
        corpo += f'<div class=lav style="top:100px"><h3>Lavagna</h3>{righe}</div>'
    elif modo == "mani":
        g = ""
        for i, (nome, note, cs) in enumerate(st["righe"][:st["n"]]):
            g += (f'<div class="{"nuova" if i == st["n"] - 1 else ""}"><div class=c5>' + "".join(f'<div style="position:relative;width:70px;height:98px">{carta(c, w=70)}</div>' for c in cs)
                  + f'</div><b>{html.escape(nome)}<span>{html.escape(note)}</span></b></div>')
        corpo += f'<div class=comb>{g}</div>'
    elif modo == "tabella":
        corpo += f'<div class=tab><h2>{html.escape(st["titolo"])}</h2><table><tr>' + "".join(f"<th>{html.escape(h)}</th>" for h in st["testa"]) + "</tr>"
        for i, r in enumerate(st["righe"][:st["n"]]):
            corpo += f'<tr class="{"nuova" if i == st["n"] - 1 else ""}">' + "".join(f'<td class="{"n" if j == len(r) - 1 else ""}">{rich(c)}</td>' for j, c in enumerate(r)) + "</tr>"
        corpo += "</table></div>"
    elif modo == "glossario":
        corpo += f'<div class="glos{" cp" if st.get("tutti") else ""}">' + "".join(f'<div class="{"nuova" if i == st["n"] - 1 and not st.get("tutti") else ""}"><b>{html.escape(a)}</b><span>{rich(b)}</span></div>' for i, (a, b) in enumerate(st["voci"][:st["n"]])) + "</div>"
    elif modo == "bilancia":
        ang = {"sx": -11, "dx": 11}.get(st.get("incl"), 0)
        corpo += (f'<div class=bil><svg width="1000" height="420" viewBox="0 0 1000 420"><g transform="rotate({ang} 500 120)"><rect x="100" y="112" width="800" height="16" rx="8" fill="#c9a66b"/>'
                  '<rect x="120" y="128" width="6" height="110" fill="#c9a66b"/><rect x="874" y="128" width="6" height="110" fill="#c9a66b"/>'
                  '<rect x="30" y="236" width="220" height="14" rx="7" fill="#c9a66b"/><rect x="750" y="236" width="220" height="14" rx="7" fill="#c9a66b"/>'
                  '<text x="140" y="290" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="34" fill="#52e08a">LA MIA EQUITY</text>'
                  '<text x="860" y="290" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="34" fill="#ff6b6b">EQUITY RICHIESTA</text></g>'
                  '<polygon points="500,128 440,360 560,360" fill="#8a6a3a"/></svg>'
                  + (f'<div class=verdetto style="color:{"#52e08a" if st["incl"] == "sx" else "#ff6b6b"}">{"CALL" if st["incl"] == "sx" else "FOLD"}</div>' if st.get("incl") else "") + "</div>")
    elif modo == "barre":
        h_ = ""
        for hh, vv, pc in st["righe"][:st["n"]]:
            ca = "".join(f'<div style="position:relative;width:84px;height:118px">{carta(c, w=84)}</div>' for c in hh); cb = "".join(f'<div style="position:relative;width:84px;height:118px">{carta(c, w=84)}</div>' for c in vv)
            h_ += (f'<div class=riga><div class=mani>{ca}<span>contro</span>{cb}</div><div class=barra><i style="width:{pc}%;background:#2f9e5f">{pc}%</i>'
                   f'<i style="width:{100 - pc}%;background:#b83a3a">{100 - pc}%</i></div></div>')
        corpo += f'<div class=barre>{h_}</div>'
    elif modo == "cartelli":
        corpo += '<div class=cart>' + "".join(f'<div><i>{i + 1}</i><span>{rich(t)}</span></div>' for i, t in enumerate(st["testi"][:st["n"]])) + "</div>"
    elif modo == "scheda":
        passi = "".join(f"<li>{rich(p)}</li>" for p in st["passi"][:st["n"]])
        t1 = t2 = ""
        if st.get("tabelle"):
            t1 = '<table><tr><th>Progetto</th><th>Outs</th></tr>' + "".join(f"<tr><td>{rich(a)}</td><td>{b}</td></tr>" for a, b in OUTS_BREVE) + "</table>"
            t2 = '<table><tr><th>Bet</th><th>Equity richiesta</th></tr>' + "".join(f"<tr><td>{rich(a)}</td><td>{b}</td></tr>" for a, b in ODDS_BREVE) + "</table>"
        corpo += f'<div class=sch><ol>{passi}</ol><div class=dos>{t1}{t2}</div></div>'
    elif modo == "chiusura":
        corpo += ('<div class=fin><div class=d18>18+</div><h1>GIOCA RESPONSABILMENTE</h1>'
                  '<p>La matematica riduce gli errori ma non elimina la varianza.</p><p>Gioca solo con soldi che puoi permetterti di perdere. Il poker è vietato ai minori di 18 anni.</p>'
                  '<div class=num>800 940 789</div><p>Numero verde unico dipendenze · Istituto Superiore di Sanità · gratuito e anonimo</p></div>')
    sov = "".join(f"<div>{rich(t)}</div>" for t in st.get("sov", [])[-3:])
    if modo not in ("chiusura",):
        corpo += f'<div class=sov>{sov}</div>'
    return (f'<!doctype html><meta charset=utf-8><style>{CSS}</style><div class=top>Texas Hold\'em · <span>{html.escape(titolo)}</span></div>'
            f'{corpo}<div class=bar style="width:{prog * 100:.1f}%"></div>')


OUTS_BREVE = [("Flush draw", "9"), ("Open-ended", "8"), ("Gutshot", "4"), ("Due overcard", "6"), ("Coppia → set", "2"), ("Flush draw + open-ended", "15")]
ODDS_BREVE = [("1/3 del pot", "20%"), ("1/2 del pot", "25%"), ("2/3 del pot", "28,6%"), ("Pot pieno", "33,3%"), ("2 volte il pot", "40%")]
TAB_OUTS = (["Progetto", "Esempio (mano · board)", "Outs"], [["Flush draw", "9♥8♥ · K♥7♥2♣", "9"], ["Open-ended straight draw", "9♠8♦ · 7♣6♥2♠ (servono 10 o 5)", "8"],
            ["Gutshot", "9♠8♦ · 6♣5♥2♠ (serve un 7)", "4"], ["Due overcard", "A♠K♦ · 9♣6♥2♠", "6"], ["Coppia che cerca il set", "5♣5♦ · K♥9♠2♣", "2"],
            ["Flush draw + open-ended", "J♠T♠ · 9♠8♠2♦", "15"]])
TAB_EQUITY = (["Outs", "× 2 (una carta)", "Esatto turn→river", "× 4 (solo all-in)", "Esatto flop→river"], [["4 (gutshot)", "8%", "8,7%", "16%", "16,5%"], ["8 (open-ended)", "16%", "17,4%", "32%", "31,5%"],
              ["9 (flush draw)", "18%", "19,6%", "36% − 1 = 35%", "35,0%"], ["15 (combo draw)", "30%", "32,6%", "60% − 7 = 53%", "54,1%"]])
TAB_ODDS = (["Bet del villain", "Esempio (pot 100)", "Equity richiesta"], [["1/3 del pot", "bet 33 → 33 ÷ 166", "20%"], ["1/2 del pot", "bet 50 → 50 ÷ 200", "25%"],
            ["2/3 del pot", "bet 67 → 67 ÷ 234", "28,6%"], ["Pot pieno", "bet 100 → 100 ÷ 300", "33,3%"], ["2 volte il pot", "bet 200 → 200 ÷ 500", "40%"]])
GLOS_RAPIDO = [("PREFLOP", "prima delle carte comuni"), ("FLOP", "prime 3 carte comuni"), ("TURN", "4ª carta comune"), ("RIVER", "5ª carta comune"), ("BOARD", "carte comuni sul tavolo"), ("POT", "il piatto"),
               ("BET", "puntare"), ("CHECK", "passare"), ("CALL", "pareggiare"), ("RAISE", "rilanciare"), ("FOLD", "abbandonare"), ("ALL-IN", "puntare tutto"), ("HERO", "tu"), ("VILLAIN", "l'avversario")]
GLOS_COMPLETO = [("Preflop / Flop / Turn / River", "le fasi: prima delle carte comuni, le prime 3, la 4ª, la 5ª"), ("Board", "le carte comuni scoperte"), ("Pot", "il piatto, le fiches in palio"),
                 ("Bet / Check / Call / Raise / Fold", "puntare / passare / pareggiare / rilanciare / abbandonare"), ("All-in", "puntare tutte le proprie fiches"), ("Hero / Villain", "chi decide (tu) / l'avversario"),
                 ("Draw", "progetto: mano incompleta che può migliorare"), ("Flush draw / Straight draw", "progetto di colore / di scala"), ("Open-ended / Gutshot", "scala aperta da due lati (8 outs) / interna (4 outs)"),
                 ("Outs", "carte nel mazzo che migliorano la tua mano"), ("Dirty outs", "outs che possono dare all'avversario una mano migliore"), ("Equity", "% di volte che vinci la mano se si arriva in fondo"),
                 ("Pot odds", "% minima di vittoria che ti serve per chiamare"), ("Implied odds", "fiches extra che vincerai dopo, se centri"), ("Overcard", "carta più alta di quelle sul board"),
                 ("Overpair", "coppia in mano più alta di tutte le carte del board"), ("Set / Set mining", "tris con coppia in mano / chiamare per fare set"), ("Kicker", "carta laterale che decide a parità di coppia"),
                 ("Dominated hand", "mano dominata: stessa carta alta, l'altra peggiore"), ("Top pair", "coppia con la carta più alta del board"), ("Bluff / Value bet", "puntare senza mano per far foldare / puntare forte per farsi pagare"), ("Blind / Stack", "puntata obbligatoria iniziale / le fiches davanti a te"), ("Range", "tutte le mani che l'avversario può avere"), ("Showdown", "quando si scoprono le carte a fine mano"),
                 ("Varianza", "la fortuna nel breve periodo")]

# ---------------------------------------------------------------- scene: stati per frase
# Per le scene da tavolo: base + extra (da frase i in poi), lav = righe della lavagna (da frase i), sov = sovrimpressioni (da frase i).
B1 = ["9h", "8h"]; BD = ["Kh", "7h", "2c", "4s"]


def T(base, lav=(), sov=(), extra=()):
    return dict(modo="tavolo", base=base, lav=list(lav), sov=list(sov), extra=list(extra))


SCENE = {
    1: T(dict(hero=[], board=[], pot=None, bet=None), extra=[(0, dict(hero=B1)), (1, dict(board=BD)), (3, dict(pot=100, bet=50))], lav=[(4, "?", "y")], sov=[(4, "Chiami o lasci?")]),
    3: None,  # composta sotto
    4: T(dict(hero=B1, board=BD, pot=None, bet=None, ev=["Kh", "7h", "9h", "8h"]), lav=[(3, "52 − 2 − 4 = 46", "w"), (5, "9 ÷ 46 = 19,6%", "y"), (8, "1 carta → × 2", "b"), (9, "9 × 2 = 18% (esatto 19,6%)", "y"),
                                                                                   (10, "2 carte, solo all-in → × 4", "b"), (16, "15 × 4 = 60 → 60 − 7 = 53%", "y"), (17, "esatto 54%", "g")],
         sov=[(1, "EQUITY = % di volte che vinci la mano"), (8, "Una carta da vedere → outs × 2"), (10, "Due carte, solo se ALL-IN → outs × 4"), (14, "Più di 8 outs → togli (outs − 8)")]),
    7: T(dict(hero=B1, board=BD, pot=100, bet=50), lav=[(3, "1) OUTS: 9 cuori", "w"), (6, "2) EQUITY: 9 × 2 = 18% (esatto 19,6%)", "y"), (8, "3) POT ODDS: 50 ÷ 200 = 25%", "b"), (9, "4) 19,6% < 25% → FOLD", "r")],
         sov=[(10, "19,6% < 25% → FOLD")]),
    8: T(dict(hero=B1, board=BD, pot=100, bet=25), lav=[(3, "Equity: 19,6%", "y"), (4, "Pot odds: 25 ÷ 150 = 16,7%", "b"), (5, "19,6% > 16,7% → CALL", "g")], sov=[(7, "Stessa mano, bet diversa → decisione diversa")]),
    9: T(dict(hero=["Js", "Ts"], board=["9s", "8s", "2d"], pot=100, bet=100, bet_t="ALL-IN", vil="x"), extra=[(4, dict(vil=["Ad", "Ac"])), (19, dict(vil=["9d", "9c"]))],
         lav=[(5, "9 picche (flush draw)", "w"), (8, "6 carte per la scala (Q o 7)", "w"), (9, "9 + 6 = 15 outs", "y"), (11, "15 × 4 = 60", "w"), (13, "60 − (15 − 8) = 53%", "y"), (14, "esatto ~54%", "g"), (15, "Pot odds: 100 ÷ 300 = 33,3%", "b"), (16, "54% > 33,3% → CALL", "g")],
         sov=[(10, "All-in sul flop → × 4"), (16, "54% > 33,3% → CALL (e sei favorito)")]),
    11: None,
    12: T(dict(hero=["5c", "5d"], board=[], pot=None, bet=30, bet_t="RILANCIO", stack="1000"), lav=[(4, "Set al flop: circa 12% (1 volta su 8,5)", "w"), (7, "7,5 × 30 = circa 225 fiches", "r"), (8, "Pareggio: vincere 225 in più", "y"), (12, "1000 ÷ 30 ≈ 33 volte > 15-20 → CALL", "g")],
          sov=[(0, "IMPLIED ODDS = fiches che vincerai dopo, se centri"), (1, "SET MINING = chiamare con coppia piccola per fare set"), (10, "Regola pratica: fiches vincibili ≥ 15-20 × il call")]),
}
SOV3 = [(0, "OUTS = carte che migliorano la tua mano"), (3, "DRAW = progetto · FLUSH DRAW = progetto di colore"), (11, "STRAIGHT DRAW = progetto di scala"), (12, "OPEN-ENDED = scala aperta da due lati"), (13, "GUTSHOT = scala interna"),
        (14, "OVERCARD = carta più alta del board"), (16, "SET = tris con coppia in mano"), (17, "DIRTY OUTS = outs che possono aiutare anche l'avversario")]


def stato(n, i, nfr):
    """Stato (dizionario) della scena n alla frase i."""
    if n == 2:
        rev = [(4, 1), (5, 2), (6, 3), (7, 4), (8, 5), (9, 6), (11, 7), (12, 8), (13, 9), (14, 10), (15, 11), (16, 12), (17, 14)]
        k = max([c for f, c in rev if f <= i] or [0])
        sov = [f"{GLOS_RAPIDO[k - 1][0]} = {GLOS_RAPIDO[k - 1][1]}"] if k else []
        return dict(modo="glossario", voci=GLOS_RAPIDO, n=max(k, 1) if k else 0, sov=sov)
    if n == 3:
        if i <= 9:
            lav = [t for f, t in [(5, ("13 cuori − 4 visibili", "w")), (8, ("13 − 4 = 9", "y")), (9, ("9 OUTS", "g"))] if f <= i]
            return dict(modo="tavolo", hero=B1, board=BD, pot=None, bet=None, ev=["Kh", "7h", "9h", "8h"], lav=lav, sov=[t for f, t in SOV3 if f <= i])
        rev = [(10, 1), (12, 2), (13, 3), (15, 4), (16, 5)]
        k = max([c for f, c in rev if f <= i] or [1])
        return dict(modo="tabella", titolo="Gli outs dei progetti più comuni", testa=TAB_OUTS[0], righe=TAB_OUTS[1], n=k if i < 17 else 6, sov=[t for f, t in SOV3 if f <= i])
    if n == 5:
        if i <= 10:
            lav = [t for f, t in [(4, ("call ÷ (pot + bet + call)", "w")), (8, ("100 + 50 + 50 = 200", "y")), (9, ("50 ÷ 200 = 25%", "g"))] if f <= i]
            return dict(modo="tavolo", hero=B1, board=BD, pot=100, bet=50, lav=lav,
                        sov=[t for f, t in [(2, "POT ODDS = % minima di vittoria che ti serve per chiamare"), (4, "Equity richiesta = call ÷ (pot + bet + call)")] if f <= i])
        return dict(modo="tabella", titolo="Le pot odds dei cinque casi più comuni", testa=TAB_ODDS[0], righe=TAB_ODDS[1], n=5 if i >= 12 else 1, sov=["Più grande la bet, più equity ti serve"])
    if n == 6:
        incl = {2: "sx", 3: "dx"}.get(i) if i in (2, 3) else None
        sov = ["EQUITY > EQUITY RICHIESTA → CALL · altrimenti → FOLD"] if i >= 2 else []
        return dict(modo="bilancia", incl=incl, sov=sov)
    if n == 10:
        if i <= 11:
            lav = [t for f, t in [(5, ("4 outs (un 10)", "w")), (8, ("4 × 2 = 8% (esatto 8,5%)", "y")), (10, ("60 ÷ 210 = 28,6%", "b")), (11, ("8% < 28,6% → FOLD", "r"))] if f <= i]
            return dict(modo="tavolo", hero=["9c", "8d"], board=["Jh", "7s", "2c"], pot=90, bet=60, lav=lav, ev=["7s"])
        lav = [t for f, t in [(14, ("8 outs (Q o 7)", "w")), (15, ("8 × 4 = 32%  ✗", "r")), (19, ("8 × 2 = 16% (esatto 17%)", "y")), (20, ("17% < 28,6% → FOLD", "r"))] if f <= i]
        return dict(modo="tavolo", hero=["9c", "8d"], board=["Jh", "Ts", "2c"], pot=90, bet=60, lav=lav, ev=["Ts"], sov=["NON sei all-in? → × 2, mai × 4"] if i >= 17 else [])
    if n == 11:
        if i <= 6:
            k = {0: 0, 1: 0}.get(i, 3 if i >= 6 else (2 if i >= 4 else 1))
            k = 1 if i == 2 else (2 if i == 3 else (3 if i >= 4 else 0))
            righe = [(["7s", "7h"], ["Ad", "Kc"], 55), (["Ks", "Kh"], ["Qd", "Qc"], 82), (["Ac", "Qh"], ["As", "Kd"], 25)]
            sov = [t for f, t in [(3, "OVERPAIR = coppia più alta"), (4, "DOMINATED HAND = stessa carta alta, l'altra peggiore"), (5, "KICKER = carta laterale che decide a parità di coppia")] if f <= i]
            return dict(modo="barre", righe=righe, n=k, sov=sov)
        lav = [t for f, t in [(8, ("Call 400, pot 200", "w")), (10, ("200 + 400 + 400 = 1000", "y")), (11, ("400 ÷ 1000 = 40%", "g")), (12, ("vs A-K: 55% > 40% → CALL", "g")), (13, ("vs Q-Q: ~20% < 40% → FOLD", "r"))] if f <= i]
        vil = ["Ad", "Kc"] if i == 12 else (["Qd", "Qc"] if i == 13 else "x")
        return dict(modo="tavolo", hero=["7s", "7h"], board=[], pot=200, bet=400, bet_t="ALL-IN", vil=vil, lav=lav, sov=["RANGE = tutte le mani che l'avversario può avere"] if i >= 15 else [])
    if n == 13:
        testi = ["× 4 solo all-in", "Dirty outs = outs a metà", "Guarda la bet, non solo le tue carte", "Pensa al range, non a una mano"]
        k = 1 if i >= 1 else 0
        k = 2 if i >= 3 else k
        k = 3 if i >= 5 else k
        k = 4 if i >= 7 else k
        return dict(modo="cartelli", testi=testi, n=k)
    if n == 14:
        passi = ["Conta gli outs", "Equity: outs × 2 (una carta) · × 4 (solo all-in)", "Equity richiesta = call ÷ (pot + bet + call)", "Equity > richiesta → CALL · altrimenti → FOLD"]
        k = min(4, i)
        return dict(modo="scheda", passi=passi, n=k, tabelle=i >= 5)
    if n == 16:
        return dict(modo="glossario", voci=GLOS_COMPLETO, n=len(GLOS_COMPLETO), tutti=True, sov=["Salva questa schermata"]) if i == 0 else dict(modo="chiusura")
    s = SCENE[n]
    base = dict(s["base"])
    for f, e in s["extra"]:
        if f <= i:
            base.update(e)
    base["lav"] = [(t, c) for f, t, c in s["lav"] if f <= i]
    base["sov"] = [t for f, t in s["sov"] if f <= i]
    base["modo"] = "tavolo"
    return base


# ---------------------------------------------------------------- beat
def beats():
    """[(titolo scena, stato, parlato, pausa_dopo, silenzio_s)]"""
    out = []
    for sc in TESTI["scene"]:
        n, titolo, fr = sc["n"], sc["titolo"], sc["frasi"]
        tit = re.sub(r"^Scena[e]? [\d\-]+ — ", "", titolo)
        if n == 15:
            out.append((tit, dict(modo="tavolo", hero=[], board=[], pot=None, bet=None, sov=["Tocca a te"]), parla(" ".join(fr[:2])), 0.6, 0))
            ties = [(["Qc", "Jd"], ["Ts", "9h", "3c", "2d"], 100, 100), (["7d", "6d"], ["Qd", "Jd", "3c", "2s"], 200, 50), (["8c", "7c"], ["Ac", "Jc", "4h"], 100, 50)]
            for q, (hh, bb, pot, bet) in zip(TESTI["quiz"], ties):
                base = dict(modo="tavolo", hero=hh, board=bb, pot=pot, bet=bet)
                out.append((tit, dict(base, sov=["Metti in pausa e decidi: CALL o FOLD?"]), parla("Domanda. " + q["d"].replace("(turn)", "al turn").replace("(flop)", "al flop")), 0.4, 0))
                out.append((tit, dict(base, pausa=True, sov=["Metti in pausa e decidi: CALL o FOLD?"]), "", 0, 6.0))
                sol = q["s"].replace("Soluzione: ", "")
                righe = [(x.strip(), "y") for x in re.split(r"(?<=[.])\s+", sol) if x.strip()]
                righe = [(t, "g" if t.startswith("CALL") else ("r" if t.startswith("FOLD") else c)) for t, c in righe]
                out.append((tit, dict(base, lav=righe, sov=["Soluzione"]), parla("Soluzione. " + sol), 0.9, 0))
            out.append((tit, dict(modo="tavolo", hero=[], board=[], pot=None, bet=None), parla(fr[2]), 1.2, 0))
            continue
        for i, f in enumerate(fr):
            st = stato(n, i, len(fr))
            fine = i == len(fr) - 1
            out.append((tit, st, parla(f), 1.4 if fine else 0.35, 0))
    return out


def durata(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout or 0)


async def genera(uscita, prova=None, bt=None):
    from playwright.async_api import async_playwright
    bt = bt or beats()
    if prova:
        bt = bt[:prova]
    lav = QUI / "_cache" / "poker"; lav.mkdir(parents=True, exist_ok=True)
    tot = len(bt); print(f"{tot} battute", flush=True)
    segmenti, capitoli, t, ult = [], [], 0.0, None
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        for i, (tit, st, testo, pausa, silenzio) in enumerate(bt):
            h = hashlib.sha1(f"{testo}|{json.dumps(st, sort_keys=True, default=str)}|{tit}|{NS.VOCE}".encode()).hexdigest()[:12]
            mp3, png, seg = lav / f"{h}.mp3", lav / f"{h}.png", lav / f"{h}_{int(pausa * 100)}.mp4"
            if not seg.exists():
                if silenzio or not testo:
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{silenzio or 1:.2f}", str(mp3)], check=True)
                elif not mp3.exists():
                    if os.environ.get("POKER_SENZA_VOCE"):
                        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{max(1.0, len(testo.split()) / 2.7):.2f}", str(mp3)], check=True)
                    else:
                        await NS.voce(testo, VELOCITA, mp3)
                await pg.set_content(pagina(st, tit, (i + 1) / tot)); await pg.wait_for_timeout(60)
                await pg.screenshot(path=str(png))
                d = durata(mp3) + pausa
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "1", "-i", str(png), "-i", str(mp3), "-af", f"apad=pad_dur={pausa}", "-t", f"{d:.2f}",
                                "-vf", "scale=1600:900,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage", "-crf", "30", "-r", "2", "-g", "20", "-c:a", "aac", "-b:a", "80k", "-ar", "24000", "-ac", "1", str(seg)], check=True)
            if tit != ult:
                capitoli.append((t, tit)); ult = tit
            t += durata(seg); segmenti.append(seg)
            if i % 25 == 0:
                print(f"  {i}/{tot}  {t / 60:.1f} min", flush=True)
        await b.close()
    lista = lav / "lista.txt"
    lista.write_text("".join(f"file '{s}'\n" for s in segmenti))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(uscita)], check=True)
    cap = "\n".join(f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d} {nome}" for s, nome in capitoli)
    Path(uscita).with_suffix(".capitoli.txt").write_text(cap + "\n")
    print(f"Fatto: {uscita} ({t / 60:.1f} min)\n{cap}")
    return capitoli


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", type=int); ap.add_argument("--uscita", type=Path, default=QUI / "poker.mp4"); ap.add_argument("--invia", action="store_true"); ap.add_argument("--corso", action="store_true")
    a = ap.parse_args()
    bt = None
    if a.corso:
        import poker_corso as PC
        bt = PC.beats_corso()
    cap = asyncio.run(genera(a.uscita, a.prova, bt))
    if a.invia and not a.prova:
        import lezione as L
        L.invia_telegram(a.uscita, cap, "Quando chiamare: il corso completo (da zero)" if a.corso else "Quando chiamare: la matematica del Texas Hold'em", prefisso="🃏 ")


if __name__ == "__main__":
    main()
