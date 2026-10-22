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


def slice_range(series, start, end):
    return series.loc[pd.Timestamp(start):pd.Timestamp(end)]
