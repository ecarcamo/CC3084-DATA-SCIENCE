# Inciso 10. Análisis y conclusiones

## 10.1 ¿Tiene el modelo capacidad suficiente para apoyar el monitoreo de cianobacteria?

El modelo desarrollado es razonable como **herramienta de apoyo** al monitoreo, no como reemplazo del muestreo físico ni del índice de cianobacteria del que deriva su variable respuesta. La evidencia acumulada en los incisos anteriores respalda esta lectura con matices importantes:

- El inciso 5 muestra que, sobre una división aleatoria convencional, los modelos alcanzan un desempeño reportable en Accuracy, Precision, Recall, F1 y ROC-AUC, y el inciso 5.3 fija explícitamente el criterio de uso operativo: priorizar Recall (minimizar falsos negativos), porque el costo ambiental de no detectar una floración real es mayor que el de una falsa alarma.
- El inciso 6 muestra que ese desempeño bajo validación aleatoria **sobreestima** la capacidad real del modelo para predecir zonas nuevas: la validación espacial, que respeta la dependencia entre píxeles vecinos, da una estimación más realista y es la que debería usarse para decidir si el modelo es apto para producción.
- El inciso 7 muestra que el modelo **no generaliza libremente entre lagos**: un modelo entrenado solo en Atitlán o solo en Amatitlán pierde desempeño al evaluarse en el otro lago. Esto significa que el modelo debe entrenarse y calibrarse por lago, o con datos combinados de ambos, y no debe usarse en un tercer cuerpo de agua sin datos propios de entrenamiento.
- El inciso 9 muestra que el error de predicción no es aleatorio: se concentra en zonas de transición y bordes, lo que sugiere que el modelo es más confiable lejos de esas zonas y requiere lectura con más cautela cerca de ellas.

En conjunto, el modelo es útil como **primer filtro de vigilancia**, capaz de priorizar qué fechas y qué regiones de cada lago revisar con más detalle (incluyendo muestreo físico), pero no como fuente única de decisión sanitaria, dado el desbalance de clases (inciso 2.4), la caída de desempeño bajo validación espacial (inciso 6) y la falta de generalización entre lagos (inciso 7).

## 10.2 Limitaciones principales

- **Cantidad de fechas**: 11 fechas por lago en año y medio son insuficientes para que el modelo aprenda la variabilidad estacional completa documentada en la Parte I (patrón seco/lluvioso, tendencia ascendente). Con tan pocas fechas, el riesgo de sobreajustar a las condiciones particulares de esas 22 escenas es alto.
- **Nubosidad**: aunque el inciso 1 filtra píxeles con nube confirmada o alta probabilidad de nube, la cobertura de nubes reduce la cantidad de observaciones válidas en fechas puntuales (por ejemplo, la fecha de mayor pico en Amatitlán coincide con la de mayor nubosidad oficial, según la Parte I), lo que introduce incertidumbre justo en los eventos más relevantes de detectar.
- **Resolución espacial**: los 20 m de resolución de Sentinel-2 mezclan, en un mismo píxel, agua con distintas condiciones (orilla, afluentes, zonas de circulación distinta), lo que puede explicar parte de los errores sistemáticos identificados en el inciso 9.7.
- **Diferencias entre lagos**: el inciso 7 muestra que Atitlán y Amatitlán tienen regímenes espectrales y tróficos suficientemente distintos como para que un modelo entrenado en uno no transfiera bien al otro, lo que limita la generalización del modelo a otros cuerpos de agua no incluidos en el entrenamiento.
- **Metodología de validación**: la validación aleatoria del inciso 4 sobreestima el desempeño real (inciso 6); incluso la validación espacial por bloques asume que basta con separar por posición, sin considerar explícitamente la dependencia temporal entre fechas cercanas del mismo lago.
- **Ausencia de verdad de campo independiente**: la variable respuesta se deriva del propio índice satelital (`clorofila`), no de mediciones de laboratorio en el lago. El modelo aprende a reproducir el índice espectral, no una medición físico-química validada de forma independiente.

## 10.3 Información adicional que podría mejorar el modelo

- **Datos meteorológicos**: temperatura y precipitación (por ejemplo, de las fuentes de WeatherSpark referenciadas en el enunciado) permitirían modelar directamente el mecanismo estacional ya identificado en la Parte I (estancamiento y calentamiento en temporada seca), en lugar de que el modelo intente inferirlo indirectamente solo a partir de bandas espectrales.
- **Datos hidrológicos**: caudal de afluentes, tiempo de residencia del agua y niveles del lago ayudarían a explicar las zonas de acumulación por baja circulación ya identificadas en la Parte I (el estrecho y la bahía sur de Amatitlán), y podrían mejorar la predicción en esas zonas de mayor error (inciso 9.7).
- **Muestreos físicos de calibración**: mediciones de clorofila-a o de conteo de cianobacterias en campo, aunque sean puntuales, permitirían validar el umbral de 10 µg/L del inciso 2 con datos independientes del propio satélite, y detectar si el índice NDCI se desvía de la concentración real bajo ciertas condiciones (por ejemplo, alta turbidez no asociada a cianobacteria).
- **Mayor frecuencia temporal**: más fechas por año, especialmente alrededor de los picos de floración de marzo a junio ya identificados en la Parte I, reducirían el riesgo de que el modelo dependa de unos pocos eventos extremos para aprender el patrón de "alta presencia".
- **Datos de otros lagos o cuerpos de agua**: dado que el inciso 7 muestra generalización limitada entre solo dos lagos, incorporar datos de más cuerpos de agua con regímenes tróficos distintos ayudaría a que el modelo aprenda un patrón espectral más general de cianobacteria, en lugar de memorizar la firma particular de Atitlán y Amatitlán.
