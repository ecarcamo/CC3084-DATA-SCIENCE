from math import isfinite
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SERIES_DIR = ROOT / "insumos" / "series"
RESULTS_DIR = ROOT / "insumos" / "resultados"

GRANULARITY = {
    "month": {"label": "Mensual", "rule": None, "months": 1},
    "quarter": {"label": "Trimestral", "rule": "QS", "months": 3},
    "year": {"label": "Anual", "rule": "YS", "months": 12},
}


def load_labels():
    frame = pd.read_csv(RESULTS_DIR / "comparativo_series.csv", usecols=["clave", "etiqueta", "categoria"])
    return frame.set_index("clave")


def load_series(key):
    frame = pd.read_csv(SERIES_DIR / f"serie_{key}.csv", parse_dates=["fecha"])
    return frame.set_index("fecha")["viajeros"]


def aggregate(series, granularity):
    spec = GRANULARITY[granularity]
    if spec["rule"] is None:
        return series
    grouped = series.resample(spec["rule"])
    totals = grouped.sum()
    counts = grouped.count()
    return totals[counts == spec["months"]]


def incomplete_periods(series, granularity):
    spec = GRANULARITY[granularity]
    if spec["rule"] is None or series.empty:
        return pd.Series(dtype=int)
    counts = series.resample(spec["rule"]).count()
    return counts[counts < spec["months"]]


def slice_range(series, start, end):
    return series.loc[pd.Timestamp(start):pd.Timestamp(end)]


def monthly_series(key):
    if key not in load_labels().index:
        raise ValueError("Seleccione una serie disponible.")
    try:
        series = load_series(key)
    except (OSError, ValueError, KeyError) as error:
        raise ValueError("No se pudo leer la serie mensual seleccionada.") from error
    if not isinstance(series.index, pd.DatetimeIndex) or series.index.hasnans:
        raise ValueError("La serie contiene fechas inválidas.")
    if series.index.to_period("M").has_duplicates:
        raise ValueError("La serie contiene meses repetidos; deben revisarse antes de comparar.")
    if not series.index.is_month_start.all():
        raise ValueError("Las fechas deben identificar el inicio de cada mes.")
    if series.empty:
        raise ValueError("La serie no contiene observaciones mensuales.")
    values = pd.to_numeric(series, errors="coerce")
    return values.where(values.map(isfinite) & values.ge(0)).sort_index()


def select_years(series, years):
    if not years or len(years) != 2 or any(not isinstance(year, int) for year in years):
        raise ValueError("Seleccione un rango de años válido.")
    first, last = years
    if first > last or first < series.index.year.min() or last > series.index.year.max():
        raise ValueError("Seleccione años dentro de la cobertura de la serie, en orden.")
    months = pd.date_range(f"{first}-01-01", f"{last}-12-01", freq="MS")
    return series.reindex(months)
