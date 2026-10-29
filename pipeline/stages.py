import hashlib
from pathlib import Path

import pandas as pd


def read_source(config):
    path = Path(config["source"]["path"])
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró la fuente institucional: {path}")
    return pd.read_excel(path, sheet_name=config["source"]["sheet"], engine="openpyxl")


def prepare_series(df, config):
    selected = df.loc[df["Tipo de Viajero"].isin(config["target"]["visitor_types"])]
    if selected.empty:
        raise ValueError("La fuente no contiene los tipos de visitantes configurados.")
    dates = pd.to_datetime({
        "year": selected["Año"],
        "month": selected["Mes cod"],
        "day": 1,
    })
    values = pd.to_numeric(selected[config["source"]["value_column"]], errors="raise")
    series = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(dates), name="value")
    series = series.groupby(level=0).sum(min_count=1).sort_index().asfreq("MS")
    return series * config["destination"]["allocation_factor"]


def source_fingerprint(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
