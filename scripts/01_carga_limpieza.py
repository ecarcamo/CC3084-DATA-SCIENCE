#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
sys.path.append("../src")

import pandas as pd
import matplotlib.pyplot as plt

from carga import cargar_base
from limpieza import limpiar_base, validar_calidad
from series import generar_series, FECHA_INICIO, FECHA_FIN, FECHA_FIN_TRAIN

RUTA_RAW = "../data/raw/Base_Migracion_2009-2026jun.xlsx"
RUTA_PROCESSED = "../data/processed"
RUTA_SERIES = "../data/processed/series"
RUTA_FIGURAS = "../informe/figuras"


# ## 1. Carga de la base

# In[2]:


df_raw = cargar_base(RUTA_RAW)
print("Shape:", df_raw.shape)
print("Meses únicos:", df_raw["fecha"].nunique())
print("Rango:", df_raw["fecha"].min(), "a", df_raw["fecha"].max())
df_raw.head()


# **Notas de la hoja `Notas` del Excel (resumen):**
# 
# - Los datos son solo para uso académico; no son cifras oficiales de INGUAT ni del Instituto Guatemalteco de Migración.
# - Cobertura: enero 2009 a junio 2026, 210 meses consecutivos, 161,036 registros, sin huecos.
# - Formato largo: una fila por combinación de mes, vía, frontera, país/agrupación y tipo de viajero. Sin filas de total ni doble conteo.
# - Tres tramos de fuente con distinta metodología: 2009-2020 (respaldos históricos), 2021-2022 (entrega IGM), 2023-jun 2026 (sistema depurado INGUAT). Los niveles no son perfectamente comparables entre tramos, en particular el quiebre 2022→2023 en `Tipo de Viajero` (ver sección de decisiones más abajo).
# - Desde 2023 la columna `País` reporta por agrupación de mercado (27 grupos) en vez de país individual (226 países hasta 2022); los mercados principales siguen siendo comparables.
# - Vía Marítima pierde detalle desde 2017 (cambio de registro).

# ## 2. Limpieza

# In[3]:


df = limpiar_base(df_raw)
checks = validar_calidad(df)
checks


# **Problemas detectados y resueltos** (valores originales conservados en columnas `_raw`):
# 
# | Problema | Resolución |
# |---|---|
# | `Región dos`: "Cruceristas" (2009-2021) y "Cruceros" (2022) son la misma categoría | Unificados en `"Cruceros"` |
# | `Región dos`: valor basura `"0"` (2022, 821 viajeros) | Reetiquetado como `"Sin especificar"` |
# | `País`: duplicados por casing (ej. `"OTROS PAISES DEL MUNDO"` vs `"Otros Paises Del Mundo"`, y 12 casos adicionales del mismo tipo detectados por código) | Unificados a la variante con más registros |
# | `Regiones OMT`: valores basura `"0x2a"` y `"SIN ESPECIFICAR"` | Unificados en `"Sin especificar"` |
# | `Frontera`: `"Cruceros"` aparece como si fuera una frontera, junto a `"22 Otra frontera"` | Se deja igual, queda documentado aquí |
# | `Viajero`: 51,272 registros con decimales (estimaciones/prorrateos) y 54 valores en exactamente 0 | No se redondea; queda documentado aquí |
# 
# Cero nulos y cero duplicados exactos confirmados por código arriba.

# ## 3. Decisiones fijadas

# In[4]:


total_general = df["Viajero"].sum()
total_guatemala = df.loc[df["País"] == "Guatemala", "Viajero"].sum()
print(f"Guatemala acumula {total_guatemala:,.0f} viajeros ({total_guatemala/total_general:.1%} del total)")

top3_sin_guatemala = (
    df.loc[df["País"] != "Guatemala"].groupby("País")["Viajero"].sum().sort_values(ascending=False).head(3)
)
top3_sin_guatemala


# **Decisión — `País == "Guatemala"`:** acumula ~14.8M viajeros (28% del total). Son residentes
# retornando, no viajeros internacionales entrantes. Se **mantienen en la serie total** (para no
# alterar el total oficial), pero se **excluyen del ranking de países de residencia**. El Top 3 de
# países de residencia queda: **El Salvador, Estados Unidos de América, Honduras**.
# 
# **Decisión — 2026 es un año parcial:** solo cubre enero-junio 2026. No es comparable en totales
# anuales contra los demás años; cualquier comparación anual debe advertir esto.
# 
# **Decisión — `Tipo de Viajero`:** tiene 4 valores (Turista, Excursionista, Viajero, Cruceristas).
# Entre 2022 y 2023 la categoría "Viajero" cae fuertemente (~1.06M a ~0.33M) por un cambio de
# criterio metodológico (exclusión de comercio fronterizo y tránsito), no por una caída real de
# turismo. Para comparar visitantes durante todo el período conviene usar Turista + Excursionista,
# que son consistentes en toda la serie.

# ## 4. Split temporal 70/30

# In[5]:


meses = pd.date_range(FECHA_INICIO, FECHA_FIN, freq="MS")
meses_train = pd.date_range(FECHA_INICIO, FECHA_FIN_TRAIN, freq="MS")
meses_test = meses.difference(meses_train)

print(f"Total de meses: {len(meses)}")
print(f"Train: {meses_train.min().date()} a {meses_train.max().date()} ({len(meses_train)} meses, {len(meses_train)/len(meses):.1%})")
print(f"Test:  {meses_test.min().date()} a {meses_test.max().date()} ({len(meses_test)} meses, {len(meses_test)/len(meses):.1%})")


# **El corte 2021-03 / 2021-04 no es arbitrario:** deja la caída de la pandemia (colapso desde
# marzo 2020, piso 2020-2021 en ~27% del nivel de 2019) **dentro del conjunto de entrenamiento**, y
# la **recuperación completa posterior a 2022 queda en el conjunto de prueba**. Esto es intencional
# y debe justificarse en el informe: el modelo entrena viendo el shock y su fondo, pero es evaluado
# prediciendo una recuperación con una dinámica distinta a la de la caída.

# ## 5. Construcción de series

# In[6]:


series = generar_series(df, RUTA_SERIES)
print("Series generadas y guardadas en", RUTA_SERIES)
sorted(series.keys())


# In[7]:


import os
os.makedirs(RUTA_PROCESSED, exist_ok=True)
df.to_csv(os.path.join(RUTA_PROCESSED, "base_limpia.csv"), index=False)
print("base_limpia.csv guardado:", df.shape)


# ## 6. Verificación visual de la serie total

# In[8]:


fechas = pd.to_datetime(series["total"]["fecha"])

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(fechas, series["total"]["viajeros"])
ax.set_title("Serie total mensual de viajeros internacionales (2009-01 a 2026-06)")
ax.set_xlabel("Fecha")
ax.set_ylabel("Viajeros")
fig.tight_layout()
fig.savefig(os.path.join(RUTA_FIGURAS, "serie_total.png"), dpi=150)
plt.show()


# **Resumen de validaciones ejecutadas:**
# - Shape de la base cruda: 161,036 × 13 ✓
# - 210 meses únicos, 2009-01 a 2026-06, sin huecos ✓
# - Cero nulos, cero duplicados exactos tras limpieza ✓
# - Suma de las 3 series por vía == serie total (verificado por código en `generar_series`) ✓
# - 7 series + sus versiones train guardadas en `data/processed/series/` ✓
