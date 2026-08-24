# Inciso 5. Evaluación de los modelos

## Metodología

Los tres modelos ajustados en el inciso 4 se evalúan (`notebooks/p2_05_evaluacion.ipynb`) sobre el mismo conjunto de prueba (`data/processed/p2_test_set.parquet`), calculando Accuracy, Precision, Recall, F1, ROC-AUC y matriz de confusión (`src.modelado.evaluar`).

## Resultados

### 5.1 Métricas de evaluación

Sobre el conjunto de prueba compartido (89,998 observaciones, 5.5 % de clase positiva), los tres modelos obtienen:

| Modelo | Accuracy | Precision | Recall | F1 | F2 | ROC-AUC |
|---|---|---|---|---|---|---|
| Random Forest | 0.9915 | 0.8739 | 0.9878 | **0.9274** | **0.9627** | **0.9994** |
| Gradient Boosting | 0.9890 | 0.8375 | 0.9909 | 0.9077 | 0.9558 | 0.9993 |
| Regresión Logística | 0.9843 | 0.7800 | **0.9917** | 0.8732 | 0.9406 | 0.9988 |

La figura `p2_matrices_confusion.png` muestra la matriz de confusión de cada modelo y `p2_curvas_roc.png` compara sus curvas ROC.

![Matriz de confusión por modelo](../figuras/p2_matrices_confusion.png)

![Curvas ROC por modelo](../figuras/p2_curvas_roc.png)

### 5.2 Comparación de modelos

Los tres modelos alcanzan un desempeño alto y muy parecido entre sí: el ROC-AUC va de 0.9988 a 0.9994, un rango de seis diezmilésimas. La separación real entre ellos no está en la capacidad de ordenar observaciones por riesgo, sino en el **compromiso entre Precision y Recall**, y ese compromiso ordena a los modelos de forma inversa:

- **Random Forest** domina en ROC-AUC (0.9994), Precision (0.874) y F1 (0.927), y es el que menos falsas alarmas produce.
- **Regresión Logística** domina en Recall (0.9917), pero al costo de la Precision más baja (0.780): detecta casi todo, y a cambio marca como alta presencia bastantes zonas que no lo son.
- **Gradient Boosting** queda en medio en todas las métricas.

Es decir, **no hay un modelo que domine en todo**: el mejor en ROC-AUC no es el mejor en Recall. La diferencia de Recall entre el mejor (0.9917) y el peor (0.9878) es de apenas 0.4 puntos porcentuales, mientras que la diferencia de Precision es de 9.4 puntos. En la práctica, mover el criterio hacia Recall puro compra muy poca detección adicional y paga mucho en falsas alarmas, lo que se refleja en el F2 del apartado siguiente: **Random Forest gana también en F2 (0.9627)**, y es el modelo seleccionado como mejor para los incisos 8 y 9.

### 5.3 Consecuencias ambientales de los errores y métrica más adecuada

Los dos tipos de error de clasificación no tienen el mismo costo ambiental:

- **Falso positivo** (clasificar como alta presencia una zona que no lo es): genera una alerta innecesaria, con costo de cerrar temporalmente una zona de baño, generar preocupación pública injustificada o desviar recursos de monitoreo hacia un punto sin riesgo real. Es un costo principalmente económico y de confianza en el sistema de monitoreo.
- **Falso negativo** (no detectar una zona que sí presenta alta presencia de cianobacteria): implica que una floración tóxica real queda sin alerta, con riesgo directo para la salud de bañistas y usuarios del lago, sin activar medidas de mitigación.

El falso negativo tiene un costo potencial más alto (riesgo sanitario) que el falso positivo (costo operativo), por lo que se prioriza **minimizar los falsos negativos**, es decir, maximizar el **Recall** de la clase "alta presencia". La comparación final entre modelos para su uso como herramienta de alerta usa el Recall de la clase 1 como criterio principal, complementado con un **F2-score** (que pondera el Recall el doble que la Precision) y con ROC-AUC como criterio secundario entre modelos con Recall similar.

## Figuras generadas

- `informe/figuras/p2_matrices_confusion.png`
- `informe/figuras/p2_curvas_roc.png`

## Decisiones técnicas

- Se usa F2-score, no solo F1, como métrica compuesta de desempate: F1 pondera Precision y Recall por igual, mientras que el análisis ambiental del inciso 5.3 concluye que el Recall debe pesar más.
- El accuracy se reporta por completitud del enunciado, pero no se usa como criterio de comparación entre modelos, dado el desbalance de clases documentado en el inciso 2.4.
- La selección del mejor modelo se hace por F2 y no por Recall crudo: como los tres modelos están dentro de 0.4 puntos porcentuales de Recall, elegir por Recall crudo equivaldría a elegir por ruido, mientras que el F2 sí discrimina al penalizar la Precision muy inferior de la Regresión Logística.
- Un accuracy de 0.98-0.99 no es evidencia de buen desempeño en este problema: un clasificador trivial que siempre predijera "baja presencia" obtendría 0.945 de accuracy sobre este mismo conjunto de prueba. Lo que distingue a los modelos es el Recall sobre el 5.5 % positivo, no el accuracy global.
