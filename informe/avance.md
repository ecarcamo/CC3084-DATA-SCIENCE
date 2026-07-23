---
title: "Laboratorio 1 — Series de Tiempo · Avance"
---

# Universidad del Valle de Guatemala
## Facultad de Ingeniería — CC3084 Data Science
### Laboratorio 1 — Series de Tiempo (Avance)

**Integrantes:** Esteban Cárcamo · Hugo · Ernesto

**Fecha:** 23 de julio de 2026

Este documento reúne el avance del Laboratorio 1: la carga y limpieza de la base de
migración, el análisis exploratorio de datos y el análisis preliminar de dos series de
tiempo. El alcance del avance es diagnóstico; el ajuste y la evaluación de modelos de
pronóstico corresponden a la entrega final.

\newpage

# 1. Datos y limpieza

## Origen y dimensiones

La base de datos contiene el registro mensual del ingreso de viajeros internacionales a Guatemala
entre enero de 2009 y junio de 2026: 210 meses consecutivos, sin huecos, y 161,036 registros en
formato largo (una fila por combinación de mes, vía de ingreso, frontera, país o agrupación de
residencia y tipo de viajero). Los datos se proporcionan únicamente para uso académico y no
corresponden a cifras oficiales de INGUAT ni del Instituto Guatemalteco de Migración.

La base combina tres tramos con distinta fuente y metodología: 2009-2020 proviene de respaldos
históricos, 2021-2022 de una entrega del Instituto Guatemalteco de Migración, y 2023 en adelante
de un sistema depurado de conteos de INGUAT. Esto implica que los niveles no siempre son
perfectamente comparables entre tramos, en particular alrededor del quiebre metodológico de
2022 a 2023.

Además, desde 2023 la columna de país deja de reportar país individual (226 posibles hasta 2022)
y pasa a reportar por agrupación de mercado (27 grupos). Los mercados principales —El Salvador,
Estados Unidos, Honduras, México, entre otros— siguen siendo comparables como serie a lo largo de
todo el período; los países más pequeños quedan absorbidos dentro de su agrupación a partir de
2023.

## Limpieza aplicada

Sobre la base cruda se detectaron y corrigieron cuatro inconsistencias, sin eliminar ninguna fila
y conservando siempre el valor original en una columna paralela con sufijo `_raw`:

- **Región dos**: la categoría de cruceros aparece partida en dos etiquetas según el año
  ("Cruceristas" de 2009 a 2021, "Cruceros" en 2022), cuando en realidad es la misma categoría.
  Se unificó en un solo valor. Adicionalmente existía el valor literal `"0"` en 13 registros de
  2022 (821 viajeros), que se reetiquetó como "Sin especificar".
- **País**: se detectaron 13 pares de valores que representan el mismo país pero con capitalización
  distinta (por ejemplo, "OTROS PAISES DEL MUNDO" frente a "Otros Paises Del Mundo", o variantes
  con conectores en mayúscula como "República De Corea"). En todos los casos la variante mal
  escrita corresponde a un puñado de registros aislados de 2020-2021, mientras que la forma
  correcta se usa de manera consistente en el resto del período. Se unificaron ambas hacia la
  variante con más registros.
- **Regiones OMT**: existían los valores basura `"0x2a"` y `"SIN ESPECIFICAR"`, que se unificaron
  en la etiqueta "Sin especificar".
- **Frontera**: la categoría "Cruceros" aparece mezclada en la misma columna junto con fronteras
  terrestres, aéreas y marítimas legítimas (y junto con la categoría genérica "Otra frontera").
  Se decidió no modificarla, ya que corregirla requeriría inventar una frontera específica que no
  está en los datos; queda documentado aquí para quien la use más adelante.
- **Viajero**: 51,272 registros (cerca de un tercio de la base) tienen valores decimales. No son
  errores: corresponden a estimaciones y prorrateos de la fuente, no a conteos exactos de
  personas. Además, 54 registros valen exactamente 0. En ningún caso se redondeó ni se descartó
  esta información; se documenta como una característica conocida de los datos.

Tras aplicar la limpieza se confirmó por código que la base no contiene valores nulos ni filas
duplicadas exactas.

## Decisiones fijadas

**Guatemala como país de residencia.** El valor "Guatemala" en la columna de país acumula
aproximadamente 14.8 millones de viajeros a lo largo de todo el período, un 28% del total. Estos
registros corresponden a residentes guatemaltecos que regresan al país, no a viajeros
internacionales entrantes en el sentido habitual. Se decidió **mantenerlos dentro de la serie
total** de viajeros, para no alterar el total oficial reportado por la fuente, pero
**excluirlos del ranking de países de residencia**. Bajo este criterio, el Top 3 de países de
residencia queda: El Salvador, Estados Unidos de América y Honduras.

**2026 como año parcial.** El último año de la base solo cubre de enero a junio. Cualquier
comparación de totales anuales que incluya 2026 debe advertir explícitamente que ese año está
incompleto; no es comparable en la misma base que los años completos.

**Quiebre en "Tipo de Viajero".** Esta variable toma cuatro valores: Turista, Excursionista,
Viajero y Cruceristas. Entre 2022 y 2023 la categoría "Viajero" cae fuertemente (de
aproximadamente 1.06 millones a 0.33 millones) porque el sistema depurado de 2023 excluye a los
viajeros no turísticos de alta frecuencia (comercio fronterizo, tránsito), mientras que el tramo
anterior sí los incluía. Esta caída es un efecto de cambio de criterio metodológico, no una caída
real de actividad, y debe tenerse en cuenta al interpretar la serie total o cualquier serie que
dependa de esta variable. Para comparaciones de visitantes consistentes en todo el período se
recomienda usar la suma de Turista + Excursionista.

## Split de entrenamiento y prueba

El split es temporal, nunca aleatorio, sobre los 210 meses de la base:

- **Entrenamiento**: 2009-01 a 2021-03 (147 meses, 70% de los datos).
- **Prueba**: 2021-04 a 2026-06 (63 meses, 30% de los datos).

Este corte no es arbitrario: deja la caída provocada por la pandemia (colapso a partir de marzo de
2020, con un piso en 2020-2021 de aproximadamente 27% del nivel de 2019) **dentro** del conjunto
de entrenamiento, mientras que la **recuperación completa** posterior a 2022 queda **dentro** del
conjunto de prueba. Esto significa que cualquier modelo entrenado con este split aprende a partir
de un choque y su punto más bajo, pero es evaluado prediciendo una dinámica de recuperación
distinta a la que vio durante el entrenamiento. Es un punto que debe justificarse explícitamente
al interpretar el desempeño de los modelos, no una limitación que deba ocultarse.

## Series construidas

Las categorías de análisis elegidas por el equipo son **vías de ingreso** y **países de residencia
(Top 3, excluyendo Guatemala)**. Todas las series son mensuales, con exactamente dos columnas
(`fecha` y `viajeros`) e índice completo sin huecos (los meses sin registros quedan en 0). Cada
serie tiene además una versión de entrenamiento truncada a 2021-03.

| Serie | Inicio | Fin | Frecuencia |
|---|---|---|---|
| Total de viajeros | 2009-01 | 2026-06 | Mensual |
| Vía aérea | 2009-01 | 2026-06 | Mensual |
| Vía terrestre | 2009-01 | 2026-06 | Mensual |
| Vía marítima | 2009-01 | 2026-06 | Mensual |
| País: El Salvador | 2009-01 | 2026-06 | Mensual |
| País: Estados Unidos de América | 2009-01 | 2026-06 | Mensual |
| País: Honduras | 2009-01 | 2026-06 | Mensual |

Se verificó por código que la suma de las series de las tres vías de ingreso reproduce, mes a mes,
la serie total de viajeros.

\newpage

# 2. Análisis exploratorio de datos

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

\newpage

# 3. Análisis preliminar de series

Este bloque analiza dos series mensuales de viajeros sobre el **conjunto de entrenamiento**
(enero 2009 a marzo 2021, 147 observaciones): la **Total mensual** —obligatoria— y la de
**Vía Aérea**, elegida por contraste, ya que colapsó a casi cero en 2020 mientras la vía
terrestre mantuvo flujo. El notebook reproducible es `notebooks/03_series_preliminar.ipynb`
y las figuras se guardan en `informe/figuras/` con prefijo `serie_` a 150 dpi, usando solo
`matplotlib` y `statsmodels`. El objetivo es **diagnosticar** cada serie (tendencia,
estacionalidad, estacionariedad y órdenes de diferenciación), **no** ajustar modelos: eso
corresponde a la entrega final.

## Serie 1 — Total mensual

**Ficha.** Inicio enero 2009, fin marzo 2021, frecuencia mensual (12 observaciones por año),
**147 observaciones**. Media **~237,000** viajeros/mes; mínimo **9,779 (mayo 2020)** por el
colapso pandémico y máximo **515,820 (diciembre 2019)** en el pico prepandemia.

**Lectura del gráfico.** La serie en niveles (figura `serie_total_nivel.png`) muestra un
**nivel creciente** (de ~169,000 en 2009 a ~391,000 en 2019), una **estacionalidad anual
marcada** y el **quiebre abrupto de 2020**. La amplitud de las oscilaciones **crece con el
nivel**: la desviación estándar pasa de **~32,000** en 2009-2013 a **~74,000** en 2014-2019.
Esa amplitud creciente justifica una descomposición **multiplicativa** y una transformación
que estabilice la varianza.

**Descomposición.** La descomposición multiplicativa (figura `serie_total_descomposicion.png`)
separa tendencia, estacionalidad y residuo. La **tendencia** crece de forma sostenida hasta
2019 y se desploma en 2020. La **estacionalidad** es estable, con **pico en diciembre**
(factor ~1.35) y **valle en septiembre** (~0.80), más un repunte secundario en Semana Santa
(marzo). Para el INGUAT esto implica dimensionar capacidad hotelera y fronteriza para el fin
de año y aprovechar el valle de septiembre para mantenimiento y promoción. El **residuo no se
comporta como ruido**: 2020 deja una estructura enorme sin explicar y distorsiona los factores
multiplicativos de ese año, por lo que la lectura estacional se toma del tramo estable
2009-2019. En consecuencia, la serie **no es estacionaria en media ni en varianza**.

**Transformación.** Se aplica `log1p` —hay meses de valores muy bajos, por eso `log1p` y no
`log`— y se compara con la original (figura `serie_total_log.png`). La transformación
**estabiliza la varianza** y vuelve aproximadamente aditiva la estacionalidad, condición útil
para el modelado.

**Estacionariedad en media.** La ACF en niveles (figura `serie_total_acf_niveles.png`) **decae
lentamente** y se mantiene alta en muchos rezagos, evidencia clásica de no estacionariedad; la
PACF muestra un primer rezago dominante. La prueba de Dickey-Fuller aumentada confirma el
diagnóstico:

| Serie | Estadístico ADF | p-valor | V. críticos (1% / 5% / 10%) | Conclusión |
|---|---|---|---|---|
| Log niveles | -2.236 | 0.194 | -3.480 / -2.883 / -2.578 | No se rechaza H0: **no estacionaria** |
| Log con d=1 | -3.100 | 0.027 | -3.480 / -2.883 / -2.578 | Se rechaza al 5%: estacionaria |
| Log con d=1 y D=1 (s=12) | -6.148 | <0.001 | -3.485 / -2.886 / -2.580 | Fuertemente estacionaria |

La hipótesis nula del ADF es la existencia de una **raíz unitaria**; con p=0.194 en niveles no
se rechaza, así que la serie no es estacionaria en media. Una **diferencia regular (d=1)** ya
la vuelve estacionaria al 5%, y añadir una **diferencia estacional (D=1, s=12)** la limpia por
completo (figura `serie_total_acf_diff.png`). **Conclusión: d=1, D=1.** La ACF de la serie
diferenciada sugiere componentes de media móvil de orden bajo (q~1) y estacional (Q~1), y la
PACF, componentes autorregresivos de orden bajo (p~1, P~1). Hasta aquí llega el diagnóstico:
no se ajusta ningún modelo.

## Serie 2 — Vía Aérea

**Ficha.** Inicio enero 2009, fin marzo 2021, frecuencia mensual, **147 observaciones**. Media
**~89,000** viajeros/mes; mínimo **489 (abril 2020)** —el aeropuerto La Aurora prácticamente
cerró— y máximo **157,842 (diciembre 2019)**.

**Lectura del gráfico.** La serie en niveles (figura `serie_aerea_nivel.png`) tiene una
tendencia creciente **más suave** que la total (de ~78,000 en 2009 a ~124,000 en 2019) y una
**caída aún más profunda** en 2020. La amplitud también crece con el nivel (std ~12,000 en
2009-2013 a ~18,000 en 2014-2019), de nuevo a favor de descomposición multiplicativa y
transformación.

**Descomposición.** La descomposición multiplicativa (figura `serie_aerea_descomposicion.png`)
muestra tendencia creciente hasta 2019 y estacionalidad con **pico en diciembre** (~1.28) y
**valle en septiembre** (~0.81), con un repunte adicional en julio, coherente con las
vacaciones del hemisferio norte y el peso del mercado estadounidense en la vía aérea. El
residuo tampoco es ruido: 2020 domina la varianza. Ni la media ni la varianza son constantes.

**Transformación.** `log1p` es imprescindible aquí porque el valor de abril 2020 (489) está
muy cerca de cero (figura `serie_aerea_log.png`); estabiliza la varianza.

**Estacionariedad en media.** Caso matizado. La ADF en niveles da un resultado que
formalmente rechazaría la raíz unitaria, pero la ACF (figura `serie_aerea_acf_niveles.png`)
decae lentamente y la tendencia y la estacionalidad son evidentes: el ADF está siendo
**engañado por la fuerte reversión pandémica** (la caída y el rebote imitan una media estable).

| Serie | Estadístico ADF | p-valor | V. críticos (1% / 5% / 10%) | Conclusión |
|---|---|---|---|---|
| Log niveles | -4.018 | 0.001 | -3.477 / -2.882 / -2.578 | Rechazo formal, pero ACF y tendencia contradicen |
| Log con d=1 | -3.213 | 0.019 | -3.480 / -2.883 / -2.578 | Estacionaria al 5% |
| Log con d=1 y D=1 (s=12) | -6.396 | <0.001 | -3.485 / -2.886 / -2.580 | Fuertemente estacionaria |

El diagnóstico robusto —ACF de decaimiento lento y estacionalidad clara— indica diferenciar
igualmente: con **d=1** y **D=1 (s=12)** la ACF/PACF quedan limpias (figura
`serie_aerea_acf_diff.png`). **Conclusión práctica: d=1, D=1**, con órdenes sugeridos p~1,
q~1 y estacionales P~1, Q~1. No se ajusta ningún modelo. Este caso ilustra por qué la ADF no
debe leerse aislada de la ACF.

## Comportamiento durante y después de la pandemia

Ambas series colapsan en marzo-abril de 2020, pero **no en la misma magnitud** (figura
`serie_pandemia_comparacion.png`, índice base media 2019 = 100):

| Serie | Media 2019 | Mínimo pandémico | Caída |
|---|---|---|---|
| Total | ~390,985 | 9,779 (mayo 2020) | **~97.5%** |
| Vía Aérea | ~123,615 | 489 (abril 2020) | **~99.6%** |

La aérea cae casi por completo porque el aeropuerto cerró, mientras que el total conserva un
**piso mayor** gracias a la vía terrestre, que nunca se detuvo del todo por el tráfico
fronterizo esencial. En el índice base 2019=100 la aérea toca prácticamente cero mientras el
total mantiene un pequeño colchón. La recuperación posterior queda **fuera del entrenamiento**
(el corte es marzo 2021), pero el distinto fondo de caída anticipa dinámicas de recuperación
diferentes: la aérea, más golpeada, parte de más abajo. Para el modelado esto confirma que
**cada serie necesita su propio diagnóstico**; total y aérea no comparten el mismo
comportamiento pandémico.

## Síntesis

- **Total mensual:** tendencia creciente 2009-2019, estacionalidad con pico en diciembre y
  valle en septiembre, varianza creciente (requiere `log1p`), no estacionaria en niveles
  (ADF p=0.194); **d=1, D=1**, órdenes sugeridos p~1, q~1, P~1, Q~1.
- **Vía Aérea:** misma forma general con caída pandémica más profunda; la ADF en niveles
  rechaza de forma engañosa, pero la ACF exige diferenciar igual; **d=1, D=1**, órdenes
  sugeridos p~1, q~1, P~1, Q~1.
- **Pandemia:** caída de ~97.5% (total) frente a ~99.6% (aérea); la vía terrestre explica el
  piso mayor del total. Cada serie requiere diagnóstico y modelado propios.
- **Alcance:** el bloque se detiene en el diagnóstico; el ajuste de modelos y la evaluación
  de pronósticos corresponden a la entrega final.

\newpage

# 4. Conclusión del avance

El avance deja la base **limpia, documentada y verificada** (sin nulos ni duplicados, con las
inconsistencias de la fuente resueltas o registradas), un **análisis exploratorio** que
caracteriza el ingreso de viajeros a Guatemala —fuertemente estacional, regional y dominado por
la vía terrestre— y un **diagnóstico preliminar** de las series Total y Vía Aérea. Ambas series
resultan **no estacionarias en media ni en varianza**: requieren transformación logarítmica y
una diferenciación regular más una estacional (**d=1, D=1**), con órdenes tentativos p~1, q~1,
P~1, Q~1 sugeridos por la ACF/PACF. El evento pandémico afecta de forma desigual a cada serie
(caída de ~97.5% en el total frente a ~99.6% en la aérea), lo que confirma que cada una necesita
su propio modelo. Con este diagnóstico queda preparado el terreno para el ajuste y la comparación
de modelos de la entrega final.
