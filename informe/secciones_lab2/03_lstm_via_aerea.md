# 3. Modelado LSTM de la vía aérea

La vía aérea es la serie mejor predicha del Laboratorio 1, con un MAPE de 35.62 % usando SES, la
vía menos volátil (CV de 0.216) y la de recuperación más rápida: alcanzó el 80 % del nivel de 2019
en diciembre de 2021. También es la serie donde 18 de las 36 especificaciones SARIMA se
descartaron por pronóstico explosivo, así que la vara a superar es la más alta de las siete series
y el fracaso de los modelos paramétricos lineales ya está documentado. Todo lo que sigue está en
`notebooks/10_lstm_via_aerea.ipynb`, sobre el protocolo descrito en la sección 1 y con el split del
Laboratorio 1 sin modificar: entrenamiento de enero de 2009 a marzo de 2021, 147 meses, y prueba de
abril de 2021 a junio de 2026, 63 meses.

## La rejilla ejecutada y su costo

Se recorrieron las 16 combinaciones de la rejilla para cada una de las dos estrategias, 32 ajustes
en total. La rejilla completa costó 2.4 minutos de CPU, entre 3.2 y 9.3 segundos por ajuste, y el
detalle de las 32 filas quedó en `resultados/lstm_tuneo_via_aerea.csv`.

Ninguna combinación falló. Las 32 entrenaron hasta que `EarlyStopping` las detuvo, restauraron sus
mejores pesos y produjeron un pronóstico finito; no hay filas con `rmse_val` infinito ni pronósticos
negativos o nulos.

El estancamiento temprano de la estrategia recursiva se repite en esta serie: las 16 combinaciones
pararon entre las épocas 21 y 26, así que con una paciencia de 20 épocas su mejor época de
validación estuvo entre la 1 y la 6. La estrategia directa volvió a comportarse mejor: épocas
efectivas entre 29 y 59, con la mejor época estimada entre la 9 y la 39.

## Configuraciones seleccionadas

| Estrategia | Ventana | Unidades | Capas | Dropout | Épocas efectivas | Parámetros | MAE val. | RMSE val. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Recursiva | 12 | 32 | 1 | 0.0 | 26 | 4,385 | 39,360 | 45,464 |
| Directa | 24 | 32 | 2 | 0.0 | 49 | 14,751 | 25,853 | 38,698 |

Las dos ganadoras coinciden en 32 unidades por capa y en dropout 0.0, y se separan en la ventana y
la profundidad: la recursiva prefiere la ventana corta de 12 meses con una sola capa, y la directa
la ventana larga de 24 meses con dos capas. A diferencia de la serie total, ninguna de las dos
estrategias eligió aquí la configuración más grande de la rejilla (64 unidades, dropout 0.2): la
vía aérea es más regular y no exige esa capacidad extra.

Dentro de cada estrategia la dispersión sigue siendo informativa. Entre la mejor y la peor
configuración recursiva hay un 50.6 % de diferencia en `rmse_val`, de 45,464 a 68,450 viajeros.
Entre la mejor y la peor directa hay un 33.5 %, de 38,698 a 51,648.

### Las dos arquitecturas de referencia

El enunciado pide al menos dos modelos con configuraciones distintas por serie. La rejilla contiene
16 por estrategia; estas dos delimitan el rango explorado: la LSTM de una capa con 32 unidades y sin
dropout, la más pequeña, y la apilada de dos capas con 64 unidades y dropout 0.2, la más grande.

| Estrategia | Ventana | Arquitectura | Parámetros | RMSE val. |
|---|---:|---|---:|---:|
| Recursiva | 12 | 1 capa, 32 unidades, dropout 0.0 | 4,385 | 45,464 |
| Recursiva | 12 | 2 capas, 64 unidades, dropout 0.2 | 49,985 | 58,576 |
| Recursiva | 24 | 1 capa, 32 unidades, dropout 0.0 | 4,385 | 68,450 |
| Recursiva | 24 | 2 capas, 64 unidades, dropout 0.2 | 49,985 | 50,901 |
| Directa | 12 | 1 capa, 32 unidades, dropout 0.0 | 6,431 | 41,248 |
| Directa | 12 | 2 capas, 64 unidades, dropout 0.2 | 54,015 | 44,593 |
| Directa | 24 | 1 capa, 32 unidades, dropout 0.0 | 6,431 | 44,508 |
| Directa | 24 | 2 capas, 64 unidades, dropout 0.2 | 54,015 | 45,875 |

Aquí el contraste no es monótono como en la serie total. En la estrategia recursiva la arquitectura
grande pierde con ventana de 12 meses (28.8 % peor) pero gana con ventana de 24 (34.5 % mejor): el
efecto de la capacidad depende de cuánta historia ve la red, no solo de su tamaño. En la estrategia
directa la arquitectura pequeña gana en las dos ventanas, aunque por márgenes moderados: 8.1 % con
ventana de 12 y 3.1 % con ventana de 24. Para esta serie, más parámetros no compran de forma
consistente mejor validación.

## Qué hiperparámetro movió el error

La comparación toma la mediana de `rmse_val` entre los dos valores de cada hiperparámetro, dentro
de cada estrategia, para que un solo ajuste afortunado no defina la lectura.

| Estrategia | Hiperparámetro | Valor bajo | RMSE val. | Valor alto | RMSE val. | Brecha |
|---|---|---:|---:|---:|---:|---:|
| Recursiva | Capas | 1 | 56,641 | 2 | 49,337 | 14.8 % |
| Recursiva | Dropout | 0.0 | 48,979 | 0.2 | 51,233 | 4.6 % |
| Recursiva | Ventana | 12 | 49,155 | 24 | 51,233 | 4.2 % |
| Recursiva | Unidades | 32 | 49,337 | 64 | 50,461 | 2.3 % |
| Directa | Dropout | 0.0 | 42,102 | 0.2 | 45,234 | 7.4 % |
| Directa | Capas | 1 | 43,629 | 2 | 45,072 | 3.3 % |
| Directa | Ventana | 12 | 44,754 | 24 | 43,963 | 1.8 % |
| Directa | Unidades | 32 | 44,712 | 64 | 43,963 | 1.7 % |

En la estrategia recursiva el factor dominante es el número de capas, con 14.8 % a favor de dos
capas; le siguen el dropout, 4.6 % a favor de 0.0, y la ventana, 4.2 % a favor de 12 meses. El orden
es distinto al de la serie total, donde mandaban las unidades: aquí una segunda capa recurrente
ayuda más que ensanchar la primera.

En la estrategia directa manda el dropout, con 7.4 % a favor de 0.0, y el resto queda por debajo
del 3.5 %. La regularización explícita no aporta en una serie ya de por sí menos volátil: con 147
observaciones y una serie estable, el dropout resta capacidad sin compensarla con menos sobreajuste.

![Cinco mejores configuraciones por estrategia](../figuras/lstm_tuneo_via_aerea.png)

La figura muestra las cinco mejores de cada estrategia y no las diez mejores del conjunto, porque
`rmse_val` no es comparable entre estrategias: la recursiva se valida sobre un tramo consecutivo y
la directa sobre varias ventanas de 63 valores cada una.

## Curvas de entrenamiento

![Curvas de pérdida del mejor modelo por estrategia](../figuras/lstm_curvas_via_aerea.png)

Las dos curvas describen el mismo problema en escalas distintas. En la recursiva la pérdida de
validación toca su mínimo en la época 6, en 0.124, y a partir de ahí se queda plana en 0.137
mientras la de entrenamiento sigue bajando hasta 0.0006, más de doscientas veces menor: sobreajuste
puro desde la sexta época. En la directa la validación baja durante unas 28 épocas hasta 0.058 y
ahí se estabiliza, mientras la de entrenamiento termina en 0.0025; hay más aprendizaje real antes
del estancamiento, igual que en la serie total.

El `EarlyStopping` con paciencia 20 volvió a hacer su trabajo en las dos estrategias: ninguna de las
32 combinaciones se acercó al tope de 300 épocas.

## Predicción sobre el test

Cada configuración ganadora se reentrenó sobre las 147 observaciones completas, sin partición de
validación, con las épocas fijadas en las efectivas del tuneo, y ese modelo produjo los 63 meses de
prueba. Las dos predicciones están en `resultados/predicciones/via_aerea_lstm_recursivo.csv` y
`via_aerea_lstm_directo.csv`.

| Modelo | MAE | RMSE | MAPE | Media pronosticada | Sesgo medio | Correlación con test |
|---|---:|---:|---:|---:|---:|---:|
| lstm_recursivo | 31,638 | 37,766 | 31.14 % | 63,494 | −31,110 | 0.391 |
| lstm_directo | **22,635** | **29,623** | **24.93 %** | 85,409 | −9,196 | −0.150 |

El test real promedia 94,605 viajeros mensuales. La estrategia directa gana en las tres métricas:
28.5 % menos MAE, 21.6 % menos RMSE y 6.21 puntos porcentuales menos de MAPE. La brecha entre
estrategias es menor que en la serie total, porque aquí la recursiva ya parte de un sesgo más chico,
pero el orden es el mismo: la salida completa en una sola pasada evita la acumulación de error de la
recursiva a lo largo de 63 pasos.

El sesgo agregado confirma la historia: −32.9 % del nivel medio en la recursiva, que subestima 59 de
los 63 meses, contra −9.7 % en la directa, que subestima 34 de 63. Pero la correlación negativa de
la directa es la advertencia que el MAE y el RMSE no muestran por sí solos: el modelo gana en error
agregado porque su nivel medio está cerca del real, no porque reproduzca la dirección del movimiento
mes a mes. Esto se desarrolla en la sección siguiente.

![Predicciones LSTM de la vía aérea](../figuras/lstm_pred_via_aerea.png)

## ¿Reproduce la recuperación pospandemia?

La vía aérea fue la vía de recuperación más rápida en el Laboratorio 1. La tabla anual muestra si el
LSTM captura esa dinámica o solo su nivel promedio.

| Año | Test real | lstm_recursivo | lstm_directo |
|---|---:|---:|---:|
| 2021 (abr-dic) | 65,700 | 37,905 | 82,331 |
| 2022 | 117,232 | 56,206 | 85,084 |
| 2023 | 82,153 | 66,793 | 89,985 |
| 2024 | 95,279 | 71,494 | 96,849 |
| 2025 | 99,081 | 73,403 | 87,270 |
| 2026 (ene-jun) | 107,307 | 74,041 | 54,920 |

La estrategia recursiva falla igual que en la serie total: una trayectoria monótona creciente que
nunca despega de los 74,000 viajeros, muy por debajo del pico de 117,232 en 2022 y del nivel de
2026. Su correlación de 0.391 con el test viene de la tendencia general al alza, no de acertar
niveles.

La estrategia directa cuenta una historia distinta a la de la serie total. Sobreestima 2021 en
25.3 % (82,331 contra 65,700, el año todavía deprimido), y desde ahí se acerca al nivel real en 2023
y 2024, dentro de un 10 % de diferencia, pero vuelve a alejarse al final: subestima 2025 en 11.9 % y
colapsa en el primer semestre de 2026, con 54,920 contra 107,307, un 48.8 % por debajo. Ese colapso
final es lo que produce la correlación negativa pese al buen MAE agregado: el modelo aprendió un
nivel medio razonable para el tramo intermedio de la serie, pero no anticipa que la recuperación
siguiera acelerando hacia 2026.

## Lectura honesta de la calidad predictiva

El LSTM directo mejora la mejor referencia del Laboratorio 1 (SES) en las tres métricas: 37.3 %
menos MAE, 28.4 % menos RMSE y 10.68 puntos porcentuales menos de MAPE, de 35.62 % a 24.93 %. Es la
primera vez en las dos entregas que un modelo de la vía aérea baja del 25 % de MAPE. Pero conviene
dejar tres reservas escritas, porque las métricas de error agregado esconden más de lo que muestran
en esta serie.

La primera es la correlación negativa de la estrategia ganadora con el test, −0.150. El modelo bate
a SES en MAE y RMSE porque su nivel medio (85,409) está más cerca del real (94,605) que el de la
recursiva, no porque reproduzca la dirección del movimiento mes a mes. Un pronóstico que acertara la
dinámica de la serie tendría correlación positiva incluso con métricas de error algo peores; este es
el caso inverso.

La segunda es el colapso en el tramo final: 48.8 % por debajo del real en el primer semestre de
2026, justo el periodo más reciente y el de mayor interés operativo. El modelo aprendió el nivel de
2023-2024 y lo proyectó hacia adelante, sin anticipar que la recuperación siguiera acelerando.

La tercera es de tamaño de muestra, igual que en la serie total: la estrategia ganadora estima
14,751 parámetros con relativamente pocas ventanas de entrenamiento, y su curva de validación se
estabiliza temprano, en la época 28. El resultado del test es sólido porque el protocolo nunca vio
ese tramo, pero la varianza de la estimación es alta y el buen MAPE de esta serie no debería leerse
como evidencia de que el LSTM directo entiende la trayectoria de la vía aérea mejor de lo que
entiende la de la serie total: en ambas, gana por cancelación de errores en direcciones opuestas más
que por seguimiento fiel de la dinámica.
