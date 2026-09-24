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
from IPython.display import Markdown, display

df_2025 = spark.read.parquet(f"{PROCESSED_DIR}/eneic_2025.parquet")
NUMERIC_VARS = ["salario_mensual", "edad", "antiguedad", "horas_semanales"]
_n_2025 = df_2025.count()
assert _n_2025 > 0, "El Parquet de 2025 no contiene registros elegibles"

summary_pdf = (
    df_2025.select(*NUMERIC_VARS)
    .summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "95%", "max")
    .toPandas()
    .set_index("summary")
    .T
    .rename(columns={
        "count": "n", "mean": "media", "50%": "mediana",
        "stddev": "desviacion_estandar", "25%": "p25", "75%": "p75", "95%": "p95",
        "min": "minimo", "max": "maximo",
    })
)
summary_pdf = summary_pdf.apply(pd.to_numeric)
summary_pdf = summary_pdf[
    ["n", "media", "mediana", "desviacion_estandar", "minimo", "maximo", "p25", "p75", "p95"]
]
summary_pdf

# %% [markdown]
# Las estadísticas se calculan sobre todos los registros elegibles de 2025,
# sin ponderar por `FACTOR`. Las diferencias entre media y mediana describen
# asimetría, pero no prueban su causa. `FACTOR` permitiría estimar resultados
# poblacionales con el diseño de la encuesta; aquí se describe la muestra
# analítica, no el número de trabajadores del país.

# %%
salario_resumen = summary_pdf.loc["salario_mensual"]
display(Markdown(
    f"**Lectura de la tabla:** Hay {int(salario_resumen['n']):,} salarios válidos. "
    f"La media salarial es Q{salario_resumen['media']:,.0f}, frente a una mediana "
    f"de Q{salario_resumen['mediana']:,.0f}; el percentil 95 es "
    f"Q{salario_resumen['p95']:,.0f} y el máximo Q{salario_resumen['maximo']:,.0f}. "
    "No se eliminan salarios extremos."
))
for variable, unidad in [("edad", "años"), ("antiguedad", "años"), ("horas_semanales", "horas")]:
    estadisticas = summary_pdf.loc[variable]
    display(Markdown(
        f"**{variable}:** media {estadisticas['media']:.1f} {unidad}, "
        f"mediana {estadisticas['mediana']:.1f} {unidad}, "
        f"p25–p75 de {estadisticas['p25']:.1f} a "
        f"{estadisticas['p75']:.1f} {unidad}; "
        f"el rango observado llega a {estadisticas['maximo']:.1f} {unidad}."
    ))

# %%
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
distribuciones = {}
for ax, col in zip(axes, ["categoria_ocupacional", "nivel_educativo", "dominio"]):
    counts_pdf = df_2025.groupBy(col).count().orderBy(col).toPandas()
    distribuciones[col] = counts_pdf
    ax.bar(counts_pdf[col].astype(str), counts_pdf["count"])
    ax.set_title(col)
    ax.set_ylabel("Registros")
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# Las barras muestran conteos de la muestra, no estimaciones poblacionales;
# cada gráfico se interpreta con sus conteos calculados, sin suponer de
# antemano qué categoría es la más frecuente.

# %%
for col, counts_pdf in distribuciones.items():
    dominante = counts_pdf.loc[counts_pdf["count"].idxmax()]
    porcentaje = 100 * dominante["count"] / counts_pdf["count"].sum()
    display(Markdown(
        f"**{col}:** la categoría `{dominante[col]}` concentra "
        f"{int(dominante['count']):,} registros ({porcentaje:.1f}% del total). "
        "Las diferencias entre barras reflejan composición de la muestra no ponderada."
    ))

# %%
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
axes[1].set_title("log(1 + salario mensual), solo visualización")
axes[0].set_xlabel("Q")
axes[1].set_xlabel("log(1 + Q)")
plt.tight_layout()
plt.show()

# %% [markdown]
# El histograma usa como máximo 5,000 filas para visualizar la forma; los
# percentiles, la media y la mediana proceden de toda la población analítica.
# La escala logarítmica modifica solo la visualización, no el salario usado
# en las estadísticas ni en el modelado.

# %%
display(Markdown(
    f"**Distribución salarial:** en la muestra de {len(sample_salario_pdf):,} filas "
    f"se observa la forma en escala original y logarítmica. En el total, "
    f"la mediana es Q{salario_resumen['mediana']:,.0f} y el p95 "
    f"Q{salario_resumen['p95']:,.0f}; su diferencia muestra cuánto se extiende "
    "la parte alta de la distribución. El eje logarítmico permite distinguir "
    "los salarios bajos sin recortar los altos."
))

# %%
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["Media", "Mediana"], salario_resumen[["media", "mediana"]], color=["steelblue", "darkorange"])
ax.set_ylabel("Salario mensual (Q)")
ax.set_title("Media y mediana salarial, todos los registros elegibles")
plt.tight_layout()
plt.show()

# %% [markdown]
# La comparación usa ambos estadísticos calculados sobre el total. Si la
# media supera la mediana, los salarios altos elevan la media más de lo que
# desplazan el valor central; si no, no corresponde atribuir esa asimetría.

# %%
relacion_salario = "supera" if salario_resumen["media"] > salario_resumen["mediana"] else "no supera"
display(Markdown(
    f"**Media frente a mediana:** Q{salario_resumen['media']:,.0f} "
    f"{relacion_salario} Q{salario_resumen['mediana']:,.0f}. "
    "La mediana es menos sensible a salarios extremos que la media."
))

# %%
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
medianas_por_grupo = {}
for ax, col in zip(axes, ["nivel_educativo", "categoria_ocupacional"]):
    agg_pdf = (
        df_2025.groupBy(col)
        .agg(F.expr("percentile_approx(salario_mensual, 0.5)").alias("mediana"), F.count("*").alias("n"))
        .orderBy(col)
        .toPandas()
    )
    medianas_por_grupo[col] = agg_pdf
    ax.bar(agg_pdf[col].astype(str), agg_pdf["mediana"])
    ax.set_title(f"Salario mediano por {col}")
    ax.set_ylabel("Q")
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# Estas medianas se calculan sobre todos los registros de cada grupo. Las
# barras no implican que educación u ocupación causen diferencias salariales;
# la categoría `DESCONOCIDO`, si aparece, se conserva y se señala como tal.

# %%
for col, agg_pdf in medianas_por_grupo.items():
    mayor = agg_pdf.loc[agg_pdf["mediana"].idxmax()]
    menor = agg_pdf.loc[agg_pdf["mediana"].idxmin()]
    display(Markdown(
        f"**Salario por {col}:** la mediana más alta corresponde a "
        f"`{mayor[col]}` (Q{mayor['mediana']:,.0f}, n={int(mayor['n']):,}) "
        f"y la más baja a `{menor[col]}` "
        f"(Q{menor['mediana']:,.0f}, n={int(menor['n']):,}). "
        "Los tamaños de grupo importan al comparar estas cifras."
    ))

# %%
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
# Cada trimestre corresponde al nombre del archivo, no al código
# `TRIMESTRE` de la encuesta. Los conteos y medianas no ponderados muestran
# cambios en la muestra, pero por sí solos no prueban cambios poblacionales
# ni descartan problemas de armonización.

# %%
display(Markdown(
    f"**Trimestres:** el tamaño de muestra varía de {trim_pdf['n'].min():,} a "
    f"{trim_pdf['n'].max():,} registros; la mediana salarial va de "
    f"Q{trim_pdf['mediana'].min():,.0f} a Q{trim_pdf['mediana'].max():,.0f}. "
    "La línea y las barras usan el total elegible de cada trimestre."
))

# %% [markdown]
# ## S3 — Relaciones entre variables numéricas (dueño: P2, Ej.3 — 5 pts)

# %%
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation

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

# %% [markdown]
# ## S5 — Baseline + Pipeline de regresión lineal (dueño: P1, Ej.5 — 20 pts)

# %%
# TODO(P1): baseline = media de salario_mensual en train. MAE/RMSE/R² en validación.


# %%

# %% [markdown]
# ## S6 — Pipeline de Random Forest (dueño: P2, Ej.6 — 20 pts)
# Usa el mismo split y las mismas columnas categóricas que S5.

# %%


# %% [markdown]
# **Comparación LR vs. RF (P2):** ¿cuál obtuvo mejor RMSE de validación y qué
# diferencias explican el resultado?

# %% [markdown]
# ## S7 — Entrenamiento final y evaluación en 2026 (dueños: P1 + P2, Ej.7 — 20 pts)

# %%
# TODO(P1): reentrenar configuración ganadora de LR con todo 2025.
# TODO(P2): reentrenar configuración ganadora de RF con todo 2025.


# %%

# %% [markdown]
# ## S8 — Visualización y análisis de errores (dueño: P3, Ej.8 — 15 pts)
# Requiere las predicciones de prueba de S7.

# %%


# %%


# %%

# %% [markdown]
# ### Discusión final (P3, con insumos de todo el equipo)
# Integrar perfiles de KMeans, correlaciones, comparación LR vs. RF y patrón
# de errores. Recordar: las asociaciones encontradas no son causales.

# %%
spark.stop()
