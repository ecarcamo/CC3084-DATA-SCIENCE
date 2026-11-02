def fit_and_forecast(series, config):
    """Ajusta el procedimiento configurado y estima los meses futuros.

    Entrada: `series` es la serie mensual de `prepare_series`, con `DatetimeIndex` de frecuencia `MS`
    y meses sin cobertura como `NaN`; `config` es la configuración con rutas resueltas. El ajuste usa
    los meses desde `periods.fit_start` hasta `periods.expected_last_period` y `model.seed`.

    Salida: DataFrame con las columnas `period` y `value`, una fila por mes entre
    `periods.forecast_start` y `periods.forecast_end`, en orden. `period` usa el formato `AAAA-MM` y
    `value` es un número finito. `run.py` completa las demás columnas de `outputs.estimate_columns`
    y asigna `kind="estimado"`.
    """
    raise NotImplementedError("fit_and_forecast pendiente: persona A")


def model_parameters(series, config):
    """Devuelve los parámetros necesarios para reproducir el ajuste.

    Entrada: las mismas `series` y `config` de `fit_and_forecast`.

    Salida: diccionario serializable en JSON con, como mínimo, `procedure`, `procedure_version`,
    `fit_start`, `fit_end`, `seed` y los parámetros ajustados del modelo. Se guarda en `run.json`
    bajo `model_parameters` y se registra en MLflow.
    """
    raise NotImplementedError("model_parameters pendiente: persona A")
