# 1. Metodología LSTM

## Series seleccionadas

El Laboratorio 1 construyó siete series mensuales de viajeros. El enunciado de este laboratorio
pide trabajar con dos de ellas, sobre la misma partición, para que la comparación entre familias
de modelos sea directa.

El criterio de descarte fue la presencia de meses en cero dentro del entrenamiento. Un cero obliga
a `log1p` a devolver 0 y arrastra el mínimo del escalador hasta ese punto, lo que comprime el resto
de la serie, y además deja el MAPE indefinido en esos meses. Solo tres series cumplen la condición:
total, vía aérea y vía terrestre. Vía marítima acumula 16 ceros en entrenamiento y las tres series
por país de residencia acumulan 5 cada una.

De las tres candidatas se descartó vía terrestre. Total y vía aérea ya tenían análisis preliminar
propio en `notebooks/03_series_preliminar.ipynb`, y contrastan mejor entre sí: total es la serie
agregada de referencia y la que peor se predijo en el Laboratorio 1, con un MAPE de 58.11 % en el
mejor modelo, mientras que vía aérea fue la mejor predicha, con 35.62 %. Las dos ponen a prueba la
red en condiciones distintas.

| Serie | Ceros en train | Mejor modelo del Lab 1 | MAE | RMSE | MAPE |
|---|---:|---|---:|---:|---:|
| Total | 0 | SES | 175,088 | 194,791 | 58.11 % |
| Vía aérea | 0 | SES | 36,109 | 41,368 | 35.62 % |

La partición es la del Laboratorio 1 y no se rehace: entrenamiento de enero de 2009 a marzo de 2021
(147 meses) y prueba de abril de 2021 a junio de 2026 (63 meses). El conjunto de prueba no
interviene en ninguna etapa del ajuste ni del tuneo.

## Preprocesamiento

La transformación es la misma del Laboratorio 1, `log1p`, lo que mantiene comparables los dos
conjuntos de resultados. Estabiliza la varianza, que en estas series crece con el nivel, y tolera
valores en cero.

Sobre la serie transformada se ajusta un `MinMaxScaler` que lleva el entrenamiento al intervalo
[0, 1], rango en el que la LSTM converge sin saturar sus activaciones. El escalador se ajusta
únicamente con las 147 observaciones de entrenamiento. Para la serie total sus límites son 9.1881 y
13.1535 en escala `log1p`, exactamente el mínimo y el máximo del entrenamiento; uno de los 63 meses
de prueba cae fuera de ese intervalo al transformarse, prueba de que el escalador nunca lo vio.

La reversión de cualquier pronóstico aplica `inverse_transform`, luego `expm1` y finalmente un
recorte en cero, porque un conteo de viajeros negativo no tiene sentido.

## Ventaneo y tamaño de la muestra

La red se alimenta con ventanas deslizantes sobre el vector escalado. Cada observación de
entrenamiento es una secuencia de `ventana` meses consecutivos y su objetivo son los
`horizonte_salida` meses siguientes. Las ventanas se construyen en orden temporal y no se barajan.

| Estrategia | Ventana | Ventanas totales | Ajuste | Validación |
|---|---:|---:|---:|---:|
| Recursiva | 12 | 135 | 115 | 20 |
| Recursiva | 24 | 123 | 105 | 18 |
| Directa | 12 | 73 | 62 | 11 |
| Directa | 24 | 61 | 52 | 9 |

El tamaño de muestra es la restricción dominante del laboratorio. Con 147 observaciones mensuales,
la estrategia directa dispone de 73 ventanas con ventana de 12 meses, una cifra baja para una red
recurrente, y eso acota tanto la profundidad de la arquitectura como el tamaño de la rejilla.

## Estrategias de pronóstico

El horizonte de 63 meses se cubre de dos formas, y el laboratorio las compara en lugar de suponer
cuál conviene.

La estrategia recursiva entrena un modelo de un paso, `Dense(1)`, y realimenta cada predicción como
último elemento de la ventana para producir la siguiente. Aprovecha las 135 ventanas disponibles,
pero acumula error a lo largo de 63 iteraciones: cualquier sesgo inicial se propaga y la trayectoria
tiende a aplanarse.

La estrategia directa entrena un modelo con salida `Dense(63)` que emite el horizonte completo en
una sola pasada. No acumula error, pero aprende 63 salidas con apenas 73 ventanas y multiplica los
parámetros de la capa densa.

## Validación y criterio de selección

La validación es el último 15 % de las ventanas, tomado en orden temporal y sin barajar, de modo
que el modelo se evalúa siempre sobre meses posteriores a los que vio. El entrenamiento usa Adam
con tasa de aprendizaje 1e-3, pérdida `mse` y hasta 300 épocas, con `EarlyStopping` de paciencia 20
sobre `val_loss` y restauración de los mejores pesos. Se registra el número de épocas efectivas de
cada combinación.

El error de validación se calcula en viajeros, no en escala escalada, y con la misma mecánica que
se usará en el test:

- En la estrategia recursiva se toman los meses previos al tramo de validación como contexto y se
  pronostica recursivamente el tramo completo. Así se tunea contra el error multi-paso, que es el
  objetivo real, y no contra el error a un paso, que siempre parece bueno.
- En la estrategia directa se evalúan todas las ventanas de validación, cada una con sus 63 salidas,
  y el error se calcula sobre el conjunto completo de predicciones revertidas.

Se selecciona la combinación de menor `rmse_val`; si ninguna converge, la de menor `val_loss`. Este
`rmse_val` solo ordena configuraciones **dentro** de una misma estrategia, porque el tramo evaluado
no es el mismo en las dos: veinte meses consecutivos en la recursiva frente a once ventanas de 63
valores en la directa. La comparación entre estrategias se resuelve hasta el conjunto de prueba,
con las mismas métricas del Laboratorio 1.

La configuración ganadora se reentrena sobre las 147 observaciones completas, ya sin partición de
validación, fijando las épocas en las efectivas registradas durante el tuneo. Ese modelo produce el
pronóstico de los 63 meses de prueba.

## Rejilla de hiperparámetros

La rejilla es idéntica para las dos series y las dos estrategias, y se recorre por producto
cartesiano con `itertools`, igual que la rejilla SARIMA del Laboratorio 1.

| Hiperparámetro | Valores |
|---|---|
| Ventana | 12, 24 |
| Unidades por capa | 32, 64 |
| Capas LSTM | 1, 2 |
| Dropout | 0.0, 0.2 |
| Tasa de aprendizaje | 1e-3 |
| Tamaño de lote | 16 |

Son 16 combinaciones por estrategia, 32 por serie y 64 ajustes en el laboratorio, muy por encima
del mínimo de dos configuraciones distintas que pide el enunciado. Dos de ellas se destacan como
referencias de arquitectura: la LSTM de una capa con 32 unidades y sin dropout, que es el modelo
más pequeño, y la apilada de dos capas con 64 unidades y dropout 0.2, que es el más grande.

Las ventanas de 12 y 24 meses cubren uno y dos ciclos estacionales completos, la dimensión relevante
en series mensuales de turismo. El resto de valores se mantuvo acotado por dos razones: la muestra
es pequeña y arquitecturas mayores sobreajustan, y TensorFlow no dispone de GPU en Windows nativo
desde la versión 2.11, de modo que todo el laboratorio corre en CPU. Cada ajuste toma entre ocho y
doce segundos según la ventana y el número de capas, lo que sitúa cada rejilla completa en el orden
de tres minutos.

## Reproducibilidad

El enunciado exige que los resultados sean reproducibles. Antes de cada ajuste se fija la semilla 42
con `keras.utils.set_random_seed`, que cubre los generadores de Python, NumPy y TensorFlow, y se
activa `tf.config.experimental.enable_op_determinism()`, que elimina el no determinismo de las
operaciones sobre CPU. La sesión de Keras se limpia entre combinaciones para que los grafos no se
acumulen a lo largo de la rejilla.

Con eso, dos ejecuciones seguidas de `notebooks/08_lstm_preparacion.ipynb` devuelven exactamente los
mismos valores de `val_loss`, `mae_val`, `rmse_val` y épocas efectivas. Ese cuaderno documenta el
protocolo, verifica los conteos de ventanas y comprueba la ausencia de fuga de información antes de
que los cuadernos 09 y 10 ejecuten la rejilla completa.
