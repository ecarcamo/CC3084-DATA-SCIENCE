from pathlib import Path

import numpy as np
import rasterio

from src.evalscripts import OUTPUT_BANDS


def abrir(ruta: Path) -> dict[str, np.ndarray]:
    with rasterio.open(ruta) as src:
        datos = src.read()
    return {nombre: datos[i] for i, nombre in enumerate(OUTPUT_BANDS)}


def resumen(ruta: Path) -> dict:
    with rasterio.open(ruta) as src:
        ancho, alto = src.width, src.height
        crs = src.crs

    bandas = abrir(ruta)
    mascara = bandas["mascara"]
    agua = bandas["agua"]

    cobertura_valida_pct = float(mascara.mean() * 100)
    if mascara.sum() > 0:
        agua_pct = float(agua[mascara > 0].mean() * 100)
    else:
        agua_pct = float("nan")

    return {
        "ruta": str(ruta),
        "ancho": ancho,
        "alto": alto,
        "crs": str(crs),
        "cobertura_valida_pct": cobertura_valida_pct,
        "agua_pct": agua_pct,
    }


def vista_rgb(bandas: dict[str, np.ndarray], percentil: float = 98) -> np.ndarray:
    canales = np.stack([bandas["rojo"], bandas["verde"], bandas["azul"]], axis=-1)
    valida = bandas["mascara"] > 0
    if valida.sum() > 0:
        maximo = np.percentile(canales[valida], percentil)
    else:
        maximo = canales.max()
    maximo = max(maximo, 1e-6)
    normalizado = np.clip(canales / maximo, 0, 1)
    return (normalizado * 255).astype(np.uint8)
