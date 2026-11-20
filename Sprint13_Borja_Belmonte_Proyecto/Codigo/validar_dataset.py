#!/usr/bin/env python3
"""Comprobaciones del dataset sintético frente a la calibración (CBP, EUIPO) y coherencia interna."""
import numpy as np, pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 40)

e = pd.read_csv("envios_sinteticos.csv"); c = pd.read_csv("costes_por_pais.csv")
t = pd.read_csv("tarifas_ue_2022.csv")
ok = lambda b: "OK" if b else "REVISAR"

print(f"Filas: envíos {len(e):,} | costes {len(c):,} | nulos {int(e.isna().sum().sum() + c.isna().sum().sum())}")
print("IDs únicos:", ok(e.id_envio.is_unique), "| costes = envíos x 15 países:", ok(len(c) == len(e) * 15))

print("\n1) Tamaño de los envíos frente a CBP (percentiles de unidades, todos los envíos de la vía)")
obj = {  # (P50, P90, P99) FY2023 y FY2024 observados en CBP
    "Express Consignment": [(17, 112, 817), (11, 150, 2099)],
    "Mail": [(2, 29, 240), (3, 22, 164)],
    "Cargo": [(3, 1454, 22495)],
    "Other": [(42, 1000, 22380), (46.5, 1502, 14775)]}
for v, g in e.groupby("via_transporte"):
    q = g.unidades.quantile([.5, .9, .99]).round(0).tolist()
    print(f"  {v:20s} sim P50/P90/P99 = {q} | CBP = {obj[v]}")
print("  Líneas por envío (mediana/P90) sim:", {v: (round(g.n_lineas.median()), round(g.n_lineas.quantile(.9))) for v, g in e.groupby("via_transporte")},
      "| CBP: exprés (3,13), correo (1,8), carga (2,16), otra (2,22)")
print("  % con <3 uds sim:", e.assign(p=e.unidades < 3).groupby("via_transporte").p.mean().round(2).to_dict(),
      "| CBP: correo 0,51/0,47; exprés 0,17/0,25; carga 0,17/0,50; otra 0,06/0,11")

print("\n2) Circuitos y custodia")
print("  circuitos %:", (e.circuito.value_counts(normalize=True) * 100).round(1).to_dict())
print("  elegibles a simplificado %:", round(e.elegible_simplificado.mean() * 100, 1), "| correo y exprés:",
      e[e.via_transporte.isin(["Mail", "Express Consignment"])].elegible_simplificado.mean().round(2))
print("  carga y otra elegibles (debe ser 0):", int(e[e.via_transporte.isin(["Cargo", "Other"])].elegible_simplificado.sum()))
print("  simplificado solo si elegible:", ok(not ((e.circuito == "simplificado") & ~e.elegible_simplificado).any()))
print("  días de custodia por circuito (mín/mediana/P90/máx):")
print(e.groupby("circuito").dias_custodia.agg(["min", "median", lambda s: s.quantile(.9), "max"]).round(0).to_string())
print("  fecha destrucción >= decomiso:", ok((pd.to_datetime(e.fecha_destruccion) >= pd.to_datetime(e.fecha_decomiso)).all()))

print("\n3) Peso, volumen y emisiones")
print("  peso por unidad medio (kg):", (e.peso_kg / e.unidades).groupby(e.categoria).mean().round(2).to_dict())
print("  peso del envío (mediana kg) por vía:", e.groupby("via_transporte").peso_kg.median().round(1).to_dict())
print("  envíos de más de 1 t:", int((e.peso_kg > 1000).sum()), f"({(e.peso_kg > 1000).mean() * 100:.1f} %) | peso total: {e.peso_kg.sum() / 1000:,.0f} t")
print("  emisiones incineración total (tCO2):", round(e.emisiones_incineracion_tco2.sum(), 1),
      "| por categoría:", e.groupby("categoria").emisiones_incineracion_tco2.sum().round(1).to_dict())

print("\n4) Costes (España como referencia)")
es = c[c.iso2 == "ES"].merge(e[["id_envio", "circuito", "peso_kg"]], on="id_envio")
for col in ["coste_titular_s1_eur", "coste_titular_s2_eur"]:
    print(f"  {col} por circuito (mediana / P90 / P99 / máx):")
    print(es.groupby("circuito")[col].agg(["median", lambda s: s.quantile(.9), lambda s: s.quantile(.99), "max"]).round(1).to_string())
tot = es.coste_titular_s1_eur.sort_values(ascending=False)
print(f"  Concentración S1: el 1 % de envíos concentra {tot.head(len(tot)//100).sum() / tot.sum() * 100:.0f} % del coste del titular; el 10 %, {tot.head(len(tot)//10).sum() / tot.sum() * 100:.0f} %")
print(f"  Coste total del titular en España: S1 {es.coste_titular_s1_eur.sum():,.0f} EUR | S2 {es.coste_titular_s2_eur.sum():,.0f} EUR (x{es.coste_titular_s1_eur.sum() / es.coste_titular_s2_eur.sum():.1f})")
est = es[es.circuito != "simplificado"]
print(f"  Mínimo de 1 t: en envíos estándar y litigiosos el S1 de destrucción es {est.destruccion_s1_eur.sum() / est.destruccion_s2_eur.sum():.0f} veces el S2")
print("  Coste titular > coste sistema (no simplificados):", int((c.merge(e[['id_envio','circuito']], on='id_envio').query("circuito!='simplificado'").pipe(lambda d: (d.coste_titular_s1_eur > d.coste_sistema_s1_eur + 0.01).sum()))))
print("  costes negativos:", int((c.select_dtypes('number') < 0).sum().sum()))
fr = c[c.iso2 == "FR"]
print("  Francia: coste titular máximo (debe ser 0):", fr.coste_titular_s1_eur.max(), "| coste sistema medio S1:", round(fr.coste_sistema_s1_eur.mean(), 1))

print("\n5) Mismo lote en los 15 países (estándar, 300 kg, 1 palé, 24 días; sin espera)")
filas = []
for _, r in t.iterrows():
    sh = {"si": 1.0, "parcial": 0.5, "no": 0.0}
    alm = r.almacen_eur_palet_dia_modelo * 24 + r.manipulacion_eur_palet
    tar = 324.6 if r.iso2 == "FR" else r.destr_textil_eur_t_modelo
    des = tar * 0.3
    filas.append((r.iso2, round(alm + des, 1), round(sh[r.titular_paga_almacenaje] * alm + sh[r.titular_paga_destruccion] * des, 1)))
print(pd.DataFrame(filas, columns=["pais", "coste_sistema_eur", "coste_titular_eur"]).sort_values("coste_titular_eur").to_string(index=False))
