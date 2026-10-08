"""Copertina (1080x1920, formato TikTok) con 2-3 foto affiancate in diagonale, titolo grande e logo.

  python3 copertina.py spec.json uscita.png

spec.json:
{ "serie": "F1" | "MotoGP", "etichetta": "ULTIM'ORA", "titolo": ["FERRARI A SINGAPORE:", "È IL MOMENTO?"], "evidenzia": 1 (riga del titolo in giallo, opzionale),
  "sottotitolo": "Non vince da 7 gare",
  "foto": [ {"file": "percorso.jpg", "credito": "Foto: … · licenza · Wikimedia Commons", "pos": "50% 15%"}, … ] }
Il titolo della copertina sta nella parte centrale (al centro della miniatura del profilo, che taglia in alto e in basso).
"""
import asyncio, base64, html, json, sys
from pathlib import Path

from playwright.async_api import async_playwright

QUI = Path(__file__).parent; SITO = QUI.parent / "docs"; FONT = QUI / "logo" / "font"
W, H = 1080, 1920
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()
esc = html.escape


def pagina(spec):
    col = "#1f5fd1" if spec.get("serie") == "MotoGP" else "#e8352f"
    foto = spec["foto"]; n = len(foto)
    largh = (W + 90 * (n - 1)) // n                      # i pannelli si sovrappongono sulle diagonali
    pannelli = ""
    for i, f in enumerate(foto):
        x = i * (largh - 90)
        # bordi obliqui: il primo parte dritto a sinistra, l'ultimo finisce dritto a destra
        sin = 0 if i == 0 else 90; des = 0 if i == n - 1 else 90
        poli = f"polygon({sin}px 0,{largh}px 0,{largh - des}px 100%,0 100%)" if False else f"polygon({sin}px 0,100% 0,calc(100% - {des}px) 100%,0 100%)"
        pannelli += (f"<div class=p style='left:{x}px;width:{largh}px;clip-path:{poli}'><div class=im style=\"background:url(data:image/jpeg;base64,{b64(f['file'])}) {f.get('pos', '50% 15%')}/cover no-repeat\"></div></div>")
    righe = ""
    for i, r in enumerate(spec["titolo"]):
        giallo = spec.get("evidenzia") == i
        righe += f"<div class='r{' g' if giallo else ''}'><span>{esc(r)}</span></div>"
    crediti = " · ".join(dict.fromkeys(f.get("credito", "") for f in foto if f.get("credito")))
    font = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")
    return f"""<!doctype html><meta charset=utf-8><style>{font}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.p{{position:absolute;top:0;height:1240px;overflow:hidden}} .im{{position:absolute;inset:0}}
.sep{{position:absolute;top:0;height:1240px;width:{W}px;pointer-events:none}}
.velo{{position:absolute;left:0;top:560px;width:{W}px;height:1360px;background:linear-gradient(180deg,rgba(11,11,14,0) 0%,rgba(11,11,14,.88) 34%,#0b0b0e 62%)}}
.logo{{position:absolute;left:50px;top:90px;width:230px}}
.tag{{position:absolute;right:50px;top:104px;font:700 36px Oswald;letter-spacing:.08em;text-transform:uppercase;background:{col};padding:6px 20px;border-radius:6px}}
.tit{{position:absolute;left:46px;right:46px;top:930px}}
.r{{font:700 118px/1.02 Oswald;text-transform:uppercase;margin:6px 0;-webkit-text-stroke:3px #000;paint-order:stroke fill}}
.r span{{display:inline-block;background:{col};padding:2px 22px 0}} .r.g span{{background:#ffd21f;color:#0b0b0e;-webkit-text-stroke:0}}
.sub{{position:absolute;left:50px;right:50px;top:1420px;font:700 56px/1.1 Oswald;text-transform:uppercase;color:#ffd21f;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.url{{position:absolute;left:50px;top:1760px;font:700 54px Oswald;letter-spacing:.04em;color:{col}}}
.cred{{position:absolute;left:50px;right:50px;bottom:34px;font:500 19px Inter;color:rgba(255,255,255,.65)}}
.bar{{position:absolute;left:0;top:1236px;width:{W}px;height:10px;background:{col}}}
</style>{pannelli}<div class=bar></div><div class=velo></div>
<img class=logo src="data:image/png;base64,{b64(SITO / 'img/logo-wide-scuro.png')}"><div class=tag>{esc(spec.get('etichetta', "Ultim'ora"))}</div>
<div class=tit>{righe}</div><div class=sub>{esc(spec.get('sottotitolo', ''))}</div><div class=url>gpoggi.it</div>
<div class=cred>{esc(crediti)} · Sito non ufficiale, non affiliato a Formula 1, FIA, MotoGP, Dorna o ai team</div>"""


async def main(spec, uscita):
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.set_content(pagina(spec)); await pg.wait_for_timeout(500)
        await pg.screenshot(path=str(uscita)); await b.close()
    print("Fatto:", uscita)


if __name__ == "__main__":
    asyncio.run(main(json.load(open(sys.argv[1])), sys.argv[2]))
