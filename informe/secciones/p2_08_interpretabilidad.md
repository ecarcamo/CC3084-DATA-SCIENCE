# Inciso 8. Interpretación y explicabilidad del modelo

## Metodología

`notebooks/p2_08_interpretabilidad.ipynb` toma el modelo con mejor F2-score del inciso 5 (`data/processed/p2_metricas_modelos.csv`), el criterio orientado a Recall definido en el 5.3, y lo interpreta con importancia global de variables (`src.modelado.importancia_global`) y con SHAP. Random Forest y Gradient Boosting exponen `feature_importances_` directamente; Regresión Logística, envuelta en un `Pipeline` con escalado, se interpreta con el valor absoluto de sus coeficientes estandarizados. Para SHAP, los modelos de árboles usan `shap.TreeExplainer` (exacto y eficiente); Regresión Logística usa el `shap.Explainer` genérico sobre `predict_proba`, con una muestra de referencia. Los valores SHAP se calculan sobre una submuestra de 2,000 observaciones del conjunto de prueba del inciso 4, suficiente para un resumen estable sin el costo de explicar el conjunto completo.

## Resultados

### 8.1 Importancia global de variables

La figura `p2_importancia_variables.png` muestra la importancia de cada predictora para el mejor modelo (`data/processed/p2_importancia_variables.csv`).

![Importancia global de variables del mejor modelo](../figuras/p2_importancia_variables.png)

### 8.2 SHAP Summary Plot

La figura `p2_shap_summary.png` muestra la dispersión de valores SHAP de cada predictora sobre la submuestra explicada.

![SHAP summary plot del mejor modelo](../figuras/p2_shap_summary.png)

### 8.3 y 8.4 Variables de mayor influencia e interpretación ambiental

Interpretación ambiental esperada, a confirmar con el gráfico generado:

- **`ndvi` y `verde_azul_ratio`**: valores altos deberían empujar la predicción hacia "alta presencia". Ambas variables capturan, de forma indirecta, la señal de pigmentos fotosintéticos (biomasa algal, absorción de clorofila) que también produce el NDCI excluido en el inciso 2.5, consistente con su correlación positiva ya observada en el inciso 3.
- **`ndwi`**: valores altos deberían empujar la predicción hacia "baja presencia". Un NDWI alto indica agua "limpia", con poca interferencia de materia en suspensión; las floraciones dispersan más luz visible/NIR y reducen esta señal.
- **`fai` y `b8a`**: valores altos, asociados a materia flotante en superficie, deberían empujar la predicción hacia "alta presencia", coherente con el diseño del Floating Algae Index para detectar acumulaciones superficiales de algas.
- **Bandas SWIR (`b11`, `b12`)**: se espera una influencia más moderada y menos monótona que las anteriores, aportando información complementaria sobre turbidez/sedimento más que una señal directa de biomasa algal.

Si el mejor modelo resulta ser Random Forest o Gradient Boosting, es esperable que el orden de importancia de `p2_importancia_variables.png` sea consistente con el patrón de dispersión del SHAP summary plot, aunque no necesariamente idéntico: la importancia global promedia el efecto absoluto de cada variable, mientras que SHAP además muestra la dirección del efecto para cada observación individual.

## Figuras generadas

- `informe/figuras/p2_importancia_variables.png`
- `informe/figuras/p2_shap_summary.png`

## Decisiones técnicas

- SHAP se calcula sobre una submuestra de 2,000 observaciones del conjunto de prueba, no sobre el conjunto completo: `TreeExplainer` es exacto pero su costo crece con el número de observaciones explicadas, y una submuestra de este tamaño ya da un resumen visual estable.
- Para Regresión Logística se usa el `shap.Explainer` genérico sobre `predict_proba` en lugar de `LinearExplainer`, para tener una única ruta de código (aplicable a cualquier modelo con `predict_proba`) en vez de una rama adicional específica para modelos lineales.
- El criterio de selección del "mejor modelo" es el F2-score del inciso 5.3 (orientado a Recall), no ROC-AUC, para mantener la interpretabilidad alineada con la prioridad ambiental ya establecida: minimizar falsos negativos.
- Los valores numéricos exactos (importancias, variables de mayor influencia SHAP) se generan al ejecutar `p2_08_interpretabilidad.ipynb` sobre el dataset completo.
