# Inciso 3. Índices de cianobacteria, NDVI y NDWI

## Metodología

El índice de cianobacteria, el NDVI y el NDWI se calculan directamente en la Process API de Sentinel
Hub, en la misma pasada en que se descargan los rasters (inciso 2), mediante el evalscript propio
`src/evalscripts.py`. Ese evalscript porta la matemática del script oficial *CyanoLakes Chlorophyll-a
NDCI L1C* (repositorio `sentinel-hub/custom-scripts`), pero en lugar de devolver el colormap RGB del
script original devuelve valores numéricos: primero calcula el NDCI, `(B05-B04)/(B05+B04)`, y luego
aplica el mismo polinomio cúbico del script oficial para obtener `clorofila`
(`826.57·NDCI³ - 176.43·NDCI² + 19·NDCI + 4.071`), que es la banda que responde al índice de
cianobacteria pedido en el enunciado. El NDVI y el NDWI se calculan con las bandas exactas que exige
el enunciado: `NDVI = (B08-B04)/(B08+B04)` y `NDWI = (B03-B08)/(B03+B08)`.

Este notebook carga con `src.raster.abrir` el raster de la primera fecha oficial de cada lago
(`FECHAS_OFICIALES`), aplica la máscara de agua propia del script (`agua > 0`) para descartar los
píxeles de tierra, y grafica los tres índices. La escala de color de cada mapa se recorta al percentil
2–98 dentro de la máscara de agua (`src.raster.recorte_percentil`) en lugar de usar el mínimo/máximo
absoluto, porque la banda `clorofila` presenta valores extremos en píxeles mixtos de borde donde el
denominador del NDCI (`B05+B04`) es cercano a cero; este recorte evita que esos outliers saturen la
visualización sin alterar los datos ni el evalscript.

## Resultados

En **Atitlán** (2025-01-18) el índice de cianobacteria se mantiene mayormente entre -1 y 1 dentro del
lago, con un valor algo más bajo en la zona central-oeste (más profunda) y algo más alto cerca de las
orillas y bahías, coherente con aguas más someras y con mayor influencia de sedimento o vegetación
ribereña. El NDVI es negativo en todo el cuerpo de agua (aprox. -0.35 a -0.10), como corresponde a
agua abierta sin vegetación emergente, y el NDWI es alto y uniforme (0.40–0.60), confirmando que la
máscara delimita correctamente agua.

En **Amatitlán** (2025-01-28) el índice de cianobacteria es notablemente más alto y con más
variación espacial que en Atitlán, con valores predominantemente entre 3.5 y 5 y una zona de valores
bajos y aislados en el extremo suroeste del lago. Los valores más altos se concentran en el brazo
norte y en la franja central del lago, zonas de menor profundidad y más cercanas a la mancha urbana y
a los principales afluentes, mientras que el NDVI y el NDWI muestran el mismo patrón esperado de agua
abierta (NDVI negativo, NDWI alto) en toda la superficie.

La comparación entre ambos lagos en esta misma escala de percentiles evidencia una diferencia de
magnitud relevante: el rango de `clorofila` en Amatitlán (~3.5 a 5) está muy por encima del de
Atitlán (~-1 a 1), consistente con el mayor deterioro ambiental reportado para Amatitlán frente a
Atitlán.

## Decisiones técnicas

- No se reprocesa nada: los tres índices ya vienen calculados desde la descarga (inciso 2); este
  inciso es de visualización y no vuelve a llamar a la Process API salvo que el archivo no exista aún
  en `data/raw/`.
- Se usa un `cmap` distinto por índice (`viridis` para clorofila, `RdYlGn` para NDVI, `Blues` para
  NDWI) para facilitar la lectura visual de cada magnitud.
- El recorte por percentil se aplica por separado a cada lago y cada índice, ya que el rango de valores
  razonables difiere fuertemente entre Atitlán y Amatitlán.
