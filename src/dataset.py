"""Construcción del conjunto de datos tabular para Machine Learning (Parte 2, inciso 1).

Convierte los rasters de la Parte I en una tabla de observaciones por píxel de agua válido,
con coordenadas en WGS84 y en UTM 15N (EPSG:32615), bandas espectrales, índices y filtros de
calidad aplicados de forma explícita y auditable.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from src.config import FECHAS_OFICIALES, LAGOS
from src.descarga import ruta_raster
from src.evalscripts import OUTPUT_BANDS

CRS_UTM = "EPSG:32615"

# Mínimo de fechas (de las 11 oficiales por lago) en que un píxel debe clasificarse como agua
# para conservarse como parte de la máscara de agua "estable" del lago. Mismo criterio y mismo
# valor que MIN_FECHAS_VALIDAS del inciso 8 de la Parte I: descarta píxeles de borde observados
# como agua en muy pocas fechas, cuyos ratios espectrales son inestables.
MIN_FECHAS_AGUA_ESTABLE = 9

# CLP se entrega en DN (0-255); 0.35 de probabilidad de nube equivale a 89.25 en esa escala.
CLP_MAX_DN = 0.35 * 255
REFLECTANCIA_MAX = 1.6
NDCI_DENOM_MIN = 1e-4

BANDAS_REFLECTANCIA = ["rojo", "verde", "azul", "b05", "b07", "b08", "b8a", "b11", "b12"]

# Columnas de banda que sí se conservan en la tabla final. `mascara`, `agua` y `clm` se usan
# únicamente como filtros: tras aplicarlos, las tres quedan en un valor constante (1, 1 y 0
# respectivamente) y no aportan información adicional como predictoras.
BANDAS_SALIDA = [
    "rojo", "verde", "azul", "b05", "b07", "b08", "b8a", "b11", "b12",
    "ndci", "clorofila", "fai", "ndvi", "ndwi", "clp",
]

_TRANSFORMER = Transformer.from_crs("EPSG:4326", CRS_UTM, always_xy=True)


def _leer_bandas(ruta: Path) -> tuple[dict[str, np.ndarray], rasterio.Affine, int, int]:
    with rasterio.open(ruta) as src:
        datos = src.read()
        transform = src.transform
        alto, ancho = src.height, src.width
    bandas = {nombre: datos[i] for i, nombre in enumerate(OUTPUT_BANDS)}
    return bandas, transform, alto, ancho


def _coordenadas_centro(transform: rasterio.Affine, alto: int, ancho: int) -> tuple[np.ndarray, np.ndarray]:
    columnas, filas = np.meshgrid(np.arange(ancho), np.arange(alto))
    lon = transform.c + (columnas + 0.5) * transform.a
    lat = transform.f + (filas + 0.5) * transform.e
    return lon, lat


def mascara_agua_estable(lago: str, min_fechas: int = MIN_FECHAS_AGUA_ESTABLE) -> np.ndarray:
    """Píxeles clasificados como agua en al menos `min_fechas` de las fechas oficiales del lago."""
    conteo = None
    for fecha in FECHAS_OFICIALES[lago]:
        with rasterio.open(ruta_raster(lago, fecha)) as src:
            agua = src.read(OUTPUT_BANDS.index("agua") + 1)
        if conteo is None:
            conteo = np.zeros_like(agua, dtype=np.int16)
        conteo += (agua > 0).astype(np.int16)
    return conteo >= min_fechas


def _aplicar_filtros(
    bandas: dict[str, np.ndarray], mascara_estable: np.ndarray | None
) -> dict[str, np.ndarray]:
    """Aplica en orden los filtros de validez del inciso 1.3 y retorna el booleano acumulado
    en cada etapa (cada máscara ya incluye las anteriores). Función compartida por `tabla_fecha`
    (conteos y selección final) y `mapa_motivo_descarte` (diagnóstico espacial), para no repetir
    los mismos umbrales en dos lugares.
    """
    etapas = {}

    valido = bandas["mascara"] > 0
    etapas["mascara_valida"] = valido.copy()

    valido &= bandas["agua"] > 0
    etapas["agua"] = valido.copy()

    # CLM usa 255 como "sin dato" del modelo s2cloudless, no como nube; tratarlo como nube
    # descarta píxeles de agua válidos (reflectancia y CLP bajos) en varias fechas. Por eso solo
    # se excluye CLM == 1 (nube confirmada) y se deja a CLP, que sí trae un valor continuo incluso
    # donde CLM es "sin dato", como criterio principal de nubosidad.
    valido &= (bandas["clm"] != 1) & (bandas["clp"] < CLP_MAX_DN)
    etapas["sin_nubes"] = valido.copy()

    for nombre in BANDAS_REFLECTANCIA:
        b = bandas[nombre]
        valido &= np.isfinite(b) & (b > 0) & (b <= REFLECTANCIA_MAX)
    etapas["reflectancia_valida"] = valido.copy()

    denominador_ndci = bandas["rojo"] + bandas["b05"]
    valido &= np.abs(denominador_ndci) > NDCI_DENOM_MIN
    etapas["ndci_valido"] = valido.copy()

    if mascara_estable is not None:
        valido &= mascara_estable
        etapas["agua_estable"] = valido.copy()

    return etapas


def tabla_fecha(
    lago: str,
    fecha: str,
    mascara_estable: np.ndarray | None = None,
    registro_filtros: list[dict] | None = None,
) -> pd.DataFrame:
    """Construye la tabla de observaciones válidas de una combinación lago-fecha.

    Aplica, en orden, los filtros de validez del inciso 1.3: máscara de datos válidos, agua,
    nubes/sombra de nube, reflectancias fuera de rango y denominador del NDCI casi nulo. Si se
    provee `mascara_estable`, se aplica como filtro adicional. Cada paso se registra en
    `registro_filtros` con el número de píxeles retenidos, para reportar el efecto de la
    limpieza en el inciso 1.4.
    """
    ruta = ruta_raster(lago, fecha)
    bandas, transform, alto, ancho = _leer_bandas(ruta)
    lon, lat = _coordenadas_centro(transform, alto, ancho)

    etapas = _aplicar_filtros(bandas, mascara_estable)

    if registro_filtros is not None:
        conteos = {
            "n_total": alto * ancho,
            "n_mascara_valida": int(etapas["mascara_valida"].sum()),
            "n_agua": int(etapas["agua"].sum()),
            "n_sin_nubes": int(etapas["sin_nubes"].sum()),
            "n_reflectancia_valida": int(etapas["reflectancia_valida"].sum()),
            "n_ndci_valido": int(etapas["ndci_valido"].sum()),
        }
        if mascara_estable is not None:
            conteos["n_agua_estable"] = int(etapas["agua_estable"].sum())
        registro_filtros.append({"lago": lago, "fecha": fecha, **conteos})

    valido = etapas["agua_estable"] if mascara_estable is not None else etapas["ndci_valido"]

    fila_idx, col_idx = np.nonzero(valido)
    datos = {
        "lago": lago,
        "fecha": fecha,
        "fila": fila_idx.astype(np.int32),
        "columna": col_idx.astype(np.int32),
        "lon": lon[fila_idx, col_idx].astype(np.float64),
        "lat": lat[fila_idx, col_idx].astype(np.float64),
    }
    for nombre in BANDAS_SALIDA:
        datos[nombre] = bandas[nombre][fila_idx, col_idx].astype(np.float32)

    df = pd.DataFrame(datos)
    x_utm, y_utm = _TRANSFORMER.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    df["x_utm"] = x_utm.astype(np.float32)
    df["y_utm"] = y_utm.astype(np.float32)
    return df


def mapa_motivo_descarte(
    lago: str, fecha: str, mascara_estable: np.ndarray | None = None
) -> tuple[np.ndarray, list[str]]:
    """Clasifica cada píxel del raster según el primer filtro del inciso 1.3 que lo descarta.

    Retorna una matriz de enteros con la misma forma que el raster y la lista de etiquetas, en
    el orden correspondiente a cada código. Se usa para el mapa de cobertura espacial del
    inciso 1.5, que muestra dónde se concentra cada motivo de descarte dentro del lago.
    """
    bandas, _, alto, ancho = _leer_bandas(ruta_raster(lago, fecha))
    etapas = _aplicar_filtros(bandas, mascara_estable)

    etiquetas = ["sin_dato", "tierra", "nube_o_sombra", "reflectancia_invalida", "borde_ndci_inestable"]
    motivo = np.zeros((alto, ancho), dtype=np.int8)
    motivo[etapas["mascara_valida"] & ~etapas["agua"]] = 1
    motivo[etapas["agua"] & ~etapas["sin_nubes"]] = 2
    motivo[etapas["sin_nubes"] & ~etapas["reflectancia_valida"]] = 3
    motivo[etapas["reflectancia_valida"] & ~etapas["ndci_valido"]] = 4

    if mascara_estable is not None:
        etiquetas.append("borde_agua_inestable")
        etiquetas.append("valido")
        motivo[etapas["ndci_valido"] & ~etapas["agua_estable"]] = 5
        motivo[etapas["agua_estable"]] = 6
    else:
        etiquetas.append("valido")
        motivo[etapas["ndci_valido"]] = 5

    return motivo, etiquetas


def construir_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye el dataset completo de las 22 combinaciones lago-fecha y el registro de filtros.

    Retorna (dataset, resumen_filtros): `dataset` es la tabla de observaciones válidas y
    `resumen_filtros` es una tabla con el número de píxeles retenidos por lago, fecha y filtro.
    """
    tablas = []
    registro_filtros: list[dict] = []
    for lago in LAGOS:
        estable = mascara_agua_estable(lago)
        for fecha in FECHAS_OFICIALES[lago]:
            tablas.append(tabla_fecha(lago, fecha, mascara_estable=estable, registro_filtros=registro_filtros))

    dataset = pd.concat(tablas, ignore_index=True)
    dataset["fecha"] = pd.to_datetime(dataset["fecha"])
    dataset["lago"] = dataset["lago"].astype("category")

    resumen_filtros = pd.DataFrame(registro_filtros)
    resumen_filtros["fecha"] = pd.to_datetime(resumen_filtros["fecha"])
    return dataset, resumen_filtros


def muestra_trabajo(df: pd.DataFrame, n_por_lago: int = 150_000, semilla: int = 42) -> pd.DataFrame:
    """Submuestreo aleatorio reproducible, proporcional entre las fechas de cada lago.

    Se usa como conjunto de trabajo para los incisos de modelado (4 en adelante), donde el
    volumen del dataset completo (millones de filas) haría lento el ajuste de hiperparámetros,
    la validación espacial y SHAP sin aportar precisión adicional relevante.
    """
    partes = []
    for lago, grupo_lago in df.groupby("lago", observed=True):
        n_fechas = grupo_lago["fecha"].nunique()
        objetivo_por_fecha = max(1, n_por_lago // n_fechas)
        for fecha, grupo_fecha in grupo_lago.groupby("fecha"):
            n = min(len(grupo_fecha), objetivo_por_fecha)
            partes.append(grupo_fecha.sample(n=n, random_state=semilla))
    return pd.concat(partes, ignore_index=True).sort_values(["lago", "fecha"]).reset_index(drop=True)
