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
    ├── predictions.py       (G6: observado frente a predicciones)
    ├── model_errors.py      (G7: comparación de errores entre modelos)
    └── model_deviations.py  (G8: desviación observado menos estimado)
insumos/                     (series y resultados del Lab 1, copiados de lab9)
docs/                        (enunciado, entregables, figuras y scripts de revisión)
```

Para añadir una visualización: crear `app/components/<nombre>.py` con `layout()` y `register(app)`,
y agregarla a `OBSERVED` o `MODELS` en `app/main.py`; el menú y «Gráficas visibles» la incluyen. Para
enlazar una gráfica con la serie temporal, su callback escribe en `Output("series-selector", "value")`.

## Laboratorio 11: pipeline (avance)

Requisitos: Python 3.12 y las dependencias del proyecto.

```bash
pip install -r requirements.txt
```

La base institucional no se sube al repositorio. Colóquela en
`data/raw/base_migracion_2009_2026jun.xlsx` (hoja `Datos`); la ruta, los períodos y los umbrales
están en `config/pipeline.yaml`.

```bash
python -m pipeline.run --config config/pipeline.yaml
```

Cada ejecución crea `results/candidates/<run_id>/` con `quality_report.json` (resultado de los seis
controles de calidad), `run.json` (etapas, advertencias, errores y estado de la publicación) y, si
ningún control la detiene, `observed.csv` con la serie mensual de visitantes. El mismo registro se
copia en `logs/<run_id>.json`. Si un control crítico falla, el comando termina con código 1, marca
la ejecución como `failed` con la causa y no modifica `results/approved/`.

```bash
python -m unittest tests.test_checks tests.test_pipeline
```
