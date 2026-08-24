# Inciso 7. Generalización entre lagos

## Metodología

`notebooks/p2_07_generalizacion_lagos.ipynb` evalúa si un modelo entrenado en un lago generaliza al otro, comparado contra una línea base de "mismo lago": los tres modelos base (`src.modelado.construir_modelos_base`, hiperparámetros por defecto, iguales a los del inciso 6) se entrenan y evalúan en cuatro configuraciones:

- **Baseline Atitlán / Amatitlán**: entrenamiento y prueba 70/30 dentro del mismo lago (`dividir_datos`), la referencia de "mismo lago".
- **Experimento A**: entrenamiento con la totalidad de las observaciones de Atitlán, evaluación con la totalidad de Amatitlán.
- **Experimento B**: entrenamiento con la totalidad de Amatitlán, evaluación con la totalidad de Atitlán.

## Resultados

### 7.1 a 7.3 Experimentos y métricas

`data/processed/p2_generalizacion_lagos.csv` reúne Accuracy, Precision, Recall, F1 y ROC-AUC de las cuatro configuraciones para los tres modelos:

**Líneas base (mismo lago, división 70/30)**

| Lago | Modelo | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Atitlán | Regresión Logística | 0.423 | 1.000 | 0.595 | 1.000 |
| Atitlán | Random Forest | 0.579 | 1.000 | 0.733 | 1.000 |
| Atitlán | Gradient Boosting | 0.533 | 0.727 | 0.615 | 0.818 |
| Amatitlán | Regresión Logística | 0.830 | 0.983 | 0.900 | 0.998 |
| Amatitlán | Random Forest | 0.933 | 0.969 | 0.951 | 0.999 |
| Amatitlán | Gradient Boosting | 0.857 | 0.989 | 0.918 | 0.999 |

**Experimentos cruzados**

| Experimento | Modelo | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| A: Atitlán → Amatitlán | Regresión Logística | 0.797 | 0.788 | 0.792 | 0.978 |
| A: Atitlán → Amatitlán | Random Forest | 0.976 | **0.010** | 0.020 | 0.837 |
| A: Atitlán → Amatitlán | Gradient Boosting | 0.943 | **0.016** | 0.032 | **0.497** |
| B: Amatitlán → Atitlán | Regresión Logística | 0.242 | 1.000 | 0.390 | 1.000 |
| B: Amatitlán → Atitlán | Random Forest | 0.469 | 0.811 | 0.594 | 0.9999 |
| B: Amatitlán → Atitlán | Gradient Boosting | 0.231 | 1.000 | 0.376 | 0.9996 |

### 7.4 Comparación con mismo lago

La figura `p2_generalizacion_lagos.png` compara, para cada lago evaluado, el ROC-AUC del modelo entrenado en ese mismo lago contra el del modelo entrenado en el otro lago.

![ROC-AUC: modelo entrenado en el mismo lago vs. entrenado en el otro lago](../figuras/p2_generalizacion_lagos.png)

### 7.5 ¿Un modelo entrenado en un lago generaliza adecuadamente al otro?

**No, y el fracaso es asimétrico: los dos experimentos fallan por razones opuestas.**

**Experimento A (entrenar en Atitlán, evaluar en Amatitlán): colapso del Recall.** Random Forest pasa de un Recall de 0.969 en su línea base de Amatitlán a **0.010** cuando se entrena en Atitlán: detecta 1 de cada 100 zonas con alta presencia. Gradient Boosting queda igual de mal (0.016) y su ROC-AUC cae a **0.497**, indistinguible de lanzar una moneda. Nótese que la Precision se mantiene altísima (0.94-0.98): cuando estos modelos se atreven a marcar algo, aciertan; el problema es que casi nunca se atreven. La causa es directa: en el entrenamiento con Atitlán, la clase positiva representa el 0.026 % de las observaciones (razón 3,885 : 1). El modelo aprende, correctamente para ese lago, que la alta presencia de cianobacteria es un evento prácticamente inexistente, y traslada ese apriori a un lago donde ocurre en el 10.7 % de los píxeles.

**Experimento B (entrenar en Amatitlán, evaluar en Atitlán): colapso de la Precision.** Aquí el ROC-AUC se mantiene altísimo (0.9996-1.0000) y el Recall es excelente (0.81-1.00), pero la Precision se derrumba a 0.23-0.47. El modelo entrenado en Amatitlán ordena perfectamente los píxeles de Atitlán por riesgo —de ahí el ROC-AUC— pero coloca su umbral de decisión donde tenía sentido para un lago hipereutrófico, y termina marcando como alta presencia entre dos y cuatro veces más píxeles de los que realmente lo son. Es un problema de **calibración del umbral**, no de capacidad discriminativa.

**Esto contradice la expectativa inicial**, que anticipaba una caída mayor en B que en A. Ocurre lo contrario en términos de utilidad operativa: B produce un modelo demasiado sensible pero recuperable con un simple recalibrado del umbral, mientras que A produce un modelo inservible como sistema de alerta, porque no detecta las floraciones que debe detectar y ningún ajuste de umbral lo arregla en los modelos de árboles, cuya probabilidad predicha casi nunca supera niveles significativos.

**El único modelo que generaliza de forma aceptable en ambas direcciones es la Regresión Logística** (F1 de 0.79 en A y ROC-AUC de 1.00 en B), el mismo patrón observado en la validación temporal del inciso 6: la frontera lineal, al no poder ajustarse a las particularidades del lago de entrenamiento, transfiere mejor. Es un recordatorio de que el modelo con mejores métricas dentro de su dominio no es necesariamente el que mejor se traslada fuera de él.

### 7.6 Diferencias geográficas, ambientales y espectrales

- **Tamaño y profundidad**: Atitlán es un lago volcánico profundo y de gran superficie; Amatitlán es considerablemente más pequeño y somero, con mayor influencia relativa de las descargas urbanas e industriales de su cuenca. Estas diferencias físicas cambian la relación entre reflectancia superficial y concentración real de pigmentos.
- **Estado trófico de base**: la Parte I y el inciso 2 de esta parte documentan que Amatitlán opera en un régimen de clorofila-a sistemáticamente más alto que Atitlán; un modelo entrenado solo en Atitlán casi no observa ejemplos de "alta presencia" durante el entrenamiento, y uno entrenado solo en Amatitlán casi no observa ejemplos de "baja presencia" claramente estables.
- **Firma espectral de fondo**: diferencias en profundidad, sedimento en suspensión y composición del fondo del lago alteran la reflectancia de las bandas SWIR (`b11`, `b12`) y NIR (`b08`, `b8a`) incluso en ausencia de cianobacteria, por lo que un modelo puede confundir la firma espectral "normal" de un lago con una señal de floración en el otro.
- **Consecuencia práctica**: un modelo de este tipo debe entrenarse y calibrarse con datos del lago específico donde se va a usar, o al menos incluir observaciones de ambos lagos en el entrenamiento, en lugar de asumir que un modelo ajustado para un lago es directamente transferible al otro.

## Figuras generadas

- `informe/figuras/p2_generalizacion_lagos.png`

## Decisiones técnicas

- Los experimentos A y B entrenan con la totalidad de las observaciones del lago de origen, no con un 70%, porque en estos experimentos el conjunto de prueba es el otro lago completo; no hay riesgo de fuga entre entrenamiento y prueba al usar el 100% de un lago para entrenar y el 100% del otro para evaluar.
- Se usan los tres modelos con hiperparámetros por defecto, sin repetir la búsqueda del inciso 4.3, para mantener la comparación enfocada en el efecto del lago de entrenamiento y no en variaciones de ajuste fino entre modelos.
- Las líneas base de Atitlán deben leerse con cautela: su conjunto de prueba contiene apenas unas decenas de observaciones positivas (0.026 % de clase positiva), de modo que Precision y Recall se calculan sobre una muestra muy pequeña y son inestables. Es la razón por la que Atitlán muestra Recall de 1.000 con Precision de 0.42-0.58: basta con marcar generosamente para capturar los pocos positivos existentes.
