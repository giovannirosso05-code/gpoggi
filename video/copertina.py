"""Copertina in stile 'volto grande + titolo su due righe': sfondo colorato solo dietro le parole, visibile subito nella griglia del profilo.
Uso: python copertina.py "Marco Bezzecchi" "VINCE" "BEZZECCHI!" uscita.png [--serie F1|MotoGP] [--alt chiave_foto_extra]
Il volto e' la foto libera del sito (alt = foto alternativa di foto-extra.json)."""
import argparse
import asyncio
import re

from playwright.async_api import async_playwright

import notizia_sub as n


def html_copertina(pilota, righe, serie="MotoGP", alt=None, pos="center 12%", sfondo=None, titolo_top=1040):
    """sfondo = immagine creata con IA (file): al posto della foto del pilota; il titolo si può alzare con titolo_top."""
    f = None if sfondo else n.trova_foto(pilota, alt)
    col = "#1f5fd1" if serie == "MotoGP" else "#e8352f"
    autore = re.sub(r"Original:\s*", "", f["autore"]) if f else ""
    cred = "Immagine creata con intelligenza artificiale" if sfondo else f"Foto: {autore} · {f['licenza']} · Wikimedia Commons"
    img = (n.b64(sfondo), "png" if str(sfondo).endswith(".png") else "jpeg") if sfondo else (n.b64(n.file_foto(f)), "jpeg")
    logo = n.b64(n.SITO / "img/logo-wide-scuro.png")
    strisce = "".join(f'<span style="display:inline-block;background:{col};padding:0 26px 6px;margin:6px 0">{n.esc(r)}</span><br>' for r in righe)
    return f"""<!doctype html><meta charset=utf-8><style>{n.CSS_FONT}
html,body{{margin:0;width:{n.W}px;height:{n.H}px;overflow:hidden;position:relative;background:#0b0b0e;font-family:Inter,sans-serif}}
.bg{{position:absolute;inset:0;background:url(data:image/{img[1]};base64,{img[0]}) {pos}/cover no-repeat}}
.velo{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 45%,rgba(8,8,10,.92) 78%,#0b0b0e 100%)}}
.logo{{position:absolute;left:50px;top:250px;width:190px}}
.tag{{position:absolute;left:265px;top:272px;font:700 30px Oswald;letter-spacing:.06em;text-transform:uppercase;background:{col};color:#fff;padding:4px 16px;border-radius:6px}}
.t{{position:absolute;left:60px;top:{titolo_top}px;font:700 150px/1.04 Oswald;text-transform:uppercase;color:#fff;-webkit-text-stroke:2px #000;paint-order:stroke fill}}
.cred{{position:absolute;right:40px;bottom:36px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:600px;text-align:right}}
</style><div class=bg></div><div class=velo></div><img class=logo src="data:image/png;base64,{logo}"><div class=tag>Ultim'ora</div><div class=t>{strisce}</div><div class=cred>{n.esc(cred)}</div>"""


async def scatta(html, uscita):
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": "/opt/pw-browsers/chromium"} if n.Path("/opt/pw-browsers/chromium").exists() else {}), args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": n.W, "height": n.H})
        await pg.set_content(html)
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=uscita)
        await b.close()


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("pilota"); a.add_argument("riga1"); a.add_argument("riga2"); a.add_argument("uscita")
    a.add_argument("--serie", default="MotoGP"); a.add_argument("--alt"); a.add_argument("--pos", default="center 12%"); a.add_argument("--sfondo"); a.add_argument("--titolo-top", type=int, default=1040)
    x = a.parse_args()
    asyncio.run(scatta(html_copertina(x.pilota, [x.riga1, x.riga2], x.serie, x.alt, x.pos, x.sfondo, x.titolo_top), x.uscita))
    print("Fatto:", x.uscita)
