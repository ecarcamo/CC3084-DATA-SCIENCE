#!/usr/bin/env python
# coding: utf-8

# # 9. LSTM de la serie total
# 
# Tuneo, ajuste final y evaluación de redes LSTM sobre la serie total de viajeros, con el mismo
# split del Laboratorio 1: entrenamiento de enero de 2009 a marzo de 2021 y prueba de abril de 2021
# a junio de 2026. El protocolo, el escalado y el criterio de validación están documentados en
# `informe/secciones_lab2/01_metodologia_lstm.md` y verificados en
# `notebooks/08_lstm_preparacion.ipynb`.
# 
# El horizonte de 63 meses se cubre con dos estrategias, recursiva y directa, y las dos se tunean
# por separado sobre la misma rejilla. El conjunto de prueba no interviene en el tuneo: solo aparece
# en la evaluación final, después de que las configuraciones ganadoras ya están fijadas.
# 
# Este cuaderno produce `resultados/lstm_tuneo_total.csv`, `resultados/metricas_lstm_total.csv`, las
# dos predicciones en `resultados/predicciones/` y las tres figuras `lstm_*_total.png`.

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

CLAVE = "total"
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
# multiplicaría el costo sin margen real de mejora.
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


# La rejilla completa cuesta 1.9 minutos de CPU, entre 2.8 y 5.8 segundos por ajuste. Ninguna de
# las 32 combinaciones falló ni devolvió un error infinito: las 32 entrenaron, pararon por
# `EarlyStopping` y produjeron un pronóstico finito.

# ## Configuraciones ganadoras
# 
# | Estrategia | Ventana | Unidades | Capas | Dropout | Épocas | Parámetros | RMSE val. |
# |---|---:|---:|---:|---:|---:|---:|---:|
# | Recursiva | 24 | 64 | 1 | 0.2 | 24 | 16,961 | 149,716 |
# | Directa | 24 | 64 | 2 | 0.0 | 42 | 54,015 | 130,075 |
# 
# Las dos coinciden en la ventana de 24 meses y en 64 unidades, y se separan en la profundidad: la
# recursiva prefiere una capa con dropout y la directa dos capas sin él. El contraste entre estos
# dos valores de `rmse_val` no significa nada todavía, porque cada estrategia valida sobre un tramo
# distinto; la comparación real se hace sobre el test más abajo.
# 
# Dentro de cada estrategia la brecha entre la mejor y la peor configuración sí es informativa: 39.9 %
# en la recursiva, de 149,716 a 209,463 viajeros, y 15.3 % en la directa, de 130,075 a 149,939. La
# elección de hiperparámetros importa bastante más cuando el error se realimenta 63 veces.

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
# estrategia, y estas dos delimitan el rango: la LSTM de una capa con 32 unidades y sin dropout, que
# es la más pequeña con 4,385 parámetros en la recursiva, y la apilada de dos capas con 64 unidades
# y dropout 0.2, que es la más grande con 49,985.
# 
# En la estrategia recursiva la diferencia entre las dos es grande y va en la dirección esperada: con
# ventana de 24 meses, 187,605 contra 155,304 de RMSE de validación, un 17 % a favor de la
# arquitectura mayor. En la directa las dos quedan casi empatadas, 136,507 contra 132,213, un 3 %.
# La salida `Dense(63)` ya aporta la mayor parte de la capacidad del modelo y la profundidad
# recurrente agrega poco.

# In[6]:


referencia_pequena = (tuneo["unidades"] == 32) & (tuneo["capas"] == 1) & (tuneo["dropout"] == 0.0)
referencia_grande = (tuneo["unidades"] == 64) & (tuneo["capas"] == 2) & (tuneo["dropout"] == 0.2)
referencias = tuneo[referencia_pequena | referencia_grande].sort_values(
    ["estrategia", "rmse_val"]
)
print(referencias[columnas].to_string(index=False))


# ## Qué hiperparámetro mueve el error
# 
# La tabla compara la mediana de `rmse_val` entre los dos valores de cada hiperparámetro, dentro de
# cada estrategia. La mediana, y no el mínimo, para que un solo ajuste afortunado no defina la
# lectura.
# 
# En la estrategia recursiva el número de unidades es el factor dominante: la mediana pasa de 180,907
# con 32 unidades a 155,652 con 64, una brecha de 16.2 %. Le siguen el dropout, 12.1 % a favor de
# 0.2, y el número de capas, 11.7 % a favor de dos. Los tres apuntan al mismo lado: un modelo de un
# paso que va a realimentarse 63 veces necesita capacidad y regularización, porque cualquier sesgo
# sistemático se acumula a lo largo del horizonte.
# 
# En la estrategia directa el orden se invierte y las brechas se achican. Manda la ventana, 5.1 % a
# favor de 24 meses, y el resto queda por debajo del 3 %; el número de capas es prácticamente
# irrelevante, 0.8 %. Con la salida completa en una sola pasada, lo que importa es cuánta historia
# ve la red, no cuán profunda es.

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
# ![Tuneo LSTM de la serie total](../informe/figuras/lstm_tuneo_total.png)

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


# Las dos curvas cuentan historias distintas.
# 
# En la recursiva la pérdida de validación toca su mínimo en la época 4 y a partir de ahí se queda
# plana alrededor de 0.13, mientras la de entrenamiento sigue bajando hasta 0.006. Las 20 épocas que
# faltan hasta la 24 son la paciencia del `EarlyStopping`, no aprendizaje. El patrón se repite en
# toda la rejilla: las 16 combinaciones recursivas paran entre las épocas 21 y 25, es decir que su
# mejor época está entre la 1 y la 5. El modelo de un paso aprende casi todo lo que puede aprender en
# los primeros minutos y después solo memoriza el entrenamiento.
# 
# En la directa la validación baja durante unas doce épocas hasta 0.068 y se estabiliza; las épocas
# efectivas van de 28 a 78, con la mejor época entre la 8 y la 58. Hay algo más de aprendizaje real
# antes de que el sobreajuste tome el control.
# 
# ![Curvas de pérdida LSTM, serie total](../informe/figuras/lstm_curvas_total.png)

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


# El primer contraste ya es claro. La estrategia recursiva pronostica una media de 133,712 viajeros
# mensuales frente a 276,685 reales, y su recorrido completo, de 64,931 a 163,165, no llega ni al
# máximo del test. La directa promedia 232,356 y se mueve entre 171,712 y 304,305, un rango que sí se
# solapa con el real.

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
# | lstm_recursivo | 143,303 | 164,706 | 46.90 % |
# | lstm_directo | **76,957** | **100,290** | **33.76 %** |
# 
# La estrategia directa gana en las tres métricas y por un margen amplio: 46.3 % menos MAE, 39.1 %
# menos RMSE y 13.1 puntos porcentuales menos de MAPE. No es una diferencia discutible dentro del
# ruido de la semilla, es un cambio de orden de magnitud en la calidad del pronóstico.
# 
# La razón se ve en el sesgo. La recursiva subestima 62 de los 63 meses y su error medio es de
# −142,973 viajeros, un 51.7 % del nivel medio del test; la directa subestima 45 de 63 y su sesgo es
# de −44,329, un 16.0 %. Realimentar 63 veces un modelo entrenado con datos que terminan en el punto
# más bajo de la pandemia arrastra el pronóstico hacia ese nivel, y ni la ventana de 24 meses ni las
# 64 unidades lo evitan. La menor muestra de la estrategia directa, 61 ventanas contra 123, resultó
# un precio menor que el de la acumulación de error.

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


# El LSTM directo reduce el MAE del mejor modelo del Laboratorio 1 en 56.0 %, el RMSE en 48.5 % y el
# MAPE en 24.3 puntos porcentuales, de 58.11 % a 33.76 %. Es la primera vez en las dos entregas que
# un modelo de la serie total baja del 50 % de MAPE.

# ## Lectura de la predicción
# 
# ![Predicciones LSTM de la serie total](../informe/figuras/lstm_pred_total.png)

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


# La figura y la tabla anual responden la pregunta de fondo: ¿reproduce el modelo la recuperación
# pospandemia, o la subestima como hicieron todos los del Laboratorio 1?
# 
# La estrategia recursiva la subestima, y de la misma forma que los modelos anteriores. Su
# trayectoria es una curva monótona que sube de 64,931 a 163,165 viajeros y ahí se detiene, sin
# estacionalidad visible; su correlación con el test es de 0.507, de modo que acierta la dirección
# general pero nunca el nivel.
# 
# La estrategia directa sí reproduce la forma. Emite un perfil estacional con picos y valles, y su
# nivel medio queda a un 16 % del real en lugar del 62 % que le faltaba a SES. Pero acierta por
# tramos: sobreestima 2021, el año todavía deprimido, con 198,112 contra 110,282 reales, y subestima
# con claridad el rebote de 2022, con 213,867 contra 359,680, un 40.5 % por debajo. De 2023 en
# adelante el error se estabiliza entre el 12 % y el 13 % anual, y vuelve a abrirse en el tramo de
# 2026, con 188,390 contra 280,439.
# 
# Dicho de otro modo: el LSTM directo aprendió el nivel y la estacionalidad de la serie prepandemia y
# los proyectó sobre el horizonte, en lugar de prolongar el nivel deprimido de los últimos meses de
# entrenamiento. Eso lo acerca mucho más al test que cualquier modelo del Laboratorio 1, pero el pico
# de 2022 sigue fuera de su alcance, y con razón: no hay nada en las 147 observaciones de
# entrenamiento que anticipe una reapertura.
