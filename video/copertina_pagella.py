"""Copertina 'pagella': un foglio di quaderno inclinato con i voti e, sul foglio, la foto dell'uomo del weekend con il voto cerchiato di rosso.
Uso: python copertina_pagella.py f1|motogp uscita.png [--alt chiave_foto] [--righe 5]
I voti vengono da docs/data/pagella.json (build_pagella.py). Testi nella zona sicura TikTok (y 230-1650)."""
import argparse
import asyncio
import json
import re

import notizia_sub as n
from copertina import scatta


def html_pagella(serie, alt=None, quante=5):
    d = json.load(open(n.DATA / "pagella.json"))[serie]
    moto = serie == "motogp"
    col = "#1f5fd1" if moto else "#e8352f"
    righe = d["righe"]
    eroe, altri = righe[0], list(reversed(righe[1:1 + quante]))
    f = n.trova_foto(eroe["nome"], alt)
    autore = re.sub(r"Original:\s*", "", f["autore"])
    cred = f"Foto: {autore} · {f['licenza']} · Wikimedia Commons"
    foto = n.b64(n.file_foto(f))
    logo = n.b64(n.SITO / "img/logo-wide-scuro.png")
    voto = lambda r: str(r["voto"]).replace(".0", "").replace(".", ",")
    cognome = lambda nome: nome.split()[-1].upper() if "Di Giannantonio" not in nome else "DI GIANNANTONIO"
    rr = "".join(f'<div class=r><span>{n.esc(cognome(r["nome"]))}</span><b>{voto(r)}</b></div>' for r in altri)
    gp = d["nome"].replace("Gran Premio di ", "").replace("Gran Premio del ", "").replace("Gran Premio dell'", "").replace("Gran Premio d'", "").replace("GP ", "").upper()
    return f"""<!doctype html><meta charset=utf-8><style>{n.CSS_FONT}
html,body{{margin:0;width:{n.W}px;height:{n.H}px;overflow:hidden;position:relative;background:#0b0b0e;font-family:Inter,sans-serif}}
.bg{{position:absolute;inset:-80px;background:url(data:image/jpeg;base64,{foto}) center 15%/cover no-repeat;filter:blur(30px) brightness(.35)}}
.logo{{position:absolute;left:50px;top:240px;width:190px}}
.carta{{position:absolute;left:90px;top:330px;width:900px;height:1300px;background:#f6f1e3;transform:rotate(-2.2deg);box-shadow:0 40px 90px rgba(0,0,0,.65);
 background-image:repeating-linear-gradient(180deg,transparent 0 69px,rgba(60,90,180,.25) 69px 71px);border-radius:6px}}
.carta:before{{content:"";position:absolute;left:70px;top:0;bottom:0;width:3px;background:rgba(220,60,60,.45)}}
.tit{{position:absolute;left:100px;top:34px;font:700 112px/1 Oswald;text-transform:uppercase;color:#16161b}}
.gp{{position:absolute;left:104px;top:150px;font:700 44px Oswald;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:{col};padding:2px 16px}}
.foto{{position:absolute;left:104px;top:230px;width:430px;height:500px;background:url(data:image/jpeg;base64,{foto}) center 14%/cover;border:12px solid #fff;box-shadow:0 12px 30px rgba(0,0,0,.4);transform:rotate(-2deg)}}
.elenco{{position:absolute;left:100px;top:770px;width:700px}}
.r{{display:flex;justify-content:space-between;align-items:baseline;height:70px;font:700 42px Oswald;text-transform:uppercase;color:#16161b}} .r b{{font-size:48px}}
.sigillo{{position:absolute;right:50px;top:350px;width:320px;height:320px;border:14px solid #d6201a;border-radius:50%;color:#d6201a;font:700 220px/290px Oswald;text-align:center;transform:rotate(-9deg);background:rgba(246,241,227,.85)}}
.nota{{position:absolute;left:100px;bottom:50px;right:50px;font:600 28px Inter;color:#4a4a52;line-height:1.35}}
.cred{{position:absolute;right:40px;bottom:34px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:700px;text-align:right}}
</style><div class=bg></div><img class=logo src="data:image/png;base64,{logo}">
<div class=carta><div class=tit>Pagella</div><div class=gp>{n.esc(gp)}</div>
<div class=foto></div><div class=sigillo>{voto(eroe)}</div>
<div class=elenco>{rr}</div>
<div class=nota><b>Uomo del weekend: {n.esc(eroe["nome"].upper())}.</b> Voti calcolati da GP Oggi sui risultati ufficiali.</div></div>
<div class=cred>{n.esc(cred)}</div>"""


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("serie", choices=["f1", "motogp"]); a.add_argument("uscita")
    a.add_argument("--alt"); a.add_argument("--righe", type=int, default=5)
    x = a.parse_args()
    asyncio.run(scatta(html_pagella(x.serie, x.alt, x.righe), x.uscita))
    print("Fatto:", x.uscita)
