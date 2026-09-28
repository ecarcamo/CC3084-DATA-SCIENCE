# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Laboratorio 7 — Spark MLlib
# CC3066 — Data Science, Semestre II 2026
#
# Datos: bases de Personas de la ENEIC (INE). 2025 T1–T4 para desarrollo y 2026 T1 para la prueba final.
#
# Todo el análisis y los modelos usan Spark 3.5 (`pyspark.ml`). pandas solo se usa para leer los
# archivos originales y para graficar tablas agregadas o muestras de hasta 5,000 registros.
# El notebook corre de principio a fin con el entorno de `docker/`.

# %% [markdown]
# ## 0. Configuración

# %%
import os
from pathlib import Path

if "JAVA_HOME" not in os.environ:
    for _java in ["/opt/java-home", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home",
                  "/usr/lib/jvm/java-17-openjdk"]:
        if Path(_java).exists():
            os.environ["JAVA_HOME"] = _java
            break

try:
    import setuptools  # noqa: F401  (pyspark 3.5 importa distutils, que no existe en Python 3.12)
except ImportError:
    pass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

spark = (
    SparkSession.builder.appName("lab7-spark-mllib")
    .master("local[8]")
    .config("spark.driver.memory", "5g")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.sql.execution.arrow.pyspark.enabled", "true")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

ROOT = Path.cwd()
while not (ROOT / "data" / "raw" / "eneic").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent

RAW_DIR = ROOT / "data" / "raw" / "eneic"
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
FIG_DIR = ROOT / "outputs" / "lab7"
for _d in [PROCESSED_DIR, MODELS_DIR, FIG_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

SEED = 42
sns.set_theme(style="whitegrid")
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")


def guardar(fig, nombre):
    fig.savefig(FIG_DIR / f"{nombre}.png", dpi=130, bbox_inches="tight")


print("Spark", spark.version, "| JAVA_HOME:", os.environ.get("JAVA_HOME"))

# %% [markdown]
# ## 1. Carga, armonización y calidad de datos
#
# Cada archivo se lee por separado. I-2025 viene en `.xlsx` (pandas + openpyxl) y los demás en `.sav`
# (pyreadstat). Se seleccionan solo las columnas requeridas, se convierten a número y se crea el
# DataFrame de Spark con un esquema explícito.
#
# El período sale del archivo, no de `TRIMESTRE`.

# %%
import pyreadstat

RAW_COLS = [
    "ANIO", "TRIMESTRE", "DOMINIO", "NUM_HOGAR", "NUM_PERSONA", "FACTOR",
    "OCUPADOS", "P02A03", "P03A03A", "P05C07A", "P05C07B", "P05C16",
    "P05D01", "P05H01A",
]
CODE_COLS = ["ANIO", "TRIMESTRE", "DOMINIO", "NUM_HOGAR", "NUM_PERSONA", "OCUPADOS", "P03A03A", "P05C16"]

FILE_MANIFEST = [
    dict(archivo="personas_2025_T1.xlsx", fmt="xlsx", periodo="2025T1", anio=2025, trimestre=1, esperado=51588),
    dict(archivo="personas_2025_T2.sav", fmt="sav", periodo="2025T2", anio=2025, trimestre=2, esperado=51167),
    dict(archivo="personas_2025_T3.sav", fmt="sav", periodo="2025T3", anio=2025, trimestre=3, esperado=51583),
    dict(archivo="personas_2025_T4.sav", fmt="sav", periodo="2025T4", anio=2025, trimestre=4, esperado=49338),
    dict(archivo="personas_2026_T1.sav", fmt="sav", periodo="2026T1", anio=2026, trimestre=1, esperado=49843),
]
PERIODOS_2025 = ["2025T1", "2025T2", "2025T3", "2025T4"]

RAW_SCHEMA = T.StructType(
    [T.StructField(c, T.DoubleType(), True) for c in RAW_COLS]
    + [
        T.StructField("periodo_archivo", T.StringType(), False),
        T.StructField("anio_archivo", T.IntegerType(), False),
        T.StructField("trimestre_calendario", T.IntegerType(), False),
        T.StructField("archivo_origen", T.StringType(), False),
    ]
)


def a_numero(serie):
    if serie.dtype == object:
        serie = serie.map(lambda v: v.strip() if isinstance(v, str) else v)
    return pd.to_numeric(serie, errors="coerce").astype("float64")


def leer_archivo(spec):
    ruta = RAW_DIR / spec["archivo"]
    if spec["fmt"] == "xlsx":
        pdf = pd.read_excel(ruta, usecols=RAW_COLS)
        n_columnas = len(pd.read_excel(ruta, nrows=0).columns)
    else:
        pdf, _ = pyreadstat.read_sav(str(ruta), usecols=RAW_COLS)
        n_columnas = len(pyreadstat.read_sav(str(ruta), metadataonly=True)[1].column_names)
    tipos = {c: str(pdf[c].dtype) for c in RAW_COLS}
    for c in RAW_COLS:
        pdf[c] = a_numero(pdf[c])
    pdf = pdf[RAW_COLS].copy()
    pdf["periodo_archivo"] = spec["periodo"]
    pdf["anio_archivo"] = spec["anio"]
    pdf["trimestre_calendario"] = spec["trimestre"]
    pdf["archivo_origen"] = spec["archivo"]
    sdf = spark.createDataFrame(pdf, schema=RAW_SCHEMA)
    for c in RAW_COLS:
        sdf = sdf.withColumn(c, F.when(F.isnan(c), None).otherwise(F.col(c)))
    for c in CODE_COLS:
        sdf = sdf.withColumn(c, F.when(F.col(c) == F.floor(c), F.col(c).cast("int")))
    return sdf, len(pdf), n_columnas, tipos


frames, resumen_archivos, tipos_origen = {}, [], {}
for spec in FILE_MANIFEST:
    sdf, n, n_cols, tipos = leer_archivo(spec)
    frames[spec["periodo"]] = sdf
    tipos_origen[spec["periodo"]] = tipos
    resumen_archivos.append(dict(periodo_archivo=spec["periodo"], archivo_origen=spec["archivo"],
                                 columnas_originales=n_cols, registros=n, esperado=spec["esperado"]))

resumen_archivos = pd.DataFrame(resumen_archivos)
resumen_archivos["coincide"] = resumen_archivos["registros"] == resumen_archivos["esperado"]
display(resumen_archivos)

# %% [markdown]
# Los conteos y el número de columnas coinciden con el enunciado. Los tipos de origen no son iguales:
# en el `.xlsx` varias columnas llegan como enteros y en los `.sav` todo llega como decimal. Por eso
# todo se convierte a número antes de unir y los códigos se pasan a entero.

# %%
display(pd.DataFrame(tipos_origen).loc[["DOMINIO", "NUM_HOGAR", "P02A03", "P03A03A", "P05C16", "P05D01"]])

# %% [markdown]
# ### Por qué IV-2025 no se puede apilar por posición
# Se comparan los encabezados de III-2025 y IV-2025 sin cargar los datos.

# %%
_cols_t3 = pyreadstat.read_sav(str(RAW_DIR / "personas_2025_T3.sav"), metadataonly=True)[1].column_names
_cols_t4 = pyreadstat.read_sav(str(RAW_DIR / "personas_2025_T4.sav"), metadataonly=True)[1].column_names
_primera = next(i for i, (a, b) in enumerate(zip(_cols_t3, _cols_t4)) if a != b)
print(f"III-2025: {len(_cols_t3)} columnas | IV-2025: {len(_cols_t4)} columnas")
print(f"Primera posición distinta: {_primera} -> III-2025 '{_cols_t3[_primera]}' vs IV-2025 '{_cols_t4[_primera]}'")
print(f"Columnas nuevas en IV-2025: {len(set(_cols_t4) - set(_cols_t3))} | ausentes en IV-2025: {len(set(_cols_t3) - set(_cols_t4))}")
display(pd.DataFrame(
    {"posicion_III_2025": [_cols_t3.index(c) for c in RAW_COLS], "posicion_IV_2025": [_cols_t4.index(c) for c in RAW_COLS]},
    index=RAW_COLS,
).T)

# %% [markdown]
# ### Columnas analíticas y unión con `unionByName`

# %%
LABELS_EDUCACION = {0: "Ninguno", 1: "Preprimaria", 2: "Primaria", 3: "Básico", 4: "Diversificado",
                    5: "Superior", 6: "Maestría", 7: "Doctorado"}
LABELS_CATEGORIA = {1: "Gobierno", 2: "Empresa privada", 3: "Jornalero o peón", 4: "Servicio doméstico"}
LABELS_DOMINIO = {1: "Urbano metropolitano", 2: "Resto urbano", 3: "Rural nacional"}
ORDEN_EDUCACION = list(LABELS_EDUCACION.values()) + ["DESCONOCIDO"]
ORDEN_CATEGORIA = list(LABELS_CATEGORIA.values())
ORDEN_DOMINIO = list(LABELS_DOMINIO.values()) + ["DESCONOCIDO"]


def armonizar(sdf):
    return sdf.select(
        "periodo_archivo", "anio_archivo", "trimestre_calendario", "archivo_origen",
        "ANIO", "TRIMESTRE", "NUM_HOGAR", "NUM_PERSONA", "FACTOR",
        F.col("P05D01").alias("salario_mensual"),
        F.col("P02A03").alias("edad"),
        F.col("P05C07A").alias("antiguedad_anios"),
        F.col("P05C07B").alias("antiguedad_meses"),
        F.col("P05H01A").alias("horas_semanales"),
        F.col("P03A03A").alias("nivel_educativo_cod"),
        F.col("P05C16").alias("categoria_ocupacional_cod"),
        F.col("DOMINIO").alias("dominio_cod"),
        F.col("OCUPADOS").alias("ocupado"),
    ).withColumn("antiguedad", F.col("antiguedad_anios") + F.col("antiguedad_meses") / 12.0)


df_2025_raw = armonizar(frames["2025T1"])
for _p in PERIODOS_2025[1:]:
    df_2025_raw = df_2025_raw.unionByName(armonizar(frames[_p]))
df_2025_raw = df_2025_raw.cache()
df_2026_raw = armonizar(frames["2026T1"]).cache()
df_all_raw = df_2025_raw.unionByName(df_2026_raw).cache()

print(f"2025 unido: {df_2025_raw.count():,} registros | 2026: {df_2026_raw.count():,} registros")
df_2025_raw.printSchema()
df_2025_raw.show(5, truncate=False)

# %% [markdown]
# Valores de `TRIMESTRE` por archivo. Se conservan, pero no se usan como trimestre calendario.

# %%
display(df_all_raw.groupBy("periodo_archivo", "TRIMESTRE").count().orderBy("periodo_archivo", "TRIMESTRE").toPandas())

# %% [markdown]
# El resultado coincide con el enunciado: II-2025 trae 175 registros con `TRIMESTRE = 2`. Restar uno
# al código dejaría esos 175 en el trimestre 1, así que el período se toma del archivo.

# %% [markdown]
# ### Faltantes por variable antes de los filtros

# %%
VARS_SELECCIONADAS = [
    "ANIO", "TRIMESTRE", "NUM_HOGAR", "NUM_PERSONA", "FACTOR", "salario_mensual", "edad",
    "antiguedad_anios", "antiguedad_meses", "horas_semanales", "nivel_educativo_cod",
    "categoria_ocupacional_cod", "dominio_cod", "ocupado",
]


def tabla_faltantes(df):
    agg = df.groupBy("periodo_archivo").agg(
        F.count("*").alias("n"), *[F.sum(F.col(c).isNull().cast("int")).alias(c) for c in VARS_SELECCIONADAS]
    ).toPandas().set_index("periodo_archivo").sort_index()
    total_2025 = agg.loc[PERIODOS_2025].sum()
    salida = pd.DataFrame({
        "faltantes_2025": total_2025[VARS_SELECCIONADAS].astype(int),
        "pct_2025": 100 * total_2025[VARS_SELECCIONADAS] / total_2025["n"],
    })
    for p in agg.index:
        salida[f"pct_{p}"] = 100 * agg.loc[p, VARS_SELECCIONADAS] / agg.loc[p, "n"]
    return salida


faltantes_pdf = tabla_faltantes(df_all_raw)
display(faltantes_pdf)

# %% [markdown]
# Antes de filtrar, el salario falta en 74 % de los registros. Antigüedad, horas, categoría y `OCUPADOS`
# faltan en 56.7 %: son las personas no ocupadas, a quienes no se les hace esa parte del cuestionario.
# El nivel educativo falta en 12.9 %. La tabla siguiente separa el faltante del salario dentro y fuera del
# universo donde la pregunta aplica (15 años o más, ocupado y asalariado).

# %%
_universo = (F.col("edad") >= 15) & (F.col("ocupado") == 1) & F.col("categoria_ocupacional_cod").isin(1, 2, 3, 4)
faltante_salario = (
    df_all_raw.withColumn("universo_asalariado", F.coalesce(_universo, F.lit(False)))
    .groupBy("periodo_archivo", "universo_asalariado")
    .agg(F.count("*").alias("registros"), F.sum(F.col("salario_mensual").isNull().cast("int")).alias("salario_faltante"))
    .withColumn("pct_faltante", F.round(100 * F.col("salario_faltante") / F.col("registros"), 2))
    .orderBy("periodo_archivo", "universo_asalariado")
    .toPandas()
)
display(faltante_salario)

# %% [markdown]
# Fuera del universo asalariado el salario falta en 100 % de los casos. Dentro no falta ninguno. Todo el
# faltante del salario es estructural.

# %% [markdown]
# Validación de códigos categóricos contra el diccionario. Lo ausente o no reconocido se marca como
# `DESCONOCIDO`. El código educativo 0 es "Ninguno", no un faltante.

# %%
def codigos_fuera(df, col, validos):
    return df.select(
        F.lit(col).alias("variable"),
        F.sum(F.col(col).isNull().cast("int")).alias("nulos"),
        F.sum((F.col(col).isNotNull() & ~F.col(col).isin(validos)).cast("int")).alias("no_reconocidos"),
    )


_val = (
    codigos_fuera(df_all_raw, "nivel_educativo_cod", list(LABELS_EDUCACION))
    .unionByName(codigos_fuera(df_all_raw, "categoria_ocupacional_cod", list(range(1, 10))))
    .unionByName(codigos_fuera(df_all_raw, "dominio_cod", list(LABELS_DOMINIO)))
)
display(_val.toPandas())

# %% [markdown]
# ### Filtros de población y calidad
# El orden es siempre el mismo. Cada paso cuenta cuántos registros excluye por archivo. Los registros
# que no permiten evaluar un criterio (valor nulo) se excluyen en ese paso. El salario no se imputa.

# %%
def es_finito(c):
    return F.col(c).isNotNull() & ~F.isnan(c) & (F.abs(F.col(c)) < float("inf"))


PASOS = [
    ("1. edad finita y >= 15", es_finito("edad") & (F.col("edad") >= 15)),
    ("2. OCUPADOS = 1", F.col("ocupado") == 1),
    ("3. P05C16 en {1, 2, 3, 4}", F.col("categoria_ocupacional_cod").isin(1, 2, 3, 4)),
    ("4. P05D01 finito y > 0", es_finito("salario_mensual") & (F.col("salario_mensual") > 0)),
    ("5. antigüedad en años >= 0", es_finito("antiguedad_anios") & (F.col("antiguedad_anios") >= 0)),
    ("6. meses entero entre 0 y 11", es_finito("antiguedad_meses") & (F.col("antiguedad_meses") >= 0)
     & (F.col("antiguedad_meses") <= 11) & (F.col("antiguedad_meses") == F.floor("antiguedad_meses"))),
    ("7. antigüedad <= edad", F.col("antiguedad") <= F.col("edad")),
    ("8. 0 < horas <= 168", es_finito("horas_semanales") & (F.col("horas_semanales") > 0) & (F.col("horas_semanales") <= 168)),
]


def conteo_por_periodo(df):
    return dict(df.groupBy("periodo_archivo").count().collect())


def aplicar_filtros(df):
    periodos = sorted(conteo_por_periodo(df))
    previo = conteo_por_periodo(df)
    filas = [dict(paso="0. registros originales", **{p: previo.get(p, 0) for p in periodos})]
    for nombre, condicion in PASOS:
        df = df.filter(condicion)
        actual = conteo_por_periodo(df)
        filas.append(dict(paso=nombre, **{p: previo.get(p, 0) - actual.get(p, 0) for p in periodos}))
        previo = actual
    filas.append(dict(paso="registros finales", **{p: previo.get(p, 0) for p in periodos}))
    tabla = pd.DataFrame(filas).set_index("paso")
    tabla["total_2025"] = tabla[PERIODOS_2025].sum(axis=1)
    return df, tabla


def recodificar(df):
    def mapa(col, labels):
        expr = F.lit("DESCONOCIDO")
        for cod, etiqueta in labels.items():
            expr = F.when(F.col(col) == cod, F.lit(etiqueta)).otherwise(expr)
        return expr

    return (
        df.withColumn("nivel_educativo", mapa("nivel_educativo_cod", LABELS_EDUCACION))
        .withColumn("categoria_ocupacional", mapa("categoria_ocupacional_cod", LABELS_CATEGORIA))
        .withColumn("dominio", mapa("dominio_cod", LABELS_DOMINIO))
    )


df_all_filtrado, cascada = aplicar_filtros(df_all_raw)
display(cascada)
_ok = (cascada.loc["0. registros originales"] - cascada.iloc[1:-1].sum() == cascada.loc["registros finales"]).all()
print("Originales - excluidos = finales en todos los archivos:", _ok)

# %% [markdown]
# Casi toda la exclusión viene de los tres primeros pasos: menores de 15 años, no ocupados y no
# asalariados. Los pasos 4 a 8 no excluyen registros: todos los asalariados tienen salario positivo y
# antigüedad y horas válidas. La suma cuadra en todos los archivos.
#
# Registros por archivo antes y después de los filtros.

# %%
antes_despues = pd.DataFrame({
    "antes": cascada.loc["0. registros originales"],
    "despues": cascada.loc["registros finales"],
})
antes_despues["pct_conservado"] = 100 * antes_despues["despues"] / antes_despues["antes"]
display(antes_despues)

# %% [markdown]
# Se conserva cerca de 26 % de cada archivo: 53,025 registros en 2025 y 13,258 en 2026. Ningún registro
# quedó con nivel educativo o dominio `DESCONOCIDO`.

# %% [markdown]
# ### Unicidad de `periodo_archivo`, `NUM_HOGAR`, `NUM_PERSONA`
# Se revisa antes y después de filtrar. Si una clave se repite, se compara la fila completa para saber si
# es una repetición exacta o un registro en conflicto.

# %%
CLAVE = ["periodo_archivo", "NUM_HOGAR", "NUM_PERSONA"]


def revisar_clave(df, etiqueta):
    nulos = df.filter(F.col("NUM_HOGAR").isNull() | F.col("NUM_PERSONA").isNull()).count()
    repetidas = df.groupBy(*CLAVE).count().filter("count > 1")
    n_rep = repetidas.count()
    exactas = conflicto = 0
    if n_rep:
        cols = [c for c in df.columns if c not in CLAVE]
        detalle = (df.join(repetidas.select(*CLAVE), CLAVE)
                   .groupBy(*CLAVE).agg(F.countDistinct(F.to_json(F.struct(*cols))).alias("versiones")))
        exactas = detalle.filter("versiones = 1").count()
        conflicto = detalle.filter("versiones > 1").count()
    return dict(conjunto=etiqueta, registros=df.count(), claves_nulas=nulos, claves_repetidas=n_rep,
                repeticiones_exactas=exactas, claves_en_conflicto=conflicto)


display(pd.DataFrame([
    revisar_clave(df_2025_raw, "2025 antes de filtrar"),
    revisar_clave(df_2026_raw, "2026 antes de filtrar"),
    revisar_clave(df_all_filtrado.filter(F.col("anio_archivo") == 2025), "2025 filtrado"),
    revisar_clave(df_all_filtrado.filter(F.col("anio_archivo") == 2026), "2026 filtrado"),
]))

# %% [markdown]
# No hay claves repetidas dentro de un mismo período, así que no hace falta eliminar nada.
#
# La misma persona sí puede aparecer en varios trimestres. Se cuentan los pares hogar-persona de 2025
# (sin filtrar) que aparecen en más de un archivo y cuya edad cambia a lo sumo un año.

# %%
_panel = (
    df_2025_raw.groupBy("NUM_HOGAR", "NUM_PERSONA")
    .agg(F.countDistinct("periodo_archivo").alias("periodos"), (F.max("edad") - F.min("edad")).alias("rango_edad"))
)
display(_panel.groupBy("periodos").agg(
    F.count("*").alias("hogar_persona"),
    F.sum((F.col("rango_edad") <= 1).cast("int")).alias("edad_consistente"),
).orderBy("periodos").toPandas())

# %% [markdown]
# 61,056 pares hogar-persona aparecen en dos o más trimestres de 2025. En 99.6 % de ellos la edad cambia a
# lo sumo un año. Son las mismas personas observadas en varios períodos.

# %% [markdown]
# ### Guardado en Parquet

# %%
FINAL_COLS = [
    "periodo_archivo", "anio_archivo", "trimestre_calendario", "archivo_origen",
    "ANIO", "TRIMESTRE", "NUM_HOGAR", "NUM_PERSONA", "FACTOR",
    "salario_mensual", "edad", "antiguedad", "antiguedad_anios", "antiguedad_meses", "horas_semanales",
    "nivel_educativo", "categoria_ocupacional", "dominio",
    "nivel_educativo_cod", "categoria_ocupacional_cod", "dominio_cod", "ocupado",
]

df_final = recodificar(df_all_filtrado).select(*FINAL_COLS)
df_final.filter(F.col("anio_archivo") == 2025).write.mode("overwrite").parquet(str(PROCESSED_DIR / "eneic_2025.parquet"))
df_final.filter(F.col("anio_archivo") == 2026).write.mode("overwrite").parquet(str(PROCESSED_DIR / "eneic_2026.parquet"))

df_2025 = spark.read.parquet(str(PROCESSED_DIR / "eneic_2025.parquet")).cache()
df_2026 = spark.read.parquet(str(PROCESSED_DIR / "eneic_2026.parquet")).cache()
print(f"eneic_2025.parquet: {df_2025.count():,} filas | eneic_2026.parquet: {df_2026.count():,} filas")
df_2025.printSchema()
df_2025.select("periodo_archivo", "salario_mensual", "edad", "antiguedad", "horas_semanales",
               "nivel_educativo", "categoria_ocupacional", "dominio").show(5, truncate=False)

# %% [markdown]
# ### Respuestas
#
# **¿Por qué IV-2025 no puede apilarse por posición?** Tiene 302 columnas y los demás 270. Además, el
# orden cambia desde la posición 7: en IV-2025 la edad (`P02A03`) está en la columna 8 y en III-2025 en
# la 12. Un apilado por posición mezclaría variables distintas. `unionByName` une por nombre.
#
# **¿Dato ausente porque no corresponde vs. respuesta no registrada?** El primero es estructural: la
# pregunta no se hace a esa persona. Por ejemplo, el salario no se pregunta a quien no está ocupado.
# El segundo ocurre cuando la pregunta sí aplicaba y no quedó registrada. El primero no debe tratarse
# como error ni imputarse; el segundo sí indica pérdida de información. En estos archivos todo el
# faltante del salario es del primer tipo: fuera del universo asalariado falta en 100 % y dentro en 0 %.
#
# **¿Por qué no eliminar como duplicado a una persona observada en dos períodos?** La ENEIC es un panel
# con rotación. Cada fila es una observación de un período distinto. Borrarla quitaría información
# válida de ese trimestre. Por eso la clave incluye `periodo_archivo`.
#
# **¿Por qué la base filtrada no representa a todos los trabajadores del país?** Solo incluye
# asalariados de 15 años o más con salario positivo registrado. Deja fuera a cuenta propia,
# empleadores, trabajo no remunerado y a quien no reportó salario. Además, cada fila es una persona de
# la muestra, no de la población.
#
# **Uso de `FACTOR`.** Es el factor de expansión: cuántas personas de la población representa cada
# registro. Serviría para estimar totales, medias o proporciones poblacionales como promedios ponderados.
# Aquí no se usa: el análisis describe los registros, no el país.

# %% [markdown]
# ## 2. Estadística descriptiva y exploración
# Todas las estadísticas usan los registros elegibles de 2025 completos. Los percentiles son exactos.

# %%
NUMERIC_VARS = ["salario_mensual", "edad", "antiguedad", "horas_semanales"]


def resumen_numerico(df, cols):
    filas = []
    for c in cols:
        r = df.agg(
            F.count(c).alias("n"), F.mean(c).alias("media"), F.stddev(c).alias("desviacion_estandar"),
            F.min(c).alias("minimo"), F.max(c).alias("maximo"), F.skewness(c).alias("asimetria"),
            F.expr(f"percentile({c}, array(0.25, 0.5, 0.75, 0.95))").alias("p"),
        ).first()
        filas.append(dict(variable=c, n=r["n"], media=r["media"], mediana=r["p"][1],
                          desviacion_estandar=r["desviacion_estandar"], minimo=r["minimo"], maximo=r["maximo"],
                          p25=r["p"][0], p75=r["p"][2], p95=r["p"][3], asimetria=r["asimetria"]))
    return pd.DataFrame(filas).set_index("variable")


resumen_2025 = resumen_numerico(df_2025, NUMERIC_VARS)
display(resumen_2025)

# %% [markdown]
# El salario tiene media Q3,422 y mediana Q3,000. La desviación estándar (Q2,902) es casi igual a la media.
# El p95 es Q8,000 y el máximo Q99,000. La asimetría es 6.0: la cola derecha es larga. Hay salarios muy
# bajos (mínimo Q1) y muy altos. Se conservan todos.
#
# La edad media es 35.2 años y la mediana 33. La mitad está entre 24 y 44 años.
#
# La antigüedad tiene media 5.6 años y mediana 2. La mayoría lleva poco tiempo en su trabajo y pocos
# llevan décadas (asimetría 2.4).
#
# Las horas habituales tienen media 46.3 y mediana 45. La mitad trabaja entre 40 y 55 horas. Hay jornadas
# reportadas de hasta 126 horas.

# %% [markdown]
# ### Distribución por categoría ocupacional, nivel educativo y dominio

# %%
def conteo_categoria(df, col, orden):
    pdf = df.groupBy(col).count().toPandas().set_index(col).reindex(orden).dropna()
    pdf["pct"] = 100 * pdf["count"] / pdf["count"].sum()
    return pdf


distribuciones = {
    "categoria_ocupacional": conteo_categoria(df_2025, "categoria_ocupacional", ORDEN_CATEGORIA),
    "nivel_educativo": conteo_categoria(df_2025, "nivel_educativo", ORDEN_EDUCACION),
    "dominio": conteo_categoria(df_2025, "dominio", ORDEN_DOMINIO),
}
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
for ax, (col, pdf) in zip(axes, distribuciones.items()):
    ax.bar(pdf.index, pdf["count"], color="steelblue")
    for i, (v, pct) in enumerate(zip(pdf["count"], pdf["pct"])):
        ax.text(i, v, f"{pct:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.set_title(col.replace("_", " ").capitalize())
    ax.set_ylabel("Registros")
    ax.tick_params(axis="x", rotation=35)
plt.tight_layout()
guardar(fig, "01_distribucion_categorias")
plt.show()
for col, pdf in distribuciones.items():
    display(pdf.rename(columns={"count": "registros"}))

# %% [markdown]
# - Categoría: empresa privada concentra 54.1 %. Siguen jornalero o peón (26.1 %), gobierno (12.4 %) y
#   servicio doméstico (7.4 %).
# - Educación: diversificado (31.8 %) y primaria (29.8 %) son los niveles más comunes. Básico 15.6 %,
#   superior 12.9 % y ninguno 7.5 %. Maestría y doctorado suman 1.6 %. Ningún registro quedó como `DESCONOCIDO`.
# - Dominio: urbano metropolitano 41.6 %, resto urbano 38.0 % y rural nacional 20.4 %.
#
# Son conteos de la muestra, sin ponderar.

# %% [markdown]
# ### Forma de la distribución del salario
# El histograma usa una muestra de 5,000 registros. Las líneas de media y mediana vienen del total.
# El panel derecho usa escala logarítmica en el eje x solo para visualizar.

# %%
_n_2025 = df_2025.count()
muestra_salario = (
    df_2025.select("salario_mensual").sample(fraction=min(1.0, 6000 / _n_2025), seed=SEED).limit(5000).toPandas()
)
_media, _mediana = resumen_2025.loc["salario_mensual", ["media", "mediana"]]

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
axes[0].hist(muestra_salario["salario_mensual"], bins=60, color="steelblue")
axes[0].set_title("Salario mensual (Q), escala lineal")
axes[0].set_xlabel("Quetzales")
_bins = np.logspace(np.log10(muestra_salario["salario_mensual"].min()), np.log10(muestra_salario["salario_mensual"].max()), 50)
axes[1].hist(muestra_salario["salario_mensual"], bins=_bins, color="darkorange")
axes[1].set_xscale("log")
axes[1].set_title("Salario mensual (Q), eje x en escala logarítmica")
axes[1].set_xlabel("Quetzales (escala log)")
for ax in axes:
    ax.axvline(_media, color="black", linestyle="--", label=f"Media Q{_media:,.0f}")
    ax.axvline(_mediana, color="crimson", linestyle="-", label=f"Mediana Q{_mediana:,.0f}")
    ax.set_ylabel("Registros (muestra)")
    ax.legend()
plt.tight_layout()
guardar(fig, "02_distribucion_salario")
plt.show()

# %% [markdown]
# La distribución es asimétrica a la derecha. En escala lineal casi todo se acumula por debajo de Q6,000 y
# la cola llega a Q99,000. En escala logarítmica la forma se parece más a una campana.
#
# La media (Q3,422) es Q422 mayor que la mediana (Q3,000). Los salarios altos jalan la media hacia arriba.
# La mediana describe mejor al asalariado típico.

# %% [markdown]
# ### Salario mediano por nivel educativo y categoría ocupacional

# %%
def mediana_por(df, col, orden):
    pdf = (df.groupBy(col).agg(F.count("*").alias("n"), F.expr("percentile(salario_mensual, 0.5)").alias("mediana"),
                                F.mean("salario_mensual").alias("media"))
           .toPandas().set_index(col).reindex(orden).dropna())
    return pdf


medianas_educacion = mediana_por(df_2025, "nivel_educativo", ORDEN_EDUCACION)
medianas_categoria = mediana_por(df_2025, "categoria_ocupacional", ORDEN_CATEGORIA)

fig, axes = plt.subplots(1, 2, figsize=(15, 4.5))
for ax, pdf, titulo in [(axes[0], medianas_educacion, "nivel educativo"), (axes[1], medianas_categoria, "categoría ocupacional")]:
    ax.bar(pdf.index, pdf["mediana"], color="seagreen")
    for i, (v, n) in enumerate(zip(pdf["mediana"], pdf["n"])):
        ax.text(i, v, f"Q{v:,.0f}\nn={int(n):,}", ha="center", va="bottom", fontsize=8)
    ax.set_title(f"Salario mediano por {titulo}")
    ax.set_ylabel("Quetzales")
    ax.set_ylim(0, pdf["mediana"].max() * 1.25)
    ax.tick_params(axis="x", rotation=35)
plt.tight_layout()
guardar(fig, "03_mediana_educacion_categoria")
plt.show()
display(medianas_educacion)
display(medianas_categoria)

# %% [markdown]
# La mediana sube con el nivel educativo: Q1,500 sin educación, Q2,200 con primaria, Q3,600 con
# diversificado, Q5,000 con superior y Q10,000 con maestría. Doctorado llega a Q12,000, pero con solo 60 registros.
#
# Por categoría, gobierno tiene la mediana más alta (Q5,000). Siguen empresa privada (Q3,568), jornalero o
# peón (Q1,800) y servicio doméstico (Q1,000).
#
# Son asociaciones. No prueban que la educación o la categoría causen el salario.

# %% [markdown]
# ### Tamaño de muestra y salario mediano por trimestre

# %%
trimestres = (
    df_2025.groupBy("periodo_archivo")
    .agg(F.count("*").alias("n"), F.expr("percentile(salario_mensual, 0.5)").alias("mediana"),
         F.mean("salario_mensual").alias("media"))
    .orderBy("periodo_archivo").toPandas().set_index("periodo_archivo")
)
fig, ax1 = plt.subplots(figsize=(8, 4.5))
ax1.bar(trimestres.index, trimestres["n"], color="lightgray")
ax1.set_ylabel("Registros elegibles")
ax1.set_ylim(0, trimestres["n"].max() * 1.2)
ax2 = ax1.twinx()
ax2.plot(trimestres.index, trimestres["mediana"], color="crimson", marker="o")
ax2.set_ylabel("Salario mediano (Q)", color="crimson")
ax2.set_ylim(0, trimestres["mediana"].max() * 1.2)
ax2.grid(False)
ax1.set_title("Registros elegibles y salario mediano por trimestre, 2025")
plt.tight_layout()
guardar(fig, "04_trimestres")
plt.show()
display(trimestres)

# %% [markdown]
# La muestra analítica es estable: entre 12,664 (T4) y 13,492 (T2) registros. La mediana pasa de Q3,000 en
# T1 y T2 a Q3,200 en T3 y T4. La media sube de Q3,316 a Q3,545. El cambio es pequeño y no ponderado. No
# basta para afirmar un aumento en la población.

# %% [markdown]
# ## 3. Relaciones entre variables numéricas
# Correlación de Pearson con `VectorAssembler` y `Correlation.corr()` sobre todos los registros elegibles de 2025.

# %%
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation

_vec = VectorAssembler(inputCols=NUMERIC_VARS, outputCol="vars_corr").transform(df_2025).select("vars_corr")
corr_pdf = pd.DataFrame(Correlation.corr(_vec, "vars_corr", "pearson").head()[0].toArray(),
                        index=NUMERIC_VARS, columns=NUMERIC_VARS)

fig, ax = plt.subplots(figsize=(6.5, 5))
sns.heatmap(corr_pdf, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
ax.set_title("Correlación de Pearson, registros elegibles 2025")
plt.tight_layout()
guardar(fig, "05_correlaciones")
plt.show()
display(corr_pdf)

# %% [markdown]
# - Ninguna variable tiene una asociación lineal fuerte con el salario. La mayor es la antigüedad
#   (r = 0.18), luego la edad (0.15) y las horas (0.08). El salario es muy asimétrico y depende más de las
#   variables categóricas.
# - Edad y antigüedad tienen una relación positiva moderada (r = 0.49). Para acumular antigüedad hay que
#   tener edad. No llega a 1 porque muchas personas mayores cambiaron de trabajo hace poco.
# - Las horas tienen una relación negativa débil con la edad (r = −0.11).
#
# Correlación no implica causalidad.

# %% [markdown]
# ## 4. Segmentación de perfiles con KMeans
#
# Variables base: edad, antigüedad y horas habituales. Se prueba también agregar el salario para decidir
# si vale la pena. Las variables se estandarizan con `StandardScaler` (media 0, desviación 1) dentro de
# un `Pipeline`. Se evalúa K = 2, 3, 4 y 5 con la silueta y la suma de distancias al centroide (WSSSE).

# %%
from pyspark.ml import Pipeline
from pyspark.ml.feature import StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

VARS_CLUSTER = ["edad", "antiguedad", "horas_semanales"]
VARIANTES = {"sin salario": VARS_CLUSTER, "con salario": VARS_CLUSTER + ["salario_mensual"]}


def pipeline_kmeans(cols, k):
    return Pipeline(stages=[
        VectorAssembler(inputCols=cols, outputCol="vars_cluster"),
        StandardScaler(inputCol="vars_cluster", outputCol="features_cluster", withMean=True, withStd=True),
        KMeans(k=k, seed=SEED, featuresCol="features_cluster", predictionCol="cluster", maxIter=50),
    ])


evaluador_silueta = ClusteringEvaluator(featuresCol="features_cluster", predictionCol="cluster")
filas_k, modelos_k = [], {}
for variante, cols in VARIANTES.items():
    for k in [2, 3, 4, 5]:
        modelo = pipeline_kmeans(cols, k).fit(df_2025)
        pred = modelo.transform(df_2025)
        tamanos = modelo.stages[-1].summary.clusterSizes
        filas_k.append(dict(variante=variante, k=k, silueta=evaluador_silueta.evaluate(pred),
                            wssse=modelo.stages[-1].summary.trainingCost,
                            cluster_menor_pct=100 * min(tamanos) / _n_2025))
        modelos_k[(variante, k)] = modelo

eval_k = pd.DataFrame(filas_k)
display(eval_k)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for variante, pdf in eval_k.groupby("variante"):
    axes[0].plot(pdf["k"], pdf["silueta"], marker="o", label=variante)
    axes[1].plot(pdf["k"], pdf["wssse"], marker="o", label=variante)
axes[0].set_title("Silueta por K")
axes[1].set_title("WSSSE por K (método del codo)")
for ax in axes:
    ax.set_xlabel("K")
    ax.set_xticks([2, 3, 4, 5])
    ax.legend()
plt.tight_layout()
guardar(fig, "06_kmeans_seleccion_k")
plt.show()

# %% [markdown]
# **Salario sí o no.** Con salario la silueta baja en todos los K (0.51 contra 0.55 con K = 2; 0.37
# contra 0.47 con K = 4). El salario es muy asimétrico y, aun estandarizado, sus extremos arrastran los
# centroides. Además, se busca un perfil laboral para luego comparar salarios entre perfiles. Por eso el
# salario queda fuera del clustering y solo se usa para describir los grupos.
#
# **Elección de K.** K = 2 tiene la mayor silueta (0.55), pero solo separa jóvenes de mayores. Nuestro
# criterio fue combinar el codo del WSSSE, la silueta y que ningún cluster tenga menos del 10 % de los
# registros. El WSSSE cae 21 % de 2 a 3, 24 % de 3 a 4 y solo 12 % de 4 a 5. K = 5 deja un cluster de 4.9 %.
# Se elige K = 4: silueta 0.47 y cluster menor de 12.9 %.

# %%
VARIANTE_ELEGIDA = "sin salario"
K_ELEGIDO = 4

modelo_kmeans = modelos_k[(VARIANTE_ELEGIDA, K_ELEGIDO)]
df_clusters = modelo_kmeans.transform(df_2025).drop("vars_cluster", "features_cluster").cache()

perfil = (
    df_clusters.groupBy("cluster").agg(
        F.count("*").alias("n"),
        F.mean("edad").alias("edad_media"),
        F.mean("antiguedad").alias("antiguedad_media"),
        F.mean("horas_semanales").alias("horas_media"),
        F.expr("percentile(salario_mensual, 0.5)").alias("salario_mediano"),
        F.mean("salario_mensual").alias("salario_medio"),
        F.mean((F.col("categoria_ocupacional") == "Gobierno").cast("int")).alias("pct_gobierno"),
        F.mean((F.col("categoria_ocupacional") == "Empresa privada").cast("int")).alias("pct_privada"),
        F.mean((F.col("categoria_ocupacional") == "Jornalero o peón").cast("int")).alias("pct_jornalero"),
        F.mean((F.col("categoria_ocupacional") == "Servicio doméstico").cast("int")).alias("pct_domestico"),
        F.mean((F.col("dominio") == "Rural nacional").cast("int")).alias("pct_rural"),
        F.mean(F.col("nivel_educativo").isin("Diversificado", "Superior", "Maestría", "Doctorado").cast("int")).alias("pct_diversificado_o_mas"),
    ).orderBy("cluster").toPandas().set_index("cluster")
)
perfil["pct_registros"] = 100 * perfil["n"] / perfil["n"].sum()
for c in [c for c in perfil.columns if c.startswith("pct_") and c != "pct_registros"]:
    perfil[c] = 100 * perfil[c]
display(perfil.T)

# %%
muestra_clusters = (
    df_clusters.select("edad", "antiguedad", "horas_semanales", "salario_mensual", "cluster")
    .sample(fraction=min(1.0, 6000 / _n_2025), seed=SEED).limit(5000).toPandas()
)
fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
_paleta = sns.color_palette("tab10", K_ELEGIDO)
for ax, (x, y) in zip(axes, [("edad", "antiguedad"), ("edad", "horas_semanales"), ("antiguedad", "salario_mensual")]):
    sns.scatterplot(data=muestra_clusters, x=x, y=y, hue="cluster", palette=_paleta, s=10, alpha=0.6, ax=ax, linewidth=0)
    ax.set_title(f"{y} vs {x}")
axes[2].set_yscale("log")
axes[2].set_ylabel("salario_mensual (escala log)")
plt.tight_layout()
guardar(fig, "07_kmeans_perfiles")
plt.show()

# %% [markdown]
# | Cluster | Registros | Perfil |
# |---|---|---|
# | 0 | 46.0 % | **Jóvenes que empiezan.** 26 años, 2.4 años de antigüedad y 41 horas. 52 % con diversificado o más. Mediana Q3,000. |
# | 1 | 17.5 % | **Jornada extendida.** 30 años, 3.4 años de antigüedad y 74 horas por semana. 67 % en empresa privada. Mediana Q3,000. |
# | 2 | 23.6 % | **Adultos con poca antigüedad.** 49 años pero solo 4.1 años en su trabajo y 40 horas. Más servicio doméstico (12 %). Mediana Q3,000. |
# | 3 | 12.9 % | **Trayectoria estable.** 50 años, 22 años de antigüedad y 41 horas. 31 % en gobierno. Mediana Q3,800 y media Q4,683. |
#
# Los grupos se separan por edad, antigüedad y jornada, no por salario. La mediana es Q3,000 en tres de
# los cuatro perfiles. Solo el de trayectoria estable gana claramente más, y ahí pesa el empleo público.
# Esto concuerda con las correlaciones bajas de la sección 3. Los perfiles describen la muestra, no la
# población, y el cluster no se usa como predictor.

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
