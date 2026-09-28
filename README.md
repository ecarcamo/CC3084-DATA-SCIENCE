# CC3084-DATA-SCIENCE

## Laboratorio 7 — Spark MLlib

Notebook: `Lab7_Spark_MLlib.ipynb` (ejecutado, con salidas). La fuente versionada es
`notebooks/Lab7_Spark_MLlib.py` (jupytext, formato `py:percent`).

Datos: bases de Personas de la ENEIC en `data/raw/eneic/` (2025 T1–T4 y 2026 T1).

### Entorno

Python 3.11, Java 17 y PySpark 3.5 con la imagen de `docker/` (la misma del curso más `openpyxl`,
`pyreadstat` y `jupytext`).

```bash
docker compose -f docker/docker-compose.yml up --build
```

Jupyter queda en http://localhost:8888 con el repositorio montado.

### Ejecución de principio a fin

```bash
docker compose -f docker/docker-compose.yml run --rm pyspark bash -c "jupytext --to ipynb notebooks/Lab7_Spark_MLlib.py -o Lab7_Spark_MLlib.ipynb && jupyter nbconvert --to notebook --execute --inplace Lab7_Spark_MLlib.ipynb"
```

El notebook escribe `data/processed/eneic_2025.parquet`, `data/processed/eneic_2026.parquet`, los modelos
en `models/` y las figuras en `outputs/lab7/`.

Informe: `docs/Informe_Laboratorio7.pdf`.
