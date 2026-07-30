# 2. Modelado LSTM de la serie total

La serie total es la agregada de referencia del estudio y la peor predicha del Laboratorio 1, con
un MAPE de 58.11 % en su mejor modelo. Todo lo que sigue está en `notebooks/09_lstm_total.ipynb`,
sobre el protocolo descrito en la sección 1 y con el split del Laboratorio 1 sin modificar:
entrenamiento de enero de 2009 a marzo de 2021, 147 meses, y prueba de abril de 2021 a junio de
2026, 63 meses.

## La rejilla ejecutada y su costo

Se recorrieron las 16 combinaciones de la rejilla para cada una de las dos estrategias, 32 ajustes
en total. La rejilla completa costó 1.9 minutos de CPU, entre 2.8 y 5.8 segundos por ajuste, y el
detalle de las 32 filas quedó en `resultados/lstm_tuneo_total.csv`.

Ninguna combinación falló. Las 32 entrenaron hasta que `EarlyStopping` las detuvo, restauraron sus
mejores pesos y produjeron un pronóstico finito; el bloque de captura de excepciones de `grid_lstm`
no se activó ni una vez y no hay filas con `rmse_val` infinito. Tampoco hubo pronósticos negativos
ni valores nulos.

Lo que sí hubo fue estancamiento, y conviene reportarlo porque afecta la lectura de los resultados.
Las 16 combinaciones de la estrategia recursiva pararon entre las épocas 21 y 25, y como la
paciencia del `EarlyStopping` es de 20 épocas, eso significa que su mejor época de validación estuvo
entre la 1 y la 5. El modelo de un paso alcanza su mejor error de validación casi de inmediato y
después solo mejora sobre el entrenamiento. Las combinaciones directas se comportaron mejor: épocas
efectivas entre 28 y 78, con la mejor época entre la 8 y la 58.

## Configuraciones seleccionadas

| Estrategia | Ventana | Unidades | Capas | Dropout | Épocas efectivas | Parámetros | MAE val. | RMSE val. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Recursiva | 24 | 64 | 1 | 0.2 | 24 | 16,961 | 121,320 | 149,716 |
| Directa | 24 | 64 | 2 | 0.0 | 42 | 54,015 | 97,483 | 130,075 |

Las dos ganadoras coinciden en la ventana de 24 meses y en las 64 unidades por capa, y se separan
en la profundidad y la regularización: la recursiva prefiere una sola capa con dropout de 0.2 y la
directa dos capas sin dropout. Los dos valores de `rmse_val` de la tabla no son comparables entre
sí, porque cada estrategia valida sobre un tramo distinto; la comparación entre estrategias se
resuelve en el test.

Dentro de cada estrategia, en cambio, la dispersión sí es informativa. Entre la mejor y la peor
configuración recursiva hay un 39.9 % de diferencia en `rmse_val`, de 149,716 a 209,463 viajeros.
Entre la mejor y la peor directa hay un 15.3 %, de 130,075 a 149,939. La elección de
hiperparámetros importa más cuando el error se realimenta 63 veces.

### Las dos arquitecturas de referencia

El enunciado pide al menos dos modelos con configuraciones distintas por serie. La rejilla contiene
16 por estrategia, y dos de ellas delimitan el rango de arquitecturas exploradas: la LSTM de una
capa con 32 unidades y sin dropout, la más pequeña, y la apilada de dos capas con 64 unidades y
dropout 0.2, la más grande.

| Estrategia | Arquitectura | Ventana | Parámetros | RMSE val. |
|---|---|---:|---:|---:|
| Recursiva | 1 capa, 32 unidades, dropout 0.0 | 24 | 4,385 | 187,605 |
| Recursiva | 2 capas, 64 unidades, dropout 0.2 | 24 | 49,985 | 155,304 |
| Directa | 1 capa, 32 unidades, dropout 0.0 | 24 | 6,431 | 136,507 |
| Directa | 2 capas, 64 unidades, dropout 0.2 | 24 | 54,015 | 132,213 |

El contraste entre las dos arquitecturas depende de la estrategia. En la recursiva la arquitectura
mayor mejora el error de validación en 17 %; en la directa la diferencia baja a 3 %. La salida
`Dense(63)` ya concentra la mayor parte de la capacidad del modelo directo, y agregar profundidad
recurrente aporta poco.

## Qué hiperparámetro movió el error

La comparación toma la mediana de `rmse_val` entre los dos valores de cada hiperparámetro, dentro
de cada estrategia, para que un solo ajuste afortunado no defina la lectura.

| Estrategia | Hiperparámetro | Valor bajo | RMSE val. | Valor alto | RMSE val. | Brecha |
|---|---|---:|---:|---:|---:|---:|
| Recursiva | Unidades | 32 | 180,907 | 64 | 155,652 | 16.2 % |
| Recursiva | Dropout | 0.0 | 181,810 | 0.2 | 162,257 | 12.1 % |
| Recursiva | Capas | 1 | 175,112 | 2 | 156,732 | 11.7 % |
| Recursiva | Ventana | 12 | 162,257 | 24 | 171,988 | 6.0 % |
| Directa | Ventana | 12 | 138,634 | 24 | 131,920 | 5.1 % |
| Directa | Dropout | 0.0 | 135,615 | 0.2 | 139,625 | 3.0 % |
| Directa | Unidades | 32 | 138,971 | 64 | 135,615 | 2.5 % |
| Directa | Capas | 1 | 137,244 | 2 | 136,215 | 0.8 % |

En la estrategia recursiva manda el número de unidades, con una brecha de 16.2 % a favor de 64,
seguido del dropout, 12.1 % a favor de 0.2, y del número de capas, 11.7 % a favor de dos. Los tres
apuntan en la misma dirección: un modelo de un paso que se realimentará 63 veces necesita capacidad
y regularización, porque cualquier sesgo sistemático se acumula a lo largo del horizonte. La
ventana es el único hiperparámetro cuya mediana favorece al valor bajo, 12 meses, aunque la
configuración ganadora usa 24; la brecha de 6.0 % en la mediana convive con el mejor resultado
individual en el otro extremo, señal de que la ventana interactúa con el resto y no domina por sí
sola.

En la estrategia directa el orden se invierte y todas las brechas se achican. Manda la ventana, con
5.1 % a favor de 24 meses, y el resto queda por debajo del 3 %. El número de capas es
prácticamente irrelevante, con 0.8 %. Con la salida completa emitida en una sola pasada, lo
determinante es cuánta historia ve la red, no cuán profunda es.

![Cinco mejores configuraciones por estrategia](../figuras/lstm_tuneo_total.png)

La figura muestra las cinco mejores de cada estrategia y no las diez mejores del conjunto, porque
`rmse_val` no es comparable entre estrategias: la recursiva se valida sobre veinte meses
consecutivos y la directa sobre once ventanas de 63 valores cada una. Un ranking global mezclaría
dos escalas distintas.

## Curvas de entrenamiento

![Curvas de pérdida del mejor modelo por estrategia](../figuras/lstm_curvas_total.png)

Las dos curvas describen problemas distintos. En la recursiva la pérdida de validación toca su
mínimo en la época 4, en 0.129, y a partir de ahí se queda plana mientras la de entrenamiento sigue
bajando hasta 0.006, más de veinte veces menor. Es sobreajuste puro desde la quinta época: el
modelo memoriza las 105 ventanas de ajuste sin mejorar su capacidad de generalizar. En la directa
la validación baja durante una docena de épocas hasta 0.068 y a partir de ahí apenas se mueve,
con su mínimo formal en la época 22, mientras la de entrenamiento termina en 0.004; la brecha final
es de 16 veces en lugar de 22 y hay más aprendizaje real antes del estancamiento.

La lectura práctica es que el `EarlyStopping` con paciencia 20 hizo su trabajo en las dos
estrategias, y que ampliar el número máximo de épocas no habría cambiado nada: ninguna de las 32
combinaciones se acercó al tope de 300.

## Predicción sobre el test

Cada configuración ganadora se reentrenó sobre las 147 observaciones completas, sin partición de
validación, con las épocas fijadas en las efectivas del tuneo, y ese modelo produjo los 63 meses de
prueba. Las dos predicciones están en `resultados/predicciones/total_lstm_recursivo.csv` y
`total_lstm_directo.csv`.

| Modelo | MAE | RMSE | MAPE | Media pronosticada | Sesgo medio |
|---|---:|---:|---:|---:|---:|
| lstm_recursivo | 143,303 | 164,706 | 46.90 % | 133,712 | −142,973 |
| lstm_directo | **76,957** | **100,290** | **33.76 %** | 232,356 | −44,329 |

El test real promedia 276,685 viajeros mensuales. La estrategia directa gana en las tres métricas:
46.30 % menos MAE, 39.11 % menos RMSE y 13.13 puntos porcentuales menos de MAPE. La diferencia es
demasiado grande para atribuirla al azar del ajuste y no se explica por la muestra, porque la
estrategia directa entrena con menos de la mitad de las ventanas, 61 contra 123 con ventana de 24
meses. Se explica por el sesgo: la recursiva subestima 62 de los 63 meses, con un error medio de
−142,973 viajeros, un 51.7 % del nivel medio del test, mientras que la directa subestima 45 de 63,
con −44,329, un 16.0 %. Realimentar 63 veces un modelo entrenado con datos que terminan en el punto
más bajo de la pandemia arrastra el pronóstico hacia ese nivel, y ni la ventana de 24 meses ni las
64 unidades lo evitan. La acumulación de error pesó más que el tamaño de la muestra.

![Predicciones LSTM de la serie total](../figuras/lstm_pred_total.png)

## ¿Reproduce la recuperación pospandemia?

Esta es la pregunta que el Laboratorio 1 dejó abierta, porque los cinco modelos anteriores
subestimaron la recuperación sin excepción.

| Año | Test real | lstm_directo | Diferencia | lstm_recursivo | Diferencia |
|---|---:|---:|---:|---:|---:|
| 2021 (abr-dic) | 110,282 | 198,112 | +79.6 % | 81,033 | −26.5 % |
| 2022 | 359,680 | 213,867 | −40.5 % | 112,870 | −68.6 % |
| 2023 | 270,726 | 236,230 | −12.7 % | 136,809 | −49.5 % |
| 2024 | 299,490 | 263,214 | −12.1 % | 151,202 | −49.5 % |
| 2025 | 299,770 | 263,777 | −12.0 % | 159,088 | −46.9 % |
| 2026 (ene-jun) | 280,439 | 188,390 | −32.8 % | 162,489 | −42.1 % |

La estrategia recursiva no la reproduce, y falla igual que los modelos del Laboratorio 1: su
trayectoria es una curva monótona que sube de 64,931 a 163,165 viajeros y se detiene ahí, sin
estacionalidad visible, entre un 47 % y un 69 % por debajo del real en los cuatro años completos. Su
correlación con el test es de 0.507, de modo que acierta la dirección general y nunca el nivel.

La estrategia directa sí la reproduce parcialmente, y es el primer modelo de esta serie en las dos
entregas que lo consigue. Emite un perfil estacional con picos y valles, alcanza el nivel correcto
desde 2023 y se estabiliza en un error anual de entre 12.0 % y 12.7 % en el tramo 2023-2025. Sus
dos zonas de error son los extremos del horizonte: sobreestima 2021 en 79.6 %, cuando la serie real
todavía estaba deprimida, y se queda 40.5 % corta en el rebote de 2022, el año del pico de 526,190
viajeros que ningún modelo entrenado hasta marzo de 2021 podía anticipar.

## Lectura honesta de la calidad predictiva

El resultado es una mejora sustancial y sigue siendo un pronóstico de calidad limitada. Un MAPE de
33.76 % significa que el error típico es de un tercio del valor real: sirve para dimensionar
órdenes de magnitud y para planificación agregada, no para asignación fina de capacidad sin
intervalos amplios ni reentrenamiento periódico.

Tres reservas que conviene dejar escritas:

La primera es que el modelo no captura el pico de 2022 y ese es justamente el evento de mayor
interés operativo del periodo. Su acierto está en el régimen estable posterior, no en la
transición.

La segunda es que la mejora frente al Laboratorio 1 depende de una coincidencia favorable entre lo
que el modelo aprendió y lo que ocurrió. La LSTM directa reconstruye el patrón prepandemia en lugar
de prolongar el nivel deprimido del final del entrenamiento, y el test resultó ser un retorno a
niveles prepandemia. Si la serie no se hubiera recuperado, esa misma propiedad habría producido una
sobreestimación sistemática y el orden del ranking sería el inverso.

La tercera es de tamaño de muestra. La estrategia ganadora estima 54,015 parámetros con 61
ventanas de entrenamiento, y sus curvas muestran sobreajuste desde la época doce. El resultado del
test es sólido porque el protocolo nunca vio ese tramo, pero la varianza de la estimación es alta y
no debería leerse como una medida precisa de la capacidad de la arquitectura.
