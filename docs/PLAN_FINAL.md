# Lab 7 — Plan final (Ejercicios 5–8, 75 pts)

**Entrega:** domingo 27 de septiembre de 2026, 23:59 hrs.
**Alcance:** regresión lineal (Ej.5), Random Forest (Ej.6), entrenamiento final
y evaluación en 2026 (Ej.7), visualización y análisis de errores (Ej.8).
**Prerrequisito:** `docs/PLAN_AVANCE.md` completo, `data/processed/eneic_2025.parquet`
y `data/processed/eneic_2026.parquet` existentes.

## Splits (acordados por todo el equipo antes de empezar S5)

- **Desarrollo:** train = 2025 T1+T2+T3 (`trimestre_calendario ∈ {1,2,3}`);
  validación = 2025 T4 (`trimestre_calendario = 4`).
- **Selección de configuración:** menor RMSE de validación, por algoritmo.
- **Entrenamiento final:** reentrenar la configuración ganadora de cada
  algoritmo con **todo 2025** (T1–T4).
- **Prueba final:** evaluar sobre 2026 T1, con las mismas reglas de preparación
  y **exactamente los mismos registros elegibles** para ambos modelos.
- **Baseline de referencia:** modelo que predice la media de `salario_mensual`
  del set de entrenamiento correspondiente. Sirve para interpretar si LR/RF
  realmente aportan.

Todos los `StringIndexer` / `OneHotEncoder` / `StandardScaler` se ajustan
**solo con datos de entrenamiento**, dentro del `Pipeline` (evita fuga de
información). Semilla fija en todo el notebook.

## Reparto

| Persona | Sección | Ejercicio | Pts |
|---|---|---|---|
| **P1** | Baseline + S5 Pipeline LinearRegression | Ej.5 | 20 |
| **P2** | S6 Pipeline RandomForest | Ej.6 | 20 |
| **P1 + P2** | S7 Entrenamiento final y evaluación en 2026 (cada quien corre su modelo, comparan juntos) | Ej.7 | 20 |
| **P3** | S8 Visualización y análisis de errores + discusión final | Ej.8 | 15 |

**Orden:** P1 cierra S5 primero (fija baseline, splits y convención de columnas
categóricas/OHE); P2 arranca S6 en cuanto eso esté commiteado en `lab7`, para
usar exactamente los mismos conjuntos. P3 empieza en cuanto P1 y P2 tienen
predicciones de validación, y termina con las de prueba (S7).

## Detalle por persona

### P1 — Baseline + S5 Pipeline de regresión lineal (Ej.5, 20 pts)

1. Baseline: predicción constante = media de `salario_mensual` en train.
   MAE/RMSE/R² en validación, para comparar contra LR y RF.
2. Pipeline:
   - `StringIndexer` + `OneHotEncoder` para `nivel_educativo`,
     `categoria_ocupacional`, `dominio`.
   - `VectorAssembler` combinando `edad`, `antiguedad`, `horas_semanales` con
     las categóricas codificadas.
   - Estandarización: usar `standardization=True` de `LinearRegression`
     **o** `StandardScaler` — no ambos.
   - `LinearRegression` para `salario_mensual`.
3. Probar ≥2 configuraciones de regularización (`regParam`, `elasticNetParam`).
   Documentar los valores probados.
4. Elegir la de menor RMSE de validación. Guardar el modelo (`models/lr_best`).
5. Presentar MAE, RMSE, R² e interpretar frente al baseline.

### P2 — S6 Pipeline de Random Forest (Ej.6, 20 pts)

Usa los mismos conjuntos de entrenamiento/validación que P1 (sin estandarizar:
`RandomForestRegressor` no lo requiere).

1. Pipeline: mismo `StringIndexer` + `OneHotEncoder` + `VectorAssembler` que
   S5 (misma convención de columnas), `RandomForestRegressor`.
2. Probar ≥2 configuraciones variando número de árboles y/o profundidad
   máxima. Semilla fija. Documentar valores.
3. Elegir la de menor RMSE de validación. Guardar el modelo (`models/rf_best`).
4. Presentar MAE, RMSE, R²; comparar contra LR y el baseline.
5. Explicar en Markdown cuál algoritmo ganó en validación y qué diferencias
   (linealidad, interacciones, manejo de categóricas) lo explican.

### P1 + P2 — S7 Entrenamiento final y evaluación en 2026 (Ej.7, 20 pts)

1. Reentrenar la configuración ganadora de LR (P1) y de RF (P2), cada uno con
   **todo 2025** como entrenamiento.
2. Generar predicciones sobre 2026 T1, aplicando las mismas reglas de
   preparación de S1 (filtros de población, validaciones numéricas,
   categóricas → `"DESCONOCIDO"`).
3. Evaluar ambos modelos sobre **exactamente los mismos registros elegibles**
   de prueba (verificar que el conteo de filas evaluadas sea idéntico para
   ambos antes de comparar métricas).
4. Tabla comparativa final: baseline vs. LR vs. RF, con MAE/RMSE/R² en
   validación y en prueba 2026.

### P3 — S8 Visualización y análisis de errores (Ej.8, 15 pts)

Depende de las predicciones de prueba de P1 y P2 (S7).

1. Definir `residuo = salario_real - salario_predicho` (positivo = subestimación,
   negativo = sobreestimación) — misma definición para ambos modelos.
2. Para cada modelo (LR y RF), usando la **misma muestra** de hasta 5,000
   registros de 2026 T1:
   - gráfico de salario real vs. predicho, con línea de referencia y = x;
   - gráfico de residuos vs. predicho, con línea horizontal en 0.
3. Tabla de MAE y error medio (residuo promedio) por `nivel_educativo` y por
   `dominio`, con número de observaciones por grupo — calculada sobre **todos**
   los registros de prueba, no la muestra de graficar.
4. Analizar por percentil de salario: ¿los errores son parejos? ¿hay tendencia
   a subestimar o sobreestimar salarios altos?
5. **Discusión final** integrando: perfiles de KMeans, resultados de
   correlación, comparación LR vs. RF, y el patrón de errores encontrado.
   Recordar la advertencia del enunciado: las asociaciones no son causales.

## Reglas técnicas comunes (recordatorio, iguales al avance)

- No usar scikit-learn para entrenar — solo `pyspark.ml`.
- No usar `FACTOR` como peso en modelos ni métricas.
- No transformar `salario_mensual` (sin log) en la comparación obligatoria;
  escala log solo permitida para visualizar.
- No recortar outliers de salario.
- Solo tablas agregadas o muestras ≤5,000–10,000 filas van a pandas para
  graficar; métricas siempre sobre el conjunto completo correspondiente.
- El notebook corre de principio a fin sin variables de sesiones previas.
- Ninguna tabla o gráfica sin interpretación en Markdown.

## Flujo de Git

Igual que en el avance: commitear solo `notebooks/Lab7_Spark_MLlib.py`
(jupytext). Antes de la entrega final, una sola persona corre todo el
notebook y regenera `Lab7_Spark_MLlib.ipynb` con salidas — ese es el commit
final del `.ipynb` que se entrega junto con el link del repositorio.

## Checklist antes de entregar

- [ ] Baseline, LR y RF evaluados con las mismas métricas y los mismos splits.
- [ ] ≥2 configuraciones documentadas para LR y para RF.
- [ ] Mejor LR y mejor RF guardados en `models/`.
- [ ] LR y RF evaluados sobre el mismo conjunto de registros elegibles de 2026 T1
      (conteo de filas verificado idéntico).
- [ ] Gráficas real-vs-predicho y residuos para ambos modelos, misma muestra.
- [ ] Tabla de MAE/error medio por nivel educativo y dominio, sobre todo el
      conjunto de prueba.
- [ ] Discusión final redactada, integrando EDA + clustering + modelos + errores.
- [ ] `Kernel → Restart & Run All` corre sin error de principio a fin.
- [ ] `.ipynb` final regenerado con `jupytext --sync`, con salidas visibles.
- [ ] Link del repositorio listo para entregar.
