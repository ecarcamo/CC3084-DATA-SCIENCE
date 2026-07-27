#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.modelos import (
    ajustar_sarima,
    diagnostico_residuos,
    grid_sarima,
    seleccionar_sarima,
)
from src.utils import RUTA_FIGURAS, RUTA_RESULTADOS, SERIES, cargar_serie

PARAMETROS = {
    clave: {"d": 2 if clave == "via_maritima" else 1, "D": 1}
    for clave in SERIES
}
RUTA_RESULTADOS.mkdir(parents=True, exist_ok=True)


# In[2]:


def ejecutar_auto_arima(serie_log, d, D):
    try:
        from pmdarima import auto_arima

        modelo = auto_arima(
            serie_log,
            seasonal=True,
            m=12,
            d=d,
            D=D,
            start_p=0,
            start_q=0,
            max_p=2,
            max_q=2,
            start_P=0,
            start_Q=0,
            max_P=1,
            max_Q=1,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
        )
        return modelo.order, modelo.seasonal_order, modelo.aic()
    except Exception as error:
        return None, None, f"No disponible: {error}"


comparaciones = []
automaticos = []
for clave in SERIES:
    serie_log = np.log1p(cargar_serie(clave, "train"))
    parametros = PARAMETROS[clave]
    rejilla = grid_sarima(serie_log, horizonte=63, **parametros)
    validos = rejilla[np.isfinite(rejilla["aic"])]
    estables = validos[validos["estable"]]
    elegida = seleccionar_sarima(rejilla)
    candidatos = estables.head(3) if len(estables) >= 3 else validos.head(3)

    print(f"\n{SERIES[clave]}: top 5 por AIC con filtro de estabilidad")
    print(
        validos[
            ["order", "seasonal_order", "aic", "bic", "estable", "max_pronostico"]
        ]
        .head(5)
        .to_string(index=False)
    )
    print(
        f"ajustados={len(validos)} estables={len(estables)} "
        f"elegida={elegida['order']}{elegida['seasonal_order']} "
        f"estable={bool(elegida['estable'])}"
    )

    auto_order, auto_seasonal, auto_aic = ejecutar_auto_arima(
        serie_log,
        parametros["d"],
        parametros["D"],
    )
    automaticos.append(
        {
            "serie": clave,
            "order": auto_order,
            "seasonal_order": auto_seasonal,
            "aic": auto_aic,
        }
    )
    print(
        "auto_arima:",
        auto_order,
        auto_seasonal,
        auto_aic,
    )

    for _, fila in candidatos.reset_index(drop=True).iterrows():
        order = tuple(fila["order"])
        seasonal_order = tuple(fila["seasonal_order"])
        modelo = ajustar_sarima(serie_log, order, seasonal_order)
        residuos, figura = diagnostico_residuos(modelo)
        seleccionado = (
            order == tuple(elegida["order"])
            and seasonal_order == tuple(elegida["seasonal_order"])
        )
        if seleccionado:
            ruta = RUTA_FIGURAS / f"modelo_{clave}_residuos.png"
            figura.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(figura)
        comparaciones.append(
            {
                "serie": clave,
                "order": order,
                "seasonal_order": seasonal_order,
                "aic": modelo.aic,
                "bic": modelo.bic,
                "ljung_box_p": residuos["ljung_box_p"],
                "jarque_bera_p": residuos["jarque_bera_p"],
                "max_pronostico": fila["max_pronostico"],
                "estable": bool(fila["estable"]),
                "n_ajustados": len(validos),
                "n_estables": len(estables),
                "seleccionado": seleccionado,
            }
        )

    if not any(
        fila["seleccionado"]
        for fila in comparaciones
        if fila["serie"] == clave
    ):
        modelo = ajustar_sarima(
            serie_log,
            tuple(elegida["order"]),
            tuple(elegida["seasonal_order"]),
        )
        residuos, figura = diagnostico_residuos(modelo)
        ruta = RUTA_FIGURAS / f"modelo_{clave}_residuos.png"
        figura.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(figura)
        comparaciones.append(
            {
                "serie": clave,
                "order": tuple(elegida["order"]),
                "seasonal_order": tuple(elegida["seasonal_order"]),
                "aic": modelo.aic,
                "bic": modelo.bic,
                "ljung_box_p": residuos["ljung_box_p"],
                "jarque_bera_p": residuos["jarque_bera_p"],
                "max_pronostico": elegida["max_pronostico"],
                "estable": bool(elegida["estable"]),
                "n_ajustados": len(validos),
                "n_estables": len(estables),
                "seleccionado": True,
            }
        )

modelos_arima = pd.DataFrame(comparaciones)
modelos_arima.to_csv(RUTA_RESULTADOS / "modelos_arima.csv", index=False)
auto_arima_resultados = pd.DataFrame(automaticos)
print("\nComparación manual consolidada")
print(modelos_arima.to_string(index=False))
print("\nResultados de auto_arima")
print(auto_arima_resultados.to_string(index=False))


# ## Criterio de selección
# 
# Para cada serie se retienen tres especificaciones convergentes con menor AIC y se comparan también por BIC, Ljung-Box y Jarque-Bera. `auto_arima` se restringe al mismo espacio de búsqueda, así que una propuesta con términos de orden bajo y diferenciación fijada es coherente con las ACF y PACF observadas. Si difiere del mínimo manual, la causa puede ser su búsqueda escalonada y no una contradicción con el diagnóstico. Si la biblioteca no carga por incompatibilidad binaria, la salida de la celda registra el error y la rejilla manual queda como método reproducible. Jarque-Bera se informa como diagnóstico, pero la falta de normalidad no invalida por sí sola el pronóstico; la ausencia de autocorrelación residual tiene mayor peso.

# ## Modelos alternativos
# 
# Se generan cuatro referencias con el mismo horizonte del test. Holt-Winters y suavizamiento exponencial simple se ajustan en `log1p` y se revierten a viajeros; seasonal naive trabaja en niveles y repite los últimos doce meses; Prophet usa estacionalidad anual sobre `log1p`. Si Prophet no está disponible, el error queda registrado y los otros tres modelos continúan.

# In[3]:


from src.modelos import (
    modelo_holt_winters,
    modelo_prophet,
    modelo_seasonal_naive,
    modelo_ses,
)

RUTA_PREDICCIONES = RUTA_RESULTADOS / "predicciones"
RUTA_PREDICCIONES.mkdir(parents=True, exist_ok=True)
MODELOS_ALTERNATIVOS = {
    "holt_winters": modelo_holt_winters,
    "ses": modelo_ses,
    "seasonal_naive": modelo_seasonal_naive,
    "prophet": modelo_prophet,
}

def guardar_prediccion(clave, modelo, prediccion):
    salida = pd.DataFrame(
        {
            "fecha": prediccion.index.strftime("%Y-%m-%d"),
            "prediccion": prediccion.to_numpy(dtype=float),
        }
    )
    salida.to_csv(RUTA_PREDICCIONES / f"{clave}_{modelo}.csv", index=False)


for clave in SERIES:
    train = cargar_serie(clave, "train")
    horizonte = len(cargar_serie(clave, "test"))
    for nombre, funcion in MODELOS_ALTERNATIVOS.items():
        try:
            prediccion = funcion(train, horizonte)
            guardar_prediccion(clave, nombre, prediccion)
            print(clave, nombre, len(prediccion))
        except Exception as error:
            print(clave, nombre, f"no disponible: {error}")

