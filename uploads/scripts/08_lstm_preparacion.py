#!/usr/bin/env python
# coding: utf-8

# # Preparación del modelado LSTM
# 
# Este cuaderno valida la infraestructura de `src/lstm.py` y sirve de plantilla para los cuadernos 09 y 10. Usa únicamente el conjunto de entrenamiento, de enero de 2009 a marzo de 2021, y no escribe nada en `resultados/`. El horizonte de pronóstico es el mismo del Laboratorio 1: los 63 meses de abril de 2021 a junio de 2026.

# In[1]:


from pathlib import Path
import sys

import numpy as np
import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.lstm import (
    HORIZONTE,
    SEMILLA,
    VENTANA_DEFECTO,
    ajustar_final,
    crear_ventanas,
    escalar_train,
    fijar_semilla,
    grid_lstm,
    particionar_validacion,
    seleccionar_lstm,
)
from src.utils import cargar_serie

fijar_semilla(SEMILLA)


# In[2]:


train = cargar_serie("total", "train")
test = cargar_serie("total", "test")

assert len(train) == 147
assert len(test) == HORIZONTE == 63

print(f"train: {len(train)} meses, de {train.index[0]:%Y-%m} a {train.index[-1]:%Y-%m}")
print(f"test:  {len(test)} meses, de {test.index[0]:%Y-%m} a {test.index[-1]:%Y-%m}")


# ## Escalado y ventaneo
# 
# `escalar_train` aplica `log1p` y luego un `MinMaxScaler` ajustado solo con entrenamiento. `crear_ventanas` recorre el vector escalado sin barajar: cada fila de `X` son `ventana` meses consecutivos y cada fila de `y` son los `horizonte_salida` meses siguientes. Con `horizonte_salida=1` el modelo es de un paso y el horizonte se cubre de forma recursiva; con `horizonte_salida=63` la salida es directa.

# In[3]:


escalado, escalador = escalar_train(train)
print(f"vector escalado: {escalado.shape}, rango [{escalado.min():.4f}, {escalado.max():.4f}]")

filas = []
for ventana in (12, 24):
    for estrategia, horizonte_salida in (("recursivo", 1), ("directo", HORIZONTE)):
        X, y = crear_ventanas(escalado, ventana, horizonte_salida)
        X_ajuste, y_ajuste, X_val, y_val = particionar_validacion(X, y)
        filas.append(
            {
                "estrategia": estrategia,
                "ventana": ventana,
                "X": str(X.shape),
                "y": str(y.shape),
                "X_val": str(X_val.shape),
                "y_val": str(y_val.shape),
                "ventanas": len(X),
                "validacion": len(X_val),
            }
        )

formas = pd.DataFrame(filas)
print(formas.to_string(index=False))


# Conteos de referencia, fijos mientras el train tenga 147 observaciones. Si un cuaderno posterior obtiene otros números, cambió el preprocesamiento y los resultados dejan de ser comparables.
# 
# | Estrategia | Ventana | Ventanas | Validación |
# |---|---:|---:|---:|
# | Recursivo | 12 | 135 | 20 |
# | Recursivo | 24 | 123 | 18 |
# | Directo | 12 | 73 | 11 |
# | Directo | 24 | 61 | 9 |
# 
# La estrategia directa entrena con la mitad de las ventanas porque cada observación consume 63 meses de salida además de la ventana de entrada.

# In[4]:


esperado = {
    ("recursivo", 12): (135, 20),
    ("recursivo", 24): (123, 18),
    ("directo", 12): (73, 11),
    ("directo", 24): (61, 9),
}
for _, fila in formas.iterrows():
    clave = (fila["estrategia"], fila["ventana"])
    assert (fila["ventanas"], fila["validacion"]) == esperado[clave], clave
print("conteos de ventanas y validación conformes")


# ## Ausencia de fuga de información
# 
# El escalador debe estar definido por el mínimo y el máximo de `log1p` del entrenamiento. Si hubiera visto el test, sus límites coincidirían con los del periodo completo y ningún valor del test caería fuera del intervalo [0, 1] al transformarse.

# In[5]:


limites = escalador.inverse_transform(np.array([[0.0], [1.0]])).ravel()
train_log = np.log1p(train.to_numpy(dtype=float))
test_log = np.log1p(test.to_numpy(dtype=float))

print(f"límites del escalador: [{limites[0]:.4f}, {limites[1]:.4f}]")
print(f"log1p del train:       [{train_log.min():.4f}, {train_log.max():.4f}]")
print(f"log1p del test:        [{test_log.min():.4f}, {test_log.max():.4f}]")

assert np.allclose(limites, [train_log.min(), train_log.max()])

test_escalado = escalador.transform(test_log.reshape(-1, 1)).ravel()
fuera = int(((test_escalado < 0) | (test_escalado > 1)).sum())
print(f"meses del test fuera del rango del escalador: {fuera} de {len(test)}")


# ## Prueba de la tubería completa
# 
# Rejilla mínima de dos combinaciones por estrategia, solo para comprobar que `grid_lstm`, `seleccionar_lstm` y `ajustar_final` encadenan bien. La rejilla de trabajo de los cuadernos 09 y 10 es la de dieciséis combinaciones acordada por el equipo.

# In[6]:


REJILLA_MINIMA = {
    "ventana": [VENTANA_DEFECTO],
    "unidades": [32, 64],
    "capas": [1],
    "dropout": [0.0],
}

rejillas = {
    estrategia: grid_lstm(train, estrategia, REJILLA_MINIMA)
    for estrategia in ("recursivo", "directo")
}

for estrategia, rejilla in rejillas.items():
    print(rejilla.drop(columns=["tiempo_s"]).to_string(index=False))
    print()


# `rmse_val` está en viajeros, pero no es comparable entre estrategias: en la recursiva mide un pronóstico de 20 pasos sobre los últimos meses del entrenamiento y en la directa mide once ventanas de 63 valores. Ordena configuraciones dentro de una estrategia; la comparación entre estrategias se resuelve hasta el test, con `src.evaluacion.metricas`.

# In[7]:


for estrategia, rejilla in rejillas.items():
    configuracion = seleccionar_lstm(rejilla)
    _, pronostico = ajustar_final(train, configuracion, estrategia)
    assert len(pronostico) == HORIZONTE
    assert pronostico.index[0] == pd.Timestamp("2021-04-01")
    assert pronostico.index[-1] == pd.Timestamp("2026-06-01")
    assert pronostico.notna().all()
    assert (pronostico >= 0).all()
    print(
        f"{estrategia}: unidades={int(configuracion['unidades'])}, "
        f"épocas={int(configuracion['epocas_efectivas'])}, "
        f"pronóstico de {len(pronostico)} meses entre "
        f"{pronostico.min():,.0f} y {pronostico.max():,.0f} viajeros"
    )


# ## Protocolo fijado
# 
# | Elemento | Decisión |
# |---|---|
# | Series | `total` y `via_aerea` |
# | Partición | La del Laboratorio 1: train 2009-01 a 2021-03 (147 meses), test 2021-04 a 2026-06 (63 meses) |
# | Escalado | `log1p` y `MinMaxScaler` ajustado solo con train; se revierte con `inverse_transform`, `expm1` y recorte en cero |
# | Ventanas | 12 y 24 meses, sin barajar |
# | Validación | Último 15 % de las ventanas, en orden temporal, nunca el test |
# | Estrategias | Recursiva de un paso y directa `Dense(63)` |
# | Criterio de selección | Menor `rmse_val` en viajeros dentro de cada estrategia; ante empate por valores no finitos, menor `val_loss` |
# | Entrenamiento | Adam, `mse`, hasta 300 épocas con `EarlyStopping` de paciencia 20 y `restore_best_weights` |
# | Ajuste final | Reentrenamiento sobre las 147 observaciones con las épocas efectivas de la configuración ganadora |
# | Reproducibilidad | `keras.utils.set_random_seed(42)` y determinismo de operaciones antes de cada ajuste |
# 
# Dos ejecuciones seguidas de este cuaderno devuelven los mismos números.
