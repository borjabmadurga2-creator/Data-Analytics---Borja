# Datasets del proyecto: ¿Cuánto cuesta destruir lo falsificado?

Autor: Borja Belmonte · Proyecto final, noviembre de 2026

## Aviso importante
Los **12.000 envíos son sintéticos** (simulados): no existe un registro público de cada envío retenido en la UE.
Lo real son las tarifas por país, quién paga, los plazos del reglamento y los factores de emisión. Todo lo demás son supuestos documentados en `parametros_generador.csv`.

## Archivos

| Archivo | Contenido |
| --- | --- |
| `envios_sinteticos.csv` | 12.000 envíos, una fila por envío y 27 columnas (peso, material, circuito, días de custodia, emisiones…) |
| `costes_por_pais.csv` | Coste de cada envío si se retuviera en cada uno de los 15 países (12.000 × 15 = 180.000 filas) |
| `tarifas_ue_2022.csv` | Tarifas de almacenaje y destrucción por país, y quién las paga (EUIPO, 2023) |
| `parametros_generador.csv` | Parámetros del generador, clasificados como real, supuesto o técnico, con su fuente |
| `diccionario_columnas.csv` | Descripción y origen de cada columna de las dos tablas principales |

## Uso en Power BI
Importar `envios_sinteticos.csv`, `costes_por_pais.csv` y `tarifas_ue_2022.csv`. `costes_por_pais` se relaciona con `envios_sinteticos` por `id_envio`, y con `tarifas_ue_2022` por país.

## Cómo se generaron
El código está en la carpeta `../codigo/`:
- `generador_dataset.py` genera los datos (semilla 2026, reproducible).
- `validar_dataset.py` comprueba IDs únicos, ausencia de nulos y coherencia de fechas.

Requiere `pandas` y `numpy`. La comparación con los datos de CBP necesita los archivos originales de CBP; sin ellos, se omite.

## Fuentes
- Tarifas: EUIPO (2023), *Storage and destruction of seized counterfeit goods in the EU*.
- Emisiones: IPCC (2006), *Guidelines for National Greenhouse Gas Inventories*, vol. 5.
- Forma de los envíos: CBP (EE. UU.), años fiscales 2023-2024.
- Marco legal: Reglamento (UE) n.º 608/2013.
