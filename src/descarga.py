from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from sentinelhub import BBox, CRS, MimeType, SentinelHubRequest, bbox_to_dimensions

from src.config import FECHAS_OFICIALES, LAGOS, RESOLUCION_M, RUTA_DATA_RAW
from src.conexion import coleccion_cdse
from src.evalscripts import EVALSCRIPT_CIANOBACTERIA, OUTPUT_BANDS


def ruta_raster(lago: str, fecha: str) -> Path:
    carpeta = RUTA_DATA_RAW / lago
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / f"{lago}_{fecha}.tif"


def descargar_fecha(config, lago: str, fecha: str, forzar: bool = False) -> Path:
    destino = ruta_raster(lago, fecha)
    if destino.exists() and not forzar:
        return destino

    bbox = BBox(LAGOS[lago]["bbox"], crs=CRS.WGS84)
    size = bbox_to_dimensions(bbox, resolution=RESOLUCION_M)
    coleccion = coleccion_cdse(config)

    request = SentinelHubRequest(
        evalscript=EVALSCRIPT_CIANOBACTERIA,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=coleccion,
                time_interval=(fecha, fecha),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config,
    )
    datos = request.get_data()[0].astype(np.float32)

    west, south, east, north = LAGOS[lago]["bbox"]
    transform = from_bounds(west, south, east, north, size[0], size[1])

    with rasterio.open(
        destino,
        "w",
        driver="GTiff",
        height=size[1],
        width=size[0],
        count=len(OUTPUT_BANDS),
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        compress="deflate",
        predictor=3,
    ) as dst:
        for indice, nombre in enumerate(OUTPUT_BANDS, start=1):
            dst.write(datos[:, :, indice - 1], indice)
            dst.set_band_description(indice, nombre)

    return destino


def descargar_lago(config, lago: str, forzar: bool = False) -> list[Path]:
    return [descargar_fecha(config, lago, fecha, forzar=forzar) for fecha in FECHAS_OFICIALES[lago]]


def descargar_todo(config, forzar: bool = False) -> dict[str, list[Path]]:
    return {lago: descargar_lago(config, lago, forzar=forzar) for lago in LAGOS}
