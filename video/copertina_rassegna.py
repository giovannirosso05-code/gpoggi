import asyncio, re, sys
sys.path.insert(0, "/home/user/F1-Site/video")
import notizia_sub as n
from playwright.async_api import async_playwright
a=n.trova_foto("Kimi Antonelli"); b=n.trova_foto("Marco Bezzecchi")
def cr(f):
    aut=re.sub(r"Original:\s*","",f["autore"]); return aut+" · "+f["licenza"]
cred="Foto: "+cr(a)+" / "+cr(b)+" · Wikimedia Commons"
logo=n.b64(n.SITO/"img/logo-wide-scuro.png")
CSS="""
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;position:relative;background:#0b0b0e;font-family:Inter,sans-serif}
.m{position:absolute;left:0;right:0;height:960px;background-size:cover;background-repeat:no-repeat}
.a{top:0;background-position:center 14%}
.b{top:960px;background-position:center 14%}
.v{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.45) 0%,rgba(0,0,0,0) 20%,rgba(0,0,0,0) 38%,rgba(0,0,0,.78) 49%,rgba(0,0,0,.35) 52%,rgba(0,0,0,0) 62%,rgba(0,0,0,.85) 96%)}
.logo{position:absolute;left:50px;top:150px;width:190px}
.tag{position:absolute;left:265px;top:172px;font:700 30px Oswald;letter-spacing:.06em;text-transform:uppercase;background:#e8352f;color:#fff;padding:4px 16px;border-radius:6px}
.t{position:absolute;left:50px;font:700 96px/1.02 Oswald;text-transform:uppercase;color:#fff;-webkit-text-stroke:2px #000;paint-order:stroke fill}
.t span{display:inline-block;padding:0 22px 6px;margin:5px 0}
.f1 span{background:#e8352f} .mg span{background:#1f5fd1}
.s{position:absolute;left:50px;font:700 34px Oswald;letter-spacing:.08em;text-transform:uppercase;color:#fff;padding:3px 16px;border-radius:6px}
.pill{position:absolute;left:0;right:0;top:876px;text-align:center}
.pill b{display:inline-block;background:#ffd400;color:#111;font:700 62px Oswald;letter-spacing:.06em;text-transform:uppercase;padding:6px 40px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.6)}
.cred{position:absolute;right:40px;bottom:30px;font:500 20px Inter;color:rgba(255,255,255,.75);max-width:700px;text-align:right}
"""
html=("<!doctype html><meta charset=utf-8><style>"+n.CSS_FONT+CSS+"</style>"
 +'<div class="m a" style="background-image:url(data:image/jpeg;base64,'+n.b64(n.file_foto(a))+')"></div>'
 +'<div class="m b" style="background-image:url(data:image/jpeg;base64,'+n.b64(n.file_foto(b))+')"></div><div class=v></div>'
 +'<img class=logo src="data:image/png;base64,'+logo+'"><div class=tag>Ultim\'ora</div>'
 +'<div class=s style="top:345px;background:#e8352f">F1</div>'
 +'<div class="t f1" style="top:555px"><span>ANTONELLI</span><br><span>CAMPIONE?</span></div>'
 +'<div class=pill><b>Rassegna stampa</b></div>'
 +'<div class=s style="top:1000px;background:#1f5fd1">MotoGP</div>'
 +'<div class="t mg" style="top:1500px"><span>«IL MIO MONDO</span><br><span>È CROLLATO»</span></div>'
 +'<div class=cred>'+cred+'</div>')
async def go():
    async with async_playwright() as p:
        br=await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg=await br.new_page(viewport={"width":n.W,"height":n.H}); await pg.set_content(html); await pg.wait_for_timeout(500)
        await pg.screenshot(path="/home/user/copertina_rassegna_stampa2.png"); await br.close()
asyncio.run(go())
