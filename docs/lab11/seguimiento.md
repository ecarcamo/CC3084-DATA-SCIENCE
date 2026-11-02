# Laboratorio 11: seguimiento, registro y monitoreo

## 4.1 Registro en MLflow

`pipeline/tracking.py` registra cada ejecución, exitosa o fallida, en el experimento `mlflow.experiment_name` de la base `mlflow.tracking_uri`. El experimento se crea con los artefactos en `mlflow.artifact_root`, de modo que la base y los archivos quedan dentro de `mlflow/`. Esa carpeta está excluida de Git y es la que debe montarse como volumen en Docker.

| Dato | Registro en MLflow |
|---|---|
| Ejecución | Etiquetas `pipeline_run_id`, `started_at`, `finished_at`, `status`, `publication` y `accepted`. |
| Código | Etiqueta `git_commit` con `git rev-parse HEAD` y `git_dirty`, que vale `true` si había cambios sin commit. Sin Git, por ejemplo dentro de Docker, ambas valen `desconocido`. |
| Fuente | Parámetros `source_path`, relativo a la raíz, y `source_fingerprint`, con la huella SHA-256. |
| Períodos | Parámetros `periods.*` de ajuste, evaluación y estimación. |
| Procedimiento | Parámetros `model.*`, tomados de `model_parameters`. |
| Métricas | `procedure.*`, `baseline.*` y `evaluated_periods`, solo cuando hubo evaluación. |
| Controles | Etiquetas `checks_status`, `check.<control>` y `monitor.<verificación>` con su estado. |
| Artefactos | Todos los archivos de la carpeta candidata, incluido `run.json`, y el YAML utilizado. |

`run.py` escribe `run.json` antes de llamar a `log_run`, así el artefacto ya incluye la hora de fin, las etapas y el resultado de la publicación. El identificador del run de MLflow se agrega después a `run.json` y a `logs/<run_id>.json`. Si el registro falla, la ejecución agrega una advertencia y conserva su error original.

Consulta: `mlflow ui --backend-store-uri sqlite:///mlflow/mlflow.db`.

## 4.2 Reproducibilidad

`python -m pipeline.reproducibility <candidato_1> <candidato_2> --config config/pipeline.yaml` compara dos carpetas candidatas: períodos y valores de `estimates.csv`, meses evaluados y MAE, RMSE y MAPE de ambos procedimientos en `metrics.json`. Ignora `run_id` y `generated_at`, que cambian en cada ejecución. Termina con código 0 si no hay diferencias.

La tolerancia es `reproducibility.relative_tolerance = 1e-9`. Con el mismo código, datos, configuración y versiones de bibliotecas, el ajuste es determinista: la inicialización estimada de Holt-Winters usa un optimizador sin componentes aleatorios y la semilla está fija. La tolerancia solo admite diferencias de redondeo de punto flotante, por ejemplo entre equipos con otra biblioteca de álgebra lineal. En una serie de cientos de miles de visitantes, 1e-9 equivale a menos de una milésima de visitante. Una diferencia mayor indica un cambio de datos, configuración o versión de `statsmodels`, y debe explicarse.

Resultado con la fuente sintética de `tests/synthetic_source.py`, porque la base institucional aún no está disponible: dos ejecuciones completas dieron estimaciones y métricas idénticas, con diferencia relativa máxima de 0. `tests/test_reproducibility.py` repite esa comparación en cada corrida de pruebas. Falta repetirla con la base institucional.

## 4.3 Ejecuciones fallidas

Cuando `metrics` es `None`, la ejecución se detuvo antes de evaluar: no se registran métricas, el run queda como `FAILED` y la etiqueta `error` guarda la causa desde `errors`. Una ejecución que falla después de evaluar también queda como `FAILED`, pero conserva sus métricas.

La evidencia está en `mlflow_runs.csv`, generado con `mlflow.search_runs`:

```powershell
python -m docs.scripts.export_mlflow_runs --config config/pipeline.yaml --experiment observatorio-guatemala-visitantes --experiment observatorio-guatemala-visitantes-sintetico --output docs/lab11/mlflow_runs.csv
```

| Experimento | Estado | Publicación | Causa |
|---|---|---|---|
| `observatorio-guatemala-visitantes` | `FAILED` | `not_attempted` | No se encontró la fuente institucional; no hay métricas. |
| `observatorio-guatemala-visitantes-sintetico` (2 runs) | `FAILED` | `failed` | Versión aceptada; `publish` sigue pendiente. Métricas registradas. |

Las ejecuciones sintéticas usan un experimento separado para no mezclarse con las institucionales. El archivo no incluye `artifact_uri` y las rutas del error quedan relativas a la raíz, para no publicar rutas locales.

## 7.1 Registro por ejecución

`run.json` y `logs/<run_id>.json` contienen inicio y fin en UTC, etapas completadas, advertencias, errores, resultado de la publicación e identificador de MLflow. Si `publish` lanza un error, `publication` vale `failed`: la publicación sí se intentó. Antes quedaba como `not_attempted`. El estado está en la tabla de `contratos.md`.

## 7.2 Verificaciones de monitoreo

`pipeline/monitoring.py` se ejecuta después de `accept` y antes de `publish`, comparando contra la versión aprobada vigente. Devuelve solo `ok` o `warning`.

| Verificación | Revisa | Advertencia |
|---|---|---|
| `monitor_freshness` | El último mes observado y los meses estimados. | La serie no llega a `periods.expected_last_period` o falta algún mes entre `forecast_start` y `forecast_end`. |
| `monitor_quality` | Valores faltantes, filas duplicadas y meses sin datos de `quality_report.json`, frente a la versión aprobada. | Algún aumento supera `max_missing_rows_increase`, `max_duplicate_rows_increase` o `max_missing_months_increase`, todos en 0. |
| `monitor_results` | Estimaciones negativas o no finitas y variación frente al mismo mes del año anterior observado. | Alguna estimación no es válida o su variación interanual supera `max_abs_year_over_year_change_pct`. |

Si no existe versión aprobada, o su reporte no trae esos datos, `monitor_quality` queda en `ok` y lo explica en el mensaje. Para comparar la calidad, `run_monitoring` recibe ahora los `checks` de la ejecución; el cambio de firma está en `contratos.md`. Como los controles críticos detienen el flujo antes del monitoreo, en la práctica esta verificación detecta sobre todo más faltantes en columnas opcionales y más meses faltantes antes del ajuste.

Los meses con observado igual a cero no tienen variación porcentual definida: se excluyen y aparecen en `not_comparable`.

### Umbral de variación interanual

`max_abs_year_over_year_change_pct` vale 30 %. Para justificarlo se usó la serie de referencia `insumos/series/serie_total.csv`, con otra definición de la variable (todos los viajeros) pero la misma escala y estacionalidad:

| Período | Meses | Variación absoluta media | Mediana | Percentil 90 | Máximo | Meses sobre 30 % |
|---|---|---|---|---|---|---|
| 2024-01 a 2026-06 | 30 | 9,5 % | 5,3 % | 21,5 % | 42,0 % | 2 |
| 2025-01 a 2026-06 | 18 | 6,0 % | 4,0 % | 13,6 % | 21,1 % | 0 |

Semana Santa, que cambia entre marzo y abril, mueve esos meses entre 13 % y 25 % de un año a otro. Las dos variaciones sobre 30 % ocurrieron en 2024 (febrero, 33,1 %, y octubre, 42,0 %) y no hubo ninguna desde 2025. El 30 % queda por encima del percentil 90 y del máximo desde 2025, de modo que no genera alertas por la estacionalidad habitual. Un estimado que lo supera corresponde a un cambio de unos 87 000 visitantes en un mes promedio de 290 000 y conviene revisarlo: puede indicar un error del modelo, una revisión de la fuente o un evento extraordinario. El umbral se revisa con la base institucional sin cambiar el criterio.

## 7.3 Alertas

Una variación elevada genera una advertencia en `monitoring`, en `warnings` de `run.json` y en la etiqueta `monitor.monitor_results` de MLflow. No detiene el flujo ni cambia la decisión de `accept`; la prueba `test_monitoring_warning_does_not_block_publication` lo verifica.

El error predictivo solo se calcula con observaciones comparables: `evaluate` excluye los meses sin observado o sin valor de referencia. MLflow registra la lista de meses evaluados en el parámetro `evaluated_periods` y su cantidad en la métrica del mismo nombre, así cada run muestra qué meses entraron en el error.

## Pendiente

- Ejecutar el pipeline con `data/raw/base_migracion_2009_2026jun.xlsx`, repetir la comparación de 4.2 y revisar el umbral de variación con la serie institucional.
- Mientras `publish` siga pendiente, las versiones aceptadas terminan con `publication: failed`.
