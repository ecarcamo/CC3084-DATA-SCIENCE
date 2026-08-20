# Laboratorio 4. Parte 2 Análisis de modelos usando datos geospaciales.

## INSTRUCCIONES

Ejercicio.
Los  lagos  Atitlán  y  Amatitlán  son  cuerpos  de  agua  de  gran  importancia  ecológica,  económica  y
cultural en Guatemala. Sin embargo, en las últimas décadas ambos han mostrado signos alarmantes
de deterioro ambiental, especialmente por la proliferación de cianobacterias — microorganismos
que  pueden  formar  floraciones  tóxicas  cuando  las  condiciones  del  agua  son  propicias  (alta
temperatura, nutrientes, estancamiento, etc.).

El monitoreo constante de estas floraciones es esencial para gestionar riesgos a la salud pública, el
turismo y los ecosistemas acuáticos. Sin embargo, realizar muestreos físicos frecuentes puede ser
costoso, limitado en alcance espacial, y logísticamente complejo.

Aquí es donde entra en juego la observación de la Tierra mediante satélites. En particular, la misión
Sentinel-2 del programa Copernicus proporciona imágenes multiespectrales de alta resolución que
permiten detectar cambios en la vegetación, calidad del agua y floraciones algales mediante índices
espectrales.

Además, herramientas como Sentinel Hub y su API nos permiten acceder a scripts personalizados
(como el de detección de cianobacteria) y procesar las imágenes directamente desde la nube, sin
necesidad de descargar grandes volúmenes de datos.

En la primera parte del laboratorio se analizaron los lagos Atitlán y Amatitlán utilizando imágenes
multiespectrales de Sentinel-2. A partir de estas imágenes se obtuvieron índices espectrales como
NDVI  y  NDWI,  así  como  información  relacionada  con  la  presencia  de  cianobacteria.  También  se
estudiaron los patrones temporales y espaciales de las floraciones y las diferencias observadas entre
ambos lagos.

En esta segunda parte se utilizarán los datos obtenidos para desarrollar modelos de Aprendizaje de
Máquinas capaces de identificar zonas con alta presencia de cianobacteria a partir de características
espectrales y geográficas.

## DESCRIPCIÓN DE LOS DATOS

Utilice como punto de partida los datos obtenidos en la Parte I del Laboratorio 4. Los datos deberán
provenir  de  las  imágenes  Sentinel-2  correspondientes  a  los  lagos  Atitlán  y  Amatitlán.  Utilice  las
mismas fechas establecidas en la Parte I.

Cada observación utilizada para los modelos deberá estar asociada a una posición geográfica dentro
de alguno de los lagos. Como mínimo deberá considerar:

- coordenadas espaciales;
- fecha de adquisición;
- lago;
- bandas espectrales disponibles;
- NDVI;
- NDWI;

información sobre presencia de cianobacteria.

Puede incorporar bandas adicionales de Sentinel-2 o construir nuevas variables si considera que
pueden mejorar los modelos. Cualquier variable adicional deberá ser explicada y justificada.

IMPORTANTE:  Debe  tener  especial  cuidado  con  los  predictores.  Una  variable  utilizada  directa  
indirectamente  para  construir  la  variable  respuesta  no  deberá  incluirse  posteriormente  como
variable predictora.

## EJERCICIOS

- 1.  Preparación de los datos para Machine Learning

1.1.  A partir de los rasters obtenidos en la Parte I, construya un conjunto de datos adecuado
para  Machine  Learning.  Cada  fila  deberá  representar  una  observación  geográfica  válida
dentro de alguno de los lagos.

1.2.  Incluya  como  mínimo:  coordenadas  de  la  observación,  fecha,  lago,  bandas  espectrales
utilizadas, NDVI, NDWI e índice o categoría asociada con la presencia de cianobacteria.
1.3.  Elimine  observaciones  correspondientes  a  áreas  fuera  de  los  límites  del  lago,  valores
NoData, píxeles no válidos, nubes u otras observaciones que considere que pueden afectar
el análisis.

1.4.  Indique el número total de observaciones, número de observaciones por lago y por fecha,

variables disponibles, tipo de cada variable y porcentaje de valores faltantes.

1.5.  Realice un análisis exploratorio de las variables que utilizará para construir los modelos.

Utilice las visualizaciones y estadísticas que considere necesarias.

1.6.  Explique las decisiones tomadas durante la preparación y limpieza de los datos.

- 2.  Construcción de la variable respuesta

2.1.  A partir de los  resultados obtenidos  mediante el índice de cianobacteria, construya una
variable  respuesta  binaria:  0  =  ausencia  o  baja  presencia  de  cianobacteria;  1  =  alta
presencia de cianobacteria.

2.2.  Explique  y  justifique  el  criterio  utilizado  para  establecer  el  punto  de  corte.  Básese  en
bibliografía  científica,  ¿Qué  se  considera  desde  el  punto  de  vista  científico  y  medio
ambiental bajo o alto índice de cianobacteria? Referencie la bibliografía consultada.

2.3.  Analice la distribución de la variable respuesta globalmente, por lago y por fecha.
2.4.  Determine  si  existe  desbalance  entre  las  clases.  En  caso  de  existir,  explique  qué

consecuencias puede tener sobre el entrenamiento y la evaluación de los modelos

2.5.  Identifique  las  variables  que  no  pueden  utilizarse  como  predictoras  debido  a  que

producirían porque se usaron para construir la variable respuesta

- 3.  Selección y construcción de variables predictoras

3.1.  Defina el conjunto de variables predictoras que utilizará para construir los modelos.
3.2.  Para  cada  variable  explique  brevemente  qué  representa,  por  qué  podría  contribuir  a
identificar la presencia de cianobacteria y si corresponde a una banda espectral, índice o
característica espacial.

3.3.  Puede realizar Ingeniería de características y construir  variables adicionales si considera
que pueden mejorar la capacidad predictiva. Toda nueva variable deberá ser explicada y
justificada.

- 4.  Construcción de modelos de Machine Learning

4.1.  Construya modelos de clasificación utilizando como mínimo: Regresión Logística, Random

Forest y Gradient Boosting o XGBoost.

4.2.  Entrene inicialmente los tres modelos utilizando una división convencional de los datos: 70

% entrenamiento y 30 % prueba.

4.3.  Cuando sea necesario, realice ajuste de hiperparámetros. Explique qué hiperparámetros

modificó, qué valores evaluó y qué criterio utilizó para seleccionar el modelo final.

4.4.  Mantenga  el  mismo  conjunto  de  prueba  para  realizar  comparaciones  justas  entre  los

modelos.

- 5.  Evaluación de los modelos

5.1.  Para cada modelo calcule como mínimo Accuracy, Precision, Recall, F1-score, ROC-AUC y

matriz de confusión.

5.2.  Compare los resultados obtenidos por los tres modelos y determine cuál presenta el mejor

desempeño.

5.3.  Desde el punto de vista ambiental, analice las consecuencias de clasificar una zona sin alta
presencia como alta presencia y de no detectar una zona que sí presenta alta presencia de
cianobacteria.  Determine  cuál  de  estos  errores  considera  más  importante  reducir  y
teniendo en cuenta esto compare los modelos usando la métrica más adecuada

- 6.  Validación espacial

6.1.  Divida cada lago utilizando una cuadrícula regular de aproximadamente 1 km × 1 km. Antes
de realizar la validación espacial, evalúe si este tamaño produce un número suficiente de
bloques  con  observaciones  válidas.  Reporte  el  número  de  bloques  obtenidos  para  cada
lago y la cantidad de observaciones por bloque. Si considera necesario utilizar un tamaño
diferente, puede hacerlo, pero deberá justificar su decisión. Antes de construir los bloques
espaciales, reproyecte los datos al sistema de referencia de coordenadas WGS 84 / UTM
zona 15N (EPSG:32615). Este sistema utiliza metros como unidad de medida y será utilizado
para ambos lagos.

6.2.  Asigne cada observación a uno de los bloques espaciales y visualice en un mapa los bloques

generados.


6.3.  Realice una validación en la cual las observaciones pertenecientes al mismo bloque espacial
permanezcan  dentro  del  mismo  grupo  de  entrenamiento  o  validación.  Puede  utilizar
GroupKFold, Spatial Cross-Validation u otra estrategia equivalente.

6.4.  Entrene nuevamente los modelos utilizando validación espacial.
6.5.  Compare los resultados de validación aleatoria y validación espacial.
6.6.  Explique si el desempeño aumentó o disminuyó, cuál fue la magnitud de la diferencia, por
qué puede ocurrir y qué estrategia proporciona una estimación más realista de la capacidad
del modelo para predecir nuevas zonas.

- 7.  Generalización entre lagos

7.1.  Experimento A: utilice Lago Atitlán para entrenamiento y Lago Amatitlán para evaluación.
7.2.  Experimento B: utilice Lago Amatitlán para entrenamiento y Lago Atitlán para evaluación.
7.3.  Calcule las métricas de evaluación para ambos experimentos.
7.4.  Compare estos resultados con los obtenidos cuando entrenamiento y prueba contienen

observaciones del mismo lago.

7.5.  Responda: ¿Un modelo entrenado en un lago puede generalizar adecuadamente al otro?
7.6.  Discuta  qué  características  geográficas,  ambientales  o  espectrales  podrían  explicar  las

diferencias encontradas.

- 8. Interpretación y explicabilidad del modelo

8.1.  Para  el  modelo  que  presente  el  mejor  desempeño,  determine  la  importancia  de  las

variables predictoras.  Genere un gráfico de importancia global.

8.2.  Utilice SHAP (SHapley Additive exPlanations) para interpretar el mejor modelo obtenido.

Genere un SHAP Summary Plot.

8.3.  Identifique las variables que presentan mayor influencia sobre las predicciones y analice si
valores altos o bajos de estas variables tienden a aumentar o disminuir la predicción de alta
presencia  de  cianobacteria.  Interprete  los  resultados  desde  el  contexto  ambiental  del
problema.

8.4.  No  se  limite  a  mostrar  las  gráficas;  explique  los  patrones  encontrados  y  su  posible

significado ambiental.
- 9.  Generación de mapas predictivos

9.1.  Utilice  el  mejor  modelo  para  calcular,  para  cada  observación,

la  probabilidad

correspondiente a alta presencia de cianobacteria.

9.2.  Reconstruya  espacialmente  las  predicciones  y  genere  un  mapa  de  probabilidad  de

presencia de cianobacteria.

9.3.  Genere como mínimo un mapa predictivo para cada lago.
9.4.  Utilice una escala que permita distinguir claramente zonas de probabilidad muy baja, baja,

alta y muy alta.

9.5.  Compare el mapa predictivo con los mapas de cianobacteria obtenidos en la Parte I.


9.6.  Identifique zonas correctamente detectadas, falsos positivos, falsos negativos y posibles

patrones espaciales de error.

9.7.  Explique si existen regiones del lago donde el modelo presenta sistemáticamente mayor

dificultad para realizar predicciones.

- 10. Análisis y conclusiones

10.1.

A partir de todos los experimentos realizados, determine si considera que el modelo
desarrollado tiene suficiente capacidad para ser utilizado como herramienta de apoyo en
el monitoreo de cianobacteria. Justifique su respuesta utilizando los principales resultados
obtenidos durante el laboratorio.

10.2.

Discuta las principales limitaciones encontradas durante el desarrollo del modelo.
Considere aspectos relacionados con los datos disponibles, resolución espacial, cantidad
de fechas, nubosidad, diferencias entre lagos y metodología de validación.

10.3.

Explique  qué  información  o  datos  adicionales  considera  que  podrían  mejorar  el
modelo.  Puede  considerar  variables  ambientales,  meteorológicas,  hidrológicas,
temporales o información obtenida mediante muestreos físicos.

## REFERENCIAS

En estos dos sitios, hay datos de precipitaciones y temperatura de los lagos que pudieran usar:
-
https://weatherspark.com/y/11701/Average-Weather-in-Amatitl%C3%A1n-Guatemala-
Year-Round#google_vignette
https://weatherspark.com/compare/y/11701~11135/Comparison-of-the-Average-
Weather-in-Amatitl%C3%A1n-and-Santiago-Atitl%C3%A1n

-

## Requisitos

### Preparación del conjunto de datos:

- Se  construye  correctamente  el  conjunto  de  datos  para  los  modelos  de  aprendizaje
automático.
- Se mantienen las coordenadas y fechas de las observaciones.
- Se eliminan correctamente observaciones inválidas.
- Se define y justifica adecuadamente la variable respuesta.
- Se identifican y evitan posibles problemas entre predictores y variable respuesta.
- Se realiza un análisis exploratorio adecuado.

### Construcción de modelos:

- Se  implementa  correctamente  los  modelos  de  Regresión  Logística,  Random  Forest  y
Gradient Boosting o XGBoost.
- Se realiza correctamente la división entrenamiento/prueba.
- Se justifican las variables utilizadas.
- Se realiza el ajuste de hiperparámetros cuando corresponde.

### Evaluación de modelos:

- Se calculan correctamente Accuracy, Precision, Recall, F1 y ROC-AUC.
- Se generan e interpretan las matrices de confusión.
- Se comparan los modelos usando las métricas más adecuada de acuerdo a la revisión de bibliografía medio ambiental
- Se interpretan los errores desde el contexto ambiental.

### Validación geoespacial y temporal

- Se implementa correctamente una estrategia de validación espacial.
- Se representan los bloques espaciales utilizados.
- Se implementa correctamente una estrategia de validación temporal.
- Se comparan los resultados con la división aleatoria.
- Se explican las diferencias encontradas.
- Se demuestra comprensión del efecto de la dependencia espacial sobre la evaluación del modelo.
- Se entrena con Atitlán y se evalúa con Amatitlán.
- Se entrena con Amatitlán y se evalúa con Atitlán.
- Se comparan correctamente los resultados.
- Se interpretan las diferencias observadas entre ambos lagos.

### Generalización entre lagos

### Interpretabilidad y mapas predictivos

-  Se analiza la importancia de las variables.

### Análisis y conclusiones

- Se utiliza correctamente SHAP.
- Se interpretan los resultados obtenidos.
- Se generan mapas de probabilidades para ambos lagos.
- Se identifican y analizan espacialmente los errores del modelo.
- Se identifican las limitaciones de los modelos.
- Las conclusiones se sustentan con evidencia.
- Se explica correctamente la importancia de considerar la dimensión espacial de los datos.
