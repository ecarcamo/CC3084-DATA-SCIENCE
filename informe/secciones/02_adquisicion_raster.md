# Inciso 2. Adquisición de datos raster

## Metodología

Para cada lago y cada una de sus 11 fechas oficiales se descarga, mediante la Process API, un único GeoTIFF de 10 bandas producido por un evalscript propio (`src/evalscripts.py`). El evalscript reproduce la matemática del script CyanoLakes Chlorophyll-a NDCI L1C del repositorio oficial de custom scripts de Sentinel Hub (detector de cuerpos de agua, índice de vegetación flotante, NDCI y polinomio de clorofila), pero en lugar de devolver el colormap RGB original devuelve los valores numéricos de cada índice, que es lo que requiere el análisis temporal y espacial de los incisos siguientes. Con esa misma pasada se calculan también NDVI y NDWI con las bandas mínimas indicadas en el enunciado (B04/B08 y B03/B08 respectivamente), evitando así descargar la escena completa o bandas no utilizadas.

Las 10 bandas de salida son: `rojo, verde, azul, ndci, clorofila, fai, ndvi, ndwi, agua, mascara`. La banda `agua` es la máscara de cuerpo de agua del propio script, usada como sustituto del geojson que no fue provisto para este laboratorio. La banda `mascara` corresponde al `dataMask` nativo de Sentinel-2, que indica si el sensor capturó datos en ese píxel.

Cada archivo se guarda en `data/raw/<lago>/<lago>_<fecha>.tif`, con la resolución fijada en 20 metros que se justifica en la sección 1. La función de descarga evita solicitar de nuevo un archivo que ya existe en disco, para no repetir el consumo de Processing Units al reejecutar el notebook.

## Resultados

Las 22 descargas (11 fechas por lago) se completan sin errores, con dimensiones de 1365x875 píxeles para Atitlán y 670x458 para Amatitlán, ambas dentro del límite de 2500x2500 píxeles de la Process API. La máscara de agua delimita correctamente el contorno de cada lago en todas las fechas revisadas, incluyendo la forma característica de Atitlán entre sus tres volcanes y la forma alargada de Amatitlán.

El manifiesto de rasters (`data/processed/manifiesto_rasters.csv`) reporta 100% de cobertura válida (`dataMask`) para las 22 fechas, incluyendo `2026-02-07` en Amatitlán, que el enunciado señala con cobertura válida parcial (~57.1%). Esta aparente contradicción se explica porque la Process API construye, para un intervalo de tiempo de un día completo, un mosaico con todas las adquisiciones que cubren el bounding box en esa fecha, en lugar de limitarse al identificador de un único producto del catálogo. Una verificación puntual con la banda de máscara de nubes (`CLM`) sobre esa misma fecha confirma 0% de nubosidad y 100% de cobertura válida en el área del lago, lo que indica que el mosaico de Sentinel Hub llena el vacío que sí está presente en la escena individual señalada por el enunciado. Se documenta este hallazgo porque contradice la expectativa inicial y aclara que el dato entregado por la Process API es, para efectos de este laboratorio, más completo que el de la escena individual.

## Decisiones técnicas

- El tamaño en píxeles de cada bounding box se calcula con `bbox_to_dimensions`, que convierte internamente a UTM para obtener un tamaño de píxel cercano a 20 metros reales, evitando la distorsión de trabajar directamente en grados.
- No se reproyecta la salida a UTM: se mantiene en EPSG:4326 para simplificar la superposición posterior con mapas interactivos (folium) en los incisos 5 y 8, a costa de una ligera anisotropía entre el tamaño de píxel horizontal y vertical, despreciable a la latitud de ambos lagos.
- Se descarta agregar una banda de nubosidad (`CLM`) al evalscript de forma permanente: la verificación puntual mostró 0% de nubosidad para el caso que motivó la duda, y añadirla de forma sistemática excede el alcance de estos dos primeros incisos.
