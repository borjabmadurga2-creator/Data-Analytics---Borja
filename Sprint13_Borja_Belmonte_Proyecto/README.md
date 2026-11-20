# ¿Cuánto cuesta destruir lo falsificado?

Proyecto final · Borja Belmonte · Noviembre de 2026

Impacto financiero y ambiental de la mercancía falsificada retenida en la frontera de la UE, y cuándo compensa reciclar en lugar de destruir.

> **Aviso:** los 12.000 envíos analizados son **sintéticos** (simulados), porque no existe un registro público de cada envío retenido. Las tarifas por país, quién paga, los plazos del reglamento y los factores de emisión son reales; el resto son supuestos documentados.

## Resumen en tres líneas
- **H1:** reciclar solo compensa a partir de cierto peso (en España, 3,7 t con un coste fijo supuesto de 500 €): 35 de 12.000 envíos.
- **H2:** esperar sale barato; lo caro es destruir.
- **H3:** el plástico supone el 33 % del peso y el 81 % del CO₂.

## Contenido

| Carpeta | Qué hay |
| --- | --- |
| `1_informe/` | Informe final en PDF (4 páginas) |
| `2_datasets/` | Datos usados en Power BI: envíos sintéticos, costes por país, tarifas, parámetros y diccionario de columnas |
| `3_powerbi/` | Panel de Power BI exportado a PDF y documento con las medidas DAX |
| `4_presentacion/` | Presentación de la defensa |
| `codigo/` | Generador y validador del dataset y notebook de análisis (Python) |

## Cómo reproducir los datos
1. Instalar `pandas` y `numpy`.
2. Ejecutar `python generador_dataset.py` para generar el dataset (semilla 2026, reproducible).
3. Ejecutar `python validar_dataset.py` para comprobar IDs únicos, ausencia de nulos y coherencia de fechas.

## Fuentes principales
Reglamento (UE) n.º 608/2013; EUIPO (2023), *Storage and destruction of seized counterfeit goods in the EU*; IPCC (2006), *Guidelines for National Greenhouse Gas Inventories*, vol. 5; CBP (EE. UU.), años fiscales 2023-2024; Agencia Tributaria, Operación Quinto (2023). Las referencias completas están en el informe.
