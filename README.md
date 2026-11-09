# CC3084-DATA-SCIENCE

## Laboratorio 10: Visualización Interactiva

Tablero en Dash para directivos de INGUAT.

```bash
pip install -r requirements.txt
python -m app.main
python -m unittest tests.test_design tests.test_predictions tests.test_model_results tests.test_model_components tests.test_year_over_year
python -m tests.test_data && python -m tests.test_theme && python -m tests.test_ranking && python -m tests.test_app && python -m tests.test_wireframe
```

```
app/
├── main.py                  (menú, selección de gráficas visibles, integración y arranque)
├── data.py                  (carga y validación de series; agregación mensual, trimestral y anual)
├── model_results.py         (lectura de predicciones existentes y cálculo de errores)
├── theme.py                 (paleta y plantilla de Plotly)
├── assets/style.css
└── components/
    ├── time_series.py       (G1: serie temporal observada)
    ├── ranking.py           (G2: ranking por vía o país, enlazado con G1)
    ├── seasonality.py       (G3: mapa de calor por año y mes)
    ├── annual_comparison.py (G4: totales anuales)
    ├── year_over_year.py    (G5: variación interanual mensual)
    ├── predictions.py       (G6: observado y estimado de la versión aprobada)
    └── model_errors.py      (G7: error del procedimiento frente a la referencia)
insumos/                     (series y resultados del Lab 1, copiados de lab9)
docs/                        (enunciado, entregables, figuras y scripts de revisión)
```

Para añadir una visualización: crear `app/components/<nombre>.py` con `layout()` y `register(app)`,
y agregarla a `OBSERVED` o `MODELS` en `app/main.py`; el menú y «Gráficas visibles» la incluyen. Para
enlazar una gráfica con la serie temporal, su callback escribe en `Output("series-selector", "value")`.

## Laboratorio 12: Power BI

Segunda versión del tablero en Power BI Desktop (`powerbi/observatorio_turismo.pbix`, v1.0). Instrucciones para
abrir el informe, cambiar `RutaInsumos`, actualizar, identificar las tablas de predicciones y métricas, reproducir
las tres pruebas y abrir el Lab 10 en [powerbi/README.md](powerbi/README.md). Documento final:
`docs/lab12/Lab12_PowerBI_Final.pdf`; detalle en `docs/lab12/`.

## Laboratorio 11: MLOps

Detalle técnico en `docs/lab11/` (`contratos.md`, `evaluacion.md`, `seguimiento.md`).

### Requisitos previos

- Docker 24 o posterior con Docker Compose v2.
- La base institucional, que no se sube al repositorio ni entra a la imagen. Colóquela en
  `data/raw/base_migracion_2009_2026jun.xlsx` (hoja `Datos`) o indique otra carpeta con `DATA_DIR`.
- Sin Docker: Python 3.12 y `pip install -r requirements.txt` (versiones fijas).

Rutas, períodos, parámetros, semilla y umbrales están en `config/pipeline.yaml`.

### Construcción e inicio

```bash
mkdir -p results logs mlflow
GIT_COMMIT=$(git rev-parse HEAD) docker compose build
docker compose up -d
```

En PowerShell: `$env:GIT_COMMIT = git rev-parse HEAD; docker compose build`.

- Tablero: http://localhost:8050 (modo debug con `DASH_DEBUG=true`).
- MLflow: http://localhost:5000, experimento `observatorio-guatemala-visitantes`.

### Ejecución del pipeline

```bash
docker compose run --rm pipeline
DATA_DIR=/otra/carpeta docker compose run --rm pipeline
```

Lee, valida (seis controles), prepara la serie, ajusta Holt-Winters, evalúa con meses ocultos, aplica la
regla de aceptación, monitorea y, solo si la versión se acepta, la publica. Termina con código 1 si un
control crítico falla, y en ese caso no toca la versión aprobada.

### Registros y resultados

| Ruta | Contenido |
|---|---|
| `results/candidates/<run_id>/` | Los cinco archivos de cada ejecución |
| `results/approved/current/` | Versión aprobada que lee el tablero |
| `results/approved/history/<run_id>/` | Versiones aprobadas anteriores |
| `logs/<run_id>.json` | Registro de la ejecución: etapas, advertencias, errores y publicación |
| `mlflow/` | Base SQLite y artefactos de MLflow |

Las cuatro carpetas se montan desde el host: persisten al eliminar y volver a crear los contenedores.

### Restauración de una versión

```bash
ls results/approved/history
docker compose run --rm pipeline python -m pipeline.publish --restore <run_id>
```

El tablero lee la versión restaurada sin reiniciarse.

### Pruebas y detención

```bash
docker compose run --rm pipeline python -m unittest discover -s tests -t . -p "test_*.py"
docker compose down
```

`docker compose down` detiene y elimina los contenedores; los resultados y MLflow quedan en el host.
