#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path
import sys

import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.comparativo import (
    comparar_serie,
    figura_estacionalidad,
    figura_recuperacion,
    figura_tendencia,
    figura_volatilidad,
    perfil_estacional,
)
from src.utils import RUTA_RESULTADOS, SERIES, cargar_serie

COLUMNAS = [
    "clave",
    "etiqueta",
    "categoria",
    "fs",
    "ft",
    "amplitud_estacional_log",
    "factor_max_mes",
    "factor_min_mes",
    "pendiente_viajeros_mes",
    "pendiente_pct_media",
    "cv_2009_2019",
    "vol_retornos_log",
    "media_2019",
    "min_pandemia",
    "fecha_min_pandemia",
    "caida_pct",
    "mes_recuperacion_80",
]

RUTA_RESULTADOS.mkdir(parents=True, exist_ok=True)


# In[2]:


completas = {clave: cargar_serie(clave, "completa") for clave in SERIES}
trains = {clave: cargar_serie(clave, "train") for clave in SERIES}

filas = [comparar_serie(clave, trains[clave], completas[clave]) for clave in SERIES]

factores = pd.read_csv(RUTA_RESULTADOS / "diagnostico_series.csv")[
    ["clave", "factor_max_mes", "factor_min_mes", "amplitud_estacional_log"]
]
comparativo = pd.DataFrame(filas).merge(factores, on="clave")[COLUMNAS]
comparativo.to_csv(RUTA_RESULTADOS / "comparativo_series.csv", index=False)
print(comparativo.round(3).to_string(index=False))


# In[3]:


tabla = comparativo.set_index("clave")
categorias = tabla[tabla["categoria"] != "Referencia"]
perfiles = pd.DataFrame(
    {clave: perfil_estacional(trains[clave]) for clave in categorias.index}
)

figura_estacionalidad(categorias, perfiles)
figura_tendencia(categorias)
figura_volatilidad(categorias)
figura_recuperacion(tabla, completas)
print(perfiles.round(3).to_string())


# In[4]:


maritima = completas["via_maritima"]
anuales = maritima.resample("YE").sum()
print("totales anuales de marítima")
print(anuales.loc["2019":"2025"].round().to_string())
print()
print("umbral de recuperación:", round(0.8 * tabla.loc["via_maritima", "media_2019"]))
print("meses de 2022:")
print(maritima.loc["2022"].round().to_string())


# In[5]:


total = completas["total"]
for nombre, tramo in [
    ("2009-2019", slice("2009-01-01", "2019-12-01")),
    ("2021-04 a 2026-06", slice("2021-04-01", "2026-06-01")),
]:
    reparto = {
        clave: 100 * completas[clave].loc[tramo].sum() / total.loc[tramo].sum()
        for clave in ["via_terrestre", "via_aerea", "via_maritima"]
    }
    print(nombre, {clave: round(valor, 1) for clave, valor in reparto.items()})


# ## Categoría vías de ingreso
# 
# La mayor estacionalidad es de la vía marítima, con Fs de 0.405 frente a 0.169 de la terrestre y 0.142 de la aérea, y una amplitud estacional en logaritmos de 3.273 contra 0.578 y 0.953. El perfil mensual muestra por qué: los cruceros concentran su temporada en diciembre (factor 3.328) y se apagan en junio (0.153), un contraste que las otras dos vías no tienen.
# 
# La mayor tendencia de crecimiento es de la vía terrestre. En pendiente absoluta suma 1,448 viajeros por mes, y normalizada equivale a 0.974 % de su media mensual, la más alta de la categoría. Su fuerza de tendencia, 0.653, confirma que la trayectoria domina la variación de la serie. La comparación absoluta y la normalizada coinciden aquí, pero la marítima ilustra el problema de mirar solo la absoluta: sus 38 viajeros por mes se traducen en 0.444 %, apenas por encima del 0.428 % de la aérea.
# 
# La mayor volatilidad es de la marítima por amplio margen, con coeficiente de variación de 0.790 contra 0.431 de la terrestre y 0.216 de la aérea, y desviación de retornos logarítmicos de 2.185 contra 0.236 y 0.171. Las dos medidas coinciden en el orden, aunque la de retornos exagera la distancia porque la marítima tiene 16 ceros en el entrenamiento, incluidos meses aislados prepandemia, y cada cero produce un retorno logarítmico enorme.
# 
# La más afectada por la pandemia es la marítima. Cae 100 % contra su media de 2019 y es la última en cruzar el umbral del 80 %, en diciembre de 2022, doce meses después de la aérea. Ese cruce es un artefacto de un mes puntual y no una recuperación: la celda anterior muestra que el total anual pasa de 130,789 viajeros en 2019 a 26,030 en 2022 y a cerca de 6,600 entre 2023 y 2025.

# ## Categoría países de residencia
# 
# En estacionalidad las tres series son bajas y muy parecidas: Honduras 0.119, Estados Unidos 0.109 y El Salvador 0.105. Honduras es la mayor, pero la diferencia con El Salvador es de 0.014 puntos de Fs y no sostiene una conclusión operativa. Lo informativo es el calendario, no la intensidad: Honduras y El Salvador tienen su pico en enero y diciembre, mientras Estados Unidos lo tiene en julio (factor 1.449) con valle en septiembre (0.606).
# 
# La mayor tendencia de crecimiento es de El Salvador, con 0.978 % de la media por mes, seguido por Honduras con 0.579 % y Estados Unidos con 0.374 %. En viajeros absolutos el orden es el mismo, 641 contra 56 y 112 por mes, porque El Salvador es además la serie de mayor volumen del grupo.
# 
# En volatilidad las dos medidas discrepan. El Salvador tiene el mayor coeficiente de variación, 0.453 contra 0.335 de Honduras y 0.300 de Estados Unidos, pero Estados Unidos tiene la mayor desviación de retornos, 0.318 contra 0.267 y 0.219. El coeficiente de variación mide dispersión alrededor de la media de once años, y El Salvador la infla porque su nivel casi se duplica en el tramo. La desviación de retornos mide el salto de un mes al siguiente, y ahí Estados Unidos gana por su estacionalidad más marcada entre julio y septiembre.
# 
# En impacto pandémico las tres caen 100 % porque no registran viajeros entre abril y agosto de 2020, así que la profundidad no discrimina. El desempate es la velocidad de recuperación: Estados Unidos vuelve al 80 % del nivel de 2019 en diciembre de 2021, Honduras en marzo de 2022 y El Salvador en abril de 2022.

# ## Descubrimientos para el INGUAT
# 
# 1. El flujo depende de la frontera terrestre. La terrestre aporta 58.9 % del total en 2009-2019 y 65.5 % después del corte, mientras la aérea baja de 37.7 % a 34.2 %. La capacidad terrestre define el volumen, pero el crecimiento de la aérea es el más estable, con el menor coeficiente de variación de la categoría, 0.216.
# 2. El calendario operativo es común. Diciembre es pico en cinco de las siete series y el valle cae en septiembre o febrero. Septiembre es la ventana natural para mantenimiento, capacitación y campañas de temporada baja.
# 3. Estados Unidos se recupera antes que los vecinos. Alcanza el 80 % del nivel de 2019 en diciembre de 2021, cuatro meses antes que El Salvador. Ante un choque, la promoción rinde más rápido en el mercado aéreo de larga distancia que en el flujo fronterizo.
# 4. El segmento de cruceros no volvió. Marítima pasa de 130,789 viajeros en 2019 a cerca de 6,600 anuales entre 2023 y 2025, un nivel veinte veces menor. Es un cambio de régimen que exige decidir si se reactiva la ruta o se reasignan los recursos portuarios.
# 5. Los modelos entrenados sobre historia que cruza la pandemia no sirven como pronóstico operativo. El mejor modelo por serie es SES en seis de siete casos, con MAPE de 35.62 % a 74.32 %. Cualquier planificación con estas series debe reestimarse con datos posteriores a la reapertura.
# 6. La estacionalidad marítima es la única que justifica planificación dedicada. Su Fs de 0.405 es más del doble que el de cualquier otra vía, y su factor de diciembre, 3.328, implica que la operación portuaria se concentra en pocos meses.
