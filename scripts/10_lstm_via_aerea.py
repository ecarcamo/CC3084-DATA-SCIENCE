#!/usr/bin/env python
# coding: utf-8

# # 10. LSTM de la serie vía aérea
# 
# Tuneo, ajuste final y evaluación de redes LSTM sobre la serie de viajeros por vía aérea, con el
# mismo split del Laboratorio 1: entrenamiento de enero de 2009 a marzo de 2021 y prueba de abril de
# 2021 a junio de 2026. El protocolo, el escalado y el criterio de validación están documentados en
# `informe/secciones_lab2/01_metodologia_lstm.md` y verificados en
# `notebooks/08_lstm_preparacion.ipynb`. Este cuaderno replica `notebooks/09_lstm_total.ipynb`
# cambiando la serie objetivo.
# 
# El horizonte de 63 meses se cubre con dos estrategias, recursiva y directa, y las dos se tunean
# por separado sobre la misma rejilla. El conjunto de prueba no interviene en el tuneo: solo aparece
# en la evaluación final, después de que las configuraciones ganadoras ya están fijadas.
# 
# Este cuaderno produce `resultados/lstm_tuneo_via_aerea.csv`,
# `resultados/metricas_lstm_via_aerea.csv`, las dos predicciones en `resultados/predicciones/` y las
# tres figuras `lstm_*_via_aerea.png`.

# In[1]:


from pathlib import Path
import sys

import keras
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.evaluacion import metricas
from src.lstm import (
    HORIZONTE,
    ajustar_final,
    construir_lstm,
    crear_ventanas,
    entrenar,
    escalar_train,
    fijar_semilla,
    grid_lstm,
    particionar_validacion,
    seleccionar_lstm,
)
from src.utils import RUTA_FIGURAS, RUTA_RESULTADOS, SERIES, cargar_serie

CLAVE = "via_aerea"
RUTA_PREDICCIONES = RUTA_RESULTADOS / "predicciones"
ESTRATEGIAS = ("recursivo", "directo")
COLORES = {"recursivo": "tab:orange", "directo": "tab:green"}

fijar_semilla()


# ## Datos
# 
# La serie llega de `data/processed/series/`, tal como la dejó el Laboratorio 1. Las aserciones
# fijan las longitudes: si alguna cambia, los resultados dejan de ser comparables con los del
# laboratorio anterior y el cuaderno falla en lugar de producir cifras engañosas.

# In[2]:


train = cargar_serie(CLAVE, "train")
test = cargar_serie(CLAVE, "test")

assert len(train) == 147
assert len(test) == HORIZONTE == 63
assert train.index[-1] < test.index[0]

print(f"serie: {SERIES[CLAVE]}")
print(f"train: {len(train)} meses, de {train.index[0]:%Y-%m} a {train.index[-1]:%Y-%m}")
print(f"test:  {len(test)} meses, de {test.index[0]:%Y-%m} a {test.index[-1]:%Y-%m}")
print(f"train: media {train.mean():,.0f}, ultimo mes {train.iloc[-1]:,.0f} viajeros")
print(f"test:  media {test.mean():,.0f}, ultimo mes {test.iloc[-1]:,.0f} viajeros")


# ## Rejilla de hiperparámetros
# 
# Ventana de 12 o 24 meses, uno o dos ciclos estacionales completos; 32 o 64 unidades por capa; una
# o dos capas LSTM; dropout de 0.0 o 0.2. La tasa de aprendizaje y el tamaño de lote quedan fijos en
# 1e-3 y 16 porque la muestra es de 147 observaciones y ampliar la rejilla en esas dos dimensiones
# multiplicaría el costo sin margen real de mejora. Misma rejilla que en la serie total, para que las
# dos series sean comparables en el cuaderno 11.
# 
# Son 16 combinaciones por estrategia y 32 ajustes en total, muy por encima de las dos
# configuraciones distintas que pide el enunciado.

# In[3]:


REJILLA = {
    "ventana": [12, 24],
    "unidades": [32, 64],
    "capas": [1, 2],
    "dropout": [0.0, 0.2],
    "learning_rate": [1e-3],
    "batch_size": [16],
}

combinaciones = np.prod([len(valores) for valores in REJILLA.values()])
print(f"{combinaciones} combinaciones por estrategia, {2 * combinaciones} ajustes en total")


# In[4]:


tuneo_recursivo = grid_lstm(train, "recursivo", REJILLA)
tuneo_directo = grid_lstm(train, "directo", REJILLA)

tuneo = pd.concat([tuneo_recursivo, tuneo_directo], ignore_index=True)
tuneo.insert(0, "serie", CLAVE)
tuneo["seleccionado"] = False

mejores = {}
for estrategia in ESTRATEGIAS:
    ganadora = seleccionar_lstm(tuneo[tuneo["estrategia"] == estrategia])
    tuneo.loc[ganadora.name, "seleccionado"] = True
    mejores[estrategia] = tuneo.loc[ganadora.name]

tuneo.to_csv(RUTA_RESULTADOS / f"lstm_tuneo_{CLAVE}.csv", index=False)
print(f"costo total de la rejilla: {tuneo['tiempo_s'].sum() / 60:.1f} minutos")
print(f"ajuste mas lento: {tuneo['tiempo_s'].max():.1f} s, mas rapido: {tuneo['tiempo_s'].min():.1f} s")
print(f"combinaciones fallidas: {int((~np.isfinite(tuneo['rmse_val'])).sum())}")
tuneo.head(4)


# La rejilla completa cuesta 2.4 minutos de CPU, entre 3.2 y 9.3 segundos por ajuste. Ninguna
# de las 32 combinaciones falló ni devolvió un error infinito: las 32 entrenaron, pararon por
# `EarlyStopping` y produjeron un pronóstico finito.

# ## Configuraciones ganadoras
# 
# | Estrategia | Ventana | Unidades | Capas | Dropout | Épocas | Parámetros | RMSE val. |
# |---|---:|---:|---:|---:|---:|---:|---:|
# | Recursiva | 12 | 32 | 1 | 0.0 | 26 | 4,385 | 45,464 |
# | Directa | 24 | 32 | 2 | 0.0 | 49 | 14,751 | 38,698 |
# 
# Las dos coinciden en 32 unidades y dropout 0.0, y se separan en ventana y profundidad: la recursiva
# prefiere la ventana corta de 12 meses con una sola capa, y la directa la ventana larga de 24 meses
# con dos capas. A diferencia de la serie total, aquí ninguna de las dos estrategias eligió la
# configuración más grande de la rejilla (64 unidades, dropout 0.2): la vía aérea es una serie más
# regular y no necesita esa capacidad extra.
# 
# Dentro de cada estrategia la brecha entre la mejor y la peor configuración es amplia: 50.6 % en la
# recursiva, de 45,464 a 68,450 viajeros, y 33.5 % en la directa, de 38,698 a 51,648. La elección de
# hiperparámetros vuelve a importar más en la estrategia que realimenta su propio error.

# In[5]:


columnas = [
    "estrategia",
    "ventana",
    "unidades",
    "capas",
    "dropout",
    "epocas_efectivas",
    "n_parametros",
    "val_loss",
    "mae_val",
    "rmse_val",
    "tiempo_s",
]
print("Mejor configuracion por estrategia")
print(tuneo[tuneo["seleccionado"]][columnas].to_string(index=False))

print("\nPeor configuracion por estrategia")
peores = tuneo.sort_values("rmse_val").groupby("estrategia").tail(1)
print(peores[columnas].to_string(index=False))


# ### Las dos arquitecturas de referencia
# 
# El enunciado pide al menos dos modelos con configuraciones diferentes. La rejilla contiene 16 por
# estrategia, y estas dos delimitan el rango: la LSTM de una capa con 32 unidades y sin dropout, la
# más pequeña con 4,385 parámetros, y la apilada de dos capas con 64 unidades y dropout 0.2, la más
# grande con 49,985.
# 
# Aquí el resultado no es monótono como en la serie total. En la estrategia recursiva la arquitectura
# pequeña gana con ventana de 12 meses (45,464 contra 58,576, un 28.8 % mejor) pero pierde con ventana
# de 24 (68,450 contra 50,901, un 34.5 % peor): el efecto de la capacidad depende de cuánta historia
# ve la red, no solo de su tamaño. En la estrategia directa la pequeña gana en ambas ventanas, aunque
# por márgenes moderados: 8.1 % con ventana de 12 y 3.1 % con ventana de 24. Para esta serie, más
# parámetros no compran mejor validación de forma consistente.

# In[6]:


referencia_pequena = (tuneo["unidades"] == 32) & (tuneo["capas"] == 1) & (tuneo["dropout"] == 0.0)
referencia_grande = (tuneo["unidades"] == 64) & (tuneo["capas"] == 2) & (tuneo["dropout"] == 0.2)
referencias = tuneo[referencia_pequena | referencia_grande].sort_values(
    ["estrategia", "rmse_val"]
)
print(referencias[columnas].to_string(index=False))


# ## Qué hiperparámetro mueve el error
# 
# En la estrategia recursiva el factor dominante es el número de capas: la mediana de `rmse_val` baja
# de 56,641 con una capa a 49,337 con dos, una brecha de 14.8 %. Le siguen el dropout, 4.6 % a favor
# de 0.0, y la ventana, 4.2 % a favor de 12 meses; el número de unidades es casi irrelevante, 2.3 %.
# La lectura es la opuesta a la de la serie total: aquí una segunda capa recurrente ayuda más que
# ensanchar la primera.
# 
# En la estrategia directa manda el dropout, 7.4 % a favor de 0.0, seguido de las capas (3.3 % a favor
# de una sola) y la ventana y las unidades, ambas por debajo del 2 %. La regularización explícita no
# aporta en una serie que ya es menos volátil (CV de 0.216 según el Laboratorio 1): con 147
# observaciones y una serie estable, el dropout resta capacidad sin compensarla con menos sobreajuste.

# In[7]:


filas = []
for hiperparametro in ("ventana", "unidades", "capas", "dropout"):
    for estrategia in ESTRATEGIAS:
        subconjunto = tuneo[tuneo["estrategia"] == estrategia]
        agregado = subconjunto.groupby(hiperparametro)["rmse_val"].median()
        filas.append(
            {
                "estrategia": estrategia,
                "hiperparametro": hiperparametro,
                "valor_bajo": agregado.index[0],
                "rmse_val_bajo": agregado.iloc[0],
                "valor_alto": agregado.index[-1],
                "rmse_val_alto": agregado.iloc[-1],
                "brecha_%": 100 * abs(agregado.iloc[-1] - agregado.iloc[0]) / agregado.min(),
            }
        )

sensibilidad = pd.DataFrame(filas).sort_values(
    ["estrategia", "brecha_%"], ascending=[True, False]
)
print(sensibilidad.to_string(index=False))


# In[8]:


destacadas = (
    tuneo.sort_values("rmse_val").groupby("estrategia").head(5).sort_values("rmse_val")
)
etiquetas = [
    f"v{fila.ventana} u{fila.unidades} c{fila.capas} d{fila.dropout:.1f}"
    for fila in destacadas.itertuples()
]

figura, eje = plt.subplots(figsize=(9, 5))
posiciones = np.arange(len(destacadas))
eje.barh(
    posiciones,
    destacadas["rmse_val"],
    color=[COLORES[e] for e in destacadas["estrategia"]],
)
eje.set_yticks(posiciones, etiquetas, fontsize=8)
eje.invert_yaxis()
eje.set(
    title=f"Tuneo LSTM: cinco mejores configuraciones por estrategia ({SERIES[CLAVE]})",
    xlabel="RMSE de validacion (viajeros)",
)
eje.legend(
    handles=[
        plt.Line2D([], [], color=COLORES[e], linewidth=8, label=e) for e in ESTRATEGIAS
    ],
    fontsize=8,
)
for posicion, valor in zip(posiciones, destacadas["rmse_val"]):
    eje.text(valor, posicion, f" {valor:,.0f}", va="center", fontsize=7)
figura.tight_layout()
figura.savefig(RUTA_FIGURAS / f"lstm_tuneo_{CLAVE}.png", dpi=150)
plt.close(figura)
print(destacadas[columnas].to_string(index=False))


# La figura muestra las cinco mejores configuraciones de cada estrategia y no las diez mejores del
# conjunto, porque `rmse_val` no es comparable entre estrategias: la recursiva se valida sobre veinte
# meses consecutivos y la directa sobre once ventanas de 63 valores. Un ranking global mezclaría dos
# escalas distintas y sugeriría una conclusión que el tuneo no sostiene.
# 
# ![Tuneo LSTM de la vía aérea](../informe/figuras/lstm_tuneo_via_aerea.png)

# ## Curvas de entrenamiento
# 
# `ajustar_final` no guarda historial porque reentrena sin partición de validación. Para graficar las
# curvas se repite el ajuste de la configuración ganadora en las mismas condiciones del tuneo, con la
# misma semilla; la aserción comprueba que el número de épocas coincide con el registrado en la
# rejilla, lo que confirma de paso que la ejecución es reproducible.

# In[9]:


curvas = {}
for estrategia, configuracion in mejores.items():
    horizonte_salida = 1 if estrategia == "recursivo" else HORIZONTE
    ventana = int(configuracion["ventana"])
    keras.backend.clear_session()
    fijar_semilla()
    escalado, _ = escalar_train(train)
    X, y = crear_ventanas(escalado, ventana, horizonte_salida)
    X_ajuste, y_ajuste, X_val, y_val = particionar_validacion(X, y)
    modelo = construir_lstm(
        ventana,
        int(configuracion["unidades"]),
        int(configuracion["capas"]),
        float(configuracion["dropout"]),
        horizonte_salida,
        float(configuracion["learning_rate"]),
    )
    historial = entrenar(
        modelo,
        X_ajuste,
        y_ajuste,
        X_val,
        y_val,
        batch_size=int(configuracion["batch_size"]),
    )
    curvas[estrategia] = historial.history
    print(
        f"{estrategia}: {len(historial.history['loss'])} epocas reproducidas, "
        f"{int(configuracion['epocas_efectivas'])} registradas en la rejilla, "
        f"val_loss minimo {min(historial.history['val_loss']):.5f}"
    )
    assert len(historial.history["loss"]) == int(configuracion["epocas_efectivas"])


# In[10]:


figura, ejes = plt.subplots(1, 2, figsize=(12, 4.5))
for eje, estrategia in zip(ejes, ESTRATEGIAS):
    historia = curvas[estrategia]
    eje.plot(historia["loss"], label="Entrenamiento", color="black", linewidth=1)
    eje.plot(historia["val_loss"], label="Validacion", color=COLORES[estrategia], linewidth=1.5)
    mejor_epoca = int(np.argmin(historia["val_loss"]))
    eje.axvline(mejor_epoca, color="gray", linestyle="--", linewidth=0.8)
    configuracion = mejores[estrategia]
    eje.set(
        title=(
            f"{estrategia}: v{int(configuracion['ventana'])} "
            f"u{int(configuracion['unidades'])} c{int(configuracion['capas'])} "
            f"d{configuracion['dropout']:.1f}"
        ),
        xlabel="Epoca",
        ylabel="MSE (escala normalizada)",
        yscale="log",
    )
    eje.legend(fontsize=8)
figura.suptitle(f"Curvas de perdida del mejor modelo por estrategia ({SERIES[CLAVE]})")
figura.tight_layout()
figura.savefig(RUTA_FIGURAS / f"lstm_curvas_{CLAVE}.png", dpi=150)
plt.close(figura)


# Las dos curvas muestran un patrón de sobreentrenamiento claro, aunque en escalas distintas.
# 
# En la recursiva la pérdida de validación toca su mínimo en la época 6 y luego se queda plana
# alrededor de 0.137, mientras la de entrenamiento sigue bajando hasta 0.0006. Las 20 épocas
# restantes hasta la 26 son la paciencia del `EarlyStopping`, no aprendizaje real. El patrón se repite
# en toda la rejilla: las 16 combinaciones recursivas paran entre las épocas 21 y 26, así que la mejor
# época real está siempre en el primer tramo del entrenamiento.
# 
# En la directa la validación baja durante unas 28 épocas hasta 0.059 y ahí se estabiliza, mientras el
# entrenamiento continúa hasta 0.0025; las épocas efectivas en la rejilla van de 29 a 59, un rango más
# amplio que en la recursiva, señal de que la estrategia directa sí aprovecha más iteraciones antes de
# sobreajustar.
# 
# ![Curvas de pérdida LSTM, vía aérea](../informe/figuras/lstm_curvas_via_aerea.png)

# ## Ajuste final y predicción
# 
# Cada configuración ganadora se reentrena sobre las 147 observaciones completas, sin partición de
# validación, fijando las épocas en las efectivas del tuneo. Ese modelo produce los 63 meses de
# prueba. Las aserciones verifican longitud, ausencia de nulos, ausencia de negativos y que el índice
# coincida exactamente con el del test.

# In[11]:


predicciones = {}
for estrategia, configuracion in mejores.items():
    _, pronostico = ajustar_final(train, configuracion, estrategia)
    assert len(pronostico) == HORIZONTE
    assert pronostico.notna().all()
    assert (pronostico >= 0).all()
    assert (pronostico.index == test.index).all()
    predicciones[f"lstm_{estrategia}"] = pronostico
    salida = pd.DataFrame(
        {
            "fecha": pronostico.index.strftime("%Y-%m-%d"),
            "prediccion": pronostico.to_numpy(dtype=float),
        }
    )
    salida.to_csv(RUTA_PREDICCIONES / f"{CLAVE}_lstm_{estrategia}.csv", index=False)
    print(
        f"lstm_{estrategia}: {len(salida)} filas, "
        f"media {pronostico.mean():,.0f}, minimo {pronostico.min():,.0f}, "
        f"maximo {pronostico.max():,.0f} viajeros"
    )

print(f"\ntest real: media {test.mean():,.0f}, minimo {test.min():,.0f}, maximo {test.max():,.0f}")


# El primer contraste ya distingue a las dos estrategias. La recursiva pronostica una media de
# 63,494 viajeros mensuales frente a 94,605 reales, subestimando 59 de los 63 meses, con un sesgo
# medio de −31,110 viajeros (−32.9 % del nivel medio del test) y una correlación de apenas 0.391 con
# la serie real. La directa promedia 85,409, subestima 34 de 63 meses, y su sesgo se reduce a −9,196
# (−9.7 %), pero su correlación con el test es de −0.150: en términos agregados el nivel se acerca
# mucho más al real, pero mes a mes la dirección del movimiento no coincide.

# ## Métricas sobre el test
# 
# Las métricas salen de `src.evaluacion.metricas`, la misma función del Laboratorio 1, sobre los
# mismos 63 meses. `mejor` marca la estrategia ganadora con el criterio del Laboratorio 1: menor suma
# de los rangos de MAE y RMSE.

# In[12]:


filas = []
for nombre, prediccion in predicciones.items():
    configuracion = mejores[nombre.removeprefix("lstm_")]
    filas.append(
        {
            "serie": CLAVE,
            "modelo": nombre,
            "ventana": int(configuracion["ventana"]),
            "unidades": int(configuracion["unidades"]),
            "capas": int(configuracion["capas"]),
            "dropout": float(configuracion["dropout"]),
            **metricas(test, prediccion),
            "mejor": False,
        }
    )

metricas_lstm = pd.DataFrame(filas)
puntaje = metricas_lstm["mae"].rank() + metricas_lstm["rmse"].rank()
metricas_lstm.loc[puntaje.idxmin(), "mejor"] = True
metricas_lstm.to_csv(RUTA_RESULTADOS / f"metricas_lstm_{CLAVE}.csv", index=False)
print(metricas_lstm.to_string(index=False))


# | Modelo | MAE | RMSE | MAPE |
# |---|---:|---:|---:|
# | lstm_recursivo | 31,638 | 37,766 | 31.14 % |
# | lstm_directo | **22,635** | **29,623** | **24.93 %** |
# 
# La estrategia directa gana en las tres métricas: 28.5 % menos MAE, 21.6 % menos RMSE y 6.21 puntos
# porcentuales menos de MAPE. La brecha es más chica que en la serie total, porque la recursiva ya
# parte de un sesgo menor en esta serie más estable, pero el orden es el mismo: la salida completa en
# una sola pasada evita la acumulación de error que castiga a la recursiva a lo largo de 63 pasos.
# 
# El sesgo agregado confirma la historia: −32.9 % en la recursiva contra −9.7 % en la directa. Pero la
# correlación negativa de la directa (−0.150, ver sección anterior) es la advertencia que las métricas
# de error no muestran por sí solas: el modelo gana en MAE y RMSE porque su nivel medio está cerca del
# real, no porque reproduzca la dinámica mes a mes.

# ## Contraste con el Laboratorio 1
# 
# El detalle completo, con las dos series y todos los modelos, está en
# `notebooks/11_comparativo_lstm.ipynb`. Aquí solo se ubica el resultado frente a la mejor referencia
# disponible para esta serie.

# In[13]:


metricas_lab1 = pd.read_csv(RUTA_RESULTADOS / "metricas_modelos.csv")
mejor_lab1 = metricas_lab1[
    metricas_lab1["serie"].eq(CLAVE) & metricas_lab1["mejor"]
].iloc[0]
mejor_lstm = metricas_lstm[metricas_lstm["mejor"]].iloc[0]

for metrica in ("mae", "rmse", "mape"):
    cambio = 100 * (mejor_lstm[metrica] - mejor_lab1[metrica]) / mejor_lab1[metrica]
    print(
        f"{metrica.upper():5s} {mejor_lstm['modelo']}: {mejor_lstm[metrica]:>12,.2f} | "
        f"{mejor_lab1['modelo']} (Lab 1): {mejor_lab1[metrica]:>12,.2f} | "
        f"cambio {cambio:+.1f} %"
    )


# El LSTM directo reduce el MAE del mejor modelo del Laboratorio 1 (SES) en 37.3 %, el RMSE en
# 28.4 % y el MAPE en 10.68 puntos porcentuales, de 35.62 % a 24.93 %. Es la primera vez en las dos
# entregas que un modelo de la vía aérea baja del 25 % de MAPE, y confirma la lectura del enunciado:
# esta serie ya era la mejor predicha del Laboratorio 1, y el LSTM directo la mejora todavía más en
# lugar de rendirse frente a una vara ya alta.

# ## Lectura de la predicción
# 
# ![Predicciones LSTM de la vía aérea](../informe/figuras/lstm_pred_via_aerea.png)

# In[14]:


figura, eje = plt.subplots(figsize=(12, 5))
eje.plot(train.index, train, label="Train", color="black", linewidth=1)
eje.plot(test.index, test, label="Test real", color="tab:blue", linewidth=2)
for nombre, prediccion in predicciones.items():
    eje.plot(
        prediccion.index,
        prediccion,
        label=nombre,
        color=COLORES[nombre.removeprefix("lstm_")],
        alpha=0.9,
    )
eje.set(
    title=f"Predicciones LSTM: {SERIES[CLAVE]}",
    xlabel="Fecha",
    ylabel="Viajeros",
)
eje.legend(ncol=3, fontsize=8)
figura.tight_layout()
figura.savefig(RUTA_FIGURAS / f"lstm_pred_{CLAVE}.png", dpi=150)
plt.close(figura)

resumen = pd.DataFrame(
    {
        "test_real": test.to_numpy(),
        **{nombre: prediccion.to_numpy() for nombre, prediccion in predicciones.items()},
    },
    index=test.index,
)
print(resumen.resample("YE").mean().to_string(float_format=lambda x: f"{x:,.0f}"))


# La tabla anual responde la pregunta de fondo: ¿reproduce el modelo la recuperación pospandemia
# de la vía aérea, la vía de recuperación más rápida del Laboratorio 1?
# 
# | Año | Test real | LSTM recursivo | LSTM directo |
# |---|---:|---:|---:|
# | 2021 | 65,700 | 37,905 | 82,331 |
# | 2022 | 117,232 | 56,206 | 85,084 |
# | 2023 | 82,153 | 66,793 | 89,985 |
# | 2024 | 95,279 | 71,494 | 96,849 |
# | 2025 | 99,081 | 73,403 | 87,270 |
# | 2026* | 107,307 | 74,041 | 54,920 |
# 
# \* 2026 solo cubre enero a junio.
# 
# La estrategia recursiva vuelve a fallar como en la serie total: una trayectoria monótona creciente
# que nunca despega de los 74,000 viajeros, muy por debajo del pico de 117,232 en 2022 y del nivel de
# 2026. Su correlación de 0.391 con el test viene de esa tendencia general al alza, no de acertar
# niveles.
# 
# La directa cuenta una historia más interesante. Sobreestima 2021 (82,331 contra 65,700, un 25.3 % de
# más, el año todavía deprimido), y desde ahí se acerca al nivel real en 2023 y 2024 (dentro de un
# 10 %), pero se aleja otra vez al final: subestima 2025 en 11.9 % y colapsa en el primer semestre de
# 2026, con 54,920 contra 107,307, un 48.8 % por debajo. Ese colapso final es lo que produce la
# correlación negativa pese al buen MAE agregado: el modelo aprendió un nivel medio razonable para el
# tramo intermedio de la serie, pero no anticipa que la recuperación siga acelerando hacia 2026. Dicho
# sin adjetivos: el LSTM directo bate a SES en las tres métricas de error, pero no porque entienda la
# trayectoria de la vía aérea, sino porque su error se cancela entre una sobreestimación temprana y
# una subestimación tardía.
