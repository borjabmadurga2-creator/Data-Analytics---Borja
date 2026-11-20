# ¿Cuánto cuesta destruir lo falsificado?

Proyecto final · Borja Belmonte · Noviembre de 2026

Impacto financiero y ambiental de la mercancía falsificada retenida en la frontera de la UE, y cuándo compensa reciclar en lugar de destruir.

> **Aviso:** los 12.000 envíos analizados son **sintéticos** (simulados), porque no existe un registro público de cada envío retenido. Las tarifas por país, quién paga, los plazos del reglamento y los factores de emisión son reales; el resto son supuestos documentados.

## Resumen en tres líneas
- **H1:** reciclar solo compensa a partir de cierto peso (en España, 3,7 t con un coste fijo supuesto de 500 €): 35 de 12.000 envíos.
- **H2:** esperar sale barato; lo caro es destruir.
- **H3:** el plástico supone el 33 % del peso y el 81 % del CO₂.

## Contenido de la entrega

| Entregable | Dónde está |
| --- | --- |
| Informe final (PDF, 4 páginas) | [`informe_final_ESG_falsificaciones.pdf`](informe_final_ESG_falsificaciones.pdf) |
| Conjuntos de datos usados en Power BI | carpeta [`Datasets/`](Datasets/) |
| Trabajo de Power BI en PDF | [`powerbi_ESG_falsificaciones.pdf`](powerbi_ESG_falsificaciones.pdf) |
| Documento con las fórmulas DAX | [`medidas_DAX_ESG_falsificaciones.pdf`](medidas_DAX_ESG_falsificaciones.pdf) |
| Presentación de la defensa | [`¿Cuánto cuesta destruir lo falsificado.pptx`](<¿Cuánto cuesta destruir lo falsificado.pptx>) |
| Código: generador, validador y notebook de análisis | carpeta [`Codigo/`](Codigo/) |

## Cómo reproducir los datos
1. Instalar `pandas` y `numpy`.
2. Ejecutar `python generador_dataset.py` (en `Codigo/`) para generar el dataset (semilla 2026, reproducible).
3. Ejecutar `python validar_dataset.py` para comprobar IDs únicos, ausencia de nulos y coherencia de fechas.

Más detalle en el [README de `Datasets/`](Datasets/README.md).

## Fuentes principales
Reglamento (UE) n.º 608/2013; EUIPO (2023), *Storage and destruction of seized counterfeit goods in the EU*; IPCC (2006), *Guidelines for National Greenhouse Gas Inventories*, vol. 5; CBP (EE. UU.), años fiscales 2023-2024; Agencia Tributaria, Operación Quinto (2023). Las referencias completas están en el informe.
