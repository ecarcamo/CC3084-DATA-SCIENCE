import itertools
import warnings

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.stats.diagnostic import acorr_ljungbox
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
