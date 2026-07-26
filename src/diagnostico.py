from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

from src.utils import RUTA_FIGURAS


def _adf(serie: pd.Series) -> dict:
    resultado = adfuller(serie.dropna(), autolag="AIC")
    return {
        "estadistico": resultado[0],
        "p_valor": resultado[1],
        "rezagos": resultado[2],
        "n": resultado[3],
    }


def _guardar(figura: plt.Figure, ruta: Path) -> None:
    figura.tight_layout()
    figura.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(figura)


def _figura_nivel(
    clave: str,
    serie: pd.Series,
    color: str,
    ruta: Path,
) -> None:
    figura, eje = plt.subplots(figsize=(11, 4))
    eje.plot(serie.index, serie, color=color)
    eje.axvspan(
        pd.Timestamp("2020-03-01"),
        pd.Timestamp("2021-03-01"),
        color="tab:red",
        alpha=0.12,
    )
    eje.set(
        title=f"Serie mensual: {clave}",
        xlabel="Fecha",
        ylabel="Viajeros",
    )
    _guardar(figura, ruta)


def _figura_descomposicion(
    clave: str,
    serie_log: pd.Series,
    ruta: Path,
) -> pd.Series:
    descomposicion = seasonal_decompose(
        serie_log,
        model="additive",
        period=12,
        extrapolate_trend="freq",
    )
    figura = descomposicion.plot()
    figura.set_size_inches(11, 8)
    figura.suptitle(f"Descomposición aditiva de log1p: {clave}", y=1.01)
    _guardar(figura, ruta)
    return descomposicion.seasonal


def _figura_log(
    clave: str,
    serie: pd.Series,
    serie_log: pd.Series,
    color: str,
    ruta: Path,
) -> None:
    figura, ejes = plt.subplots(1, 2, figsize=(12, 4))
    ejes[0].plot(serie.index, serie, color=color)
    ejes[0].set_title(f"{clave}: original")
    ejes[1].plot(serie_log.index, serie_log, color=color)
    ejes[1].set_title(f"{clave}: log1p")
    for eje in ejes:
        eje.set_xlabel("Fecha")
    _guardar(figura, ruta)


def _figura_correlacion(
    clave: str,
    serie: pd.Series,
    ruta: Path,
    diferenciada: bool,
) -> None:
    figura, ejes = plt.subplots(1, 2, figsize=(12, 4))
    plot_acf(serie, lags=36, ax=ejes[0])
    plot_pacf(serie, lags=36, ax=ejes[1], method="ywm")
    estado = "d=1, D=1" if diferenciada else "niveles log1p"
    ejes[0].set_title(f"ACF: {clave} ({estado})")
    ejes[1].set_title(f"PACF: {clave} ({estado})")
    _guardar(figura, ruta)


def _factores_estacionales(serie_log: pd.Series) -> tuple[str, str]:
    prepandemia = serie_log.loc[:"2019-12-01"]
    factores = np.exp(
        prepandemia.groupby(prepandemia.index.month).mean()
        - prepandemia.mean()
    )
    nombres = pd.Series(
        [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ],
        index=range(1, 13),
    )
    return (
        f"{nombres[factores.idxmax()]} ({factores.max():.3f})",
        f"{nombres[factores.idxmin()]} ({factores.min():.3f})",
    )


def analizar_serie(
    clave: str,
    serie: pd.Series,
    color: str = "tab:blue",
    ruta_figuras: Path = RUTA_FIGURAS,
) -> dict:
    ruta_figuras.mkdir(parents=True, exist_ok=True)
    serie = serie.astype(float).asfreq("MS")
    serie_log = np.log1p(serie)
    d1 = serie_log.diff().dropna()
    d1_d1 = d1.diff(12).dropna()
    d2 = serie_log.diff(2).dropna()

    _figura_nivel(
        clave,
        serie,
        color,
        ruta_figuras / f"serie_{clave}_nivel.png",
    )
    estacional = _figura_descomposicion(
        clave,
        serie_log,
        ruta_figuras / f"serie_{clave}_descomposicion.png",
    )
    _figura_log(
        clave,
        serie,
        serie_log,
        color,
        ruta_figuras / f"serie_{clave}_log.png",
    )
    _figura_correlacion(
        clave,
        serie_log,
        ruta_figuras / f"serie_{clave}_acf_niveles.png",
        False,
    )
    _figura_correlacion(
        clave,
        d1_d1,
        ruta_figuras / f"serie_{clave}_acf_diff.png",
        True,
    )

    adf_niveles = _adf(serie_log)
    adf_d1 = _adf(d1)
    adf_d1_d1 = _adf(d1_d1)
    adf_d2 = _adf(d2)
    max_mes, min_mes = _factores_estacionales(serie_log)
    d_sugerido = 1 if adf_d1["p_valor"] < 0.05 else 2

    return {
        "clave": clave,
        "n": len(serie),
        "inicio": serie.index.min().strftime("%Y-%m-%d"),
        "fin": serie.index.max().strftime("%Y-%m-%d"),
        "media": serie.mean(),
        "min": serie.min(),
        "fecha_min": serie.idxmin().strftime("%Y-%m-%d"),
        "max": serie.max(),
        "fecha_max": serie.idxmax().strftime("%Y-%m-%d"),
        "n_ceros": int(serie.eq(0).sum()),
        "std_2009_2013": serie.loc["2009":"2013"].std(),
        "std_2014_2019": serie.loc["2014":"2019"].std(),
        "adf_niveles": adf_niveles["p_valor"],
        "adf_d1": adf_d1["p_valor"],
        "adf_d1D1": adf_d1_d1["p_valor"],
        "adf_d2": adf_d2["p_valor"],
        "d_sugerido": d_sugerido,
        "D_sugerido": 1,
        "factor_max_mes": max_mes,
        "factor_min_mes": min_mes,
        "amplitud_estacional_log": estacional.max() - estacional.min(),
    }
