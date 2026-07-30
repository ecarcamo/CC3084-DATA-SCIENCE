"""Modelado LSTM de las series mensuales de viajeros.

El horizonte de 63 meses se cubre con dos estrategias: recursiva, con un modelo
de un paso realimentado, y directa, con una salida `Dense(63)`. El error de
validación solo es comparable dentro de una misma estrategia; el contraste
entre ambas se hace sobre el conjunto de prueba.
"""

import itertools
import time

import keras
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

from src.evaluacion import metricas

VENTANA_DEFECTO = 12
HORIZONTE = 63
SEMILLA = 42
FRACCION_VALIDACION = 0.15
EPOCAS_MAXIMAS = 300
PACIENCIA = 20

ESTRATEGIAS = ("recursivo", "directo")

REJILLA_DEFECTOS = {
    "ventana": [VENTANA_DEFECTO],
    "unidades": [32],
    "capas": [1],
    "dropout": [0.0],
    "learning_rate": [1e-3],
    "batch_size": [16],
}


def fijar_semilla(semilla: int = SEMILLA) -> None:
    keras.utils.set_random_seed(semilla)
    tf.config.experimental.enable_op_determinism()


def escalar_train(serie_train: pd.Series) -> tuple[np.ndarray, MinMaxScaler]:
    valores_log = np.log1p(serie_train.to_numpy(dtype=float)).reshape(-1, 1)
    escalador = MinMaxScaler()
    escalado = escalador.fit_transform(valores_log)
    return escalado.ravel(), escalador


def _revertir(valores: np.ndarray, escalador: MinMaxScaler) -> np.ndarray:
    plano = np.asarray(valores, dtype=float).reshape(-1, 1)
    return np.expm1(escalador.inverse_transform(plano).ravel()).clip(min=0)


def crear_ventanas(
    valores: np.ndarray,
    ventana: int,
    horizonte_salida: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    serie = np.asarray(valores, dtype=float).ravel()
    n = len(serie) - ventana - horizonte_salida + 1
    if n <= 0:
        raise ValueError(
            "La serie es demasiado corta para la ventana y el horizonte pedidos"
        )

    X = np.empty((n, ventana, 1), dtype=float)
    y = np.empty((n, horizonte_salida), dtype=float)
    for i in range(n):
        X[i, :, 0] = serie[i : i + ventana]
        y[i] = serie[i + ventana : i + ventana + horizonte_salida]
    return X, y


def particionar_validacion(
    X: np.ndarray,
    y: np.ndarray,
    fraccion: float = FRACCION_VALIDACION,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    corte = max(1, int(round(len(X) * fraccion)))
    if corte >= len(X):
        raise ValueError("La fracción de validación no deja ventanas de ajuste")
    return X[:-corte], y[:-corte], X[-corte:], y[-corte:]


def construir_lstm(
    ventana: int,
    unidades: int,
    capas: int,
    dropout: float,
    horizonte_salida: int,
    learning_rate: float,
) -> keras.Model:
    modelo = keras.Sequential([keras.layers.Input(shape=(ventana, 1))])
    for indice in range(capas):
        modelo.add(
            keras.layers.LSTM(unidades, return_sequences=indice < capas - 1)
        )
        if dropout > 0:
            modelo.add(keras.layers.Dropout(dropout))
    modelo.add(keras.layers.Dense(horizonte_salida))
    modelo.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=["mae"],
    )
    return modelo


def entrenar(
    modelo,
    X,
    y,
    X_val,
    y_val,
    epocas: int = EPOCAS_MAXIMAS,
    batch_size: int = 16,
    paciencia: int = PACIENCIA,
):
    parada = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=paciencia,
        restore_best_weights=True,
    )
    return modelo.fit(
        X,
        y,
        validation_data=(X_val, y_val),
        epochs=epocas,
        batch_size=batch_size,
        callbacks=[parada],
        shuffle=False,
        verbose=0,
    )


def pronostico_recursivo(
    modelo,
    contexto: np.ndarray,
    escalador: MinMaxScaler,
    horizonte: int = HORIZONTE,
) -> np.ndarray:
    historia = np.asarray(contexto, dtype=float).ravel().copy()
    ventana = len(historia)
    predicciones = np.empty(horizonte, dtype=float)
    for paso in range(horizonte):
        entrada = historia[-ventana:].reshape(1, ventana, 1)
        siguiente = float(modelo.predict(entrada, verbose=0)[0, 0])
        predicciones[paso] = siguiente
        historia = np.append(historia, siguiente)
    return _revertir(predicciones, escalador)


def pronostico_directo(
    modelo,
    contexto: np.ndarray,
    escalador: MinMaxScaler,
) -> np.ndarray:
    historia = np.asarray(contexto, dtype=float).ravel()
    entrada = historia.reshape(1, len(historia), 1)
    return _revertir(modelo.predict(entrada, verbose=0).ravel(), escalador)


def _error_validacion(
    modelo,
    serie_train: pd.Series,
    escalado: np.ndarray,
    escalador: MinMaxScaler,
    estrategia: str,
    ventana: int,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> tuple[float, float]:
    if estrategia == "recursivo":
        pasos = len(y_val)
        contexto = escalado[-(pasos + ventana) : -pasos]
        prediccion = pronostico_recursivo(modelo, contexto, escalador, pasos)
        real = serie_train.to_numpy(dtype=float)[-pasos:]
    else:
        prediccion = _revertir(
            modelo.predict(X_val, verbose=0).ravel(), escalador
        )
        real = _revertir(y_val.ravel(), escalador)

    resultado = metricas(real, prediccion)
    return float(resultado["mae"]), float(resultado["rmse"])


def grid_lstm(
    serie_train: pd.Series,
    estrategia: str,
    rejilla: dict,
    horizonte: int = HORIZONTE,
) -> pd.DataFrame:
    if estrategia not in ESTRATEGIAS:
        raise ValueError(f"Estrategia desconocida: {estrategia}")
    desconocidas = set(rejilla) - set(REJILLA_DEFECTOS)
    if desconocidas:
        raise ValueError(f"Hiperparámetros desconocidos: {sorted(desconocidas)}")

    horizonte_salida = 1 if estrategia == "recursivo" else horizonte
    escalado, escalador = escalar_train(serie_train)
    parametros = [
        rejilla.get(clave, REJILLA_DEFECTOS[clave]) for clave in REJILLA_DEFECTOS
    ]
    resultados = []

    for combinacion in itertools.product(*parametros):
        ventana, unidades, capas, dropout, learning_rate, batch_size = combinacion
        # Sin limpiar la sesión, los grafos de las 16 combinaciones se acumulan
        # y el tiempo por ajuste crece a lo largo de la rejilla.
        keras.backend.clear_session()
        fijar_semilla()
        fila = {
            "estrategia": estrategia,
            "ventana": ventana,
            "unidades": unidades,
            "capas": capas,
            "dropout": dropout,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
        }
        inicio = time.perf_counter()
        try:
            X, y = crear_ventanas(escalado, ventana, horizonte_salida)
            X_ajuste, y_ajuste, X_val, y_val = particionar_validacion(X, y)
            modelo = construir_lstm(
                ventana,
                unidades,
                capas,
                dropout,
                horizonte_salida,
                learning_rate,
            )
            historial = entrenar(
                modelo,
                X_ajuste,
                y_ajuste,
                X_val,
                y_val,
                batch_size=batch_size,
            )
            mae_val, rmse_val = _error_validacion(
                modelo,
                serie_train,
                escalado,
                escalador,
                estrategia,
                ventana,
                X_val,
                y_val,
            )
            fila.update(
                {
                    "epocas_efectivas": len(historial.history["loss"]),
                    "n_parametros": int(modelo.count_params()),
                    "val_loss": float(min(historial.history["val_loss"])),
                    "mae_val": mae_val,
                    "rmse_val": rmse_val,
                }
            )
        except (ValueError, ArithmeticError, RuntimeError):
            fila.update(
                {
                    "epocas_efectivas": 0,
                    "n_parametros": 0,
                    "val_loss": float("inf"),
                    "mae_val": float("inf"),
                    "rmse_val": float("inf"),
                }
            )
        fila["tiempo_s"] = time.perf_counter() - inicio
        resultados.append(fila)

    # `rmse_val` se mide sobre los últimos meses del train en la estrategia
    # recursiva y sobre las ventanas de validación completas en la directa, de
    # modo que solo ordena configuraciones dentro de una misma estrategia.
    return (
        pd.DataFrame(resultados)
        .sort_values("rmse_val")
        .reset_index(drop=True)
    )


def seleccionar_lstm(rejilla: pd.DataFrame) -> pd.Series:
    finitas = rejilla[np.isfinite(rejilla["rmse_val"])]
    if len(finitas) == 0:
        return rejilla.sort_values("val_loss").iloc[0]
    return finitas.sort_values("rmse_val").iloc[0]


def ajustar_final(
    serie_train: pd.Series,
    configuracion: pd.Series,
    estrategia: str,
    horizonte: int = HORIZONTE,
) -> tuple[keras.Model, pd.Series]:
    if estrategia not in ESTRATEGIAS:
        raise ValueError(f"Estrategia desconocida: {estrategia}")

    horizonte_salida = 1 if estrategia == "recursivo" else horizonte
    ventana = int(configuracion["ventana"])
    epocas = max(1, int(configuracion["epocas_efectivas"]))

    keras.backend.clear_session()
    fijar_semilla()
    escalado, escalador = escalar_train(serie_train)
    X, y = crear_ventanas(escalado, ventana, horizonte_salida)
    modelo = construir_lstm(
        ventana,
        int(configuracion["unidades"]),
        int(configuracion["capas"]),
        float(configuracion["dropout"]),
        horizonte_salida,
        float(configuracion["learning_rate"]),
    )
    modelo.fit(
        X,
        y,
        epochs=epocas,
        batch_size=int(configuracion["batch_size"]),
        shuffle=False,
        verbose=0,
    )

    contexto = escalado[-ventana:]
    if estrategia == "recursivo":
        valores = pronostico_recursivo(modelo, contexto, escalador, horizonte)
    else:
        valores = pronostico_directo(modelo, contexto, escalador)

    indice = pd.date_range(
        serie_train.index[-1] + pd.offsets.MonthBegin(),
        periods=horizonte,
        freq="MS",
    )
    pronostico = pd.Series(valores, index=indice, name=f"lstm_{estrategia}")
    return modelo, pronostico
