# -*- coding: utf-8 -*-
"""Exporta Logo_MJ.html a PNG, JPG y PDF con el tamano fisico exacto de
6 x 4,5 cm. El PDF es hoja carta con la etiqueta a tamano real: es la via
segura para imprimir, porque no depende de como escale el navegador.

Uso:
    python majo/exportar_logo.py                # 600 dpi (1417 x 1063 px) + PDF
    python majo/exportar_logo.py --dpi 1200     # 2835 x 2126 px, calidad imprenta

Los archivos llevan la resolucion escrita en los metadatos, asi Word, Canva o
InDesign los colocan directamente a 6 x 4,5 cm sin tener que reescalar a mano.
"""
import os
import sys
from playwright.sync_api import sync_playwright
from PIL import Image

ANCHO_CM, ALTO_CM = 6.0, 4.5
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logo_MJ.html")


def exportar(dpi):
    base = os.path.splitext(HTML)[0]
    px_w = round(ANCHO_CM / 2.54 * dpi)
    px_h = round(ALTO_CM / 2.54 * dpi)
    # La etiqueta se amplia por zoom y se captura a escala 1:1, en vez de
    # subir el device_scale_factor: asi el recuadro cae sobre pixeles enteros
    # y no se cuela una orla del fondo de la pagina ni hace falta reescalar
    # despues, que era lo que ablandaba el texto.
    zoom = px_w / (ANCHO_CM * 10 / 25.4 * 96)
    with sync_playwright() as pw:
        nav = pw.chromium.launch(channel="chrome", headless=True)
        pag = nav.new_page(viewport={"width": px_w + 80, "height": px_h + 80},
                           device_scale_factor=1)
        pag.goto("file:///" + HTML.replace("\\", "/"))
        pag.evaluate("z => { document.documentElement.style.zoom = z; "
                     "document.body.style.background = '#fff'; }", zoom)
        pag.wait_for_timeout(600)
        pag.locator(".etiqueta").screenshot(path=base + ".png")
        nav.close()

    # Chrome puede devolver un pixel de mas o de menos al redondear el
    # recorte: se recorta o se rellena con papel, nunca se reescala, para no
    # ablandar el texto.
    im = Image.open(base + ".png").convert("RGB")
    if im.size != (px_w, px_h):
        if abs(im.width - px_w) <= 3 and abs(im.height - px_h) <= 3:
            papel = Image.new("RGB", (px_w, px_h), (255, 255, 255))
            papel.paste(im, (min(0, px_w - im.width), min(0, px_h - im.height)))
            im = papel
        else:
            im = im.resize((px_w, px_h), Image.LANCZOS)
    im.save(base + ".png", dpi=(dpi, dpi))
    im.save(base + ".jpg", quality=98, subsampling=0, dpi=(dpi, dpi))
    for f in (base + ".png", base + ".jpg"):
        print("%s  %dx%d px  %d dpi  %.0f KB"
              % (os.path.basename(f), px_w, px_h, dpi, os.path.getsize(f) / 1024))


def exportar_pdf():
    """Hoja carta con la etiqueta a tamano real, para mandar a imprimir."""
    base = os.path.splitext(HTML)[0]
    with sync_playwright() as pw:
        nav = pw.chromium.launch(channel="chrome", headless=True)
        pag = nav.new_page()
        pag.goto("file:///" + HTML.replace("\\", "/"))
        pag.wait_for_timeout(600)
        # prefer_css_page_size respeta el @page del HTML (carta, sin margen),
        # asi los milimetros del diseno llegan intactos al papel.
        pag.pdf(path=base + ".pdf", print_background=True,
                prefer_css_page_size=True)
        nav.close()
    print("%s  hoja carta, etiqueta a tamano real  %.0f KB"
          % (os.path.basename(base + ".pdf"),
             os.path.getsize(base + ".pdf") / 1024))


if __name__ == "__main__":
    d = int(sys.argv[sys.argv.index("--dpi") + 1]) if "--dpi" in sys.argv else 600
    exportar(d)
    exportar_pdf()
