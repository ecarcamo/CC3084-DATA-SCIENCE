# Inciso 7. Análisis de los lagos y comparación entre ellos

## Metodología

Este inciso no vuelve a abrir rasters: parte de los productos ya calculados en incisos previos,
`data/processed/serie_temporal_cianobacteria.csv` (inciso 4, promedio de `clorofila` por lago y fecha
sobre la máscara de agua) y `data/processed/correlaciones_indices.csv` (inciso 6, correlación de
Pearson entre `clorofila` y NDVI/NDWI por lago). Sobre esos dos CSV se calculan estadísticos resumen
por lago (7.1), se comparan intensidad y frecuencia de floraciones bajo un criterio común (7.2), se
discuten posibles causas de la diferencia observada (7.3) y se cierra con conclusiones que citan
explícitamente cada figura y tabla generada (7.4). Todo el código vive en
`notebooks/07_comparacion_lagos.ipynb`.

Para la frecuencia de floraciones se definió un **umbral absoluto común a ambos lagos**
(`UMBRAL_FLORACION`, percentil 75 de `clorofila_promedio` combinando las 22 fechas de ambos lagos) en
lugar del criterio relativo por lago (z-score) usado en el inciso 4. La razón: un umbral relativo por
lago mide floraciones "atípicas para ese lago", no permite decir cuál de los dos lagos floreció más
veces en términos absolutos, porque cada uno se compara solo contra su propia historia. El umbral
absoluto usa la misma vara para ambos, lo que sí permite comparar frecuencia entre lagos.

## Resultados

### 7.1 Proliferación por lago

La tabla `resumen_por_lago` (celda de 7.1 en el notebook) reporta, por lago: media, mediana y
desviación estándar de `clorofila_promedio` en las 11 fechas oficiales, el valor y la fecha del pico, y
el cambio entre la primera y la última fecha del período. Amatitlán muestra un nivel medio y una
mediana sistemáticamente más altos que Atitlán a lo largo de todo el período estudiado (enero 2025 –
julio 2026), consistente con lo ya observado en el inciso 3 para las primeras fechas de cada lago.

### 7.2 Intensidad y frecuencia entre lagos

- **Intensidad** — `distribucion_intensidad_lagos.png`: boxplot de `clorofila_promedio` por lago sobre
  las 11 fechas de cada uno. Las cajas no se solapan en su mayor parte: Amatitlán opera en un rango de
  intensidad más alto que Atitlán durante todo el período, no solo en fechas puntuales.
- **Frecuencia** — `frecuencia_floraciones_lagos.png`: número y porcentaje de fechas que superan
  `UMBRAL_FLORACION` (tabla `frecuencia_por_lago`), mismo umbral para ambos lagos.
- **Evolución conjunta** — `comparacion_temporal_ambos_lagos.png`: ambas series de tiempo en un mismo
  eje con la línea de umbral superpuesta, para ubicar en qué fechas concretas cada lago cruzó el
  umbral de floración.
- El resumen consolidado (media, pico, `n_floraciones`, `frecuencia_pct` por lago) se guarda en
  `data/processed/comparacion_lagos.csv`.

### 7.3 Diferencias en las causas

Amatitlán es un lago pequeño y somero (~15 km², ~1188 msnm) al borde de la mancha urbana del área
metropolitana de Guatemala, y recibe directamente al río Villalobos con aguas residuales domésticas e
industriales y escorrentía urbana. Menor volumen de agua implica menor dilución de nutrientes y mayor
calentamiento, ambas condiciones favorables para la cianobacteria. Atitlán, en cambio, es un lago de
caldera volcánica mucho más grande y profundo (~130 km², ~1560 msnm), con menor densidad urbana
relativa a su tamaño; el mayor volumen diluye mejor la carga de nutrientes y la mayor altitud/
profundidad mantiene temperaturas más bajas, aunque no lo exime de floraciones puntuales cuando
coinciden aportes de nutrientes con aguas cálidas y estancadas. La nubosidad de las 22 fechas
oficiales (`NUBOSIDAD_OFICIAL`) es baja en la gran mayoría de los casos (<5%), por lo que la brecha de
intensidad observada entre lagos no es atribuible a diferencias de calidad de imagen.

### 7.4 Conclusiones

Amatitlán presenta una proliferación de cianobacteria más intensa (media y mediana más altas, cajas de
boxplot separadas de las de Atitlán) y, bajo el mismo criterio de umbral, más frecuente que Atitlán en
el período estudiado. Esto es consistente con la relación entre `clorofila` y NDVI/NDWI reportada en el
inciso 6 (`correlaciones_indices.csv`, figura `correlacion_indices.png`) y con la discusión de causas
de 7.3: menor tamaño y profundidad más mayor presión urbana y de aguas residuales en Amatitlán frente a
Atitlán.

## Figuras generadas

- `informe/figuras/distribucion_intensidad_lagos.png`
- `informe/figuras/frecuencia_floraciones_lagos.png`
- `informe/figuras/comparacion_temporal_ambos_lagos.png`

## Decisiones técnicas

- Se reutilizan íntegramente los CSV de los incisos 4 y 6 en vez de recalcular sobre rasters, para que
  este inciso corra en segundos y no dependa de tener los 22 `.tif` descargados localmente.
- El umbral de floración es una variable ajustable en la parte superior del notebook
  (`UMBRAL_FLORACION`), no un valor fijo dentro de la lógica de conteo, para que pueda recalibrarse sin
  tocar el resto del código.
- El notebook incluye una celda de verificación (`assert`) que confirma que `comparacion_lagos.csv`
  tiene las columnas esperadas y que el conteo de floraciones por lago nunca excede su número de
  fechas oficiales.
