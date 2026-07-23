# Análisis exploratorio de datos

El análisis se realizó sobre la base ya limpia (`data/processed/base_limpia.csv`), producida por el
bloque de carga y limpieza. El notebook reproducible es `notebooks/02_eda.ipynb` y todas las
figuras referidas se guardan en `informe/figuras/` a 150 dpi. Se usó únicamente `matplotlib`,
según la convención del equipo.

## Panorama general y estadísticas descriptivas

La base agrega **52,287,937 viajeros** repartidos en **161,036 registros** y **210 meses**
consecutivos (enero 2009 a junio 2026). A nivel de fila, la variable de conteo `Viajero` está
fuertemente sesgada a la derecha: la mediana es de apenas **7** viajeros por combinación
mes/vía/frontera/país, mientras que la media es de **~325** y el máximo llega a **92,336**. Es
decir, conviven muchísimas combinaciones pequeñas (países lejanos en meses concretos) con unas
pocas combinaciones enormes (El Salvador por vía terrestre). Esta asimetría obliga a analizar la
serie **agregada por mes** en lugar de las filas individuales.

## a. Comportamiento temporal

La serie mensual total (figura `eda_serie_temporal.png`) promedia **~249,000 viajeros por mes** y
muestra una estacionalidad regular muy marcada. Se distinguen tres regímenes: crecimiento sostenido
de 2009 a 2019; el **colapso por la pandemia** desde marzo de 2020, con el mínimo histórico en
**abril 2020 (9,779 viajeros)**, alrededor del 4% de un mes normal; y la recuperación posterior a
2022, que retoma el nivel prepandemia. El corte train/test (2021-03) deja la caída en entrenamiento
y la recuperación en prueba.

Los totales anuales (figura `eda_totales_anuales.png`) confirman el crecimiento estructural: de
**2.03M** en 2009 a **4.69M** en 2019 (máximo histórico). En 2020 y 2021 el volumen se desploma a
**~1.27M** anuales; en 2022 hay un rebote fuerte y desde 2023 el nivel se estabiliza entre 3.2M y
3.6M, algo por debajo del pico de 2019 (en parte por el cambio metodológico de 2023). **2026 es
parcial** (solo enero-junio) y no es comparable con los años completos.

El patrón estacional (figura `eda_estacionalidad.png`) es claro y estable: **diciembre y enero** son
los meses más altos (fin de año y vacaciones), con un repunte secundario en **Semana Santa
(marzo-abril)** y el valle anual en **septiembre**. Esta estacionalidad anual es la señal más
relevante para el modelado posterior.

## b. Países con mayor cantidad de viajeros

Siguiendo la decisión del bloque de limpieza, **Guatemala se excluye del ranking** (residentes
retornando, **14.79M**, ~28.3% del total). El ranking de países de residencia (figura
`eda_top_paises.png`) está dominado por los vecinos centroamericanos y Norteamérica:

| Puesto | País | Viajeros acumulados |
|---|---|---|
| 1 | El Salvador | 16.21M |
| 2 | Estados Unidos de América | 7.05M |
| 3 | Honduras | 2.79M |
| 4 | México | 1.81M |
| 5 | Belice | 1.33M |

El peso de El Salvador y Honduras refleja el intenso tráfico terrestre fronterizo, mientras que
Estados Unidos representa el principal mercado aéreo. Los tres primeros son precisamente las series
por país que construye el bloque 1.

## c. Regiones con mayor cantidad de viajeros

La distribución regional (figura `eda_regiones.png`, sobre `Región dos`) es muy concentrada:
**América del Centro** aporta **37.4M (~71%)**, seguida de lejos por **América del Norte (9.38M,
~18%)**. Europa (~2.2M), América del Sur y el Caribe (~1.4M) y Cruceros (~1.1M) completan el grueso;
Asia, Oceanía y Oriente Medio son marginales. En síntesis, el ingreso a Guatemala es
**fundamentalmente regional**: casi 9 de cada 10 viajeros provienen del continente americano.

## d. Vías de ingreso y fronteras más utilizadas

La vía **terrestre domina con 31.99M (~61%)**, seguida de la **aérea (19.06M, ~36%)** y muy detrás
la **marítima (1.23M, ~2%)** (figura `eda_vias_fronteras.png`). Consistente con esto, la frontera
más usada es el aeropuerto **La Aurora (19.03M)** —que concentra casi toda la vía aérea—, seguido de
los pasos terrestres con El Salvador y México: **Valle Nuevo (10.73M)**, **San Cristóbal (5.36M)** y
**Pedro de Alvarado (4.39M)**. El predominio terrestre explica por qué El Salvador y Honduras
encabezan el ranking de países. La categoría "Cruceros" aparece mezclada como si fuera una frontera,
tal como se documentó en el bloque de limpieza.

## e. Valores faltantes, duplicados y atípicos

Tras la limpieza, la base **no tiene valores nulos ni filas duplicadas exactas**. Persisten dos
características conocidas y legítimas: **51,272 registros con valores decimales**
(estimaciones/prorrateos de la fuente, no errores) y **54 registros en exactamente 0**
(combinaciones sin ingresos ese mes). Ninguna se corrige.

Para los valores atípicos se aplicó el criterio de rango intercuartílico (IQR) sobre la serie
mensual (figura `eda_atipicos.png`). El criterio marca solo **2 atípicos, ambos altos**: **diciembre
2019 (515,820)** y **diciembre 2022 (526,190)**, que **no son errores** sino los picos estacionales
de fin de año. Es notable que el **desplome pandémico (mínimo de 9,779 en abril 2020) no se marca
como atípico por IQR** (el límite inferior resulta negativo): es un evento estructural, no un valor a
depurar. A nivel de fila, la distribución es de cola larga (visible en escala logarítmica): unas
pocas combinaciones grandes concentran el volumen. **Conclusión: no se elimina ningún atípico**;
todos son datos reales relevantes para el modelado.

## f. Síntesis

- **Temporal:** estacionalidad fuerte (picos diciembre-enero y Semana Santa, valle en septiembre),
  crecimiento 2009-2019, colapso pandémico 2020-2021 y recuperación 2022+.
- **Países:** El Salvador, Estados Unidos y Honduras concentran el ingreso (Guatemala se excluye por
  ser retorno de residentes).
- **Regiones:** América del Centro (~71%) y del Norte (~18%) dominan; el ingreso es esencialmente
  regional.
- **Vías y fronteras:** terrestre (~61%) sobre aérea (~36%); La Aurora, Valle Nuevo y San Cristóbal
  son las fronteras clave.
- **Calidad:** sin nulos ni duplicados; decimales y ceros son legítimos; los únicos atípicos
  estadísticos son picos de diciembre, no errores.
- **Tipos de viajero:** Turista (~72%) y Excursionista (~17%) son consistentes en todo el período;
  la categoría "Viajero" sufre el quiebre metodológico de 2023 documentado en el bloque de limpieza.
