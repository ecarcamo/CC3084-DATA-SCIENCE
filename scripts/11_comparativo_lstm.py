#!/usr/bin/env python
# coding: utf-8

# # 11. LSTM contra los modelos del Laboratorio 1
# 
# Este cuaderno responde el punto 1.4 del enunciado: cuál de los modelos predijo mejor, si los LSTM
# mejoran a los del laboratorio pasado y cómo se determinó.
# 
# No entrena nada. Lee las métricas que dejaron los cuadernos 09 y 10, las métricas del Laboratorio 1
# en `resultados/metricas_modelos.csv` y las predicciones guardadas en `resultados/predicciones/`, y
# las agrega en dos tablas consolidadas.
# 
# ## Criterio de comparación
# 
# Las dos familias se comparan sobre los mismos 63 meses de prueba, de abril de 2021 a junio de 2026,
# con las mismas tres métricas calculadas por la misma función `src.evaluacion.metricas` del
# Laboratorio 1: MAE y RMSE en viajeros, y MAPE en porcentaje. El modelo ganador de cada serie es el
# de menor suma de los rangos de MAE y RMSE, el criterio que ya se usó en el Laboratorio 1 para
# elegir entre SARIMA, Holt-Winters, SES, seasonal naive y Prophet.
# 
# No se usan AIC ni BIC. Una red neuronal no tiene verosimilitud, de modo que esos criterios ni
# siquiera están definidos para los LSTM; y aunque lo estuvieran, el Laboratorio 1 ya documentó que
# no son comparables entre familias de modelos, porque miden ajuste dentro de muestra penalizado por
# número de parámetros y no capacidad predictiva fuera de muestra. La sección 5 del informe anterior
# dejó el caso extremo: el SARIMA de vía aérea, elegido por el menor AIC de su rejilla, produjo el
# peor pronóstico a 63 pasos de esa serie.

# In[1]:


from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.utils import RUTA_FIGURAS, RUTA_RESULTADOS, SERIES, cargar_serie

RUTA_PREDICCIONES = RUTA_RESULTADOS / "predicciones"
METRICAS = ("mae", "rmse", "mape")
COLORES = {"lab1": "tab:gray", "lstm": "tab:orange"}


# ## Consolidación de las métricas LSTM
# 
# La lectura se hace con un glob sobre `metricas_lstm_*.csv` y no con nombres fijos, de modo que las
# series entran sin tocar el código: basta que los cuadernos 09 y 10 hayan dejado sus archivos en
# `resultados/`.

# In[2]:


rutas = sorted(RUTA_RESULTADOS.glob("metricas_lstm_*.csv"))
if not rutas:
    raise FileNotFoundError(
        "No hay metricas_lstm_<serie>.csv; ejecute antes los cuadernos 09 y 10"
    )
print("archivos leidos:")
for ruta in rutas:
    print(f"  {ruta.name}")

metricas_lstm = pd.concat(
    [pd.read_csv(ruta) for ruta in rutas], ignore_index=True
).sort_values(["serie", "modelo"], ignore_index=True)
metricas_lstm.to_csv(RUTA_RESULTADOS / "metricas_lstm.csv", index=False)

series = list(dict.fromkeys(metricas_lstm["serie"]))
print(f"\nseries con LSTM: {series}")
print(metricas_lstm.to_string(index=False))


# ## Métricas del Laboratorio 1
# 
# Se filtran a las series que tienen LSTM. Son las cinco alternativas evaluadas en el laboratorio
# anterior, con sus cifras originales; no se reentrena ninguna.

# In[3]:


metricas_lab1 = pd.read_csv(RUTA_RESULTADOS / "metricas_modelos.csv")
metricas_lab1 = metricas_lab1[metricas_lab1["serie"].isin(series)].reset_index(drop=True)
print(
    metricas_lab1[["serie", "modelo", "mae", "rmse", "mape", "mejor"]].to_string(
        index=False
    )
)


# ## Tabla unificada
# 
# `comparativo_lstm_lab1.csv` junta las dos familias con las tres métricas comunes. `familia`
# distingue `lab1` de `lstm`, y `mejor_global` marca el mejor modelo de cada serie considerando las
# dos familias a la vez.

# In[4]:


columnas = ["serie", "modelo", "mae", "rmse", "mape"]
comparativo = pd.concat(
    [
        metricas_lab1[columnas].assign(familia="lab1"),
        metricas_lstm[columnas].assign(familia="lstm"),
    ],
    ignore_index=True,
)[["serie", "modelo", "familia", "mae", "rmse", "mape"]]
comparativo["mejor_global"] = False


def mejor_fila(tabla):
    """Mismo criterio del Lab 1: menor suma de los rangos de MAE y RMSE."""
    puntaje = tabla["mae"].rank() + tabla["rmse"].rank()
    return tabla.loc[puntaje.idxmin()]


for serie in series:
    subconjunto = comparativo[comparativo["serie"].eq(serie)]
    comparativo.loc[mejor_fila(subconjunto).name, "mejor_global"] = True

comparativo = comparativo.sort_values(
    ["serie", "familia", "rmse"], ignore_index=True
)
comparativo.to_csv(RUTA_RESULTADOS / "comparativo_lstm_lab1.csv", index=False)
print(comparativo.to_string(index=False))


# ## ¿Son mejores que los del laboratorio pasado?
# 
# La comparación enfrenta al campeón de cada familia. `mejora_%` es positiva cuando el LSTM reduce el
# error respecto del mejor modelo del Laboratorio 1.

# In[5]:


filas = []
for serie in series:
    subconjunto = comparativo[comparativo["serie"].eq(serie)]
    campeon = {
        familia: mejor_fila(subconjunto[subconjunto["familia"].eq(familia)])
        for familia in ("lab1", "lstm")
    }
    for metrica in METRICAS:
        valor_lab1 = float(campeon["lab1"][metrica])
        valor_lstm = float(campeon["lstm"][metrica])
        filas.append(
            {
                "serie": serie,
                "metrica": metrica,
                "mejor_lab1": campeon["lab1"]["modelo"],
                "valor_lab1": valor_lab1,
                "mejor_lstm": campeon["lstm"]["modelo"],
                "valor_lstm": valor_lstm,
                "mejora_%": 100 * (valor_lab1 - valor_lstm) / valor_lab1,
            }
        )

mejoras = pd.DataFrame(filas)
campeones = {
    serie: {
        familia: mejor_fila(
            comparativo[
                comparativo["serie"].eq(serie) & comparativo["familia"].eq(familia)
            ]
        )
        for familia in ("lab1", "lstm")
    }
    for serie in series
}
print(mejoras.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))


# El LSTM directo mejora al mejor modelo del Laboratorio 1 en las tres métricas y en las dos series.
# 
# En la serie total el MAE cae 56.05 %, de 175,088 a 76,957 viajeros; el RMSE cae 48.51 %, de 194,791
# a 100,290; y el MAPE baja 24.35 puntos porcentuales, de 58.11 % a 33.76 %, un 41.90 % en términos
# relativos. En vía aérea los márgenes son menores pero apuntan en la misma dirección: 37.31 % menos
# MAE, de 36,109 a 22,635; 28.39 % menos RMSE, de 41,368 a 29,623; y 10.68 puntos porcentuales menos
# de MAPE, de 35.62 % a 24.93 %.
# 
# Que el margen sea más chico en vía aérea era previsible. SES parte de un MAPE de 35.62 % en esa
# serie contra 58.11 % en total, porque su nivel constante queda 36.4 % por debajo del test y no
# 62.0 % como en la serie agregada: cuanto menos deprimido está el último mes del entrenamiento
# respecto del horizonte, menos terreno hay que recuperar.
# 
# Conviene medir los dos saltos contra la dispersión interna del Laboratorio 1. En la serie total la
# distancia entre SES y el segundo mejor modelo de esa entrega, Holt-Winters, era de 21,868 viajeros
# de MAE, y el salto de SES al LSTM directo es de 98,131, cuatro veces y media mayor. En vía aérea la
# misma distancia es de 11,935 y el salto es de 13,474, apenas 1.13 veces. La ventaja del LSTM es
# inequívoca en la serie total y modesta en vía aérea.
# 
# En las dos series gana también la estrategia perdedora. La recursiva registra 143,303 de MAE y
# 164,706 de RMSE en total, y 31,638 y 37,766 en vía aérea, por debajo de los 175,088 y 194,791 y de
# los 36,109 y 41,368 de SES.

# ## ¿Cuál de las dos estrategias LSTM predijo mejor?
# 
# `margen_%` mide cuánto error ahorra la estrategia ganadora respecto de la perdedora, dentro de la
# misma serie.

# In[6]:


filas = []
for serie in series:
    subconjunto = metricas_lstm[metricas_lstm["serie"].eq(serie)].set_index("modelo")
    ganador = subconjunto.index[
        (subconjunto["mae"].rank() + subconjunto["rmse"].rank()).argmin()
    ]
    perdedor = [modelo for modelo in subconjunto.index if modelo != ganador][0]
    fila = {"serie": serie, "gana": ganador, "pierde": perdedor}
    for metrica in METRICAS:
        fila[f"{metrica}_gana"] = subconjunto.loc[ganador, metrica]
        fila[f"{metrica}_pierde"] = subconjunto.loc[perdedor, metrica]
        fila[f"margen_{metrica}_%"] = (
            100
            * (subconjunto.loc[perdedor, metrica] - subconjunto.loc[ganador, metrica])
            / subconjunto.loc[perdedor, metrica]
        )
    filas.append(fila)

margen_lstm = pd.DataFrame(filas)
print(margen_lstm.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))


# La estrategia directa gana en las dos series, y el margen sigue el orden de la volatilidad: en la
# serie total ahorra 46.30 % de MAE, 39.11 % de RMSE y 28.00 % de MAPE respecto de la recursiva; en
# vía aérea, 28.46 %, 21.56 % y 19.95 %.
# 
# El resultado contradice la ventaja muestral de la recursiva, que en la serie total entrena con 123
# ventanas frente a 61, y confirma lo que anticipaba la sección de metodología: en un horizonte de 63
# pasos, la acumulación de error de la realimentación pesa más que el tamaño de la muestra. El sesgo
# lo deja ver: la recursiva se queda 51.7 % por debajo del test en total y 32.9 % en vía aérea,
# mientras la directa se queda en −16.0 % y −9.7 %.
# 
# Que la brecha sea más estrecha en vía aérea no contradice nada. Es la serie menos volátil de las
# siete del Laboratorio 1, con un CV de 0.216 contra 0.335 de la total, así que la trayectoria plana a
# la que tiende la recursiva se aleja menos del test que en la serie agregada.
# 
# Vale registrar que la comparación entre estrategias se resuelve aquí y no en el tuneo. Los
# `rmse_val` de la rejilla apuntaban en la misma dirección en las dos series, 149,716 contra 130,075
# en total y 45,464 contra 38,698 en vía aérea, pero se miden sobre tramos distintos según la
# estrategia y no habrían servido como argumento.

# ## Las trayectorias
# 
# Una figura por serie con el test real, el mejor LSTM, el mejor modelo del Laboratorio 1 y el SARIMA,
# que es el modelo canónico del enunciado anterior aunque no haya ganado ninguna serie.

# In[7]:


def cargar_prediccion(clave, modelo, indice):
    datos = pd.read_csv(RUTA_PREDICCIONES / f"{clave}_{modelo}.csv")
    return pd.Series(datos["prediccion"].to_numpy(), index=indice, name=modelo)


for serie in series:
    test = cargar_serie(serie, "test")
    trazos = {
        campeones[serie]["lstm"]["modelo"]: "tab:orange",
        campeones[serie]["lab1"]["modelo"]: "tab:gray",
        "sarima": "tab:red",
    }
    figura, eje = plt.subplots(figsize=(11, 5))
    eje.plot(test.index, test, label="Test real", color="tab:blue", linewidth=2.2)
    for modelo, color in trazos.items():
        prediccion = cargar_prediccion(serie, modelo, test.index)
        rmse = float(
            comparativo.loc[
                comparativo["serie"].eq(serie) & comparativo["modelo"].eq(modelo),
                "rmse",
            ].iloc[0]
        )
        eje.plot(
            prediccion.index,
            prediccion,
            label=f"{modelo} (RMSE {rmse:,.0f})",
            color=color,
            linewidth=1.4,
            alpha=0.9,
        )
    eje.set(
        title=f"Test 2021-04 a 2026-06: LSTM contra Laboratorio 1 ({SERIES[serie]})",
        xlabel="Fecha",
        ylabel="Viajeros",
    )
    eje.legend(fontsize=8)
    figura.tight_layout()
    figura.savefig(RUTA_FIGURAS / f"comp_lstm_{serie}.png", dpi=150)
    plt.close(figura)
    print(f"comp_lstm_{serie}.png")


# ![Trayectorias de la serie total](../informe/figuras/comp_lstm_total.png)
# 
# La figura de la serie total separa tres comportamientos.
# 
# SES es una recta en 105,145 viajeros: por construcción prolonga el último nivel suavizado del
# entrenamiento, que es un mes de pandemia, y no se mueve en 63 meses. El SARIMA(2,1,2)(1,1,1)12 es
# peor todavía, porque además de partir de un nivel bajo su tendencia estimada apunta hacia abajo y
# lo lleva a rozar el cero desde 2023; su correlación con el test es de −0.597, es decir que se mueve
# sistemáticamente al revés que la serie real.
# 
# El LSTM directo es el único de los tres que traza un perfil estacional con el nivel correcto a
# partir de 2023, y en el tramo 2023-2025 se superpone con el test en buena parte de los meses. Sus
# dos zonas de error son los extremos: sobreestima 2021, cuando la serie real todavía estaba
# deprimida, y se queda muy corto en el pico de 2022.
# 
# ![Trayectorias de la vía aérea](../informe/figuras/comp_lstm_via_aerea.png)
# 
# La figura de vía aérea repite el diagnóstico de las dos referencias del Laboratorio 1 y matiza el
# del LSTM. SES vuelve a ser una recta, aquí en 60,160 viajeros, y el SARIMA(2,1,2)(0,1,1)12 vuelve a
# quedarse muy por debajo, con una media de 20,639 y los 63 meses subestimados; ese es el modelo que
# el laboratorio anterior había elegido por AIC.
# 
# El LSTM directo acierta el nivel: promedia 85,409 viajeros contra 94,605 del test, un sesgo de
# −9.7 %, y en 2023-2025 se mueve dentro de la banda del test. Pero la curva es casi plana. Su CV es
# de 0.157 contra 0.244 del test, de modo que comprime a menos de dos tercios la amplitud real, y de
# ahí sale su correlación de −0.150: gana en MAE y RMSE por tener el nivel correcto, no por seguir la
# dinámica mes a mes. La figura señala además los dos tramos donde falla de forma visible, el pico de
# diciembre de 2022, que el test lleva a 158,463 viajeros, y el primer semestre de 2026, donde el
# modelo cae a 54,920 contra 107,307 reales.

# ## Comparación gráfica de las métricas
# 
# Barras agrupadas del mejor modelo de cada familia, por serie y por métrica. Las escalas de MAE y
# RMSE, en viajeros, no son comparables entre series de distinto volumen; el MAPE sí lo es, y por eso
# va en su propio panel.

# In[8]:


figura, ejes = plt.subplots(1, 3, figsize=(13, 4.2))
posiciones = np.arange(len(series))
ancho = 0.36

for eje, metrica in zip(ejes, METRICAS):
    for desplazamiento, familia in zip((-ancho / 2, ancho / 2), ("lab1", "lstm")):
        valores = [float(campeones[serie][familia][metrica]) for serie in series]
        barras = eje.bar(
            posiciones + desplazamiento,
            valores,
            ancho,
            label=familia,
            color=COLORES[familia],
        )
        formato = "%.1f" if metrica == "mape" else "%.0f"
        eje.bar_label(barras, fmt=formato, fontsize=7, padding=2)
    eje.set_xticks(posiciones, [SERIES[serie] for serie in series], fontsize=8)
    eje.set(
        title=metrica.upper(),
        ylabel="%" if metrica == "mape" else "Viajeros",
    )
    eje.margins(y=0.18)
    eje.legend(fontsize=8)

figura.suptitle("Mejor modelo de cada familia sobre los 63 meses de prueba")
figura.tight_layout()
figura.savefig(RUTA_FIGURAS / "comp_lstm_metricas.png", dpi=150)
plt.close(figura)


# ![Métricas por familia](../informe/figuras/comp_lstm_metricas.png)

# ## Resumen de las tres respuestas

# In[9]:


for serie in series:
    lstm = campeones[serie]["lstm"]
    lab1 = campeones[serie]["lab1"]
    fila = margen_lstm[margen_lstm["serie"].eq(serie)].iloc[0]
    ganador_global = comparativo[
        comparativo["serie"].eq(serie) & comparativo["mejor_global"]
    ].iloc[0]
    print(f"== {SERIES[serie]} ==")
    print(
        f"  mejor LSTM: {lstm['modelo']} (MAE {lstm['mae']:,.0f}, "
        f"RMSE {lstm['rmse']:,.0f}, MAPE {lstm['mape']:.2f} %), "
        f"por delante de {fila['pierde']} en {fila['margen_rmse_%']:.1f} % de RMSE"
    )
    print(
        f"  mejor Lab 1: {lab1['modelo']} (MAE {lab1['mae']:,.0f}, "
        f"RMSE {lab1['rmse']:,.0f}, MAPE {lab1['mape']:.2f} %)"
    )
    for metrica in METRICAS:
        cambio = mejoras[
            mejoras["serie"].eq(serie) & mejoras["metrica"].eq(metrica)
        ]["mejora_%"].iloc[0]
        signo = "reduce" if cambio > 0 else "aumenta"
        print(f"  {metrica.upper():5s}: el LSTM {signo} el error en {abs(cambio):.1f} %")
    print(f"  mejor global: {ganador_global['modelo']} ({ganador_global['familia']})\n")


# ### ¿Cuál predijo mejor?
# 
# El LSTM de estrategia directa, en las dos series. En total, con MAE de 76,957, RMSE de 100,290 y
# MAPE de 33.76 % sobre los 63 meses de prueba, por delante de la recursiva en 46.30 % de MAE y
# 39.11 % de RMSE. En vía aérea, con 22,635, 29,623 y 24.93 %, por delante en 28.46 % y 21.56 %. Es
# también el mejor modelo global de las dos series entre las dos familias, marcado como
# `mejor_global` en `comparativo_lstm_lab1.csv`.
# 
# ### ¿Son mejores que los del laboratorio pasado?
# 
# Sí, en las dos series y en las tres métricas. En la serie total el margen no admite discusión:
# 56.05 % menos MAE y 48.51 % menos RMSE que SES, el mejor de los cinco modelos del Laboratorio 1, y
# es el primer modelo de esa serie, en las dos entregas, que baja del 50 % de MAPE. En vía aérea el
# margen es más estrecho, 37.31 % y 28.39 %, del mismo orden que la distancia que separaba a SES de
# Holt-Winters en el laboratorio anterior.
# 
# Conviene decir por qué, porque el resultado no se explica solo por la capacidad del modelo. El
# Laboratorio 1 documentó que el entrenamiento termina en marzo de 2021, con la pandemia dominando el
# nivel final, y que SES ganó seis de siete series justamente por no extrapolar. Los métodos de
# suavizamiento y ARIMA anclan el pronóstico en las últimas observaciones; el LSTM, en cambio,
# aprende un patrón sobre ventanas de 24 meses que en su mayoría provienen del periodo prepandemia, y
# al pronosticar reconstruye ese patrón en lugar de prolongar el último nivel. Sobre un test que
# efectivamente vuelve a niveles prepandemia, esa forma de equivocarse resulta ser la correcta.
# 
# Con una reserva que las métricas agregadas no muestran. En vía aérea el modelo ganador tiene
# correlación −0.150 con el test: acierta el nivel medio y comprime la amplitud, de modo que gana por
# cancelación de errores y no por reproducir la dinámica. En total la correlación es de 0.249,
# positiva pero baja. Ninguno de los dos sigue el movimiento mes a mes.
# 
# ### ¿Cómo se determinó?
# 
# Con MAE, RMSE y MAPE sobre los mismos 63 meses de prueba, de abril de 2021 a junio de 2026,
# calculados con la misma función `src.evaluacion.metricas` que se usó en el Laboratorio 1 y sin que
# ninguna de las dos familias haya visto ese tramo durante el ajuste. El ganador de cada serie es el
# de menor suma de los rangos de MAE y RMSE.
# 
# No se usan AIC ni BIC. No existen para una red neuronal, que no tiene verosimilitud definida, y
# tampoco serían comparables entre familias: el Laboratorio 1 ya mostró que el SARIMA de menor AIC de
# una rejilla puede ser el peor pronosticador de esa misma serie a 63 pasos.
