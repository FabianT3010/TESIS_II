# -*- coding: utf-8 -*-
"""Renderiza cada lamina del HTML a PNG 1920x1080 y arma un PDF (una imagen por pagina).

Uso:
    python convertir_pdf.py majo/Diapositivas_MJ_v3.html
    python convertir_pdf.py majo/Diapositivas_MJ_v3.html --escala 2   # 3840x2160, mas nitido
"""
import os
import sys
from playwright.sync_api import sync_playwright
from PIL import Image

W, H = 1920, 1080


def render(html, outdir, escala):
    os.makedirs(outdir, exist_ok=True)
    pngs = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": W, "height": H},
                                device_scale_factor=escala)
        page.goto("file:///" + html.replace("\\", "/"))
        page.wait_for_timeout(2500)          # fuentes e iconos
        n = page.evaluate("document.querySelectorAll('.slide').length")
        print("laminas detectadas:", n)

        # modo presentacion con escala fija = 1 (lienzo exacto 1920x1080)
        page.evaluate("""() => {
            document.body.classList.add('pres');
            document.body.style.setProperty('--k', 1);
            document.querySelectorAll('.slide').forEach(s =>
                s.classList.remove('act', 'atras'));
            ['nv', 'pg'].forEach(id => {
                const e = document.getElementById(id);
                if (e) e.style.display = 'none';
            });
        }""")

        for i in range(n):
            page.evaluate("""(idx) => {
                const s = document.querySelectorAll('.slide');
                s.forEach(x => x.classList.remove('act', 'atras'));
                void s[idx].offsetWidth;
                s[idx].classList.add('act');
            }""", i)
            page.wait_for_timeout(3200)      # dejar terminar las animaciones
            # el flujograma es la lamina mas larga: 2,55 s de retardo
            # acumulado + 0,38 s de la ultima entrada
            out = os.path.join(outdir, f"slide_{i:02d}.png")
            page.screenshot(path=out, clip={"x": 0, "y": 0, "width": W, "height": H})
            pngs.append(out)
            print("  ->", os.path.basename(out))
        browser.close()
    return pngs


def build_pdf(pngs, pdf):
    hojas = [Image.open(p).convert("RGB") for p in pngs]
    hojas[0].save(pdf, "PDF", save_all=True, append_images=hojas[1:], resolution=96.0)
    print("PDF guardado en:", pdf, f"({os.path.getsize(pdf)/1e6:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python convertir_pdf.py <archivo.html> [--escala N]")
    html = os.path.abspath(sys.argv[1])
    escala = int(sys.argv[sys.argv.index("--escala") + 1]) if "--escala" in sys.argv else 1
    base, _ = os.path.splitext(html)
    pngs = render(html, base + "_png", escala)
    build_pdf(pngs, base + ".pdf")
