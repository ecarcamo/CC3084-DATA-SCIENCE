# CC3084-DATA-SCIENCE

## Laboratorio 10: Visualización Interactiva

Tablero en Dash para directivos de INGUAT.

```bash
pip install -r requirements.txt
python -m app.main
python -m tests.test_data
```

```
app/
├── main.py                  (layout general y arranque)
├── data.py                  (carga de series y agregación mensual, trimestral y anual)
├── theme.py                 (paleta y plantilla de Plotly)
├── assets/style.css
└── components/
    └── time_series.py       (visualización 1: serie temporal)
insumos/                     (series y resultados del Lab 1, copiados de lab9)
docs/                        (enunciado del laboratorio)
```

Para añadir una visualización: crear `app/components/<nombre>.py` con `layout()` y `register(app)`,
y llamarlas desde `app/main.py`. Para enlazar una gráfica con la serie temporal, su callback
escribe en `Output("series-selector", "value")`.
