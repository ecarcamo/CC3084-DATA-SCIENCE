# Laboratorio 11: contratos entre etapas

Este documento fija las interfaces que permiten trabajar los puntos 4 a 8 en paralelo. Cada función pendiente existe como esqueleto con su contrato en el docstring y lanza `NotImplementedError` hasta que su responsable la implementa. Las pruebas de `tests/test_stage_contracts.py` verifican que los nombres y parámetros no cambien.

## Responsables y archivos

| Persona | Puntos | Archivos que edita |
|---|---|---|
| A | 5.1 a 5.5 | `pipeline/model.py`, `pipeline/evaluation.py` |
| B | 4.1 a 4.3 y 7.1 a 7.3 | `pipeline/tracking.py`, `pipeline/monitoring.py`, `pipeline/run.py` |
| C | 6.1 a 6.4 y 7.5 | `pipeline/publish.py`, `app/approved.py` y la lectura de la versión aprobada en `app/` |
| D | 7.4 y 8.1 a 8.4 | `Dockerfile`, `docker-compose.yml`, `README.md`, `docs/lab11/` |

Solo B edita `pipeline/run.py`. Si otra persona necesita cambiar el orden de etapas o los campos de `run.json`, lo solicita a B. Un cambio de firma se acuerda con el equipo y se refleja en este documento y en `tests/test_stage_contracts.py`.

## Firmas

```python
# pipeline/model.py, persona A
fit_and_forecast(series, config) -> DataFrame[period, value]
model_parameters(series, config) -> dict

# pipeline/evaluation.py, persona A
evaluate(series, config) -> dict
accept(checks, estimates, metrics, config) -> {"accepted": bool, "reasons": [str]}

# pipeline/tracking.py, persona B
log_run(metadata, config, artifacts_dir) -> str

# pipeline/monitoring.py, persona B
run_monitoring(series, estimates, previous_approved_dir, config) -> [CheckResult]

# pipeline/publish.py, persona C
publish(candidate_dir, config) -> str
latest_approved(config) -> Path | None
restore(version_id, config) -> str

# app/approved.py, persona C
load_approved(path=None) -> dict | None
```

## Entradas y salidas

- `series` es la salida de `prepare_series`: una serie con `DatetimeIndex` mensual de frecuencia `MS`. Los meses sin cobertura quedan como `NaN` y nunca como cero.
- `config` es la salida de `load_config`, con rutas absolutas ya resueltas.
- `checks` es la lista de `CheckResult` de `run_checks`. Cada resultado tiene `name`, `status`, `message` y `details`. `status` vale `ok`, `warning` o `stop`.
- `fit_and_forecast` devuelve una fila por mes entre `periods.forecast_start` y `periods.forecast_end`, en orden. `period` usa `AAAA-MM` y `value` es finito. `run.py` agrega las demás columnas.
- `model_parameters` incluye como mínimo `procedure`, `procedure_version`, `fit_start`, `fit_end`, `seed` y los parámetros ajustados. Debe poder serializarse en JSON.
- `estimates` es el DataFrame que `run.py` escribe en `estimates.csv`.
- `run_monitoring` devuelve resultados con estado `ok` o `warning`. El monitoreo alerta, pero no detiene el flujo.
- `log_run` devuelve el identificador del run de MLflow. Si `metadata["metrics"]` es `None`, no registra métricas y registra la causa desde `metadata["errors"]`.
- `publish` y `restore` devuelven el `run_id` de la versión instalada.
- `load_approved` devuelve `None` si no existe `estimates.csv` en la carpeta aprobada. En otro caso devuelve `estimates` y `observed` como DataFrame y `metrics`, `quality_report` y `run` como diccionarios. La carpeta sale del argumento, de la variable de entorno `APPROVED_DIR` o de `outputs.approved_dir`, en ese orden.

### Métricas

`evaluate` devuelve el contenido de `metrics.json` con estas claves:

```json
{
  "procedure": {"name": "holt_winters", "mae": 0.0, "rmse": 0.0, "mape_pct": 0.0},
  "baseline": {"name": "seasonal_naive", "mae": 0.0, "rmse": 0.0, "mape_pct": null},
  "evaluated_periods": ["2025-07", "2025-08"],
  "mape_zero_rule": "Texto que explica cómo se tratan los observados iguales a cero."
}
```

`mape_pct` puede ser `null` cuando no hay observados distintos de cero. Los meses sin valor observado no se evalúan.

### Archivos de estimaciones

`observed.csv` y `estimates.csv` usan las columnas de `outputs.estimate_columns`:

`destination, period, value, unit, kind, run_id, generated_at, procedure_version`

`kind` vale `observado` en `observed.csv` y `estimado` en `estimates.csv`. Ambos archivos de una misma ejecución comparten `run_id` y `generated_at`.

## Orden de etapas

`run_pipeline` ejecuta las etapas en este orden y agrega cada nombre a `completed_stages` al terminarla:

1. `read_source`: lee el Excel y calcula su huella SHA-256.
2. `run_checks`: ejecuta los seis controles y escribe `quality_report.json`. Un `stop` deja `publication: blocked` y detiene el flujo.
3. `prepare_series`: construye la serie mensual.
4. `write_observed`: escribe `observed.csv`.
5. `fit_and_forecast`: ajusta el modelo y guarda `model_parameters` en `run.json`.
6. `evaluate`: calcula las métricas.
7. `write_estimates`: escribe `estimates.csv` y `metrics.json`.
8. `accept`: aplica la regla de aceptación y guarda la decisión en `acceptance`.
9. `run_monitoring`: compara con la versión aprobada vigente, antes de reemplazarla.
10. `publish`: solo si la versión fue aceptada. Antes de publicar, `run.py` escribe `run.json` en la carpeta candidata con `publication: published`.
11. `log_run`: se ejecuta siempre en el bloque `finally`. Si falla, se agrega una advertencia y se conserva el error original.

Al final, `run.json` se escribe en la carpeta candidata y en `logs/<run_id>.json`.

Mientras las funciones de A, B y C sigan pendientes, la ejecución termina con `status: failed`, el error `fit_and_forecast pendiente: persona A`, código de salida 1 y `results/approved/` sin cambios. `observed.csv` ya queda escrito.

## Estados de `run.json`

| Campo | Valor | Significado |
|---|---|---|
| `status` | `running` | La ejecución está en curso. |
| `status` | `completed` | Todas las etapas terminaron, se haya publicado o no. |
| `status` | `failed` | Una etapa lanzó un error; la causa queda en `errors`. |
| `publication` | `not_attempted` | El flujo se detuvo antes de decidir la publicación. |
| `publication` | `blocked` | Un control crítico de calidad detuvo el flujo. |
| `publication` | `rejected` | La versión no cumplió la regla de aceptación. |
| `publication` | `published` | La versión se instaló como aprobada. |

Otros campos de `run.json`: `run_id`, `started_at`, `finished_at`, `config_path`, `source_fingerprint`, `checks_status`, `checks`, `model_parameters`, `metrics`, `acceptance`, `monitoring`, `warnings`, `errors` y `mlflow_run_id`.

## Carpetas de resultados

```text
results/candidates/<run_id>/
    observed.csv
    estimates.csv
    metrics.json
    quality_report.json
    run.json
results/approved/current/
    los mismos cinco archivos de la versión vigente
results/approved/history/<run_id>/
    los mismos cinco archivos de cada versión anterior
logs/<run_id>.json
mlflow/
```

`tests/fixtures/approved_sample/` contiene una muestra sintética con esta estructura. `tests/test_approved_contract.py` define `assert_approved_version`, que C puede reutilizar para validar lo que instala `publish`. `results/`, `logs/` y `mlflow/` están excluidos de Git.
