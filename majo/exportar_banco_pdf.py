# -*- coding: utf-8 -*-
"""Exporta Banco_Preguntas_MJ.md a PDF con el mismo aspecto del anterior (carta, Arial, estilo GitHub).

Uso: python majo/exportar_banco_pdf.py
"""
import os
import markdown
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(AQUI, "Banco_Preguntas_MJ.md")
PDF = os.path.join(AQUI, "Banco_Preguntas_MJ.pdf")

CSS = """
body{font-family:Arial,Helvetica,sans-serif;font-size:13.5px;line-height:1.6;color:#24292e;margin:0}
h1{font-size:30px;margin:34px 0 14px;font-weight:700}
h2{font-size:22px;margin:26px 0 12px}
h3{font-size:18px;margin:22px 0 10px}
p{margin:0 0 10px}
ul,ol{margin:0 0 10px;padding-left:22px}
table{border-collapse:collapse;margin:10px 0 16px;width:100%}
th,td{border:1px solid #dfe2e5;padding:7px 12px;text-align:left;vertical-align:top}
tr:nth-child(2n){background:#f6f8fa}
hr{border:0;border-top:1px solid #e1e4e8;margin:26px 0}
code{font-family:Consolas,monospace;background:#f3f4f6;padding:1px 4px;border-radius:3px}
blockquote{margin:0 0 10px;padding:0 12px;color:#57606a;border-left:3px solid #dfe2e5}
"""

if __name__ == "__main__":
    texto = open(MD, encoding="utf-8").read()
    cuerpo = markdown.markdown(texto, extensions=["tables", "sane_lists"])
    html = f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Banco_Preguntas_MJ</title><style>{CSS}</style></head><body>{cuerpo}</body></html>"
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page()
        pg.set_content(html, wait_until="load")
        pg.pdf(path=PDF, format="Letter", print_background=True,
               margin={"top": "22mm", "bottom": "22mm", "left": "20mm", "right": "20mm"})
        b.close()
    print("PDF guardado en:", PDF, f"({os.path.getsize(PDF)/1024:.0f} KB)")
