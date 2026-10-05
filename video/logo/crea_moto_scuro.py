"""Logo MotoGP scuro: pista Mugello stilizzata (disegnata da zero) + sola moto + etichetta GP OGGI."""
import re
from moto_gp import moto_svg
PISTA = ("M70 384 L380 384 C430 384 456 356 440 326 L420 296 C410 278 428 262 444 250 C470 232 480 206 462 186 "
         "C446 168 420 176 404 192 L360 232 C344 246 322 238 316 224 L300 180 C292 158 266 148 246 160 L190 190 "
         "C170 200 150 192 148 176 C146 150 120 136 100 150 C76 166 84 196 104 212 L130 238 C146 252 140 270 120 278 "
         "L76 298 C46 312 36 346 46 366 C50 376 58 384 70 384 Z")
moto = moto_svg("#ececf0", "#2a2a32", 430, "#8a8a96", "#b9b9c3", "#16161b")
moto = moto.replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg x="40" y="296" ', 1)
moto = re.sub(r'width="430" height="\d+"', 'width="430" height="179"', moto, 1)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <!-- tracciato stilizzato (Mugello), disegnato da zero -->
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path id="pista" d="{PISTA}" stroke="#3b3b46" stroke-width="12"/>
    <use href="#pista" stroke="#ffffff" stroke-width="2" stroke-dasharray="8 8"/>
  </g>
  <ellipse cx="256" cy="474" rx="200" ry="8" fill="#000" opacity=".4"/>
  {moto}
  <rect x="95" y="122" width="112" height="100" fill="#f2f1ee"/><rect x="207" y="122" width="212" height="100" fill="#e8352f"/>
  <text x="151" y="203" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="86" fill="#15151a">GP</text><text x="313" y="203" text-anchor="middle" font-family="Oswald" font-weight="700" font-size="86" fill="#ffffff">OGGI</text>
</svg>'''
open("moto-gp-scuro.svg", "w").write(svg)
