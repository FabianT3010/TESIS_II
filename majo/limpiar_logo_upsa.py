# -*- coding: utf-8 -*-
"""Reconstruye el logotipo UPSA a alta resolucion desde el unico original que
hay en el repo (el anexo de la tesis, 410x180 px y con ruido de JPEG).

El logo es de un solo color sobre blanco, asi que se trabaja con el mapa de
tinta en vez de con el color: se sobremuestrea x8, se endurecen los bordes con
una curva suave -equivalente a redibujar el contorno- y se baja al tamano
final con LANCZOS, que devuelve el antialias limpio. Sale un PNG con
transparencia, tintado con el verde institucional.
"""
import numpy as np
from PIL import Image, ImageChops

ORIGEN = "majo/img_mj/extra-image1.png"
DESTINO = "majo/img_mj/upsa-logo.png"
VERDE = (0, 91, 66)     # muestreado del propio logotipo
ANCHO = 1600            # alcanza para imprimir a 600 dpi y de sobra en pantalla
SUPER = 8               # factor de sobremuestreo
UMBRAL, DUREZA = 0.42, 7.0


def limpiar():
    im = Image.open(ORIGEN).convert("RGB")
    caja = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
    im = im.crop(caja.convert("L").point(lambda v: 255 if v > 22 else 0).getbbox())

    # Mapa de tinta: 0 = papel, 1 = trazo pleno. Se normaliza contra la
    # luminancia del verde para que el trazo llegue de verdad al 100 %.
    lum = np.asarray(im.convert("L")).astype(np.float32) / 255.0
    piso = (0.299 * VERDE[0] + 0.587 * VERDE[1] + 0.114 * VERDE[2]) / 255.0
    tinta = np.clip((1.0 - lum) / (1.0 - piso), 0.0, 1.0)

    g = Image.fromarray((tinta * 255).astype(np.uint8), "L")
    alto = round(ANCHO * g.height / g.width)
    g = g.resize((ANCHO * SUPER // 4, alto * SUPER // 4), Image.LANCZOS)

    # Curva logistica: separa trazo de papel sin dejar el borde escalonado.
    t = np.asarray(g).astype(np.float32) / 255.0
    t = 1.0 / (1.0 + np.exp(-DUREZA * (t - UMBRAL) * 4))
    g = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8), "L")
    g = g.resize((ANCHO, alto), Image.LANCZOS)          # antialias final

    out = Image.new("RGBA", (ANCHO, alto), VERDE + (0,))
    out.putalpha(g)
    out.save(DESTINO, optimize=True)
    print(DESTINO, out.size, "%.0f KB" % (__import__("os").path.getsize(DESTINO) / 1024))


if __name__ == "__main__":
    limpiar()
