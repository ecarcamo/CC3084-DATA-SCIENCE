# 4. Análisis comparativo: LSTM contra los modelos del Laboratorio 1

Esta sección responde el punto 1.4 del enunciado. El desarrollo está en
`notebooks/11_comparativo_lstm.ipynb`, que no reentrena nada: lee las métricas de los cuadernos 09
y 10, las métricas del Laboratorio 1 en `resultados/metricas_modelos.csv` y las predicciones
guardadas en `resultados/predicciones/`, y deja dos tablas consolidadas, `metricas_lstm.csv` y
`comparativo_lstm_lab1.csv`.

## Criterio de comparación

Las dos familias se comparan sobre exactamente el mismo conjunto de prueba, los 63 meses de abril
de 2021 a junio de 2026, con las mismas tres métricas y calculadas por la misma función,
`src.evaluacion.metricas`, que se usó en el Laboratorio 1. MAE y RMSE van en viajeros y MAPE en
porcentaje. El modelo ganador de cada serie es el de menor suma de los rangos de MAE y RMSE, el
mismo criterio con el que el laboratorio anterior eligió entre SARIMA, Holt-Winters, SES, seasonal
naive y Prophet.

Las tres métricas se reportan juntas porque miden cosas distintas. El MAE promedia el error en
viajeros y trata todos los meses por igual; el RMSE penaliza los errores grandes, que en estas
series se concentran en los picos estacionales y en el rebote de 2022; el MAPE normaliza por el
nivel real y es la única de las tres comparable entre series de distinto volumen. Un modelo que
ganara en una sola de ellas exigiría una discusión; en los resultados de abajo no hace falta,
porque el ganador lo es en las tres.

Ninguna de las dos familias vio el conjunto de prueba durante el ajuste. En el Laboratorio 1 las
órdenes SARIMA se eligieron por AIC sobre el entrenamiento y los demás modelos se ajustaron solo
con esas 147 observaciones; en este laboratorio la rejilla LSTM se tuneó contra un tramo de
validación tomado del final del entrenamiento. La comparación es limpia en los dos sentidos.

### Por qué no se usan AIC ni BIC

El enunciado del Laboratorio 1 pedía comparar modelos ARIMA por AIC y BIC, y aquí esos criterios no
aparecen por dos razones.

La primera es que no están definidos para una red neuronal. AIC y BIC se construyen sobre la
verosimilitud maximizada del modelo, y una LSTM entrenada por descenso de gradiente sobre un error
cuadrático no tiene una verosimilitud que reportar ni un número de parámetros efectivos
interpretable de la misma forma; el conteo de 54,015 parámetros del modelo directo no es
comparable con los 8 o 10 coeficientes de un SARIMA.

La segunda es que, aun si estuvieran definidos, no serían el criterio adecuado. Los dos miden
ajuste dentro de muestra penalizado por complejidad, no capacidad predictiva fuera de muestra, y el
Laboratorio 1 documentó el caso extremo: el SARIMA(2,1,2)(0,1,1)12 de vía aérea fue el de menor AIC
de su rejilla, 169.72, y produjo el peor pronóstico a 63 pasos de esa serie, con un MAE de 73,966
frente a los 36,109 de SES. Elegir por AIC habría empeorado el resultado. Toda la comparación de
esta sección se resuelve, por eso, sobre el conjunto de prueba.

## Resultados

| Serie | Familia | Mejor modelo | MAE | RMSE | MAPE |
|---|---|---|---:|---:|---:|
| Total | Lab 1 | SES | 175,088 | 194,791 | 58.11 % |
| Total | LSTM | lstm_directo | **76,957** | **100,290** | **33.76 %** |
| Vía aérea | Lab 1 | SES | 36,109 | 41,368 | 35.62 % |
| Vía aérea | LSTM | *pendiente del cuaderno 10* | | | |

Las cifras de vía aérea de la familia LSTM entran en esta tabla, en las figuras y en las dos tablas
consolidadas en cuanto `notebooks/10_lstm_via_aerea.ipynb` deje su `metricas_lstm_via_aerea.csv` en
`resultados/`. El cuaderno 11 lee con un glob y no con nombres fijos, de modo que la serie se
incorpora sin editar código: basta volver a ejecutarlo. Lo que sigue está calculado sobre la serie
total, la única con resultados LSTM disponibles al escribir esta sección.

![Mejor modelo de cada familia sobre los 63 meses de prueba](../figuras/comp_lstm_metricas.png)

## Serie total

### Cuál de las dos estrategias LSTM predijo mejor

La estrategia directa, con `Dense(63)`, gana con claridad a la recursiva.

| Modelo | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| lstm_directo | 76,957 | 100,290 | 33.76 % |
| lstm_recursivo | 143,303 | 164,706 | 46.90 % |
| Margen | 46.30 % | 39.11 % | 13.13 pp |

El margen es demasiado grande para atribuirlo al azar del ajuste, y va en contra de la ventaja
muestral: la estrategia recursiva entrena con 123 ventanas y la directa con 61, la mitad. Lo que
inclina la balanza es el sesgo acumulado. La recursiva subestima 62 de los 63 meses, con un error
medio de −142,973 viajeros, el 51.7 % del nivel medio del test; la directa subestima 45 de 63, con
−44,329, el 16.0 %. Realimentar 63 veces un modelo de un paso entrenado sobre datos que terminan en
el punto más bajo de la pandemia arrastra toda la trayectoria hacia ese nivel.

Conviene señalar de dónde no sale esta conclusión. Los `rmse_val` del tuneo, 149,716 en la
recursiva y 130,075 en la directa, apuntan en la misma dirección, pero no sirven como argumento: se
miden sobre tramos distintos, veinte meses consecutivos en un caso y once ventanas de 63 valores en
el otro, y solo ordenan configuraciones dentro de una misma estrategia. La comparación entre
estrategias se resuelve únicamente en el test.

### Si son mejores que los del Laboratorio 1

Sí, y por el mayor margen registrado en las dos entregas para esta serie.

| Comparación | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| SES, Lab 1 | 175,088 | 194,791 | 58.11 % |
| lstm_directo | 76,957 | 100,290 | 33.76 % |
| Mejora | 56.05 % | 48.51 % | 24.35 pp |

Para dimensionar el salto: en el Laboratorio 1, la distancia entre SES y el segundo mejor modelo de
esta serie, Holt-Winters, era de 21,868 viajeros de MAE. Aquí la distancia entre SES y el LSTM
directo es de 98,131, cuatro veces y media mayor. No es una diferencia que exija matices ni que
pueda explicarse por la semilla: es un cambio de régimen en la calidad del pronóstico. Y no depende
de haber elegido bien la estrategia, porque incluso la perdedora supera a SES: la recursiva registra
143,303 de MAE y 164,706 de RMSE, por debajo de los 175,088 y 194,791 de SES.

El LSTM directo es, en consecuencia, el mejor modelo global de la serie total entre las dos
familias, marcado como `mejor_global` en `comparativo_lstm_lab1.csv`. Es también el primer modelo
de esta serie, en las dos entregas, que baja del 50 % de MAPE.

![Trayectorias de la serie total sobre el test](../figuras/comp_lstm_total.png)

La figura muestra por qué. SES es una recta horizontal en 105,145 viajeros durante 63 meses: por
construcción prolonga el último nivel suavizado del entrenamiento, que es un mes de pandemia. El
SARIMA(2,1,2)(1,1,1)12 es peor todavía, porque a un nivel inicial bajo le suma una tendencia
estimada que apunta hacia abajo, y termina rozando el cero desde 2023; su correlación con el test
es de −0.597, es decir que se mueve de forma sistemática al revés que la serie real. El LSTM
directo es el único de los tres que traza un perfil estacional con el nivel correcto, y en el tramo
2023-2025 se superpone con el test en buena parte de los meses.

Ahora bien, la ventaja no es uniforme a lo largo del horizonte, y decirlo importa tanto como
reportar el promedio. El LSTM directo sobreestima 2021 en 79.6 %, con 198,112 viajeros mensuales
frente a 110,282 reales, mientras que SES, por estar anclado en el nivel deprimido, acierta ese
tramo mucho mejor. La ventaja del LSTM se construye de 2022 en adelante y se estabiliza en un error
anual de entre 12.0 % y 12.7 % en 2023-2025. Un usuario interesado solo en los primeros doce meses
del horizonte no habría obtenido de esta comparación la misma conclusión que uno interesado en los
63.

## Vía aérea

Pendiente de los resultados de `notebooks/10_lstm_via_aerea.ipynb`. La referencia contra la que se
comparará está fijada desde el Laboratorio 1: SES, con MAE de 36,109, RMSE de 41,368 y MAPE de
35.62 %, la mejor de las siete series del laboratorio anterior en términos relativos. El SARIMA de
esa serie, elegido por AIC, es el ejemplo de inestabilidad citado más arriba, con MAE de 73,966.

Vale anticipar que la vara es más alta que en la serie total: SES parte de un MAPE de 35.62 %, casi
el mismo 33.76 % que alcanzó el LSTM directo en total. Una mejora del orden de la observada en la
serie agregada no debería darse por descontada.

## Qué significa el resultado dado el diseño temporal del split

El split se heredó del Laboratorio 1 sin modificarlo, y esa decisión condiciona la lectura de todo
lo anterior. El entrenamiento termina en marzo de 2021, con la serie en 105,145 viajeros
mensuales, y el test recorre la recuperación completa hasta una media de 276,685. La frontera cae
en el peor punto posible: el modelo aprende con una serie cuyo tramo final es atípico respecto de
todo lo que vendrá después.

Ese diseño explica el resultado en las dos direcciones. Explica por qué los modelos del Laboratorio
1 fallaron: SES, Holt-Winters, seasonal naive, SARIMA y Prophet anclan el pronóstico en las últimas
observaciones o en la tendencia estimada sobre ellas, y las últimas observaciones eran pandemia. El
informe anterior ya lo documentó al señalar que SES ganó seis de las siete series precisamente por
no extrapolar, es decir, por equivocarse menos que los demás y no por acertar.

Y explica también por qué el LSTM directo gana. La red aprende un patrón sobre ventanas de 24 meses
que en su mayoría provienen del periodo prepandemia, once años de los doce del entrenamiento, y al
pronosticar reconstruye ese patrón en lugar de prolongar el nivel del último mes. Sobre un test que
efectivamente vuelve a niveles prepandemia, esa forma de equivocarse resulta ser la correcta.

De ahí se sigue la reserva más importante de esta sección. La superioridad del LSTM medida aquí es
real y está calculada de forma limpia, pero se apoya en una coincidencia favorable entre lo que el
modelo aprendió y lo que ocurrió. Si la serie no se hubiera recuperado, o si el test hubiera
cubierto un periodo de deterioro sostenido, la misma propiedad que hoy lo hace ganar habría
producido una sobreestimación sistemática, y el ranking se habría invertido. Lo que estos 63 meses
demuestran no es que una LSTM sea mejor que un SARIMA en general, sino que un modelo capaz de
reconstruir el patrón histórico completo supera a uno anclado en el último nivel observado cuando
el horizonte contiene una vuelta a ese patrón histórico.

La conclusión operativa para INGUAT es más modesta que el 56 % de mejora en el MAE. Un MAPE de
33.76 % sigue significando un error típico de un tercio del valor real, útil para dimensionar
órdenes de magnitud y planificación agregada, insuficiente para asignación fina de capacidad sin
intervalos de confianza ni reentrenamiento periódico. La recomendación es reentrenar con datos
posteriores a la recuperación en cuanto haya suficientes, porque ninguno de los modelos comparados
aquí, de ninguna de las dos familias, tuvo forma de aprender el régimen que efectivamente rige la
serie desde 2023.
