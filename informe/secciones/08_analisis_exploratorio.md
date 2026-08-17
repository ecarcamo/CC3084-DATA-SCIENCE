# Inciso 8. Análisis exploratorio adicional

## Metodología

A diferencia del inciso 7, este inciso sí vuelve a abrir los 22 rasters originales (`data/raw/`), porque
sus preguntas son espaciales: requieren la posición de cada píxel dentro del lago, algo que los CSV
agregados de los incisos 4 y 6 no conservan. Las bandas `clorofila` y `agua` de las 22 combinaciones
lago-fecha se cargan una sola vez en memoria al inicio del notebook para evitar reabrir archivos.

Se define un valor "alto" de cianobacteria por lago como el **percentil 90** de todos los píxeles de
agua agrupados (pooling) de sus 11 fechas oficiales — el mismo enfoque de pooling usado en el inciso 6,
aplicado aquí para fijar un umbral en vez de una correlación. Ese umbral (`umbral_alto`, ajustable vía
`UMBRAL_PERCENTIL`) es la base de los incisos 8.1 y 8.2. Todo el código vive en
`notebooks/08_analisis_exploratorio.ipynb`.

## Resultados

### 8.1 Extensión espacial de la floración

Por cada fecha se calcula qué porcentaje del área de agua del lago supera el umbral alto de su lago —
la extensión espacial de la floración, una magnitud que el promedio del inciso 4 no distingue (un
promedio moderado puede venir de una floración extendida y débil, o de una muy intensa pero
localizada). El resultado se guarda en `data/processed/extension_floracion.csv` (columnas `lago`,
`fecha`, `pct_alto`, `n_pixeles_alto`, `n_pixeles_agua`, `umbral`) y se visualiza en
`extension_floracion.png`.

En **Amatitlán** (umbral = 10.57) el pico más extremo de todo el laboratorio (2026-06-19, ya señalado en
el inciso 4.4 como un caso a interpretar con cautela) domina también en extensión: **50.7%** del lago
supera el umbral, muy por encima de la siguiente fecha (2026-04-28, 34.0%); el resto de fechas se queda
por debajo del 7.3%. En **Atitlán** (umbral = 2.60) la floración relevante se reparte en más fechas:
2026-04-13 (33.1%) y 2026-04-28 (19.4%) encabezan, seguidas de un grupo de cuatro fechas entre 10.0% y
11.2%. Amatitlán concentra casi toda su extensión en un único evento extremo; Atitlán tiene varios
episodios de floración espacialmente relevantes.

### 8.2 Zonas persistentes de acumulación

Para cada lago se construye un mapa de persistencia: para cada píxel de agua, en cuántas de las 11
fechas su valor de `clorofila` superó el umbral alto, expresado como % de fechas
(`persistencia_floracion_atitlan.png`, `persistencia_floracion_amatitlan.png`). El cálculo se restringe
a píxeles clasificados como agua en al menos 9 de las 11 fechas de su lago (`MIN_FECHAS_VALIDAS`): sin
este filtro, un píxel de borde clasificado como agua en una sola fecha y que en esa única observación
supera el umbral mostraría un 100% de persistencia sustentado en un solo dato — el mismo tipo de píxel
de borde con ratios espectrales inestables ya documentado en el inciso 6. Ese artefacto era visible en
una primera versión del mapa de Atitlán como manchas aisladas fuera del contorno real del lago y un
valor de área persistente artificialmente alto (2.3%); tras el filtro desaparecen.

Con el filtro de robustez, la lectura es clara para **ambos** lagos: ninguno tiene una zona de
acumulación fuertemente persistente. En Amatitlán, prácticamente **0%** del área de agua estable superó
el umbral alto en 9 o más de sus 11 fechas (32.0% nunca lo superó). En Atitlán esa fracción es pequeña
pero algo mayor, **0.6%** (39.8% nunca lo superó) — visible como un fino borde de píxeles puntuales, no
como una región extensa de acumulación. Esto indica que la floración de **ambos** lagos es
predominantemente **episódica** — depende de eventos puntuales de aporte de nutrientes o condiciones
ambientales concretas (en Amatitlán, ligada a descargas del río Villalobos, ver inciso 7.3) — y no de
una fuente fija que acumule cianobacteria de forma continua en el mismo punto a lo largo del año y medio
estudiado.

### 8.3 Comparación de distribuciones entre fechas

Se compara la distribución completa de `clorofila` (no solo su promedio) entre fechas mediante tres
visualizaciones:

- **Histogramas** (`histogramas_distribucion_atitlan.png`, `histogramas_distribucion_amatitlan.png`):
  primera, pico y última fecha oficial de cada lago, superpuestas. La fecha de pico no solo desplaza la
  media sino que ensancha la distribución hacia valores más altos, consistente con una floración real y
  extendida.
- **Boxplots** (`boxplots_distribucion.png`): las 11 fechas de cada lago, sin outliers (se ocultan
  porque hay píxeles de borde de agua con ratios espectrales inestables, ver inciso 6, que aplastarían
  visualmente el cuerpo de la distribución). Confirman el mismo patrón temporal del inciso 4.
- **Mapas de diferencia** (`mapa_diferencia_atitlan.png`, `mapa_diferencia_amatitlan.png`): cambio neto
  entre la primera y la última fecha oficial de cada lago, con escala divergente centrada en cero. El
  cambio no es espacialmente uniforme: hay regiones con aumento marcado junto a otras sin cambio
  relevante o con disminución, reforzando que la floración tiene una componente espacial localizada que
  un solo promedio por fecha no captura.

### 8.4 Patrón estacional

Se clasifica cada fecha oficial como temporada seca (nov-abr) o lluviosa (may-oct) según el mes, y se
compara `clorofila_promedio` (inciso 4) y `pct_alto` (8.1) entre temporadas (`patron_estacional.png`).

El calendario oficial expone una limitación clara: Amatitlán solo tiene **una** fecha en temporada
lluviosa (2026-06-19), que es además la fecha atípica ya señalada en 8.1/8.2 y en el inciso 4.4 (mayor
nubosidad oficial del laboratorio, 13%). Por eso su comparación seca-lluviosa (5.77 vs. 11.47 de
`clorofila_media`; 6.0% vs. 50.7% de `pct_alto_medio`) está dominada casi por completo por ese único
dato. En Atitlán, con una muestra algo más balanceada (8 fechas secas, 3 lluviosas), la diferencia entre
temporadas es mínima y no concluyente (1.14 vs. 1.17 de `clorofila_media`; 9.8% vs. 10.5% de
`pct_alto_medio`). Con este conjunto de 22 fechas no hay evidencia sólida de un patrón simple
lluvia-vs-seca; lo que sí se sostiene en ambos lagos, en línea con el inciso 4.4, es la concentración de
picos hacia el **final de la temporada seca** (marzo-abril).

### 8.5 Interpretación conjunta

Amatitlán florea con mayor intensidad promedio (incisos 4 y 7) y de forma más pulsátil y concentrada en
un solo evento extremo (8.1). Atitlán, aunque menos intenso en promedio, reparte su floración relevante
en más fechas (8.1) y conserva una fracción de área con recurrencia algo mayor que Amatitlán, aunque
pequeña en ambos casos (0.6% vs. ~0%, 8.2). En ninguno de los dos lagos la floración depende de un punto
fijo de acumulación continua: en ambos casos es predominantemente episódica. Ambos lagos concentran
además sus picos hacia el final de la temporada seca (8.4), más que responder a una dicotomía estricta
lluvia/seca. La implicación práctica de monitoreo es la misma para ambos: conviene vigilar la superficie
completa del lago en las fechas de mayor riesgo (fin de temporada seca), en vez de concentrarse en un
solo punto fijo de acumulación.

## Figuras generadas

- `informe/figuras/extension_floracion.png`
- `informe/figuras/persistencia_floracion_atitlan.png`
- `informe/figuras/persistencia_floracion_amatitlan.png`
- `informe/figuras/histogramas_distribucion_atitlan.png`
- `informe/figuras/histogramas_distribucion_amatitlan.png`
- `informe/figuras/boxplots_distribucion.png`
- `informe/figuras/mapa_diferencia_atitlan.png`
- `informe/figuras/mapa_diferencia_amatitlan.png`
- `informe/figuras/patron_estacional.png`

## Decisiones técnicas

- El umbral "alto" se define por pooling (percentil 90 de los píxeles de agua agrupados de las 11
  fechas de cada lago), no como un valor fijo por fecha, para que sea comparable entre fechas del mismo
  lago y ajustable (`UMBRAL_PERCENTIL`) sin tocar el resto del código — mismo criterio de diseño que
  `UMBRAL_FLORACION` en el inciso 7.
- Los mapas de persistencia y diferencia enmascaran los píxeles que nunca fueron agua en las fechas
  comparadas (`np.ma.masked_where`), para no mezclar tierra/nubes con la señal de agua.
- El mapa de persistencia además excluye los píxeles clasificados como agua en menos de 9 de las 11
  fechas de su lago (`MIN_FECHAS_VALIDAS`). Sin este filtro, píxeles de borde poco observados producían
  valores de persistencia del 100% sustentados en una sola fecha, inflando artificialmente el resultado
  (se detectó comparando el mapa con y sin el filtro: el área "persistente" de Atitlán caía de 2.3% a
  0.6% al aplicarlo).
- Los boxplots de 8.3 ocultan outliers (`showfliers=False`) por la misma razón de ratios inestables en
  píxeles de borde de agua ya documentada en el inciso 6.
- El notebook guarda `data/processed/extension_floracion.csv` inmediatamente después de calcularlo y
  antes de generar cualquier figura, con una celda de verificación (`assert`) que confirma columnas
  esperadas, `pct_alto` en [0, 100] y conteo de fechas por lago consistente con `FECHAS_OFICIALES`,
  siguiendo el mismo patrón de self-check del inciso 7.
