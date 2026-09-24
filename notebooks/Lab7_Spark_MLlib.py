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

# Override, not setdefault: many shells already export JAVA_HOME (e.g. to an
# unversioned/newer JDK via `brew link openjdk`). Spark 3.5 needs 8/11/17;
# setdefault would silently keep an incompatible JAVA_HOME already in the env.
os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

import setuptools  # noqa: F401  (shims stdlib distutils, removed in Python 3.12; pyspark 3.5 still imports it)
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
# Leer las 5 bases de Personas de `data/raw/eneic/` (INE publica I-2025 como
# `.xlsx`; II/III/IV-2025 y I-2026 solo como `.sav` — se leen con
# `pyreadstat`, ambos formatos se homologan al mismo esquema antes de crear
# el DataFrame de Spark), seleccionar columnas, homologar tipos, derivar
# `periodo_archivo`/`anio_archivo`/`trimestre_calendario` del **nombre de
# archivo** (no de `TRIMESTRE`), unir 2025 con `unionByName`, aplicar filtros
# de población y calidad, verificar unicidad de clave, y escribir
# `data/processed/eneic_2025.parquet` y `eneic_2026.parquet`.
#
# Ver reglas técnicas completas en `docs/PLAN_AVANCE.md`.

# %%
import pandas as pd
import pyreadstat

RAW_COLS = [
    "ANIO", "TRIMESTRE", "DOMINIO", "NUM_HOGAR", "NUM_PERSONA", "FACTOR",
    "OCUPADOS", "P02A03", "P03A03A", "P05C07A", "P05C07B", "P05C16",
    "P05D01", "P05H01A",
]

# El período real depende del archivo de origen, no de TRIMESTRE (ver
# docs/PLAN_AVANCE.md): I-2025 trae TRIMESTRE=2, II-2025=3 (175 filas en 2),
# III-2025=4, IV-2025=5, I-2026=6. TRIMESTRE se conserva sin modificar.
FILE_MANIFEST = [
    dict(path=f"{RAW_DIR}/personas_2025_T1.xlsx", fmt="xlsx",
         periodo_archivo="2025T1", anio_archivo=2025, trimestre_calendario=1,
         archivo_origen="personas_2025_T1.xlsx", expected_rows=51588),
    dict(path=f"{RAW_DIR}/personas_2025_T2.sav", fmt="sav",
         periodo_archivo="2025T2", anio_archivo=2025, trimestre_calendario=2,
         archivo_origen="personas_2025_T2.sav", expected_rows=51167),
    dict(path=f"{RAW_DIR}/personas_2025_T3.sav", fmt="sav",
         periodo_archivo="2025T3", anio_archivo=2025, trimestre_calendario=3,
         archivo_origen="personas_2025_T3.sav", expected_rows=51583),
    dict(path=f"{RAW_DIR}/personas_2025_T4.sav", fmt="sav",
         periodo_archivo="2025T4", anio_archivo=2025, trimestre_calendario=4,
         archivo_origen="personas_2025_T4.sav", expected_rows=49338),
    dict(path=f"{RAW_DIR}/personas_2026_T1.sav", fmt="sav",
         periodo_archivo="2026T1", anio_archivo=2026, trimestre_calendario=1,
         archivo_origen="personas_2026_T1.sav", expected_rows=49843),
]

VALID_NIVEL_EDUCATIVO = list(range(0, 8))   # 0=NINGUNO ... 7=DOCTORADO (dic. Personas)
VALID_DOMINIO = [1, 2, 3]                   # 1=Urbano Metropolitano, 2=Resto Urbano, 3=Rural Nacional
VALID_CATEGORIA_OCUPACIONAL = [1, 2, 3, 4]  # gobierno / empresa privada / jornalero-peón / doméstico


def read_raw(path: str, fmt: str) -> pd.DataFrame:
    """Lee un archivo (xlsx u openpyxl / sav vía pyreadstat) y homologa tipos.

    Un mismo código puede llegar como número o como texto según el formato de
    origen; forzar numérico antes de construir el DataFrame de Spark evita
    ese desajuste al hacer unionByName.
    """
    if fmt == "xlsx":
        pdf = pd.read_excel(path, usecols=RAW_COLS)
    else:
        pdf, _ = pyreadstat.read_sav(path, usecols=RAW_COLS)
    for c in RAW_COLS:
        pdf[c] = pd.to_numeric(pdf[c], errors="coerce")
    return pdf


def fix_nan_to_null(sdf, cols):
    """spark.createDataFrame(pandas_df) preserva NaN de pandas como NaN de
    punto flotante, no como NULL de SQL. Spark trata NaN como mayor que
    cualquier valor en comparaciones (>, >=), así que sin esto los filtros de
    calidad de abajo dejarían pasar silenciosamente los valores faltantes."""
    for c in cols:
        sdf = sdf.withColumn(c, F.when(F.isnan(F.col(c)), F.lit(None)).otherwise(F.col(c)))
    return sdf


def load_period(spec: dict):
    pdf = read_raw(spec["path"], spec["fmt"])
    n_raw = len(pdf)
    pdf["periodo_archivo"] = spec["periodo_archivo"]
    pdf["anio_archivo"] = spec["anio_archivo"]
    pdf["trimestre_calendario"] = spec["trimestre_calendario"]
    pdf["archivo_origen"] = spec["archivo_origen"]
    sdf = spark.createDataFrame(pdf)
    sdf = fix_nan_to_null(sdf, RAW_COLS)
    return sdf, n_raw


raw_counts = {}
frames_2025 = []
sdf_2026_raw = None
for spec in FILE_MANIFEST:
    _sdf, _n_raw = load_period(spec)
    raw_counts[spec["periodo_archivo"]] = _n_raw
    if spec["anio_archivo"] == 2025:
        frames_2025.append(_sdf)
    else:
        sdf_2026_raw = _sdf

print("Conteos por archivo antes de filtros (raw), vs. esperado por el enunciado:")
for spec in FILE_MANIFEST:
    n, exp = raw_counts[spec["periodo_archivo"]], spec["expected_rows"]
    print(f"  {spec['periodo_archivo']}: {n} (esperado {exp}) -> {'OK' if n == exp else 'MISMATCH'}")

# %% [markdown]
# Derivación de columnas analíticas (renombrado + antigüedad) y `unionByName`
# de los cuatro trimestres de 2025 — nunca `union` posicional, porque IV-2025
# trae 302 columnas contra 270 en los demás (ver respuesta más abajo).

# %%
def add_analytic_columns(sdf):
    return (
        sdf.withColumnRenamed("P02A03", "edad")
        .withColumnRenamed("P05H01A", "horas_semanales")
        .withColumnRenamed("OCUPADOS", "ocupado")
        .withColumnRenamed("P05C16", "categoria_ocupacional_raw")
        .withColumn("salario_mensual", F.col("P05D01"))
        .withColumn("antiguedad_anios", F.col("P05C07A"))
        .withColumn("antiguedad_meses", F.col("P05C07B"))
        .withColumn("antiguedad", F.col("antiguedad_anios") + F.col("antiguedad_meses") / F.lit(12.0))
        .withColumnRenamed("P03A03A", "nivel_educativo_raw")
        .withColumnRenamed("DOMINIO", "dominio_raw")
    )


frames_2025 = [add_analytic_columns(s) for s in frames_2025]
sdf_2026_raw = add_analytic_columns(sdf_2026_raw)

df_2025_raw = frames_2025[0]
for _sdf in frames_2025[1:]:
    df_2025_raw = df_2025_raw.unionByName(_sdf)
df_2025_raw = df_2025_raw.cache()
print(f"Total 2025 unido (antes de filtrar): {df_2025_raw.count()}")

ANALYTIC_VARS = [
    "salario_mensual", "edad", "antiguedad_anios", "antiguedad_meses",
    "horas_semanales", "nivel_educativo_raw", "categoria_ocupacional_raw",
    "dominio_raw", "ocupado",
]


def missingness_report(sdf, cols, label):
    total = sdf.count()
    print(f"\nFaltantes antes de filtros ({label}), n={total}:")
    exprs = [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in cols]
    row = sdf.select(*exprs).collect()[0].asDict()
    for c in cols:
        pct = 100.0 * row[c] / total if total else 0.0
        print(f"  {c}: {row[c]} faltantes ({pct:.2f}%)")


missingness_report(df_2025_raw, ANALYTIC_VARS, "2025")

# %% [markdown]
# Filtros de población y calidad (docs/PLAN_AVANCE.md), aplicados siempre en
# el mismo orden y contando exclusiones en cada paso.

# %%
def filter_step(df, condition, label, counts):
    before = df.count()
    kept = df.filter(condition)
    after = kept.count()
    counts.append((label, before, after, before - after))
    return kept


def apply_quality_filters(df, label):
    counts = []
    df = filter_step(df, F.col("edad").isNotNull() & (F.col("edad") >= 15),
                      "edad finita >= 15", counts)
    df = filter_step(df, F.col("ocupado") == 1, "OCUPADOS == 1", counts)
    df = filter_step(
        df, F.col("categoria_ocupacional_raw").isin(VALID_CATEGORIA_OCUPACIONAL),
        "P05C16 in {1,2,3,4}", counts,
    )
    df = filter_step(
        df, F.col("salario_mensual").isNotNull() & (F.col("salario_mensual") > 0),
        "P05D01 finito y > 0", counts,
    )
    df = filter_step(
        df, F.col("antiguedad_anios").isNotNull() & (F.col("antiguedad_anios") >= 0),
        "antiguedad_anios >= 0", counts,
    )
    df = filter_step(
        df,
        F.col("antiguedad_meses").isNotNull()
        & (F.col("antiguedad_meses") >= 0) & (F.col("antiguedad_meses") <= 11)
        & (F.col("antiguedad_meses") == F.floor("antiguedad_meses")),
        "antiguedad_meses entero 0-11", counts,
    )
    df = filter_step(df, F.col("antiguedad") <= F.col("edad"), "antiguedad <= edad", counts)
    df = filter_step(
        df, (F.col("horas_semanales") > 0) & (F.col("horas_semanales") <= 168),
        "0 < horas_semanales <= 168", counts,
    )
    print(f"\nCascada de filtros ({label}):")
    for name, before, after, excluded in counts:
        print(f"  {name}: {before} -> {after}  (excluidos: {excluded})")
    return df


def recode_categoricals(df):
    # cast double -> int -> string para que el código quede "0","1" (no "0.0").
    return (
        df.withColumn(
            "nivel_educativo",
            F.when(
                F.col("nivel_educativo_raw").isin(VALID_NIVEL_EDUCATIVO),
                F.col("nivel_educativo_raw").cast("int").cast("string"),
            ).otherwise(F.lit("DESCONOCIDO")),
        )
        .withColumn(
            "dominio",
            F.when(
                F.col("dominio_raw").isin(VALID_DOMINIO),
                F.col("dominio_raw").cast("int").cast("string"),
            ).otherwise(F.lit("DESCONOCIDO")),
        )
        .withColumn("categoria_ocupacional", F.col("categoria_ocupacional_raw").cast("int").cast("string"))
    )


FINAL_COLS = [
    "periodo_archivo", "anio_archivo", "trimestre_calendario", "archivo_origen",
    "NUM_HOGAR", "NUM_PERSONA", "FACTOR", "ANIO", "TRIMESTRE",
    "salario_mensual", "edad", "antiguedad", "antiguedad_anios", "antiguedad_meses",
    "horas_semanales", "nivel_educativo", "categoria_ocupacional", "dominio", "ocupado",
]

df_2025_filtered = apply_quality_filters(df_2025_raw, "2025")
df_2025_final = recode_categoricals(df_2025_filtered).select(*FINAL_COLS).cache()
print(f"\n2025 final: {df_2025_final.count()} registros elegibles")

missingness_report(sdf_2026_raw, ANALYTIC_VARS, "2026")
df_2026_filtered = apply_quality_filters(sdf_2026_raw, "2026")
df_2026_final = recode_categoricals(df_2026_filtered).select(*FINAL_COLS).cache()
print(f"\n2026 final: {df_2026_final.count()} registros elegibles")

df_2025_final.printSchema()
df_2025_final.show(5, truncate=False)

# %% [markdown]
# Verificación de unicidad de `(periodo_archivo, NUM_HOGAR, NUM_PERSONA)`. Una
# persona observada en dos períodos distintos **no** es duplicado (panel
# longitudinal con rotación); lo que se busca aquí es una clave repetida
# **dentro** del mismo período.

# %%
def check_duplicate_keys(df, label):
    dups = df.groupBy("periodo_archivo", "NUM_HOGAR", "NUM_PERSONA").count().filter("count > 1")
    n_dups = dups.count()
    print(f"Unicidad de clave ({label}): {n_dups} grupos con clave repetida")
    if n_dups:
        dups.show(10, truncate=False)


check_duplicate_keys(df_2025_raw, "2025 raw, antes de filtrar")
check_duplicate_keys(df_2025_final, "2025 final, filtrado")
check_duplicate_keys(df_2026_final, "2026 final, filtrado")

# %% [markdown]
# Escritura del conjunto preparado (armonizado + filtrado) de 2025 y 2026,
# por separado, en Parquet.

# %%
df_2025_final.write.mode("overwrite").parquet(f"{PROCESSED_DIR}/eneic_2025.parquet")
df_2026_final.write.mode("overwrite").parquet(f"{PROCESSED_DIR}/eneic_2026.parquet")

_chk = spark.read.parquet(f"{PROCESSED_DIR}/eneic_2025.parquet")
print(f"Releído 2025: {_chk.count()} filas, {len(_chk.columns)} columnas")

# %% [markdown]
# **Respuestas (P1):**
#
# - **¿Por qué IV de 2025 no puede apilarse por posición de columnas?**
#   Trae 302 columnas contra 270 en los demás trimestres, y el orden de las
#   columnas no coincide entre archivos; `union` posicional emparejaría
#   columnas distintas por su posición en vez de por su nombre. `unionByName`
#   (tras seleccionar el mismo subconjunto `RAW_COLS` en todos) evita el
#   problema.
# - **¿Diferencia entre dato ausente porque la pregunta no aplica y una
#   respuesta no registrada?** Que la pregunta no aplique es una ausencia
#   estructural: a alguien fuera del universo de la pregunta (p. ej.
#   `P05D01` para quien no está ocupado) nunca se le formula, y el campo
#   queda vacío por diseño del cuestionario. Una respuesta no registrada es
#   un vacío dentro del universo elegible (la pregunta sí aplicaba, pero no
#   se obtuvo dato). Aquí no se distinguen explícitamente porque el filtro de
#   elegibilidad (ocupado, asalariado) ya restringe el análisis al universo
#   donde la pregunta aplica.
# - **¿Por qué una persona observada en dos períodos no se elimina como
#   duplicado?** La ENEIC tiene diseño longitudinal con rotación de panel: la
#   misma persona puede entrevistarse en varios trimestres. Cada fila es una
#   observación válida de un período distinto, no una repetición del mismo
#   evento; por eso la clave de unicidad usada es
#   `(periodo_archivo, NUM_HOGAR, NUM_PERSONA)`, no solo `(NUM_HOGAR, NUM_PERSONA)`.
# - **¿Por qué el número de registros de la base filtrada no representa a
#   todos los trabajadores del país?** El filtro se restringe a personas de
#   15+ años, ocupadas, asalariadas (`P05C16` en {1,2,3,4}) y con salario
#   positivo registrado — excluye cuentapropistas, empleadores, trabajadores
#   no remunerados, desocupados e inactivos. Además los resultados son
#   **no ponderados** (no se usa `FACTOR`), por lo que ni siquiera dentro de
#   ese subgrupo el conteo de filas equivale a personas en la población.

# %% [markdown]
# ## S2 — Estadística descriptiva y preguntas de exploración (dueño: P2, Ej.2 — 5 pts)
# Requiere `data/processed/eneic_2025.parquet` (de S1).

# %%
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

df_2025 = spark.read.parquet(f"{PROCESSED_DIR}/eneic_2025.parquet")
NUMERIC_VARS = ["salario_mensual", "edad", "antiguedad", "horas_semanales"]

# count, media, mediana, sd, min, max, p25, p75, p95 -- una sola pasada sobre
# el DataFrame completo (percentil aproximado nativo de Spark, no requiere
# recolectar los datos).
summary_pdf = (
    df_2025.select(*NUMERIC_VARS)
    .summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "95%", "max")
    .toPandas()
    .set_index("summary")
    .T
    .rename(columns={"50%": "mediana", "mean": "media", "stddev": "sd"})
)
summary_pdf

# %% [markdown]
# El salario mensual tiene media ≈Q3,422 pero mediana ≈Q3,000: la media supera
# a la mediana, señal de asimetría positiva (cola larga hacia salarios altos —
# el máximo observado es Q99,000 frente a un p95 de Q8,000). Edad y horas
# semanales están mucho más cerca de una distribución simétrica (media y
# mediana casi iguales). No se recortan estos valores extremos de salario por
# instrucción explícita del enunciado.

# %%
# Distribución de registros por categoría ocupacional, nivel educativo y
# dominio: conteos ya agregados (groupBy), livianos, se llevan a pandas
# directo -- no es la muestra de graficar de registros individuales.
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
labels = {
    "categoria_ocupacional": ["Gobierno", "Emp. privada", "Jornalero/peón", "Doméstico"],
    "nivel_educativo": None,
    "dominio": ["Urb. Metropolitano", "Resto Urbano", "Rural Nacional"],
}
for ax, col in zip(axes, ["categoria_ocupacional", "nivel_educativo", "dominio"]):
    counts_pdf = df_2025.groupBy(col).count().orderBy(col).toPandas()
    ax.bar(counts_pdf[col].astype(str), counts_pdf["count"])
    ax.set_title(col)
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# La población asalariada de 2025 se concentra en empleados de empresa
# privada (categoría 2) y jornaleros/peones (categoría 3); gobierno (1) y
# servicio doméstico (4) son minoría. Por nivel educativo predominan primaria
# (2) y diversificado (4); pocos casos con maestría/doctorado (6, 7). Por
# dominio, Urbano Metropolitano y Resto Urbano concentran la mayoría de la
# muestra frente a Rural Nacional.

# %%
# Forma de la distribución del salario: muestra <=5,000 filas a pandas (la
# media/mediana/sd de arriba ya se calcularon sobre el total, no sobre esta
# muestra). Escala log solo para visualizar -- el objetivo en quetzales no se
# transforma en ningún otro punto del notebook.
_n_2025 = df_2025.count()
sample_salario_pdf = (
    df_2025.select("salario_mensual")
    .sample(withReplacement=False, fraction=min(1.0, 5000 / _n_2025), seed=SEED)
    .limit(5000)
    .toPandas()
)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(sample_salario_pdf["salario_mensual"], bins=40, color="steelblue")
axes[0].set_title("Salario mensual (Q), escala normal")
axes[1].hist(np.log1p(sample_salario_pdf["salario_mensual"]), bins=40, color="darkorange")
axes[1].set_title("log(1 + salario mensual) -- solo para visualizar")
plt.tight_layout()
plt.show()

# %% [markdown]
# En escala normal la distribución es claramente asimétrica a la derecha: la
# mayoría de los salarios se agrupa por debajo de Q5,000 con una cola larga y
# delgada de valores altos. En escala logarítmica la forma se acerca más a
# una campana, lo que confirma que la asimetría es de tipo multiplicativo
# (típica de variables de ingreso).

# %%
# Salario mediano por nivel educativo y por categoría ocupacional -- agregado
# sobre el DataFrame completo.
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, col in zip(axes, ["nivel_educativo", "categoria_ocupacional"]):
    agg_pdf = (
        df_2025.groupBy(col)
        .agg(F.expr("percentile_approx(salario_mensual, 0.5)").alias("mediana"), F.count("*").alias("n"))
        .orderBy(col)
        .toPandas()
    )
    ax.bar(agg_pdf[col].astype(str), agg_pdf["mediana"])
    ax.set_title(f"Salario mediano por {col}")
    ax.set_ylabel("Q")
plt.tight_layout()
plt.show()

# %% [markdown]
# El salario mediano crece de forma prácticamente monótona con el nivel
# educativo: de ≈Q1,500 en "ninguno" hasta ≈Q12,000 en doctorado. Por
# categoría ocupacional, empleados de gobierno tienen la mediana más alta
# (≈Q5,000), seguidos de empresa privada (≈Q3,560), jornalero/peón (≈Q1,800)
# y servicio doméstico, con la mediana más baja (≈Q1,000).

# %%
# Tamaño de muestra y salario mediano por trimestre -- agregado sobre el
# DataFrame completo.
trim_pdf = (
    df_2025.groupBy("trimestre_calendario")
    .agg(F.count("*").alias("n"), F.expr("percentile_approx(salario_mensual, 0.5)").alias("mediana"))
    .orderBy("trimestre_calendario")
    .toPandas()
)
fig, ax1 = plt.subplots(figsize=(7, 4))
ax1.bar(trim_pdf["trimestre_calendario"], trim_pdf["n"], color="lightgray", label="n")
ax1.set_ylabel("n registros")
ax2 = ax1.twinx()
ax2.plot(trim_pdf["trimestre_calendario"], trim_pdf["mediana"], color="crimson", marker="o", label="mediana")
ax2.set_ylabel("Salario mediano (Q)")
ax1.set_xlabel("Trimestre calendario")
plt.title("Tamaño de muestra y salario mediano por trimestre, 2025")
plt.show()
trim_pdf

# %% [markdown]
# El tamaño de la muestra analítica se mantiene relativamente estable entre
# trimestres (~12,700–13,500 registros elegibles), sin una caída abrupta que
# sugiera un problema de armonización entre archivos. El salario mediano se
# mueve poco (Q3,000 en T1-T2, Q3,200 en T3-T4) — no hay evidencia de un salto
# artificial entre trimestres que delate una inconsistencia de preparación.

# %% [markdown]
# ## S3 — Relaciones entre variables numéricas (dueño: P2, Ej.3 — 5 pts)

# %%
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation

# Correlación de Pearson sobre todos los registros elegibles de 2025 (no una
# muestra): VectorAssembler + Correlation.corr() de pyspark.ml.stat.
_assembler = VectorAssembler(inputCols=NUMERIC_VARS, outputCol="features_corr")
_vec_df = _assembler.transform(df_2025).select("features_corr")
corr_matrix = Correlation.corr(_vec_df, "features_corr").head()[0].toArray()
corr_pdf = pd.DataFrame(corr_matrix, index=NUMERIC_VARS, columns=NUMERIC_VARS)

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(corr_pdf, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
ax.set_title("Correlación de Pearson, población analítica 2025")
plt.tight_layout()
plt.show()
corr_pdf

# %% [markdown]
# **Respuestas (P2):**
# - **¿Qué variables presentan mayor asociación lineal con el salario?**
#   Todas las correlaciones con `salario_mensual` son débiles: `antiguedad`
#   (≈0.18) y `edad` (≈0.15) son las más altas, seguidas de `horas_semanales`
#   (≈0.08, prácticamente nula). Ninguna variable numérica por sí sola explica
#   linealmente el salario — es esperable, ya que el salario también depende
#   de variables categóricas (nivel educativo, categoría ocupacional) no
#   incluidas en esta matriz.
# - **¿Existe relación entre edad y antigüedad?** Sí, es la correlación más
#   fuerte de toda la matriz (≈0.49, positiva y moderada): las personas de
#   mayor edad tienden a llevar más tiempo en su ocupación principal, lo cual
#   es consistente con una trayectoria laboral acumulada.

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
