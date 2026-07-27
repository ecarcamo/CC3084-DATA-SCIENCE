from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

from src.utils import RUTA_FIGURAS, SERIES

CATEGORIAS = {
    "total": "Referencia",
    "via_aerea": "Vía de ingreso",
    "via_terrestre": "Vía de ingreso",
    "via_maritima": "Vía de ingreso",
    "pais_el_salvador": "País de residencia",
    "pais_estados_unidos": "País de residencia",
    "pais_honduras": "País de residencia",
}

COLORES = {
    "total": "tab:blue",
    "via_aerea": "tab:orange",
    "via_terrestre": "tab:green",
    "via_maritima": "tab:purple",
    "pais_el_salvador": "tab:red",
    "pais_estados_unidos": "tab:brown",
    "pais_honduras": "tab:cyan",
}

MESES = [
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
]

INICIO_PREPANDEMIA = "2009-01-01"
FIN_PREPANDEMIA = "2019-12-01"
INICIO_PANDEMIA = "2020-01-01"
FIN_PANDEMIA = "2021-12-01"
INICIO_RECUPERACION = "2020-04-01"
UMBRAL_RECUPERACION = 0.8


def _guardar(figura: plt.Figure, ruta: Path) -> None:
    figura.tight_layout()
    figura.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(figura)


def _fuerzas(serie: pd.Series) -> tuple[float, float]:
    descomposicion = seasonal_decompose(
        np.log1p(serie),
        model="additive",
        period=12,
        extrapolate_trend="freq",
    )
    residuo = descomposicion.resid.dropna()
    estacional = descomposicion.seasonal.reindex(residuo.index)
    tendencia = descomposicion.trend.reindex(residuo.index)
    fuerza_estacional = 1 - residuo.var() / (estacional + residuo).var()
    fuerza_tendencia = 1 - residuo.var() / (tendencia + residuo).var()
    return fuerza_estacional, fuerza_tendencia


def _tendencia(prepandemia: pd.Series) -> tuple[float, float]:
    tiempo = np.arange(len(prepandemia))
    pendiente = np.polyfit(tiempo, prepandemia.to_numpy(), 1)[0]
    return pendiente, 100 * pendiente / prepandemia.mean()


def _volatilidad(prepandemia: pd.Series) -> tuple[float, float]:
    retornos = np.log1p(prepandemia).diff().dropna()
    return prepandemia.std() / prepandemia.mean(), retornos.std()


def _pandemia(serie: pd.Series) -> dict:
    media_2019 = serie.loc["2019"].mean()
    tramo = serie.loc[INICIO_PANDEMIA:FIN_PANDEMIA]
    umbral = UMBRAL_RECUPERACION * media_2019
    posterior = serie.loc[INICIO_RECUPERACION:]
    alcanzados = posterior[posterior >= umbral]
    return {
        "media_2019": media_2019,
        "min_pandemia": tramo.min(),
        "fecha_min_pandemia": tramo.idxmin().strftime("%Y-%m-%d"),
        "caida_pct": 100 * (1 - tramo.min() / media_2019),
        "mes_recuperacion_80": (
            alcanzados.index[0].strftime("%Y-%m")
            if len(alcanzados)
            else "sin recuperación"
        ),
    }


def perfil_estacional(serie: pd.Series) -> pd.Series:
    log = np.log1p(serie.loc[:FIN_PREPANDEMIA])
    factores = np.exp(log.groupby(log.index.month).mean() - log.mean())
    return factores.reindex(range(1, 13))


def comparar_serie(clave: str, train: pd.Series, completa: pd.Series) -> dict:
    prepandemia = completa.loc[INICIO_PREPANDEMIA:FIN_PREPANDEMIA]
    fuerza_estacional, fuerza_tendencia = _fuerzas(train)
    pendiente, pendiente_pct = _tendencia(prepandemia)
    cv, volatilidad_retornos = _volatilidad(prepandemia)

    return {
        "clave": clave,
        "etiqueta": SERIES[clave],
        "categoria": CATEGORIAS[clave],
        "fs": fuerza_estacional,
        "ft": fuerza_tendencia,
        "pendiente_viajeros_mes": pendiente,
        "pendiente_pct_media": pendiente_pct,
        "cv_2009_2019": cv,
        "vol_retornos_log": volatilidad_retornos,
        **_pandemia(completa),
    }


def _barras(eje: plt.Axes, tabla: pd.DataFrame, columna: str, titulo: str) -> None:
    colores = [COLORES[clave] for clave in tabla.index]
    eje.bar(tabla["etiqueta"], tabla[columna], color=colores)
    eje.set_title(titulo)
    eje.tick_params(axis="x", labelrotation=45)
    for etiqueta in eje.get_xticklabels():
        etiqueta.set_horizontalalignment("right")


def figura_estacionalidad(
    tabla: pd.DataFrame,
    perfiles: pd.DataFrame,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    figura, ejes = plt.subplots(1, 2, figsize=(12, 4.5))
    _barras(ejes[0], tabla, "fs", "Fuerza estacional (Fs) sobre log1p del train")
    ejes[0].set_ylabel("Fs")

    for clave in tabla.index:
        ejes[1].plot(
            MESES,
            perfiles[clave],
            color=COLORES[clave],
            marker="o",
            markersize=3,
            label=tabla.loc[clave, "etiqueta"],
        )
    ejes[1].axhline(1, color="grey", linewidth=0.8, linestyle="--")
    ejes[1].set(
        title="Factores estacionales prepandemia",
        xlabel="Mes",
        ylabel="Factor",
    )
    ejes[1].legend(fontsize=8)
    _guardar(figura, ruta_figuras / "comp_estacionalidad.png")


def figura_tendencia(
    tabla: pd.DataFrame,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    figura, ejes = plt.subplots(1, 2, figsize=(12, 4.5))
    _barras(
        ejes[0],
        tabla,
        "pendiente_viajeros_mes",
        "Pendiente 2009-2019 (viajeros por mes)",
    )
    ejes[0].set_ylabel("Viajeros por mes")
    _barras(
        ejes[1],
        tabla,
        "pendiente_pct_media",
        "Pendiente normalizada (% de la media del tramo)",
    )
    ejes[1].set_ylabel("% de la media")
    _guardar(figura, ruta_figuras / "comp_tendencia.png")


def figura_volatilidad(
    tabla: pd.DataFrame,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    figura, ejes = plt.subplots(1, 2, figsize=(12, 4.5))
    _barras(ejes[0], tabla, "cv_2009_2019", "Coeficiente de variación 2009-2019")
    ejes[0].set_ylabel("Desviación / media")
    _barras(
        ejes[1],
        tabla,
        "vol_retornos_log",
        "Desviación de los retornos logarítmicos mensuales",
    )
    ejes[1].set_ylabel("Desviación de log1p diferenciado")
    _guardar(figura, ruta_figuras / "comp_volatilidad.png")


def figura_recuperacion(
    tabla: pd.DataFrame,
    series: dict[str, pd.Series],
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    figura, eje = plt.subplots(figsize=(11, 5))
    for clave in tabla.index:
        indice = (
            100
            * series[clave].loc[INICIO_PANDEMIA:]
            / tabla.loc[clave, "media_2019"]
        )
        eje.plot(
            indice.index,
            indice,
            color=COLORES[clave],
            label=tabla.loc[clave, "etiqueta"],
        )
    eje.axhline(
        100 * UMBRAL_RECUPERACION,
        color="black",
        linewidth=1,
        linestyle="--",
        label="80 % de la media 2019",
    )
    eje.set(
        title="Recuperación posterior al cierre (media 2019 = 100)",
        xlabel="Fecha",
        ylabel="Índice",
    )
    eje.legend(fontsize=8, ncol=2)
    _guardar(figura, ruta_figuras / "comp_recuperacion.png")
