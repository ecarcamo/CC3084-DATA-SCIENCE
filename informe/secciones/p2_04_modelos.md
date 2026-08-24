# Inciso 4. Construcción de modelos de Machine Learning

## Metodología

Los tres modelos mínimos requeridos (`src/modelado.py`, `notebooks/p2_04_modelos.ipynb`) se construyen sobre `data/processed/dataset_ml_muestra.parquet` con las 11 predictoras del inciso 3. Regresión Logística usa un `Pipeline` con escalado (`StandardScaler`) por ser sensible a la escala de los predictores; Random Forest y Gradient Boosting, al basarse en árboles, no lo requieren. Regresión Logística y Random Forest reciben `class_weight="balanced"`; `GradientBoostingClassifier` no admite ese parámetro, así que su entrenamiento se compensa con `sample_weight` calculado como "balanced" sobre `y_train`.

## Resultados

### 4.1 Modelos base

Se instancian Regresión Logística, Random Forest y Gradient Boosting con `src.modelado.construir_modelos_base`.

### 4.2 División 70/30 y entrenamiento inicial

`dividir_datos` aplica una división estratificada por `alta_cianobacteria`, con semilla fija (`SEMILLA = 42`), sobre las 299,992 observaciones de la muestra de trabajo: 209,994 de entrenamiento y 89,998 de prueba, ambas con 5.5 % de clase positiva. Estratificar preserva en ambos subconjuntos la proporción de clases documentada en el inciso 2.4; la semilla fija permite recalcular el mismo conjunto de prueba en cualquier notebook posterior sin necesidad de persistir índices, siempre que se parta del mismo `dataset_ml_muestra.parquet`.

### 4.3 Ajuste de hiperparámetros

Cada modelo se ajusta con `RandomizedSearchCV` (validación cruzada de 3 particiones, `scoring="roc_auc"`) sobre un grid pequeño centrado en sus hiperparámetros de mayor impacto en el balance sesgo/varianza:

| Modelo | Hiperparámetros evaluados |
|---|---|
| Regresión Logística | `C` (regularización): 0.01, 0.1, 1, 10 |
| Random Forest | `n_estimators`: 200, 400; `max_depth`: 8, 16, sin límite; `min_samples_leaf`: 1, 5, 20 |
| Gradient Boosting | `n_estimators`: 100, 200; `learning_rate`: 0.05, 0.1; `max_depth`: 2, 3, 4 |

El criterio de selección es **ROC-AUC**: es la métrica menos sensible al desbalance de clases del inciso 2.4, a diferencia de accuracy, y no exige fijar de antemano un umbral de decisión como sí lo requieren precision/recall/F1.

Los hiperparámetros seleccionados (`data/processed/p2_hiperparametros.csv`) fueron:

| Modelo | Hiperparámetros seleccionados |
|---|---|
| Regresión Logística | `C = 10.0` |
| Random Forest | `n_estimators = 400`, `min_samples_leaf = 5`, `max_depth = None` (sin límite) |
| Gradient Boosting | `n_estimators = 100`, `learning_rate = 0.1`, `max_depth = 4` |

La búsqueda elige, en los tres casos, la configuración de mayor capacidad dentro del grid: la regularización más débil en Regresión Logística (`C = 10`), el bosque más grande y sin límite de profundidad en Random Forest, y la profundidad máxima disponible en Gradient Boosting. Con 210,000 observaciones de entrenamiento y solo 11 predictoras, la relación observaciones/parámetros es lo bastante holgada como para que el sobreajuste no penalice en validación cruzada, y el ligero `min_samples_leaf = 5` de Random Forest actúa como la única restricción efectiva contra hojas de un solo píxel.

### 4.4 Conjunto de prueba compartido

El mismo `X_test`/`y_test`, generado en una sola llamada a `dividir_datos`, se usa para evaluar los tres modelos en el inciso 5. Los tres modelos ajustados se guardan en `data/processed/modelos/` (`guardar_modelo`) y el conjunto de prueba en `data/processed/p2_test_set.parquet`, para reutilizarlos en los incisos 5, 7, 8 y 9 sin reentrenar.

## Decisiones técnicas

- Se usa Gradient Boosting de `scikit-learn` en lugar de XGBoost: cumple el requisito del enunciado ("Gradient Boosting o XGBoost") sin agregar una dependencia nueva al proyecto, y es directamente compatible con `shap.TreeExplainer` en el inciso 8.
- El desbalance de clases se compensa en el entrenamiento (`class_weight`/`sample_weight`), no mediante sobremuestreo u submuestreo, para no alterar la distribución espacial y temporal real de las observaciones, relevante para los incisos 6 y 9.
- La búsqueda de hiperparámetros toma ~5.5 minutos sobre la muestra de trabajo con 32 núcleos; el costo lo domina Gradient Boosting, cuya implementación en scikit-learn construye los árboles de forma secuencial y no se paraleliza dentro de un mismo ajuste.
