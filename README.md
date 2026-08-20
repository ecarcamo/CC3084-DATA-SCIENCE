# CC3084-DATA-SCIENCE

## Laboratorio 4: Análisis de Datos Geoespaciales (incisos 1-2)

Conexión con el API de Sentinel Hub (Copernicus Data Space Ecosystem) y descarga de los rasters de los lagos de Atitlán y Amatitlán necesarios para el índice de cianobacteria, NDVI y NDWI.

### Estructura

```
informe/
  secciones/     texto de cada inciso
  figuras/       gráficos y vistas generadas por los notebooks
notebooks/       01_conexion_api.ipynb ... 08_analisis_exploratorio.ipynb (Parte I)
                 p2_01_preparacion_datos.ipynb (Parte II)
src/             config.py, credenciales.py, conexion.py, evalscripts.py, descarga.py, raster.py, dataset.py
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

Construcción de un conjunto de datos tabular a nivel de píxel de agua a partir de los rasters de la Parte I, con coordenadas en WGS84 y UTM 15N (EPSG:32615), bandas espectrales, índices y filtros de calidad.

1. `p2_01_preparacion_datos.ipynb`: construye y limpia el dataset (`src/dataset.py`), genera `data/processed/dataset_ml.parquet` (dataset completo) y `data/processed/dataset_ml_muestra.parquet` (muestra de trabajo de 300,000 observaciones), y las figuras del inciso 1 en `informe/figuras/`.

El evalscript de descarga (`src/evalscripts.py`) se amplió para la Parte II: pasó de 10 a 18 bandas de salida, agregando B05, B07, B08, B8A, B11, B12, CLM y CLP después de las 10 bandas originales, por lo que los rasters de `data/raw/` deben regenerarse ejecutando de nuevo `02_descarga_raster.ipynb` o `src.descarga.descargar_todo` antes de correr `p2_01_preparacion_datos.ipynb`.
