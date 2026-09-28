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
corr_matrix = Correlation.corr(_vec_df, "features_corr", "pearson").head()[0].toArray()
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
#   Se ordenan las correlaciones absolutas calculadas, no las supuestas.
# - **¿Existe relación entre edad y antigüedad?** El signo y la magnitud
#   observados se informan debajo. Correlación no significa causalidad.

# %%
asociaciones = corr_pdf.loc["salario_mensual"].drop("salario_mensual")
asociaciones = asociaciones.reindex(asociaciones.abs().sort_values(ascending=False).index)
r_edad_antiguedad = corr_pdf.loc["edad", "antiguedad"]
relacion_edad_antiguedad = (
    "no se aprecia una relación lineal importante"
    if abs(r_edad_antiguedad) < 0.1
    else "se aprecia una relación lineal positiva"
    if r_edad_antiguedad > 0
    else "se aprecia una relación lineal negativa"
)
display(Markdown(
    "**Lectura del mapa de calor:** las asociaciones lineales con el salario, "
    "ordenadas por magnitud absoluta, son "
    + ", ".join(f"`{variable}` ({valor:+.2f})" for variable, valor in asociaciones.items())
    + f". Entre edad y antigüedad, r = {r_edad_antiguedad:+.2f}: "
    f"{relacion_edad_antiguedad}. "
    "Son correlaciones de Pearson sin ponderación sobre todos los registros "
    "elegibles de 2025; no establecen relaciones causales."
))

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
