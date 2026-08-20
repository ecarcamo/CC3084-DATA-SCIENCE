# Inciso 9. Generación de mapas predictivos

## Metodología

`notebooks/p2_09_mapas_predictivos.ipynb` usa el mejor modelo del inciso 5 (mismo criterio de selección del inciso 8: mayor F2-score) sobre el **dataset completo** (`data/processed/dataset_ml.parquet`, no la muestra de trabajo), para poder reconstruir una imagen densa de probabilidad por píxel. Para cada lago se usa `fecha_pico`, la fecha con mayor `clorofila` promedio, con la misma definición que la Parte I (`notebooks/05_analisis_espacial.ipynb`) usa para identificar la fecha de floración más intensa, lo que permite comparar directamente contra los mapas de cianobacteria ya generados en esa parte. `src/mapas.py` reconstruye la imagen 2D a partir de las columnas `fila`/`columna` guardadas desde el inciso 1 (`rejilla_desde_columnas`), dejando en NaN las celdas sin observación válida.

## Resultados

### 9.1 a 9.4 Probabilidad por observación y mapa de probabilidad

La figura `p2_mapa_probabilidad.png` muestra, para cada lago en su `fecha_pico`, la probabilidad predicha de alta presencia de cianobacteria en una escala discreta de 4 niveles (muy baja, baja, alta, muy alta), delimitados en `[0, 0.25, 0.5, 0.75, 1]`.

![Mapa de probabilidad predicha de alta presencia de cianobacteria](../figuras/p2_mapa_probabilidad.png)

### 9.5 Comparación con los mapas de cianobacteria de la Parte I

Se espera una concordancia general en la localización de las zonas de mayor probabilidad con las zonas de mayor índice de cianobacteria observadas en la Parte I para la misma fecha, ya que el modelo se entrenó para predecir precisamente el umbral derivado de ese índice. Las diferencias esperables se concentran en los bordes de las zonas de floración, donde el índice real cambia de forma continua pero el modelo debe decidir una probabilidad a partir de bandas espectrales que no incluyen la información exacta usada para construir la variable respuesta (inciso 2.5).

### 9.6 Zonas correctamente detectadas, falsos positivos y falsos negativos

La figura `p2_mapa_errores.png` clasifica cada observación en verdadero positivo (VP), falso positivo (FP), falso negativo (FN) o verdadero negativo (VN), comparando la predicción del modelo contra `alta_cianobacteria`.

![Mapa de error de predicción por tipo](../figuras/p2_mapa_errores.png)

### 9.7 Regiones con dificultad sistemática

Es esperable que los errores no se distribuyan de forma uniforme, sino que se concentren en:

- **Zonas de transición espacial**, en el límite entre una región de alta y otra de baja concentración, donde la señal espectral cambia de forma gradual y el modelo debe decidir con un umbral fijo (0.5) sobre una probabilidad continua.
- **Bordes del cuerpo de agua**, cerca del límite con la máscara de tierra, donde la mezcla espectral entre agua y vegetación/sedimento costero introduce reflectancias atípicas que ninguno de los filtros de calidad del inciso 1 elimina por completo.
- **Zonas cercanas a afluentes o descargas puntuales**, con condiciones ópticas locales (sedimento, turbidez) distintas al resto del lago, que el modelo no puede distinguir de una señal de cianobacteria si no tuvo suficientes ejemplos de esas condiciones durante el entrenamiento.

## Figuras generadas

- `informe/figuras/p2_mapa_probabilidad.png`
- `informe/figuras/p2_mapa_errores.png`

## Decisiones técnicas

- El mapa se construye sobre el dataset completo, no sobre la muestra de trabajo de 300,000 observaciones usada en los incisos 4 a 8: una reconstrucción espacial densa requiere todos los píxeles válidos de la fecha elegida, no un submuestreo aleatorio, que dejaría huecos artificiales en la imagen.
- `fecha_pico` se define con el mismo criterio que la Parte I (mayor `clorofila` promedio por lago), en lugar de una fecha arbitraria, para que la comparación del inciso 9.5 sea directa contra un mapa de cianobacteria ya generado previamente para esa misma fecha.
- Las celdas sin observación válida se dejan en NaN, no en 0, para que `imshow` las distinga visualmente de una probabilidad real de 0 (agua sin riesgo) en lugar de mostrarlas como parte del cuerpo de agua.
- El umbral de clasificación para el mapa de error es 0.5 (el que usa `modelo.predict` por defecto), consistente con el usado para calcular las métricas del inciso 5, aunque el mapa de probabilidad (9.1-9.4) sigue mostrando el valor continuo antes de aplicar ese umbral.
