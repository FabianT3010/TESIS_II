# -*- coding: utf-8 -*-
"""Mide los recorridos del PDF «4. Diagrama de recorrido 1x1» a partir de sus trazos vectoriales.

Escala: cotas impresas en cada plano, comprobadas en ambos ejes.
  Sala 1 (p1-11, p14-15): 22,45 m de ancho / 857 px · 31,92 m de alto / 1210 px
  Sala 2 (p12-13, p16-44): 14,18 m de ancho / 1222 px · 26,67 m de alto / 2274 px
Salida: analisis/recorridos_hojas.csv (una fila por hoja).
"""
import csv, io, math, os
import fitz
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(AQUI, "..", "4. Diagrama de recorrido 1x1.pdf")
M_POR_PX = {"S1": (22.45/857, 31.92/1210), "S2": (14.18/1222, 26.67/2274)}
NEGRO = (0.0, 0.0, 0.0)                      # TRANSPORTE: linea negra discontinua

def subtrayectos(items):
    """Parte un trazo en sub-trayectos (cada guion o contorno cerrado) como listas de puntos."""
    subs, cur, ultimo = [], [], None
    for it in items:
        k = it[0]
        if k == "re":
            if cur: subs.append(cur); cur = []
            r = it[1]; subs.append([r.tl, r.tr, r.br, r.bl, r.tl]); ultimo = None; continue
        if k == "qu":
            if cur: subs.append(cur); cur = []
            q = it[1]; subs.append([q.ul, q.ur, q.lr, q.ll, q.ul]); ultimo = None; continue
        pts = list(it[1:])
        if ultimo is None or abs(pts[0].x-ultimo.x) > .01 or abs(pts[0].y-ultimo.y) > .01:
            if cur: subs.append(cur)
            cur = [pts[0]]
        if k == "l":
            cur.append(pts[1])
        else:                                  # curva de Bezier: muestreo de 8 tramos
            p0, p1, p2, p3 = pts
            for i in range(1, 9):
                t = i/8; a = (1-t)**3; b = 3*t*(1-t)**2; c = 3*t*t*(1-t); d = t**3
                cur.append(fitz.Point(a*p0.x+b*p1.x+c*p2.x+d*p3.x, a*p0.y+b*p1.y+c*p2.y+d*p3.y))
        ultimo = cur[-1]
    if cur: subs.append(cur)
    return subs

def medir_hoja(doc, pn):
    pg = doc[pn]
    big = max(pg.get_images(full=True), key=lambda t: t[2]*t[3])
    bb = pg.get_image_bbox(big)
    w_px, h_px = Image.open(io.BytesIO(doc.extract_image(big[0])["image"])).size
    sala = "S1" if w_px < 1000 else "S2"
    mpx, mpy = M_POR_PX[sala]
    mx, my = mpx * w_px / bb.width, mpy * h_px / bb.height   # metros por unidad PDF, por eje
    dibujos = [d for d in pg.get_drawings() if d.get("fill") and tuple(d["fill"]) != (1.0, 1.0, 1.0)]

    # leyenda: muestras cortas y planas en la columna derecha; se excluye esa zona
    muestras = [d["rect"] for d in dibujos if 60 < d["rect"].width < 90 and d["rect"].height < 8]
    ley = fitz.Rect(min(r.x0 for r in muestras)-4, 0, 9999, max(r.y1 for r in muestras)+30) if muestras else None

    total = transp = 0.0; viajes = []
    for d in dibujos:
        color = tuple(round(c, 2) for c in d["fill"])
        subs = [s for s in subtrayectos(d["items"]) if len(s) > 1]
        util = []
        for s in subs:
            xs = [p.x for p in s]; ys = [p.y for p in s]
            r = fitz.Rect(min(xs), min(ys), max(xs), max(ys))
            if ley and r.intersects(ley) and r.x0 >= ley.x0: continue
            if r.width < 95 and r.height < 95 and abs(r.width-r.height) < 3 and r.width > 6:
                continue                                           # marcadores circulares
            per = sum(math.hypot((b.x-a.x)*mx, (b.y-a.y)*my) for a, b in zip(s, s[1:]))
            util.append((per/2, ((r.x0+r.x1)/2, (r.y0+r.y1)/2)))
        if not util: continue
        cortos = [u for u in util if u[0] < 0.6]
        if len(cortos) >= 5 and len(cortos) >= .6*len(util):       # linea discontinua
            largo, prev = cortos[0][0], cortos[0][1]
            for dl, c in cortos[1:]:
                paso = math.hypot((c[0]-prev[0])*mx, (c[1]-prev[1])*my)
                if paso < 1.5: largo += paso                       # salto >1,5 m = otro tramo
                prev = c
        else:
            largo = sum(u[0] for u in util)
        total += largo
        if color == NEGRO:
            transp += largo; viajes.append(largo)
    return sala, total, transp, len(viajes), max(viajes) if viajes else 0.0

if __name__ == "__main__":
    doc = fitz.open(PDF)
    out = os.path.join(AQUI, "recorridos_hojas.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["pagina", "sala", "total_m", "transporte_m", "tramos_transporte", "tramo_mayor_m"])
        for pn in range(len(doc)):
            sala, t, tr, n, mayor = medir_hoja(doc, pn)
            w.writerow([pn+1, sala, f"{t:.1f}", f"{tr:.1f}", n, f"{mayor:.1f}"])
            print(f"p{pn+1:02d} {sala} total {t:7.1f} m  transporte {tr:6.1f} m  tramos {n}  mayor {mayor:5.1f} m")
