# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (CC3084)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Laboratorio 7 — Spark MLlib
# CC3066 — Data Science, Semestre II 2026
#
# Reparto y reglas completas en `docs/PLAN_AVANCE.md` (Ej.1-4) y
# `docs/PLAN_FINAL.md` (Ej.5-8). Cada sección abajo tiene un dueño fijo —
# no editar fuera de la sección propia para evitar conflictos de merge.
#
# Versionado como `.py` (jupytext, formato `py:percent`). Commitear solo este
# archivo; el `.ipynb` con salidas se regenera una sola vez antes de cada
# entrega con `jupytext --sync notebooks/Lab7_Spark_MLlib.py` y se copia a la
# raíz del repo como `Lab7_Spark_MLlib.ipynb`.

# %% [markdown]
# ## S0 — Setup (dueño: P1)
# JAVA_HOME, SparkSession, imports, rutas. No modificar salvo que el setup
# esté roto para todos.

# %%
import os

os.environ.setdefault(
    "JAVA_HOME",
    "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home",
)

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

spark = (
    SparkSession.builder.appName("lab7-spark-mllib")
    .master("local[*]")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

RAW_DIR = "data/raw/eneic"
PROCESSED_DIR = "data/processed"
MODELS_DIR = "models"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

SEED = 42

spark

# %% [markdown]
# ## S1 — Carga, armonización y calidad de datos (dueño: P1, Ej.1 — 5 pts)
# Leer los 5 `.xlsx` de `data/raw/eneic/`, seleccionar columnas, homologar
# tipos, derivar `periodo_archivo`/`anio_archivo`/`trimestre_calendario` del
# **nombre de archivo** (no de `TRIMESTRE`), unir 2025 con `unionByName`,
# aplicar filtros de población y calidad, verificar unicidad de clave, y
# escribir `data/processed/eneic_2025.parquet` y `eneic_2026.parquet`.
#
# Ver reglas técnicas completas en `docs/PLAN_AVANCE.md`.

# %%
# TODO(P1): carga individual de cada archivo Excel + selección de columnas +
# homologación de tipos.


# %%
# TODO(P1): derivación de periodo_archivo / anio_archivo / trimestre_calendario
# / archivo_origen a partir del nombre de archivo. unionByName de 2025.


# %%
# TODO(P1): filtros de población y calidad, con conteo por paso.


# %%
# TODO(P1): verificación de unicidad de (periodo_archivo, NUM_HOGAR, NUM_PERSONA).


# %%
# TODO(P1): escritura de Parquet 2025 y 2026.

# %% [markdown]
# **Respuestas (P1):**
# - ¿Por qué IV de 2025 no puede apilarse por posición de columnas?
# - ¿Diferencia entre dato ausente porque la pregunta no aplica y una
#   respuesta no registrada?
# - ¿Por qué una persona observada en dos períodos no se elimina como duplicado?
# - ¿Por qué el número de registros de la base filtrada no representa a todos
#   los trabajadores del país?

# %% [markdown]
# ## S2 — Estadística descriptiva y preguntas de exploración (dueño: P2, Ej.2 — 5 pts)
# Requiere `data/processed/eneic_2025.parquet` (de S1).

# %%
# TODO(P2): lectura de Parquet 2025, tabla de n/media/mediana/sd/min/max/p25/p75/p95
# para salario_mensual, edad, antiguedad, horas_semanales.


# %%
# TODO(P2): gráficas (muestra <=5,000-10,000 filas a pandas; métricas sobre el
# total) + interpretación en Markdown de cada una.

# %% [markdown]
# ## S3 — Relaciones entre variables numéricas (dueño: P2, Ej.3 — 5 pts)

# %%
# TODO(P2): VectorAssembler + Correlation.corr() de pyspark.ml.stat sobre
# salario_mensual, edad, antiguedad, horas_semanales. Mapa de calor.

# %% [markdown]
# **Respuestas (P2):**
# - ¿Qué variables presentan mayor asociación lineal con el salario?
# - ¿Existe relación entre edad y antigüedad?

# %% [markdown]
# ## S4 — Segmentación de perfiles mediante KMeans (dueño: P3, Ej.4 — 10 pts)
# Requiere `data/processed/eneic_2025.parquet` (de S1).

# %%
# TODO(P3): selección de variables, decisión justificada sobre incluir salario,
# estandarización (StandardScaler), KMeans para K=2,3,4,5 con métrica de
# calidad (WSSSE / silueta vía ClusteringEvaluator).


# %%
# TODO(P3): elección de K + descripción de cada cluster en prosa.

# %% [markdown]
# ---
# ## MODELADO SUPERVISADO PARA PREDICCIÓN (75 pts)
# Splits acordados (ver `docs/PLAN_FINAL.md`):
# - Desarrollo: train = 2025 T1-T3, validación = 2025 T4.
# - Selección: menor RMSE de validación por algoritmo.
# - Final: reentrenar con todo 2025, evaluar en 2026 T1.
# - 6 predictores exactos: edad, antiguedad, horas_semanales, nivel_educativo,
#   categoria_ocupacional, dominio.

# %%
# TODO(P1): split de 2025 en train (T1-T3) y validación (T4). Compartido por
# S5, S6 y S7 — no duplicar la lógica, todos leen las mismas variables.

# %% [markdown]
# ## S5 — Baseline + Pipeline de regresión lineal (dueño: P1, Ej.5 — 20 pts)

# %%
# TODO(P1): baseline = media de salario_mensual en train. MAE/RMSE/R² en validación.


# %%
# TODO(P1): Pipeline StringIndexer+OneHotEncoder (nivel_educativo,
# categoria_ocupacional, dominio) + VectorAssembler + estandarización
# (standardization=True en LinearRegression o StandardScaler, no ambos) +
# LinearRegression. >=2 configuraciones de regularización documentadas.
# Guardar mejor modelo en models/lr_best.

# %% [markdown]
# ## S6 — Pipeline de Random Forest (dueño: P2, Ej.6 — 20 pts)
# Usa el mismo split y las mismas columnas categóricas que S5.

# %%
# TODO(P2): Pipeline StringIndexer+OneHotEncoder + VectorAssembler +
# RandomForestRegressor (sin estandarizar). >=2 configuraciones (numTrees /
# maxDepth) documentadas, semilla fija. Guardar mejor modelo en models/rf_best.


# %% [markdown]
# **Comparación LR vs. RF (P2):** ¿cuál obtuvo mejor RMSE de validación y qué
# diferencias explican el resultado?

# %% [markdown]
# ## S7 — Entrenamiento final y evaluación en 2026 (dueños: P1 + P2, Ej.7 — 20 pts)

# %%
# TODO(P1): reentrenar configuración ganadora de LR con todo 2025.
# TODO(P2): reentrenar configuración ganadora de RF con todo 2025.


# %%
# TODO(P1+P2): predicciones sobre 2026 T1 (mismas reglas de preparación de S1),
# verificar mismo conteo de registros elegibles para ambos modelos, tabla
# comparativa baseline/LR/RF con MAE/RMSE/R² en validación y en prueba.

# %% [markdown]
# ## S8 — Visualización y análisis de errores (dueño: P3, Ej.8 — 15 pts)
# Requiere las predicciones de prueba de S7.

# %%
# TODO(P3): residuo = salario_real - salario_predicho. Para LR y RF, misma
# muestra <=5,000 filas de 2026 T1: real vs. predicho (línea y=x), residuos
# vs. predicho (línea en 0).


# %%
# TODO(P3): tabla de MAE y error medio por nivel_educativo y por dominio
# (sobre todos los registros de prueba, con n por grupo).


# %%
# TODO(P3): análisis por percentil de salario — ¿tendencia a subestimar o
# sobreestimar salarios altos?

# %% [markdown]
# ### Discusión final (P3, con insumos de todo el equipo)
# Integrar perfiles de KMeans, correlaciones, comparación LR vs. RF y patrón
# de errores. Recordar: las asociaciones encontradas no son causales.

# %%
spark.stop()
