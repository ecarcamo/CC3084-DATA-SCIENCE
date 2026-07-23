# Análisis preliminar de series

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
