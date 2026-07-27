# 6. Análisis comparativo

## Criterio de comparación

La comparación entre series exige métricas explícitas, porque la inspección
visual favorece siempre a las series de mayor volumen. Cada pregunta se
responde con un número calculado bajo la misma definición para las siete
series en `notebooks/07_comparativo.ipynb`, y los resultados quedan en
`resultados/comparativo_series.csv`.

La estacionalidad se mide con la fuerza estacional de la descomposición
aditiva de `log1p` del entrenamiento con periodo 12, definida como uno menos
la razón entre la varianza del residuo y la varianza del componente
estacional más el residuo. Toma valores entre 0 y 1, y un valor alto indica
que la señal anual explica buena parte de la variación que no captura la
tendencia. Se complementa con la amplitud de los factores estacionales
prepandemia ya reportada en la sección 4. La fuerza de tendencia se calcula
de forma análoga sobre el componente de tendencia.

La tendencia de crecimiento se estima con la pendiente de una regresión
lineal sobre el tramo de enero de 2009 a diciembre de 2019. La pandemia se
excluye porque una caída del orden del 97 % domina cualquier ajuste lineal y
convierte la pendiente en una medida del choque y no del crecimiento. La
pendiente se reporta en viajeros por mes y también como porcentaje de la
media del tramo, ya que en términos absolutos las series de mayor volumen
ganan por construcción.

La volatilidad usa dos medidas sobre el mismo tramo prepandemia: el
coeficiente de variación, que compara la dispersión con el nivel medio, y la
desviación estándar de los retornos logarítmicos mensuales, que mide el
tamaño típico del salto de un mes al siguiente. Las dos no tienen que
coincidir y su discrepancia es informativa.

El impacto pandémico combina profundidad y velocidad. La profundidad es la
caída porcentual del mínimo entre enero de 2020 y diciembre de 2021 respecto
de la media de 2019. La velocidad es el primer mes, contado desde abril de
2020, en que la serie alcanza el 80 % de esa media. La segunda métrica es la
que discrimina cuando varias series caen a cero.

| Serie | Fs | Ft | Pendiente (viaj/mes) | Pendiente (% media) | CV | Vol. retornos | Media 2019 | Mínimo pandémico | Caída | Recupera 80 % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Total | 0.189 | 0.505 | 1,893 | 0.750 | 0.335 | 0.201 | 390,985 | 9,779 | 97.5 % | 2022-04 |
| Vía aérea | 0.142 | 0.241 | 407 | 0.428 | 0.216 | 0.171 | 123,615 | 489 | 99.6 % | 2021-12 |
| Vía terrestre | 0.169 | 0.653 | 1,448 | 0.974 | 0.431 | 0.236 | 256,470 | 5,715 | 97.8 % | 2022-04 |
| Vía marítima | 0.405 | 0.690 | 38 | 0.444 | 0.790 | 2.185 | 10,899 | 0 | 100 % | 2022-12 |
| El Salvador | 0.105 | 0.185 | 641 | 0.978 | 0.453 | 0.267 | 114,256 | 0 | 100 % | 2022-04 |
| Estados Unidos | 0.109 | 0.107 | 112 | 0.374 | 0.300 | 0.318 | 38,729 | 0 | 100 % | 2021-12 |
| Honduras | 0.119 | 0.116 | 56 | 0.579 | 0.335 | 0.219 | 17,402 | 0 | 100 % | 2022-03 |

La serie total aparece como referencia. Las comparaciones se hacen dentro de
cada categoría, porque la total es una suma de las vías y no compite con
ellas.

## Categoría vías de ingreso

La vía marítima es la más estacional, y por un margen que no admite duda: su
fuerza estacional es 0.405, más del doble que la de la terrestre, 0.169, y
casi el triple que la de la aérea, 0.142. La amplitud de sus factores
prepandemia lo confirma, 3.273 en logaritmos frente a 0.578 y 0.953. La
figura `comp_estacionalidad.png` muestra el origen del contraste: los
cruceros operan entre noviembre y abril, con factor de 3.328 en diciembre, y
prácticamente desaparecen entre junio y septiembre, con 0.153 en junio. Las
otras dos vías oscilan en una banda estrecha alrededor de la unidad, con el
mismo pico de diciembre y un valle poco profundo.

![Fuerza estacional por vía de ingreso](../figuras/comp_estacionalidad.png)

En crecimiento gana la vía terrestre. Su pendiente prepandemia es de 1,448
viajeros por mes, equivalente a 0.974 % de su media mensual, y su fuerza de
tendencia, 0.653, es la más alta de la categoría. Es el único caso en que la
medida absoluta y la normalizada coinciden en el ganador, lo que refuerza la
conclusión. La marítima ilustra el riesgo de mirar solo la absoluta: sus 38
viajeros por mes parecen despreciables frente a los 407 de la aérea, pero
normalizados son 0.444 % contra 0.428 %, es decir, un ritmo relativo muy
similar. La figura `comp_tendencia.png` contrasta las dos lecturas.

![Pendiente de crecimiento absoluta y normalizada por vía de ingreso](../figuras/comp_tendencia.png)

La marítima también es la más volátil, y aquí las dos medidas concuerdan en
el orden: coeficiente de variación de 0.790 frente a 0.431 de la terrestre y
0.216 de la aérea, y desviación de retornos de 2.185 frente a 0.236 y 0.171.
La distancia en retornos es desproporcionada y conviene explicarla en vez de
presentarla como un hallazgo. La serie acumula 16 observaciones iguales a
cero en el entrenamiento y cuatro de ellas caen dentro del tramo prepandemia
que usa esta métrica: agosto de 2017, julio de 2018, junio y agosto de 2019.
Un mes en cero seguido de un mes con miles de viajeros produce un retorno
logarítmico enorme, de modo que el valor de 2.185 mide en parte la
intermitencia del registro y no solo la variabilidad de la demanda. El
coeficiente de variación, que no depende de la transición entre meses
consecutivos, es la medida más comparable, y también sitúa a la marítima en
primer lugar. La figura `comp_volatilidad.png` contrasta las dos medidas.

![Volatilidad por vía de ingreso: coeficiente de variación y retornos logarítmicos](../figuras/comp_volatilidad.png)

La más afectada por la pandemia es de nuevo la marítima. Cae 100 % contra su
media de 2019 y es la última en cruzar el umbral del 80 %, en diciembre de
2022, doce meses después de la aérea y ocho después de la terrestre. Ese
cruce, sin embargo, no es una recuperación. El umbral es de 8,719 viajeros y
diciembre de 2022 registra 10,042, pero ese mes es un pico aislado dentro de
un año que incluye cuatro meses en cero. El total anual pasa de 130,789
viajeros en 2019 a 26,030 en 2022 y a 6,617, 6,605 y 6,944 entre 2023 y
2025, un nivel veinte veces inferior al prepandemia. La lectura correcta es
un cambio de régimen en el registro de cruceros, y la métrica de velocidad de
recuperación deja de ser válida para esta serie. La figura
`comp_recuperacion.png` muestra la trayectoria plana de la marítima después
de 2023 frente a las demás.

![Trayectoria de recuperación pospandemia por vía de ingreso](../figuras/comp_recuperacion.png)

## Categoría países de residencia

En esta categoría conviene empezar por lo que las métricas no permiten
afirmar. Las tres fuerzas estacionales son bajas y casi idénticas: Honduras
0.119, Estados Unidos 0.109 y El Salvador 0.105. Honduras es el máximo, pero
la diferencia con El Salvador es de 0.014 y no sostiene ninguna decisión
operativa. Declarar un ganador sería sobreinterpretar el tercer decimal. Lo
que sí distingue a las series es el calendario y no la intensidad: El
Salvador tiene su pico en diciembre, con factor 1.381, Honduras en enero, con
1.216, y Estados Unidos en julio, con 1.449, y su valle en septiembre, con
0.606. Los dos vecinos centroamericanos siguen el patrón del flujo terrestre
de fin de año, mientras el mercado estadounidense responde al verano boreal.

El Salvador presenta la mayor tendencia de crecimiento, con 0.978 % de su
media por mes, por delante de Honduras, 0.579 %, y de Estados Unidos,
0.374 %. En este caso el orden relativo coincide con el absoluto, 641 contra
56 y 112 viajeros por mes, porque El Salvador es además la serie de mayor
volumen del grupo. Las fuerzas de tendencia de Estados Unidos y Honduras,
0.107 y 0.116, son las más bajas de las siete series, lo que indica
trayectorias en las que la variación estacional y el ruido pesan más que el
crecimiento.

La volatilidad es el caso donde las dos medidas discrepan. El Salvador tiene
el mayor coeficiente de variación, 0.453 frente a 0.335 de Honduras y 0.300
de Estados Unidos, pero Estados Unidos tiene la mayor desviación de retornos,
0.318 frente a 0.267 y 0.219. La explicación está en lo que cada medida
captura. El coeficiente de variación mide la dispersión alrededor de una
media de once años, y El Salvador la infla porque su nivel casi se duplica en
el tramo, de modo que buena parte de esa dispersión es crecimiento y no
inestabilidad. La desviación de retornos mide el salto entre meses
consecutivos, y ahí Estados Unidos gana por su estacionalidad más contrastada
entre julio y septiembre. Para planificación de capacidad interesa la segunda:
el mercado estadounidense es el que exige mayor flexibilidad de un mes al
siguiente. Para evaluar riesgo de nivel interesa la primera.

En profundidad de impacto pandémico no hay diferencia posible. Las tres
series registran cero viajeros de abril a agosto de 2020 por el cierre de
fronteras, así que las tres caen 100 % y la métrica se satura. El desempate
es la velocidad de recuperación, y ahí el orden es claro: Estados Unidos
alcanza el 80 % del nivel de 2019 en diciembre de 2021, Honduras en marzo de
2022 y El Salvador en abril de 2022. Estados Unidos recupera cuatro meses
antes que El Salvador pese a haber caído desde un volumen tres veces menor,
lo que sugiere que el mercado aéreo de larga distancia reaccionó a la
reapertura más rápido que el tráfico fronterizo terrestre.

## Descubrimientos útiles para el INGUAT

1. El volumen depende de la frontera terrestre, pero la estabilidad viene de
   la aérea. La vía terrestre aporta 58.9 % del total entre 2009 y 2019 y
   65.5 % desde abril de 2021, mientras la aérea baja de 37.7 % a 34.2 %. La
   aérea es la vía menos volátil de las tres, con coeficiente de variación de
   0.216 contra 0.431 de la terrestre. La planificación de aforo debe
   dimensionarse por la terrestre, y la de ingresos por gasto turístico
   apoyarse en la aérea, que es más predecible.
2. Existe un calendario operativo común que permite una sola política
   estacional. Diciembre es el mes pico en cinco de las siete series, con
   factores de 1.288 a 3.328, y el valle cae en septiembre o febrero. Las
   excepciones son Estados Unidos, con pico en julio, y Honduras, en enero.
   Septiembre, valle en tres series con factores de 0.802 a 0.606, y febrero,
   valle en las otras tres con factores cercanos a 0.810, son la ventana
   natural para
   mantenimiento de infraestructura, capacitación de personal y campañas de
   temporada baja.
3. Ante un choque, la recuperación llega antes por vía aérea y desde mercados
   lejanos. Estados Unidos y la vía aérea recuperan el 80 % del nivel de 2019
   en diciembre de 2021, cuatro meses antes que El Salvador y la vía
   terrestre. Si vuelve a producirse una interrupción, el orden de prioridad
   de la promoción debería empezar por el mercado aéreo de larga distancia,
   que responde más rápido.
4. El segmento de cruceros no se recuperó y conviene tratarlo como una
   decisión de reasignación, no de reactivación. La vía marítima pasa de
   130,789 viajeros anuales en 2019 a cerca de 6,600 entre 2023 y 2025, con
   meses completos en cero incluso en 2022. Cualquier meta que use el nivel
   prepandemia como referencia para esta vía parte de un supuesto que los
   datos ya rechazan.
5. La operación portuaria es la única que justifica una planificación
   estacional dedicada. Con fuerza estacional de 0.405 y factor de 3.328 en
   diciembre frente a 0.153 en junio, la marítima concentra su actividad en
   pocos meses, mientras las demás series oscilan en una banda estrecha
   alrededor de su media. Un esquema de personal uniforme durante el año es
   razonable en las vías terrestre y aérea, pero no en la marítima.
6. Los modelos ajustados sobre historia que cruza la pandemia no sirven como
   pronóstico operativo. El mejor modelo por serie resultó ser el suavizamiento
   exponencial simple en seis de las siete, con MAPE entre 35.62 % y 74.32 %,
   porque el nivel final del entrenamiento está dominado por el cierre. La
   lectura de política pública es que la planificación cuantitativa debe
   reestimarse con datos posteriores a la reapertura, y que los pronósticos
   basados en la serie completa deben acompañarse de su error, no presentarse
   como cifras puntuales.
