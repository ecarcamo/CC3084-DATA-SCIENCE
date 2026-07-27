#!/usr/bin/env python
# coding: utf-8

# In[1]:


from ast import literal_eval
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.evaluacion import metricas
from src.modelos import ajustar_sarima
from src.utils import (
    RUTA_FIGURAS,
    RUTA_RESULTADOS,
    SERIES,
    cargar_serie,
)

RUTA_PREDICCIONES = RUTA_RESULTADOS / "predicciones"
modelos_arima = pd.read_csv(RUTA_RESULTADOS / "modelos_arima.csv")
seleccionados = modelos_arima[modelos_arima["seleccionado"]].set_index("serie")


# In[2]:


def guardar_prediccion(clave, modelo, prediccion):
    salida = pd.DataFrame(
        {
            "fecha": prediccion.index.strftime("%Y-%m-%d"),
            "prediccion": prediccion.to_numpy(dtype=float),
        }
    )
    salida.to_csv(RUTA_PREDICCIONES / f"{clave}_{modelo}.csv", index=False)


def cargar_prediccion(clave, modelo, indice):
    ruta = RUTA_PREDICCIONES / f"{clave}_{modelo}.csv"
    datos = pd.read_csv(ruta)
    return pd.Series(datos["prediccion"].to_numpy(), index=indice, name=modelo)


def graficar_predicciones(clave, train, test, predicciones):
    figura, eje = plt.subplots(figsize=(12, 5))
    eje.plot(train.index, train, label="Train", color="black", linewidth=1)
    eje.plot(test.index, test, label="Test real", color="tab:blue", linewidth=2)
    for nombre, prediccion in predicciones.items():
        eje.plot(prediccion.index, prediccion, label=nombre, alpha=0.8)
    eje.set(
        title=f"Predicciones: {SERIES[clave]}",
        xlabel="Fecha",
        ylabel="Viajeros",
    )
    eje.legend(ncol=3, fontsize=8)
    figura.tight_layout()
    figura.savefig(RUTA_FIGURAS / f"pred_{clave}.png", dpi=150)
    plt.close(figura)


filas = []
for clave in SERIES:
    train = cargar_serie(clave, "train")
    test = cargar_serie(clave, "test")
    fila_sarima = seleccionados.loc[clave]
    order = literal_eval(fila_sarima["order"])
    seasonal_order = literal_eval(fila_sarima["seasonal_order"])
    ajuste = ajustar_sarima(np.log1p(train), order, seasonal_order)
    sarima = np.expm1(ajuste.forecast(len(test))).clip(lower=0)
    sarima.index = test.index
    sarima.name = "sarima"
    guardar_prediccion(clave, "sarima", sarima)

    predicciones = {"sarima": sarima}
    for nombre in ["holt_winters", "ses", "seasonal_naive", "prophet"]:
        ruta = RUTA_PREDICCIONES / f"{clave}_{nombre}.csv"
        if ruta.exists():
            predicciones[nombre] = cargar_prediccion(clave, nombre, test.index)

    for nombre, prediccion in predicciones.items():
        resultado = metricas(test, prediccion)
        es_sarima = nombre == "sarima"
        filas.append(
            {
                "serie": clave,
                "modelo": nombre,
                "order": str(order) if es_sarima else "",
                "aic": fila_sarima["aic"] if es_sarima else np.nan,
                "bic": fila_sarima["bic"] if es_sarima else np.nan,
                **resultado,
                "mejor": False,
            }
        )
    graficar_predicciones(clave, train, test, predicciones)

metricas_modelos = pd.DataFrame(filas)
for clave in SERIES:
    mascara = metricas_modelos["serie"].eq(clave)
    subconjunto = metricas_modelos.loc[mascara]
    puntaje = subconjunto["mae"].rank() + subconjunto["rmse"].rank()
    mejor_indice = puntaje.idxmin()
    metricas_modelos.loc[mejor_indice, "mejor"] = True

metricas_modelos.to_csv(RUTA_RESULTADOS / "metricas_modelos.csv", index=False)
print(metricas_modelos.to_string(index=False))


# ## Limitación del diseño temporal
# 
# El corte termina en marzo de 2021, cuando la pandemia domina el final del entrenamiento y la recuperación todavía no aparece. Por ello, un modelo que prolonga la dinámica aprendida tenderá a subpredecir la recuperación de casi todas las series. Marítima presenta el problema opuesto: después de recuperarse parcialmente, cambia a un régimen cercano a 6,600 viajeros anuales desde 2023, unas veinte veces menor que 2019. La sobrepredicción marítima no identifica un error de implementación, sino una ruptura estructural ausente del entrenamiento.

# ## Total
# 
# SES es el mejor del conjunto evaluado, con MAE de 175,088 y RMSE de 194,791 viajeros. El error es grande frente al volumen mensual real y el MAPE de 58.11 % confirma una capacidad predictiva baja. El entrenamiento termina antes de la recuperación, por lo que todos los métodos prolongan niveles deprimidos y subestiman el test.

# ## Vía aérea
# 
# SES obtiene el menor MAE, 36,109 viajeros, y RMSE, 41,368, con MAPE de 35.62 %. Es el resultado más útil de esta serie, aunque todavía subestima la reapertura aérea. El SARIMA seleccionado por AIC es numéricamente inestable a 63 pasos y produce errores de magnitud extrema; por eso no se selecciona para pronóstico operativo.

# ## Vía terrestre
# 
# SES vuelve a ser la referencia menos mala, con MAE de 140,428 y RMSE de 156,310 viajeros. Su MAPE de 71.75 % muestra que no reproduce adecuadamente la recuperación de los cruces terrestres. La diferencia frente a los demás métodos es moderada, pero todos heredan el nivel pandémico al final del entrenamiento.

# ## Vía marítima
# 
# Prophet presenta el menor MAE, 784 viajeros, y RMSE, 1,645, con MAPE de 86.12 % calculado tras excluir 11 meses reales iguales a cero. La cifra absoluta parece pequeña porque el régimen posterior es muy bajo, pero el error relativo revela poca precisión. En estos ajustes, SARIMA, Holt-Winters y seasonal naive colapsan a pronósticos cercanos a cero por el cierre al final del train, en lugar de sobrepredecir. Aun así, cualquier especificación que extrapolara el nivel prepandemia sobrepredeciría fuertemente el quiebre cercano a 6,600 viajeros anuales desde 2023.

# ## El Salvador
# 
# SES alcanza el mejor resultado, con MAE de 94,064 y RMSE de 104,531 viajeros. El MAPE de 74.32 % es demasiado alto para planificación de capacidad sin intervalos amplios o actualización del modelo. La recuperación posterior a marzo de 2021 queda fuera de toda la muestra de ajuste.

# ## Estados Unidos
# 
# SES es el mejor modelo evaluado, con MAE de 25,115 y RMSE de 28,953 viajeros; su MAPE de 49.93 % sigue siendo elevado. El SARIMA elegido por AIC genera una trayectoria explosiva fuera de muestra, señal de que un buen ajuste interno con restricciones de estacionariedad desactivadas no garantiza estabilidad a un horizonte largo.

# ## Honduras
# 
# SES registra MAE de 17,240 y RMSE de 19,587 viajeros, los menores de la serie. El MAPE de 66.05 % indica baja calidad predictiva pese a superar a las demás alternativas. El modelo mantiene demasiado peso en los ceros y niveles reducidos del cierre fronterizo, de modo que no captura la recuperación del test.
