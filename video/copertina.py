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
    """Stesso stile della pagina: foto a tutto schermo, etichetta ULTIM'ORA, titolo in righe colorate. Con più foto: pannelli affiancati."""
    col = "#1f5fd1" if spec.get("serie") == "MotoGP" else "#e8352f"
    foto = spec["foto"]; n = len(foto); largh = W // n
    pannelli = "".join(
        f"<div class=p style='left:{i * largh}px;width:{largh + (2 if i < n - 1 else 0)}px'><div class=im style=\"background:url(data:image/jpeg;base64,{b64(f['file'])}) {f.get('pos', '50% 12%')}/cover no-repeat\"></div></div>"
        for i, f in enumerate(foto))
    righe = "".join(f"<span style='display:inline-block;background:{'#ffd21f;color:#0b0b0e;-webkit-text-stroke:0' if spec.get('evidenzia') == i else col};padding:4px 16px;margin:4px 0'>{esc(r)}</span><br>" for i, r in enumerate(spec["titolo"]))
    crediti = " · ".join(dict.fromkeys(f.get("credito", "") for f in foto if f.get("credito")))
    font = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")
    return f"""<!doctype html><meta charset=utf-8><style>{font}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.p{{position:absolute;top:0;height:{H}px;overflow:hidden}} .im{{position:absolute;inset:0}}
.velo{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 45%,rgba(8,8,10,.92) 78%,#0b0b0e 100%)}}
.logo{{position:absolute;left:50px;top:150px;width:190px}}
.tag{{position:absolute;left:265px;top:172px;font:700 30px Oswald;letter-spacing:.06em;text-transform:uppercase;background:{col};padding:4px 16px;border-radius:6px}}
.tit{{position:absolute;left:60px;right:60px;top:860px;font:700 82px/1.12 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.sub{{position:absolute;left:60px;right:60px;top:1300px;font:700 60px/1.15 Oswald;text-transform:uppercase;color:#ffd21f;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.cred{{position:absolute;right:40px;bottom:36px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:900px;text-align:right}}
</style>{pannelli}<div class=velo></div>
<img class=logo src="data:image/png;base64,{b64(SITO / 'img/logo-wide-scuro.png')}"><div class=tag>{esc(spec.get('etichetta', "Ultim'ora"))}</div>
<div class=tit>{righe}</div><div class=sub>{esc(spec.get('sottotitolo', ''))}</div><div class=cred>{esc(crediti)}</div>"""


def pagina_tondi(spec):
    """Stile del profilo: un volto a tutto schermo, titolo in righe colorate e, sotto, due tondi con gli altri protagonisti."""
    import io
    from PIL import Image
    col = "#1f5fd1" if spec.get("serie") == "MotoGP" else "#e8352f"
    pr = spec["principale"]
    righe = "".join(f"<span style='display:inline-block;background:{'#ffd21f;color:#0b0b0e;-webkit-text-stroke:0' if spec.get('evidenzia') == i else col};padding:4px 16px;margin:4px 0'>{esc(r)}</span><br>" for i, r in enumerate(spec["titolo"]))
    tondi = ""
    for i, t in enumerate(spec["tondi"]):
        im = Image.open(t["file"]).convert("RGB").crop(tuple(t["box"])).resize((360, 360), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=92)
        x = 90 if i == 0 else W - 90 - 360
        tondi += (f"<div class=tondo style='left:{x}px'><img src='data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}'></div>"
                  f"<div class=etichetta style='left:{x}px;width:360px'>{esc(t['nome'])}</div>")
    font = (f"@font-face{{font-family:Oswald;font-weight:700;src:url(data:font/woff2;base64,{b64(FONT / 'oswald-latin-700-normal.woff2')})}}"
            f"@font-face{{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,{b64(FONT / 'inter-latin-500-normal.woff2')})}}")
    return f"""<!doctype html><meta charset=utf-8><style>{font}
*{{box-sizing:border-box}} html,body{{margin:0;width:{W}px;height:{H}px;background:#0b0b0e;color:#fff;font-family:Inter,sans-serif;overflow:hidden;position:relative}}
.bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{b64(pr['file'])}) {pr.get('pos', '55% 20%')}/{pr.get('size', 'cover')} no-repeat {pr.get('sfondo', '#0b0b0e')}}}
.velo{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 38%,rgba(8,8,10,.9) 62%,#0b0b0e 82%)}}
.logo{{position:absolute;left:50px;top:150px;width:190px}}
.tag{{position:absolute;left:265px;top:172px;font:700 30px Oswald;letter-spacing:.06em;text-transform:uppercase;background:{col};padding:4px 16px;border-radius:6px}}
.nome{{position:absolute;left:60px;top:790px;background:#000;font:700 38px Oswald;text-transform:uppercase;letter-spacing:.04em;padding:6px 18px}}
.tit{{position:absolute;left:60px;right:60px;top:850px;font:700 82px/1.12 Oswald;text-transform:uppercase;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.tondo{{position:absolute;top:1230px;width:360px;height:360px;border-radius:50%;overflow:hidden;border:8px solid {col};background:#000}} .tondo img{{width:100%;height:100%;display:block}}
.etichetta{{position:absolute;top:1612px;text-align:center;font:700 40px Oswald;text-transform:uppercase;letter-spacing:.04em;background:#000;padding:6px 0}}
.sub{{position:absolute;left:0;right:0;top:1405px;text-align:center;font:700 64px/1.1 Oswald;text-transform:uppercase;color:#ffd21f;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.cred{{position:absolute;right:40px;bottom:36px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:900px;text-align:right}}
</style><div class=bg></div><div class=velo></div>
<img class=logo src="data:image/png;base64,{b64(SITO / 'img/logo-wide-scuro.png')}"><div class=tag>{esc(spec.get('etichetta', "Ultim'ora"))}</div>
<div class=nome>{esc(pr.get('nome', ''))}</div><div class=tit>{righe}</div>{tondi}<div class=sub style='top:1230px;left:{90 + 360 + 20}px;right:{90 + 360 + 20}px;font-size:46px;line-height:1.08'>{esc(spec.get('sottotitolo', ''))}</div>
<div class=cred>{esc(spec.get('credito', ''))}</div>"""


async def main(spec, uscita):
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.set_content(pagina_tondi(spec) if spec.get('tondi') else pagina(spec)); await pg.wait_for_timeout(500)
        await pg.screenshot(path=str(uscita)); await b.close()
    print("Fatto:", uscita)


if __name__ == "__main__":
    asyncio.run(main(json.load(open(sys.argv[1])), sys.argv[2]))
