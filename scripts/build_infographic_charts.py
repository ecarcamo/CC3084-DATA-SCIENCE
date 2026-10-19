from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "insumos"
OUTPUT = ROOT / "infografia" / "graficas"
BG, JADE, SAGE, TEXT, ACCENT = "#F4F0E6", "#1E4D45", "#8DA197", "#26292B", "#C4552D"
SIZES = {
    "01_panorama.png": (10.0, 2.4),
    "02_estacionalidad.png": (4.875, 2.29),
    "03_cuadrante.png": (4.875, 2.29),
    "04_modelos.png": (4.875, 2.135),
    "05_pronostico.png": (4.875, 2.135),
}
MODEL_NAMES = {
    "ses": "SES\nsuavizamiento simple",
    "holt_winters": "Holt-Winters",
    "seasonal_naive": "Ingenuo estacional",
    "sarima": "SARIMA",
    "prophet": "Prophet",
}


def configure_style():
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "Source Sans 3" if "Source Sans 3" in fonts else "DejaVu Sans",
        "font.size": 11,
        "text.color": TEXT,
        "axes.labelcolor": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "axes.facecolor": BG,
        "figure.facecolor": BG,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": SAGE,
        "axes.labelsize": 11,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "savefig.bbox": None,
    })


def load_series(key):
    frame = pd.read_csv(INPUT / "series" / f"serie_{key}.csv", parse_dates=["fecha"])
    return frame.set_index("fecha")["viajeros"].asfreq("MS")


def seasonal_factors(series):
    baseline = np.log1p(series.loc["2009":"2019"])
    return np.exp(baseline.groupby(baseline.index.month).mean() - baseline.mean())


def fit_forecast(series):
    train = series.loc["2009":"2021-03"]
    test = series.loc["2021-04":"2026-06"]
    fitted = SimpleExpSmoothing(
        np.log1p(train), initialization_method="estimated"
    ).fit(optimized=True)
    forecast_log = fitted.forecast(len(test))
    alpha = fitted.params["smoothing_level"]
    variance = np.sum(fitted.resid ** 2) / (len(train) - 1)
    deviation = np.sqrt(variance * (1 + np.arange(len(test)) * alpha ** 2))
    result = pd.DataFrame({"forecast": np.expm1(forecast_log).clip(lower=0)})
    for level, z in ((80, 1.2816), (95, 1.96)):
        result[f"lower_{level}"] = np.expm1(forecast_log - z * deviation).clip(lower=0)
        result[f"upper_{level}"] = np.expm1(forecast_log + z * deviation)
    return result


def make_figure(filename):
    return plt.figure(figsize=SIZES[filename], dpi=300)


def style_axis(ax, horizontal=False):
    ax.set_axisbelow(True)
    ax.grid(axis="x" if horizontal else "y", color=SAGE, alpha=0.3, linewidth=0.5)
    ax.tick_params(length=0, pad=3)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(SAGE)


def thousands(value, position):
    return "0" if value == 0 else f"{value / 1000:,.0f} mil"


def panorama(series):
    fig = make_figure("01_panorama.png")
    ax = fig.add_axes([0.09, 0.16, 0.895, 0.78])
    style_axis(ax)
    ax.plot(series.index, series, color=JADE, linewidth=1.3)
    ax.set(xlim=(pd.Timestamp("2009-01-01"), pd.Timestamp("2026-12-01")),
           ylim=(0, 790000), yticks=[0, 200000, 400000, 600000])
    ax.yaxis.set_major_formatter(FuncFormatter(thousands))
    ax.xaxis.set_major_locator(mdates.YearLocator(3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.axvspan(pd.Timestamp("2020-04-01"), pd.Timestamp("2020-09-01"),
               color=ACCENT, alpha=0.15, linewidth=0)
    ax.axvline(pd.Timestamp("2023-01-01"), color=SAGE, linestyle=":", linewidth=1.2)
    arrow = {"arrowstyle": "-", "color": TEXT, "linewidth": 0.7}
    ax.scatter(pd.Timestamp("2019-12-01"), series.loc["2019-12-01"], color=JADE, s=13)
    ax.annotate("Pico prepandemia: 515,820 (dic. 2019)",
                xy=(pd.Timestamp("2019-12-01"), series.loc["2019-12-01"]),
                xytext=(pd.Timestamp("2012-03-01"), 690000), arrowprops=arrow)
    ax.text(pd.Timestamp("2020-06-01"), 770000, "Cierre de fronteras",
            ha="center", va="top")
    ax.scatter(pd.Timestamp("2020-05-01"), series.loc["2020-05-01"], color=ACCENT, s=16)
    ax.annotate("9,779 (mayo 2020)",
                xy=(pd.Timestamp("2020-05-01"), series.loc["2020-05-01"]),
                xytext=(pd.Timestamp("2015-08-01"), 90000), arrowprops=arrow)
    ax.annotate("2022: 92 % de 2019",
                xy=(pd.Timestamp("2022-07-01"), series.loc["2022-07-01"]),
                xytext=(pd.Timestamp("2020-12-01"), 575000), arrowprops=arrow)
    ax.text(pd.Timestamp("2026-09-01"), 690000, "Cambio de método (2023)",
            ha="right")
    ax.annotate("2026: enero a junio",
                xy=(series.index[-1], series.iloc[-1]),
                xytext=(pd.Timestamp("2026-09-01"), 460000),
                ha="right", arrowprops=arrow)
    return fig


def seasonality(series):
    fig = make_figure("02_estacionalidad.png")
    ax = fig.add_axes([0.12, 0.18, 0.85, 0.57])
    style_axis(ax)
    values = (seasonal_factors(series) - 1) * 100
    colors = [ACCENT if month == 12 else JADE if value >= 0 else SAGE
              for month, value in values.items()]
    ax.bar(values.index, values, color=colors, width=0.7)
    ax.axhline(0, color=TEXT, linewidth=0.7)
    ax.set(xlim=(0.3, 12.8), ylim=(-27, 45), yticks=[-20, 0, 20, 40],
           xticks=range(1, 13),
           xticklabels=["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{value:+.0f} %" if value else "0"))
    ax.text(12, values.loc[12] + 1, "+37 %", ha="center", va="bottom")
    ax.text(9, values.loc[9] - 1, "−20 %", ha="center", va="top")
    for x, label in ((3.5, "Semana\nSanta"), (7, "Vacaciones\ny bono 14"),
                     (12, "Aguinaldo\ny fiestas")):
        ax.annotate(label, xy=(x, 42), xycoords="data",
                    xytext=(x, 60), textcoords="data",
                    ha="right" if x == 12 else "center", va="center",
                    annotation_clip=False,
                    arrowprops={"arrowstyle": "-", "color": SAGE, "linewidth": 0.7})
    fig.text(0.97, 0.01, "Septiembre: mes más bajo", ha="right", va="bottom")
    return fig


def route_comparison():
    fig = make_figure("03_cuadrante.png")
    keys = ["via_aerea", "via_terrestre", "via_maritima"]
    comparison = pd.read_csv(INPUT / "resultados" / "comparativo_series.csv").set_index("clave").loc[keys]
    recovery = []
    for key in keys:
        series = load_series(key)
        recovery.append(series.loc["2025"].sum() / series.loc["2019"].sum() * 100)
    panels = [
        ("¿Más estacional? (Fs)", comparison["fs"].to_numpy(), 2, 0.5, ".3f", ""),
        ("¿Crece más? (%/mes)\n2009–2019", comparison["pendiente_pct_media"].to_numpy(), 1, 1.7, ".2f", " %"),
        ("¿Más volátil? (CV)", comparison["cv_2009_2019"].to_numpy(), 2, 1.0, ".2f", ""),
        ("Recuperación en 2025\nfrente a 2019", np.array(recovery), 2, 110, ".0f", " %"),
    ]
    for index, (label, values, winner, limit, precision, suffix) in enumerate(panels):
        row, column = divmod(index, 2)
        left, bottom = (0.21 if column == 0 else 0.65), (0.55 if row == 0 else 0.09)
        ax = fig.add_axes([left, bottom, 0.32, 0.28])
        ax.barh(range(3), values, height=0.65,
                color=[ACCENT if i == winner else SAGE for i in range(3)])
        ax.set(xlim=(0, limit), ylim=(2.6, -0.6), xticks=[], yticks=range(3),
               yticklabels=["Aérea", "Terrestre", "Marítima"] if column == 0 else [])
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.text(left - (0.19 if column == 0 else 0.08), bottom + 0.30,
                 label, va="bottom", linespacing=1.0)
        for i, value in enumerate(values):
            if i == winner or index == 3:
                ax.text(value + limit * 0.025, i, f"{value:{precision}}{suffix}",
                        va="center")
    fig.text(0.97, 0.005, "Marítima: la más golpeada", ha="right", va="bottom")
    return fig


def models():
    fig = make_figure("04_modelos.png")
    ax = fig.add_axes([0.44, 0.19, 0.52, 0.75])
    style_axis(ax, horizontal=True)
    metrics = pd.read_csv(INPUT / "resultados" / "metricas_modelos.csv")
    metrics = metrics.loc[metrics["serie"].eq("total")].sort_values("mae")
    y = np.arange(len(metrics), dtype=float)
    for offset, metric, base_color, alpha in ((-0.17, "mae", JADE, 1), (0.17, "rmse", SAGE, 0.45)):
        for i, (_, model) in enumerate(metrics.iterrows()):
            winner = model["modelo"] == "ses"
            color = ACCENT if winner else base_color
            ax.barh(i + offset, model[metric] / 1000, height=0.29,
                    color=color, alpha=alpha if winner else 1)
    for i, (_, model) in enumerate(metrics.iterrows()):
        ax.text(450, i, f"{model['mae'] / 1000:.0f} / {model['rmse'] / 1000:.0f}",
                ha="right", va="center")
    ax.set(xlim=(0, 460), ylim=(4.6, -1.1), xticks=[0, 150, 300],
           yticks=y, yticklabels=[MODEL_NAMES[key] for key in metrics["modelo"]])
    ax.text(450, -0.73, "MAE / RMSE", ha="right", va="center")
    fig.text(0.97, 0.005, "Error en miles de viajeros · menor es mejor",
             ha="right", va="bottom")
    return fig


def forecast_chart(series, forecast):
    fig = make_figure("05_pronostico.png")
    ax = fig.add_axes([0.18, 0.18, 0.79, 0.59])
    style_axis(ax)
    for level, alpha in ((95, 0.18), (80, 0.35)):
        ax.fill_between(forecast.index, forecast[f"lower_{level}"],
                        forecast[f"upper_{level}"], color=ACCENT, alpha=alpha, linewidth=0)
    actual = series.loc["2018":]
    ax.plot(actual.index, actual, color=JADE, linewidth=1.2)
    ax.plot(forecast.index, forecast["forecast"], color=TEXT, linestyle="--", linewidth=1.1)
    ax.axvline(pd.Timestamp("2021-03-01"), color=SAGE, linestyle=":", linewidth=1)
    ax.set(xlim=(pd.Timestamp("2018-01-01"), pd.Timestamp("2026-12-01")),
           ylim=(0, 700000), yticks=[0, 300000, 600000])
    ax.yaxis.set_major_formatter(FuncFormatter(thousands))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.text(0.03, 0.98, "La banda sigue subiendo: en 2026, el 95 %\nva de 0.6 mil a 17 M al mes.", va="top")
    ax.text(pd.Timestamp("2023-07-01"), 675000, "Estimación 95 %", ha="center", va="top")
    ax.text(pd.Timestamp("2023-07-01"), 510000, "Estimación 80 %", ha="center",
            bbox={"facecolor": BG, "edgecolor": "none", "pad": 0.5})
    ax.text(pd.Timestamp("2026-09-01"), 135000, "Pronóstico: 105 mil al mes",
            ha="right", va="bottom")
    ax.annotate("Fin del\nentrenamiento",
                xy=(pd.Timestamp("2021-03-01"), 410000),
                xytext=(pd.Timestamp("2018-02-01"), 235000), va="top",
                arrowprops={"arrowstyle": "-", "color": TEXT, "linewidth": 0.7})
    return fig


def build_charts():
    configure_style()
    total = load_series("total")
    factors = seasonal_factors(total)
    np.testing.assert_allclose(factors.loc[[12, 9]], [1.372, 0.802], atol=0.0005, rtol=0)
    forecast = fit_forecast(total)
    saved = pd.read_csv(INPUT / "resultados" / "predicciones" / "total_ses.csv",
                        parse_dates=["fecha"]).set_index("fecha")["prediccion"]
    pd.testing.assert_index_equal(forecast.index, saved.index, check_names=False)
    np.testing.assert_allclose(forecast["forecast"], saved, atol=0.01, rtol=0)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    figures = [
        panorama(total), seasonality(total), route_comparison(),
        models(), forecast_chart(total, forecast),
    ]
    for filename, fig in zip(SIZES, figures):
        fig.savefig(OUTPUT / filename, dpi=300, facecolor=BG, bbox_inches=None)
        plt.close(fig)
        print(OUTPUT / filename)


if __name__ == "__main__":
    build_charts()
