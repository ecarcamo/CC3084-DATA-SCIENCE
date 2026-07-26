import itertools
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX


def ajustar_sarima(
    serie_log: pd.Series,
    order: tuple[int, int, int],
    seasonal_order: tuple[int, int, int, int],
):
    modelo = SARIMAX(
        serie_log,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    return modelo.fit(disp=False)


def grid_sarima(
    serie_log: pd.Series,
    d: int,
    D: int,
    max_p: int = 2,
    max_q: int = 2,
    max_P: int = 1,
    max_Q: int = 1,
) -> pd.DataFrame:
    combinaciones = itertools.product(
        range(max_p + 1),
        range(max_q + 1),
        range(max_P + 1),
        range(max_Q + 1),
    )
    resultados = []

    for p, q, P, Q in combinaciones:
        order = (p, d, q)
        seasonal_order = (P, D, Q, 12)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ajuste = ajustar_sarima(serie_log, order, seasonal_order)
            resultados.append(
                {
                    "order": order,
                    "seasonal_order": seasonal_order,
                    "aic": ajuste.aic,
                    "bic": ajuste.bic,
                    "converged": bool(ajuste.mle_retvals.get("converged", False)),
                }
            )
        except (ValueError, ArithmeticError, RuntimeError, MemoryError):
            resultados.append(
                {
                    "order": order,
                    "seasonal_order": seasonal_order,
                    "aic": float("inf"),
                    "bic": float("inf"),
                    "converged": False,
                }
            )

    return pd.DataFrame(resultados).sort_values("aic").reset_index(drop=True)


def diagnostico_residuos(modelo) -> tuple[dict, plt.Figure]:
    residuos = pd.Series(modelo.resid).dropna()
    ljung_box = acorr_ljungbox(residuos, lags=[12], return_df=True).iloc[0]
    jarque = jarque_bera(residuos)
    figura = modelo.plot_diagnostics(figsize=(11, 8))
    resultado = {
        "ljung_box_estadistico": ljung_box["lb_stat"],
        "ljung_box_p": ljung_box["lb_pvalue"],
        "jarque_bera_estadistico": jarque.statistic,
        "jarque_bera_p": jarque.pvalue,
    }
    return resultado, figura


def modelo_holt_winters(
    serie_train: pd.Series,
    horizonte: int,
) -> pd.Series:
    serie_log = np.log1p(serie_train.astype(float))
    modelo = ExponentialSmoothing(
        serie_log,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    ).fit(optimized=True)
    pronostico = np.expm1(modelo.forecast(horizonte)).clip(lower=0)
    pronostico.name = "holt_winters"
    return pronostico


def modelo_ses(
    serie_train: pd.Series,
    horizonte: int,
) -> pd.Series:
    serie_log = np.log1p(serie_train.astype(float))
    modelo = SimpleExpSmoothing(
        serie_log,
        initialization_method="estimated",
    ).fit(optimized=True)
    pronostico = np.expm1(modelo.forecast(horizonte)).clip(lower=0)
    pronostico.name = "ses"
    return pronostico


def modelo_seasonal_naive(
    serie_train: pd.Series,
    horizonte: int,
) -> pd.Series:
    if len(serie_train) < 12:
        raise ValueError("Seasonal naive requiere al menos doce observaciones")
    repeticiones = int(np.ceil(horizonte / 12))
    valores = np.tile(serie_train.iloc[-12:].to_numpy(), repeticiones)[:horizonte]
    indice = pd.date_range(
        serie_train.index[-1] + pd.offsets.MonthBegin(),
        periods=horizonte,
        freq="MS",
    )
    return pd.Series(valores, index=indice, name="seasonal_naive")


def modelo_prophet(
    serie_train: pd.Series,
    horizonte: int,
) -> pd.Series:
    from prophet import Prophet

    datos = pd.DataFrame(
        {
            "ds": serie_train.index,
            "y": np.log1p(serie_train.to_numpy(dtype=float)),
        }
    )
    modelo = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    modelo.fit(datos)
    fechas = pd.date_range(
        serie_train.index[-1] + pd.offsets.MonthBegin(),
        periods=horizonte,
        freq="MS",
    )
    futuro = pd.DataFrame({"ds": fechas})
    pronostico = np.expm1(modelo.predict(futuro)["yhat"]).clip(lower=0)
    return pd.Series(
        pronostico.to_numpy(),
        index=fechas,
        name="prophet",
    )
