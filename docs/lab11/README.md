# Laboratorio 11: pipeline

## Alcance implementado

El paquete `pipeline/` lee la fuente, calcula su huella SHA-256, ejecuta los seis controles de calidad, prepara la serie mensual y guarda un candidato observado. El orden completo de etapas ya está conectado en `pipeline/run.py`, pero el ajuste, la evaluación, el monitoreo, el registro en MLflow y la publicación siguen pendientes y lanzan `NotImplementedError`.

`pipeline/checks.py` define `run_checks(df, config)`, que devuelve una lista de `CheckResult` con estado `ok`, `warning` o `stop`. Los controles se detienen en el primer `stop`. El resultado se guarda en `quality_report.json` y en `run.json`.

Las firmas, el orden de etapas, los estados y la distribución de archivos entre integrantes están en `contratos.md`.

## Fuente y ejecución

La fuente institucional se obtiene con Cárcamo y se coloca en `data/raw/base_migracion_2009_2026jun.xlsx`. No se incluye en Git ni se sustituye por `insumos/series/serie_total.csv`, que utiliza otra definición de la variable.

Desde la raíz, con el entorno del proyecto activo:

```powershell
python -m pipeline.run --config config/pipeline.yaml
python -m pytest tests -q
```

En el entorno académico compartido de este equipo, sin activar el entorno:

```powershell
& "..\.venv\Scripts\python.exe" -m pipeline.run --config config/pipeline.yaml
& "..\.venv\Scripts\python.exe" -m pytest tests -q
```

Las dependencias están en `requirements.txt`, que incluye `mlflow` y `statsmodels` para los puntos 4 y 5.

La configuración y sus rutas relativas se resuelven desde la raíz del repositorio. El comando debe invocarse desde un lugar donde Python pueda importar el paquete `pipeline`, normalmente la raíz.

## Preparación mensual

- Selecciona los tipos de `target.visitor_types`, actualmente `Turista` y `Excursionista`.
- Agrega la columna `source.value_column` por `Año` y `Mes cod`.
- Aplica `destination.allocation_factor`, actualmente 1.
- Conserva el histórico disponible; no recorta la serie al inicio del ajuste.
- Utiliza un índice mensual y deja los meses intermedios ausentes como `NaN`.
- Una suma de valores totalmente ausentes se mantiene ausente, no se convierte en cero.

## Artefactos y estados

Cada ejecución genera un identificador UTC con sufijo aleatorio y una carpeta candidata en `results/candidates/<run_id>/`. El registro de la ejecución se copia en `logs/<run_id>.json`. La estructura completa, incluida la versión aprobada y su historial, está en `contratos.md`.

`observed.csv` contiene `destination, period, value, unit, kind, run_id, generated_at, procedure_version`. Los períodos usan `AAAA-MM` y `kind` vale `observado`. Los valores ausentes se escriben como celdas vacías.

`run.json` registra inicio y fin en UTC, etapas completadas, ruta de configuración, huella de la fuente, controles, parámetros, métricas, decisión de aceptación, monitoreo, advertencias, errores, estado de publicación e identificador de MLflow.

| Campo | Interpretación |
|---|---|
| `status: completed` | Todas las etapas terminaron, se haya publicado o no. |
| `status: failed` | La ejecución falló; se conserva la causa en `errors`. |
| `checks_status: pending` | Los controles no llegaron a ejecutarse. |
| `checks_status: executed` | Los controles se ejecutaron; su resultado está en `checks`. |
| `publication: not_attempted` | El flujo se detuvo antes de decidir la publicación. |
| `publication: blocked` | Un control crítico detuvo el flujo. |
| `publication: rejected` | La versión no cumplió la regla de aceptación. |
| `publication: published` | La versión se instaló como aprobada. |

Cualquier error termina la ejecución con código 1, muestra la causa por la salida de error y no modifica `results/approved/`. Con las etapas pendientes, la ejecución falla en `fit_and_forecast` después de escribir `observed.csv`.

## Pruebas

Las pruebas utilizan un Excel sintético temporal y rutas de salida temporales dentro del repositorio. Las etapas pendientes se sustituyen por dobles de prueba para comprobar la publicación, el rechazo y el registro sin depender de su implementación. `tests/fixtures/approved_sample/` contiene una versión aprobada sintética que sirve de referencia para el tablero y la publicación. Las pruebas no reemplazan la validación con la base institucional.

## Diagrama y redacción

- `flow_diagram.excalidraw`: diagrama editable.
- `flow_diagram.svg`: diagrama vectorial.
- `flow_diagram.png`: imagen para el informe.
- `../../informe/lab11_aporte_hugo.md`: secciones 2 y 3 para copiar manualmente a Word.

El diagrama muestra el flujo completo previsto con estilo de trazo a mano y poco texto. No se ha modificado Word ni SharePoint.
