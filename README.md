# CC3084-DATA-SCIENCE

## Laboratorio 4: Análisis de Datos Geoespaciales

Conexión con el API de Sentinel Hub (Copernicus Data Space Ecosystem) y descarga de los rasters de los lagos de Atitlán y Amatitlán necesarios para el índice de cianobacteria, NDVI y NDWI.

### Estructura

```
informe/
  secciones/     texto de cada inciso
  figuras/       gráficos y vistas generadas por los notebooks
notebooks/       01_conexion_api.ipynb ... 08_analisis_exploratorio.ipynb (Parte I)
                 p2_01_preparacion_datos.ipynb ... p2_09_mapas_predictivos.ipynb (Parte II)
src/             config.py, credenciales.py, conexion.py, evalscripts.py, descarga.py, raster.py,
                 dataset.py, modelado.py, espacial.py, mapas.py
data/            rasters y parquet/csv generados (fuera de control de versiones)
```

### Setup

```powershell
& "..\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

### Credenciales

Se requiere un OAuth client de Copernicus Data Space Ecosystem:

1. Crear el client en https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings, sección "OAuth clients".
2. Registrarlo una sola vez, desde la raíz del repo:

```powershell
& "..\.venv\Scripts\python.exe" -m src.credenciales
```

Esto guarda las credenciales en el perfil `cdse` del archivo de configuración global de `sentinelhub-py` (`~/.config/sentinelhub/config.toml`), fuera de este repositorio y reutilizable en otros laboratorios. Como alternativa, `crear_config()` también acepta las variables de entorno `SH_CLIENT_ID` y `SH_CLIENT_SECRET`.

### Ejecución

Los notebooks se ejecutan desde la carpeta `notebooks/`, en orden:

1. `01_conexion_api.ipynb`: verifica la autenticación y consulta el catálogo de las 22 escenas oficiales.
2. `02_descarga_raster.ipynb`: descarga los rasters de 18 bandas por fecha y genera el manifiesto en `data/processed/manifiesto_rasters.csv`.
3. `03` a `08`: índices, análisis temporal, espacial, correlación, comparación entre lagos y exploración adicional (Parte I).

### Laboratorio 4, Parte II: Machine Learning sobre datos geoespaciales

Construcción de un conjunto de datos tabular a nivel de píxel de agua a partir de los rasters de la Parte I y desarrollo de modelos de clasificación para detectar alta presencia de cianobacteria, con validación espacial, generalización entre lagos, interpretabilidad y mapas predictivos.

1. `p2_01_preparacion_datos.ipynb`: construye y limpia el dataset (`src/dataset.py`), genera `data/processed/dataset_ml.parquet` (dataset completo) y `data/processed/dataset_ml_muestra.parquet` (muestra de trabajo de 300,000 observaciones), y las figuras del inciso 1.
2. `p2_02_variable_respuesta.ipynb`: variable respuesta binaria `alta_cianobacteria` (`src/modelado.py`), umbral de 10 µg/L de clorofila-a, distribución de clases y variables excluidas por fuga de información.
3. `p2_03_predictoras.ipynb`: define y justifica las 11 variables predictoras, incluida `verde_azul_ratio` (única variable derivada).
4. `p2_04_modelos.ipynb`: entrena Regresión Logística, Random Forest y Gradient Boosting (división 70/30, ajuste de hiperparámetros), guarda los modelos en `data/processed/modelos/` y el conjunto de prueba en `data/processed/p2_test_set.parquet`.
5. `p2_05_evaluacion.ipynb`: evalúa los tres modelos (Accuracy, Precision, Recall, F1, ROC-AUC, matriz de confusión) y define el criterio de comparación (F2-score, orientado a Recall).
6. `p2_06_validacion_espacial.ipynb`: cuadrícula de ~1 km sobre UTM 15N (`src/espacial.py`), validación cruzada espacial (`StratifiedGroupKFold`) vs. aleatoria.
7. `p2_07_generalizacion_lagos.ipynb`: entrena en un lago y evalúa en el otro (y viceversa), comparado contra una línea base de mismo lago.
8. `p2_08_interpretabilidad.ipynb`: importancia global de variables y SHAP summary plot del mejor modelo (requiere `shap`).
9. `p2_09_mapas_predictivos.ipynb`: reconstruye espacialmente las probabilidades predichas (`src/mapas.py`) y genera mapas de probabilidad y de error por lago.

El evalscript de descarga (`src/evalscripts.py`) se amplió para la Parte II: pasó de 10 a 18 bandas de salida, agregando B05, B07, B08, B8A, B11, B12, CLM y CLP después de las 10 bandas originales, por lo que los rasters de `data/raw/` deben regenerarse ejecutando de nuevo `02_descarga_raster.ipynb` o `src.descarga.descargar_todo` antes de correr `p2_01_preparacion_datos.ipynb`. Los notebooks `p2_02` en adelante se ejecutan en orden, cada uno depende de los artefactos que guarda el anterior en `data/processed/`.
