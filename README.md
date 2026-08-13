# CC3084-DATA-SCIENCE

## Laboratorio 4: Análisis de Datos Geoespaciales (incisos 1-2)

Conexión con el API de Sentinel Hub (Copernicus Data Space Ecosystem) y descarga de los rasters de los lagos de Atitlán y Amatitlán necesarios para el índice de cianobacteria, NDVI y NDWI.

### Estructura

```
informe/
  secciones/     texto de cada inciso
  figuras/       gráficos y vistas generadas por los notebooks
notebooks/       01_conexion_api.ipynb, 02_descarga_raster.ipynb
src/             config.py, credenciales.py, conexion.py, evalscripts.py, descarga.py, raster.py
data/            rasters y csv generados (fuera de control de versiones)
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
2. `02_descarga_raster.ipynb`: descarga los rasters de 10 bandas por fecha y genera el manifiesto en `data/processed/manifiesto_rasters.csv`.
