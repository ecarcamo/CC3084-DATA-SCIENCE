def evaluate(series, config):
    """Evalúa el procedimiento y la referencia sobre los mismos meses ocultos.

    Entrada: `series` es la serie mensual de `prepare_series`; `config` es la configuración con rutas
    resueltas. Cada mes entre `periods.evaluation_start` y `periods.evaluation_end` se estima solo con
    información anterior a ese mes. Los meses sin valor observado no se evalúan.

    Salida: diccionario serializable en JSON con estas claves:
        procedure: {"name": str, "mae": float, "rmse": float, "mape_pct": float | None}
        baseline: {"name": str, "mae": float, "rmse": float, "mape_pct": float | None}
        evaluated_periods: lista de períodos `AAAA-MM` evaluados
        mape_zero_rule: texto que explica cómo se tratan los observados iguales a cero
    Se guarda como `metrics.json`.
    """
    raise NotImplementedError("evaluate pendiente: persona A")


def accept(checks, estimates, metrics, config):
    """Aplica la regla de aceptación de una versión candidata.

    Entrada: `checks` es la lista de `CheckResult` de `run_checks`; `estimates` es el DataFrame de
    `estimates.csv`; `metrics` es el resultado de `evaluate`; `config` contiene `acceptance`.

    Salida: {"accepted": bool, "reasons": [str, ...]}. `reasons` explica cada criterio incumplido y
    queda vacía cuando la versión se acepta.
    """
    raise NotImplementedError("accept pendiente: persona A")
