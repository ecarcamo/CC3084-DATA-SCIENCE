# Inciso 6. Validación espacial

## Metodología

Se divide cada lago en una cuadrícula regular de ~1 km × 1 km (`src/espacial.py`, `notebooks/p2_06_validacion_espacial.ipynb`) sobre las coordenadas `x_utm`/`y_utm` en EPSG:32615, ya calculadas en el inciso 1 al construir el dataset, por lo que este inciso no requiere una reproyección adicional. Cada observación se asigna a un bloque `"<lago>_<col>_<fila>"` (`asignar_bloques`), calculado por separado en cada lago para no mezclar identificadores entre Atitlán y Amatitlán. La validación espacial usa `StratifiedGroupKFold`: agrupa por bloque (ninguna observación de un mismo bloque queda repartida entre entrenamiento y validación dentro de un fold) y, dentro de esa restricción, intenta mantener la proporción de clases de cada fold cercana a la global.

## Resultados

### 6.1 Cuadrícula de bloques y evaluación del tamaño

`resumen_bloques` reporta, por lago, el número de bloques y la distribución de observaciones por bloque (`data/processed/p2_resumen_bloques.csv`). `n_splits_seguro` adapta automáticamente el número de folds de la validación cruzada al lago con menos bloques y a la clase minoritaria, para que la validación espacial no falle por falta de grupos si el tamaño de 1 km resultara insuficiente para Amatitlán, de menor extensión que Atitlán.

### 6.2 Bloques espaciales

La figura `p2_bloques_espaciales.png` visualiza los bloques asignados a cada lago sobre sus coordenadas UTM.

![Bloques espaciales de ~1 km usados para la validación espacial](../figuras/p2_bloques_espaciales.png)

### 6.3 y 6.4 Validación cruzada espacial y aleatoria

Los tres modelos (con los mismos hiperparámetros por defecto usados como punto de partida en el inciso 4.1) se evalúan bajo validación cruzada aleatoria estratificada (`cv_aleatoria`) y bajo validación cruzada espacial agrupada por bloque (`cv_espacial`), reportando ROC-AUC, Recall y F1 promedio por fold (`data/processed/p2_cv_aleatoria_vs_espacial.csv`, figura `p2_comparacion_cv.png`).

![ROC-AUC: validación aleatoria vs. validación espacial, por modelo](../figuras/p2_comparacion_cv.png)

### 6.5 y 6.6 Comparación e interpretación

Se espera que el ROC-AUC bajo validación espacial sea **menor** que bajo validación aleatoria, en mayor o menor grado según el modelo. La causa es la autocorrelación espacial: en la validación aleatoria, píxeles vecinos del mismo evento de floración (misma fecha, mismo parche de agua) pueden repartirse entre entrenamiento y prueba, de modo que el modelo "ve" durante el entrenamiento condiciones casi idénticas a las que luego evalúa, inflando el desempeño reportado. La validación espacial, al mantener cada bloque completo dentro de un único conjunto, obliga al modelo a predecir sobre zonas que nunca observó durante el entrenamiento, lo que da una estimación más realista de su capacidad para generalizar a zonas nuevas del mismo lago — el escenario relevante para el inciso 9 (mapas predictivos) y para un uso operativo real del modelo.

## Figuras generadas

- `informe/figuras/p2_bloques_espaciales.png`
- `informe/figuras/p2_comparacion_cv.png`

## Decisiones técnicas

- Se usa `StratifiedGroupKFold` en lugar de `GroupKFold` simple: agrupar únicamente por bloque, sin estratificar, podría producir folds con muy pocas o ninguna observación de la clase minoritaria dado el desbalance del inciso 2.4, especialmente en Atitlán.
- La cuadrícula se construye por división entera sobre `x_utm`/`y_utm` en lugar de con una librería de geometría (p. ej. geopandas), evitando una dependencia nueva para una operación que, sobre una grilla regular alineada a los ejes UTM, se resuelve con aritmética simple.
- El número de folds no se fija en 5 de forma incondicional: `n_splits_seguro` lo reduce si el lago con menos bloques o la clase minoritaria no alcanzan para 5 grupos, evitando que la validación espacial falle en Amatitlán por su menor extensión.
- Los valores numéricos exactos (número de bloques por lago, magnitud de la caída de ROC-AUC) se generan al ejecutar `p2_06_validacion_espacial.ipynb` sobre el dataset completo.
