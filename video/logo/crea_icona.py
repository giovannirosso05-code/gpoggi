"""Icona dell'app (schermata Home): etichetta GP OGGI, monoposto e moto, senza la pista (che nel quadrato si tagliava in una macchia)."""
import re, pathlib
from moto_gp import moto_svg
from playwright.sync_api import sync_playwright
L = pathlib.Path(__file__).parent
auto = (L / "auto.svg").read_text()
auto = re.sub(r'<svg[^>]*>', '<svg x="50" y="205" width="412" height="132" viewBox="6 240 500 160">', auto, 1)
auto = re.sub(r'<rect[^>]*/>', '', auto); auto = re.sub(r'<text.*?</text>', '', auto, flags=re.S)
auto = re.sub(r'<ellipse[^>]*/>', '', auto, 1)
moto = moto_svg("#15151a", "#f4f4f6", 330, "#6a6a76", "#3a3a46", "#f5f4f0")
moto = moto.replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg x="110" y="352" ', 1)
moto = re.sub(r'width="330" height="\d+"', 'width="330" height="137"', moto, 1)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<rect width="512" height="512" fill="#ffffff"/>
<rect x="46" y="64" width="150" height="118" fill="#15151a"/><rect x="196" y="64" width="270" height="118" fill="#e8352f"/>
<text x="121" y="156" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="104" fill="#ffffff">GP</text>
<text x="331" y="156" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="104" fill="#ffffff">OGGI</text>
{auto}{moto}
</svg>'''
(L / "icona.svg").write_text(svg)
f = (L / "oswald-latin-700-normal.woff2").as_uri()
(L / "_i.html").write_text(f"<style>@font-face{{font-family:Oswald;font-weight:700;src:url({f})}}body{{margin:0}}</style>{svg}")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium"); pg = b.new_page(viewport={"width": 512, "height": 512})
    pg.goto((L / "_i.html").as_uri()); pg.wait_for_timeout(500); pg.screenshot(path=str(L / "icona-512.png")); b.close()
