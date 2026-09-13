# -*- coding: utf-8 -*-
"""Actual vs propuesta por puesto, a partir de recorridos_hojas.csv.

Distancia
  Actual    = promedio de las jornadas observadas del puesto (ambas areas del PDF sumadas).
  Propuesta = la jornada mas corta (rutina estandarizada) sin los traslados repetidos al
              deposito: el carrito deja un solo viaje, el tramo de transporte mayor.
  p39 es copia exacta de p29 y se cuenta una vez. Se excluye la jornada p41-44 (parcial).

Tiempo (la distancia NO explica el tiempo de limpieza: r2 = 0,05 en las 13 hojas con tiempo)
  Jornada   = tesis, Tablas 4.10 y 4.11: 4.007,45 min reales + 332 complementarios;
              headcount 10 -> 9 operarios de 480 min.
  Por puesto= los 130 min de preparacion de quimicos (Tabla 4.11) son la parte ligada a los
              traslados. Se reparten segun la distancia de transporte de cada puesto y se
              reducen en la misma proporcion en que el carrito elimina esos traslados.

Puesto I (instructivo, Anexo 9: sala de canastillas sucias) no tiene diagrama de recorrido
  en el PDF ni en la tesis: se estima con el promedio de los ocho puestos observados (A-H)
  y entra en el reparto de los 130 min como un puesto mas.
"""
import csv, os
AQUI = os.path.dirname(os.path.abspath(__file__))
PREP_QUIM = 130.0
H = {int(r["pagina"]): r for r in csv.DictReader(open(os.path.join(AQUI, "recorridos_hojas.csv"), encoding="utf-8"))}
JORNADAS = {
 "Sala 1": [dict(A=[14,15,1], B=[2,3], C=[4], D=[5], E=[6], F=[7,8], G=[9,10], H=[11])],
 "Sala 2": [dict(A=[12,13], B=[16], C=[17], D=[18], E=[19], F=[20], G=[21], H=[22]),
            dict(B=[23], C=[24], D=[25], E=[26], F=[27,28], G=[29], H=[30]),
            dict(A=[31,32], B=[33,34], C=[35], D=[36], E=[37], F=[38], H=[40])],
}
por = {p: [0.0, 0.0, 0.0, 0.0] for p in "ABCDEFGH"}   # dist act, dist prop, transp act, transp prop
for sala, jornadas in JORNADAS.items():
    for p in "ABCDEFGH":
        obs = []
        for j in jornadas:
            if p not in j: continue
            hs = [H[n] for n in j[p]]
            obs.append((sum(float(h["total_m"]) for h in hs), sum(float(h["transporte_m"]) for h in hs),
                        max(float(h["tramo_mayor_m"]) for h in hs)))
        n = len(obs)
        mejor = min(obs, key=lambda o: o[0])
        q = por[p]
        q[0] += sum(o[0] for o in obs)/n
        q[1] += mejor[0] - (mejor[1] - mejor[2])
        t_prom = sum(o[1] for o in obs)/n
        q[2] += t_prom
        q[3] += min(mejor[2], t_prom)          # el viaje que queda no puede superar lo actual
por["I"] = [sum(q[k] for q in por.values())/8 for k in range(4)]     # estimado: promedio A-H
T_ACT = sum(q[2] for q in por.values())
pct = lambda a, b: (b-a)/a*100 if a else 0.0
filas = []
for p, (da, dp, ta, tp) in por.items():
    ma = PREP_QUIM * ta / T_ACT
    mp = ma * (tp/ta if ta else 1)
    filas.append((p, da, dp, pct(da, dp), ma, mp))
with open(os.path.join(AQUI, "resumen_optimizacion.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["puesto","dist_actual_m","dist_prop_m","dist_var_pct","prep_quim_actual_min","prep_quim_prop_min","ahorro_min"])
    for p, da, dp, v, ma, mp in filas:
        w.writerow([p, f"{da:.1f}", f"{dp:.1f}", f"{v:.1f}", f"{ma:.1f}", f"{mp:.1f}", f"{ma-mp:.1f}"])
        print(f"{p}  {da:5.0f} -> {dp:5.0f} m ({v:6.1f} %)   quimicos {ma:5.1f} -> {mp:5.1f} min  (-{ma-mp:4.1f})")
    DA = sum(r[1] for r in filas); DP = sum(r[2] for r in filas)
    MA = sum(r[4] for r in filas); MP = sum(r[5] for r in filas)
    w.writerow(["General", f"{DA:.1f}", f"{DP:.1f}", f"{pct(DA,DP):.1f}", f"{MA:.1f}", f"{MP:.1f}", f"{MA-MP:.1f}"])
    print(f"GENERAL {DA:.0f} -> {DP:.0f} m ({pct(DA,DP):.1f} %)   quimicos {MA:.1f} -> {MP:.1f} min ({pct(MA,MP):.1f} %)")
    disp_a, disp_p, req = 10*480, 9*480, 4007.45 + 332
    print(f"JORNADA  disponible {disp_a} -> {disp_p} min ({pct(disp_a,disp_p):.1f} %) | requerido {req:.2f} min = {req/480:.2f} operarios")
