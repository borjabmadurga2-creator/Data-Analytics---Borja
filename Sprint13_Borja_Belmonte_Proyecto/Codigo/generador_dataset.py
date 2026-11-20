#!/usr/bin/env python3
"""
Generador del dataset sintético: gestión de mercancía de moda incautada en la
frontera de la UE (Reglamento 608/2013).

Salidas (en la carpeta actual):
  envios_sinteticos.csv    una fila por envío (físico, legal, días, emisiones)
  costes_por_pais.csv      cada envío costeado en los 15 países (2 escenarios)
  parametros_generador.csv registro de parámetros y supuestos

Uso:  python generador_dataset.py [--n 12000] [--seed 2026] [--cargo FY2023]
Requiere tarifas_ue_2022.csv en la misma carpeta.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=12000)
ap.add_argument("--seed", type=int, default=2026)
ap.add_argument("--cargo", choices=["FY2024", "FY2023"], default="FY2024",
                help="parámetros de la carga (FY2024 base; FY2023 = sensibilidad)")
ap.add_argument("--tarifas", default="tarifas_ue_2022.csv")
ap.add_argument("--salida", default=".")
args = ap.parse_args()

rng = np.random.default_rng(args.seed)
N = args.n
OUT = Path(args.salida)

# --------------------------------------------------------------------------
# 1. PARÁMETROS (cada uno figura también en parametros_generador.csv)
# --------------------------------------------------------------------------
VIAS = ["Express Consignment", "Mail", "Cargo", "Other"]
VIA_P = [0.598, 0.260, 0.103, 0.039]                  # CBP, envíos de moda FY2023-24

# p5 = proporción de envíos de hasta 5 unidades; mu/sigma = lognormal del resto;
# cap = P99 observado; lineas = (mediana, P90) de líneas por envío
PARAM = {
    "Express Consignment": dict(p5=0.33, mu=3.59, sigma=1.25, cap=1450, lineas=(3, 13)),
    "Mail":                dict(p5=0.64, mu=2.82, sigma=0.99, cap=200,  lineas=(1, 8)),
    "Cargo":               dict(p5=0.57, mu=5.09, sigma=2.45, cap=22500, lineas=(2, 16)),
    "Other":               dict(p5=0.12, mu=4.52, sigma=1.83, cap=18500, lineas=(2, 22)),
}
if args.cargo == "FY2023":
    PARAM["Cargo"] = dict(p5=0.25, mu=4.44, sigma=2.04, cap=18900, lineas=(4, 26))

# P90 y P99 de CBP para todos los envíos de moda de cada vía (media geométrica de FY2023 y FY2024;
# carga: FY2024, o FY2023 si --cargo FY2023)
TARGET_TAIL = {"Express Consignment": (129.6, 1309.0), "Mail": (25.3, 198.4),
               "Cargo": (1454.0, 22495.0), "Other": (1226.0, 18184.0)}
if args.cargo == "FY2023":
    TARGET_TAIL["Cargo"] = (1732.0, 18855.0)
from scipy.stats import norm
for _v, _p in PARAM.items():
    t90, t99 = TARGET_TAIL[_v]
    z90 = norm.ppf((0.90 - _p["p5"]) / (1 - _p["p5"])); z99 = norm.ppf((0.99 - _p["p5"]) / (1 - _p["p5"]))
    sigs = np.linspace(0.5, 3.5, 301)
    err = (np.log(np.exp(_p["mu"] + sigs * z90) / t90)) ** 2 + (np.log(np.exp(_p["mu"] + sigs * z99) / t99)) ** 2
    _p["sigma"] = float(sigs[np.argmin(err)]); _p["cap"] = int(5 * t99)

TINY_W = {  # reparto de 1-5 unidades en envíos diminutos (calibrado con % de <3 uds)
    "Express Consignment": [0.40, 0.24, 0.16, 0.12, 0.08],
    "Mail":                [0.45, 0.25, 0.15, 0.10, 0.05],
    "Cargo":               [0.60, 0.25, 0.07, 0.05, 0.03],
    "Other":               [0.40, 0.24, 0.16, 0.12, 0.08],
}

CATS = ["Wearing Apparel/Accessories", "Handbags/Wallets", "Watches/Jewelry", "Footwear"]
CAT_P = [0.3694, 0.2676, 0.2128, 0.1501]              # peso en líneas de CBP (proxy)

# valor unitario (USD): (mediana, sigma lognormal, tope P99,9)
VALOR_UD = {
    "Wearing Apparel/Accessories": (525, 0.978, 15000),
    "Handbags/Wallets":            (1790, 0.737, 42364),
    "Watches/Jewelry":             (1280, 2.337, 812576),
    "Footwear":                    (440, 0.827, 8500),
}
# peso por unidad (kg): triangular (mín, moda, máx). Prendas y calzado: PEFCR v3.1
PESO_UD = {
    "Wearing Apparel/Accessories": (0.08, 0.31, 0.95),
    "Footwear":                    (0.35, 0.78, 1.10),
    "Handbags/Wallets":            (0.10, 0.50, 1.30),   # supuesto débil
    "Watches/Jewelry":             (0.01, 0.05, 0.14),   # supuesto débil
}
VOL_UD_L = {  # litros por unidad (PEFCR tabla 35 para prendas/calzado; resto supuesto)
    "Wearing Apparel/Accessories": 4.7, "Footwear": 15.6,
    "Handbags/Wallets": 8.0, "Watches/Jewelry": 0.3,
}
M3_POR_PALET = 1.0                                     # supuesto (coherente con Malta, 1 palé ≈ 1 m3)

# material por categoría (supuesto) y factor de incineración tCO2/t (IPCC 2006, v.5, tabs. 2.4 y 5.2)
MATERIAL_P = {
    "Wearing Apparel/Accessories": {"textil": 1.0},
    "Footwear":                    {"caucho_cuero": 0.5, "plastico_sintetico": 0.3, "textil": 0.2},
    "Handbags/Wallets":            {"plastico_sintetico": 0.5, "caucho_cuero": 0.3, "textil": 0.2},
    "Watches/Jewelry":             {"metal_otros": 1.0},
}
EF_TRI = {  # (mín, moda, máx)
    "textil":             (0.0, 0.293, 0.733),
    "caucho_cuero":       (0.0, 0.413, 1.032),
    "plastico_sintetico": (2.457, 2.750, 3.117),
    "metal_otros":        (0.0, 0.0, 0.0),
}

ORIGEN = {"China": 0.41, "Hong Kong": 0.06, "Turquía": 0.19, "Otros": 0.34}  # EUIPO/DG TAXUD 2025, incautaciones en frontera por número de artículos: China 40,77 %, Turquía 18,63 %, Hong Kong 5,70 %

P_ADHESION = 0.70      # supuesto: titulares adheridos al procedimiento simplificado
P_OPOSICION = 0.08     # anclado: 7,63 % procedimiento penal + 0,32 % juicio (EUIPO/DG TAXUD 2025, frontera); equivale al circuito litigioso
DIAS_TRAMITE = 14      # 10 días hábiles ≈ 14 naturales (Reglamento 608/2013, arts. 23 y 26)
LOGISTICA_SIMPL = (0, 2, 10)       # triangular, supuesto
LOGISTICA_EST = (3, 10, 45)        # triangular, supuesto
LITIGIO_INICIO = (14, 28)          # uniforme (arts. 23.3 y 23.4, en días naturales)
LITIGIO_MEDIANA = 180              # supuesto; sensibilidad 90/365/730
LITIGIO_SIGMA = 1.0
LITIGIO_MAX = 1460
ESPERA_AGRUP = (0, 15, 60)         # triangular, supuesto (solo envíos < 1 t)
P_FY2024 = 13881 / (13881 + 13459)
COMPARTE = {"si": 1.0, "parcial": 0.5, "no": 0.0}   # "parcial" = 0,5 (supuesto)
TARIFA_FR_SISTEMA = 324.6          # media EUIPO, para el coste del sistema en Francia
LV_ENVIO_PEQUENO_M2_MES = 8.89     # Letonia: tasa de almacén también en envíos postales

# --------------------------------------------------------------------------
# 2. ENVÍOS
# --------------------------------------------------------------------------
via = rng.choice(VIAS, size=N, p=VIA_P)

unidades = np.zeros(N, dtype=int)
for v, p in PARAM.items():
    idx = np.where(via == v)[0]
    m = len(idx)
    tiny = rng.random(m) < p["p5"]
    u_tiny = rng.choice([1, 2, 3, 4, 5], size=m, p=TINY_W[v])
    rest = np.clip(np.rint(np.exp(rng.normal(p["mu"], p["sigma"], m))), 6, p["cap"])
    unidades[idx] = np.where(tiny, u_tiny, rest.astype(int))

n_lineas = np.ones(N, dtype=int)
for v, p in PARAM.items():
    idx = np.where(via == v)[0]
    u = unidades[idx]; med, p90 = p["lineas"]
    z = rng.normal(size=len(u)); mejor = (1e9, 0.0, 0.5)
    for a in np.linspace(-1.5, 1.5, 61):
        for sd in np.linspace(0.2, 1.4, 25):
            l = np.clip(np.rint(np.exp(a + 0.5 * np.log(u) + sd * z)), 1, u)
            err = np.log(max(np.median(l), 1) / med) ** 2 + np.log(max(np.percentile(l, 90), 1) / p90) ** 2
            if err < mejor[0]:
                mejor = (err, a, sd)
    _, a, sd = mejor
    n_lineas[idx] = np.clip(np.rint(np.exp(a + 0.5 * np.log(u) + sd * z)), 1, u).astype(int)

categoria = rng.choice(CATS, size=N, p=np.array(CAT_P) / np.sum(CAT_P))

SUB_PEFCR = {  # (nombre, peso kg, volumen L) -- PEFCR ropa y calzado v3.1, tablas A.IV 2, A.IV 3 y 35
    "Wearing Apparel/Accessories": [
        ("camisetas", 0.17, 1.8), ("camisas y blusas", 0.25, 6.0), ("jerseis y sudaderas", 0.50, 10.2),
        ("chaquetas y abrigos", 0.95, 15.0), ("pantalones y shorts", 0.45, 4.0),
        ("vestidos, faldas y monos", 0.30, 7.0), ("leggings, medias y calcetines", 0.13, 0.6),
        ("ropa interior", 0.08, 0.6), ("banadores", 0.12, 0.6), ("accesorios de ropa", 0.11, 1.2)],
    "Footwear": [("calzado de punta abierta", 0.35, 4.8), ("calzado cerrado", 0.90, 18.0), ("botas", 1.10, 24.0)],
}
valor_ud = np.zeros(N); peso_ud = np.zeros(N); vol_ud = np.zeros(N)
subcat = np.full(N, "sin subcategoria", dtype=object)
material = np.empty(N, dtype=object); ef = np.zeros(N)
for c in CATS:
    idx = np.where(categoria == c)[0]
    med, sig, tope = VALOR_UD[c]
    valor_ud[idx] = np.clip(np.exp(rng.normal(np.log(med), sig, len(idx))), 1, tope)
    if c in SUB_PEFCR:
        k = rng.integers(0, len(SUB_PEFCR[c]), len(idx))
        subcat[idx] = [SUB_PEFCR[c][i][0] for i in k]
        peso_ud[idx] = np.array([SUB_PEFCR[c][i][1] for i in k]) * np.exp(rng.normal(0, 0.15, len(idx)))
        vol_ud[idx] = np.array([SUB_PEFCR[c][i][2] for i in k]) * np.exp(rng.normal(0, 0.15, len(idx)))
    else:
        lo, mo, hi = PESO_UD[c]
        peso_ud[idx] = rng.triangular(lo, mo, hi, len(idx))
        vol_ud[idx] = VOL_UD_L[c] * np.exp(rng.normal(0, 0.25, len(idx)))
    mats = list(MATERIAL_P[c].keys())
    material[idx] = rng.choice(mats, size=len(idx), p=list(MATERIAL_P[c].values()))
for mt, (lo, mo, hi) in EF_TRI.items():
    idx = np.where(material == mt)[0]
    ef[idx] = 0.0 if hi == 0 else rng.triangular(lo, mo, hi, len(idx))

valor_msrp = unidades * valor_ud
peso_kg = unidades * peso_ud
volumen_m3 = unidades * vol_ud / 1000.0
n_palets = np.maximum(1, np.ceil(volumen_m3 / M3_POR_PALET)).astype(int)
emisiones = (peso_kg / 1000.0) * ef

# procedimiento (Reglamento 608/2013, arts. 2.19, 23 y 26)
elegible = np.isin(via, ["Mail", "Express Consignment"]) & ((unidades <= 3) | (peso_kg < 2))
adhesion = rng.random(N) < P_ADHESION
oposicion = rng.random(N) < P_OPOSICION
circuito = np.where(oposicion, "litigioso",
             np.where(elegible & adhesion, "simplificado", "estandar"))

lit = circuito == "litigioso"; simp = circuito == "simplificado"
dias_tramite = np.where(lit, rng.uniform(*LITIGIO_INICIO, N), DIAS_TRAMITE).round().astype(int)
proc = np.exp(rng.normal(np.log(LITIGIO_MEDIANA), LITIGIO_SIGMA, N))
dias_proc = np.where(lit, np.clip(proc, 30, LITIGIO_MAX), 0).round().astype(int)
log_s = rng.triangular(*LOGISTICA_SIMPL, N)
log_e = rng.triangular(*LOGISTICA_EST, N)
dias_log = np.where(simp, log_s, log_e).round().astype(int)
dias_cust = dias_tramite + dias_proc + dias_log
espera = np.where(~simp & (peso_kg < 1000), rng.triangular(*ESPERA_AGRUP, N), 0).round().astype(int)

fy = np.where(rng.random(N) < P_FY2024, 2024, 2023)
inicio = np.where(fy == 2023, np.datetime64("2022-10-01"), np.datetime64("2023-10-01"))
fecha = inicio + rng.integers(0, 365, size=N).astype("timedelta64[D]")
fecha_destr = fecha + dias_cust.astype("timedelta64[D]")

origen = rng.choice(list(ORIGEN.keys()), size=N, p=list(ORIGEN.values()))

envios = pd.DataFrame({
    "id_envio": [f"ENV-{i + 1:06d}" for i in range(N)],
    "fecha_decomiso": pd.to_datetime(fecha),
    "anio_fiscal_cbp": fy,
    "trimestre": pd.to_datetime(fecha).to_period("Q").astype(str),
    "via_transporte": via,
    "categoria": categoria,
    "subcategoria": subcat,
    "material_dominante": material,
    "pais_origen": origen,
    "n_lineas": n_lineas,
    "unidades": unidades,
    "valor_msrp_usd": valor_msrp.round(0).astype(np.int64),
    "peso_kg": peso_kg.round(2),
    "volumen_m3": volumen_m3.round(4),
    "n_palets": n_palets,
    "elegible_simplificado": elegible,
    "adhesion_titular": adhesion,
    "oposicion_declarante": oposicion,
    "circuito": circuito,
    "dias_tramite": dias_tramite,
    "dias_procedimiento": dias_proc,
    "dias_logistica": dias_log,
    "dias_custodia": dias_cust,
    "dias_espera_agrupacion": espera,
    "fecha_destruccion": pd.to_datetime(fecha_destr),
    "ef_incineracion_tco2_t": ef.round(3),
    "emisiones_incineracion_tco2": emisiones.round(5),
})

# --------------------------------------------------------------------------
# 3. COSTES POR PAÍS (dos escenarios del mínimo de destrucción)
#    S1 = destrucción individual con mínimo de 1 t por envío
#    S2 = destrucción agrupada: coste proporcional al peso + días de espera
# --------------------------------------------------------------------------
tar = pd.read_csv(Path(args.tarifas) if Path(args.tarifas).exists() else OUT / args.tarifas)
peso_t = peso_kg / 1000.0
filas = []
for _, t in tar.iterrows():
    iso = t["iso2"]
    alm_d = float(t["almacen_eur_palet_dia_modelo"]); manip = float(t["manipulacion_eur_palet"])
    tarifa = float(t["destr_textil_eur_t_modelo"])
    tarifa_sis = TARIFA_FR_SISTEMA if iso == "FR" else tarifa
    sh_a = COMPARTE[t["titular_paga_almacenaje"]]; sh_d = COMPARTE[t["titular_paga_destruccion"]]
    fijo = float(t["envio_pequeno_eur_fijo"]); por_ud = float(t["envio_pequeno_eur_por_unidad"])

    # envíos estándar y litigiosos
    alm1 = n_palets * alm_d * dias_cust + n_palets * manip
    alm2 = n_palets * alm_d * (dias_cust + espera) + n_palets * manip
    des1 = tarifa_sis * np.maximum(1.0, peso_t)
    des2 = tarifa_sis * peso_t
    tit1 = sh_a * alm1 + sh_d * des1
    tit2 = sh_a * alm2 + sh_d * des2
    sis1 = alm1 + des1
    sis2 = alm2 + des2

    # envíos en procedimiento simplificado: tasas de envío pequeño (el titular las paga si el país las cobra)
    cuota = fijo + por_ud * unidades
    if iso == "LV":
        cuota = cuota + LV_ENVIO_PEQUENO_M2_MES / 30.0 * dias_cust
    cuota = cuota * (1.0 if t["titular_paga_destruccion"] != "no" else 0.0)
    sis_s = tarifa_sis * peso_t
    alm1 = np.where(simp, 0.0, alm1); alm2 = np.where(simp, 0.0, alm2)
    des1 = np.where(simp, sis_s, des1); des2 = np.where(simp, sis_s, des2)
    tit1 = np.where(simp, cuota, tit1); tit2 = np.where(simp, cuota, tit2)
    sis1 = np.where(simp, sis_s, sis1); sis2 = np.where(simp, sis_s, sis2)

    filas.append(pd.DataFrame({
        "id_envio": envios["id_envio"], "iso2": iso, "pais": t["pais"],
        "almacenaje_s1_eur": alm1.round(2), "destruccion_s1_eur": des1.round(2),
        "coste_titular_s1_eur": tit1.round(2), "coste_sistema_s1_eur": sis1.round(2),
        "almacenaje_s2_eur": alm2.round(2), "destruccion_s2_eur": des2.round(2),
        "coste_titular_s2_eur": tit2.round(2), "coste_sistema_s2_eur": sis2.round(2),
    }))
costes = pd.concat(filas, ignore_index=True)

# --------------------------------------------------------------------------
# 4. REGISTRO DE PARÁMETROS
# --------------------------------------------------------------------------
def fila(nombre, valor, tipo, fuente):
    return {"parametro": nombre, "valor": valor, "tipo": tipo, "fuente_o_nota": fuente}

reg = [
    fila("semilla", args.seed, "técnico", "reproducibilidad"),
    fila("líneas por envío", "dependen de las unidades; calibradas a mediana y P90 por vía", "real (proxy EE. UU.)", "CBP FY2023-24"),
    fila("n_envios", N, "técnico", "objetivo de la propuesta: al menos 10.000 registros"),
    fila("reparto_vias (exprés/correo/carga/otra)", "59,8/26,0/10,3/3,9 %", "real (proxy EE. UU.)", "CBP FY2023-24, envíos de moda"),
    fila("tamaño: p(≤5 uds), mu, sigma por vía", "ver código (PARAM); unidades recortadas entre 6 y el tope", "real (proxy EE. UU.)", "CBP FY2023-24; carga solo FY2024 (sensibilidad FY2023 con --cargo FY2023)"),
    fila("tope de unidades por vía (P99)", "5 x el P99 de CBP por vía", "supuesto sobre datos CBP", "evita lotes de millones de unidades; sigma de cada vía ajustada a su P90 y P99 observados"),
    fila("reparto de categorías", "37,0/26,8/21,3/15,0 %", "real (proxy) con supuesto", "líneas de CBP usadas como proxy del reparto por envío"),
    fila("valor unitario por categoría", "lognormal, mediana 440-1.790 USD", "real (proxy EE. UU.)", "CBP tras la regla de extremos"),
    fila("peso por unidad: prendas y calzado", "subcategorías PEFCR equiprobables (media 0,31 kg y 0,78 kg/par)", "real (UE) con supuesto", "PEFCR ropa y calzado v3.1, tablas A.IV 2 y A.IV 3; la equiprobabilidad es supuesto"),
    fila("peso por unidad: bolsos y relojería/joyería", "0,50 y 0,05 kg (central)", "supuesto débil", "fichas de producto; sin fuente fiable"),
    fila("volumen por unidad", "4,7 L prendas; 15,6 L calzado", "real (UE) / supuesto", "PEFCR tabla 35; bolsos 8 L y relojes 0,3 L son supuestos"),
    fila("m3 por palé", M3_POR_PALET, "supuesto", "1 palé ≈ 1 m3 (EUIPO usa palé de 0,96 m2)"),
    fila("material por categoría", "ver código (MATERIAL_P)", "supuesto", "sin fuente"),
    fila("factor de incineración (tCO2/t)", "textil 0,29; caucho y cuero 0,41; plásticos 2,75", "real (IPCC)", "IPCC 2006 vol. 5, tablas 2.4 y 5.2 (solo CO2 fósil); rangos triangulares"),
    fila("origen de la mercancía", "China 41 %, Hong Kong 6 %, Turquía 19 %, otros 34 %", "real (UE)", "EUIPO/DG TAXUD, EU enforcement of IPRs 2025: incautaciones en frontera, por número de artículos, todas las categorías (redondeado); contraste OCDE/EUIPO 2025 (2020-21): China más de la mitad, Turquía 22 %, Hong Kong 12 %"),
    fila("elegible a procedimiento simplificado", "envío postal o exprés con ≤3 uds o <2 kg", "legal", "Reglamento 608/2013, arts. 2.19 y 26"),
    fila("adhesión del titular", P_ADHESION, "supuesto", "sin fuente"),
    fila("oposición del declarante (circuito litigioso)", P_OPOSICION, "real (UE) con supuesto", "EUIPO/DG TAXUD 2025: 7,63 % penal nacional + 0,32 % juicio de los procedimientos en frontera (≈ 8 %); se asume que equivale a oposición; sensibilidad 2-15 %"),
    fila("días de trámite", DIAS_TRAMITE, "legal (conversión propia)", "10 días hábiles ≈ 14 naturales; arts. 23 y 26"),
    fila("logística de destrucción (días)", "simplificado 0/2/10; resto 3/10/45", "supuesto", "triangular; sin plazo legal"),
    fila("inicio del procedimiento litigioso (días)", "14-28", "legal", "arts. 23.3 y 23.4"),
    fila("duración del procedimiento litigioso", f"mediana {LITIGIO_MEDIANA} d, sigma {LITIGIO_SIGMA}, máx. {LITIGIO_MAX}", "supuesto", "sin fuente; sensibilidad 90/365/730"),
    fila("espera por agrupación (días, S2)", "0/15/60 en envíos < 1 t", "supuesto", "triangular; solo en escenario S2"),
    fila("escenario S1", "destrucción con mínimo de 1 t por envío", "supuesto", "EUIPO p. 31 describe el mínimo solo cualitativamente"),
    fila("escenario S2", "destrucción proporcional al peso + espera", "supuesto", "equivale a agrupar lotes"),
    fila("tarifas de destrucción y almacén por país", "15 países", "real (UE, 2022)", "EUIPO 2023, anexos I y II; ver tarifas_ue_2022.csv"),
    fila("tarifa de destrucción para bolsos, calzado y relojería", "igual que textil", "supuesto", "solo hay tarifa de textil"),
    fila("quién paga ('parcial')", 0.5, "supuesto", "'si' = 1, 'parcial' = 0,5, 'no' = 0"),
    fila("Francia: coste del sistema", TARIFA_FR_SISTEMA, "supuesto", "la tarifa informada es 0 porque paga aduanas; se usa la media EUIPO"),
    fila("fecha del decomiso", "uniforme dentro del año fiscal de CBP", "simulada", "CBP solo da el año fiscal"),
]
reg = pd.DataFrame(reg)

# --------------------------------------------------------------------------
# 5. ESCRITURA
# --------------------------------------------------------------------------
envios.to_csv(OUT / "envios_sinteticos.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d")
costes.to_csv(OUT / "costes_por_pais.csv", index=False, encoding="utf-8")
reg.to_csv(OUT / "parametros_generador.csv", index=False, encoding="utf-8")
print(f"envios_sinteticos.csv: {len(envios):,} filas | costes_por_pais.csv: {len(costes):,} filas")
