import logging
from pathlib import Path

import pandas as pd

from app import approved

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]
PROCEDURE_LABELS = {"holt_winters": "Holt-Winters", "seasonal_naive": "Referencia estacional"}
UNAVAILABLE_MESSAGE = (
    "Las estimaciones no están disponibles: todavía no hay una versión aprobada. "
    "Aparecerán aquí cuando el pipeline publique una."
)
_cache = {"key": None, "version": None}


def current_version():
    """Versión aprobada vigente para las gráficas de estimaciones, o `None` si no hay una.

    Se lee al primer uso y se vuelve a leer solo cuando cambia `run.json` en la carpeta aprobada, es decir,
    tras una publicación o una restauración. Cambiar un filtro no relee archivos ni ajusta el modelo.
    """
    folder = Path(approved.approved_dir())
    try:
        stat = (folder / "run.json").stat()
        key = (str(folder), stat.st_ino, stat.st_mtime_ns, stat.st_size)
    except OSError:
        key = (str(folder), None)
    if key != _cache["key"]:
        try:
            version = approved.load_approved(folder)
        except (OSError, ValueError, KeyError):
            logging.getLogger(__name__).exception("No se pudo leer la versión aprobada en %s.", folder)
            version = None
        _cache.update(key=key, version=version)
    return _cache["version"]


def monthly(frame):
    """Valores de `observed` o `estimates` por mes; los meses sin registro quedan vacíos, nunca en cero."""
    values = pd.Series(
        pd.to_numeric(frame["value"], errors="coerce").to_numpy(),
        index=pd.PeriodIndex(frame["period"], freq="M").to_timestamp(),
    ).sort_index()
    if values.empty:
        return values
    return values.reindex(pd.date_range(values.index.min(), values.index.max(), freq="MS"))


def month_name(date):
    return f"{MONTHS[date.month - 1]} de {date.year}"


def number(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def procedure_label(name):
    return PROCEDURE_LABELS.get(name, name)


def updated_label(generated_at):
    moment = pd.Timestamp(generated_at)
    moment = moment.tz_localize("UTC") if moment.tzinfo is None else moment.tz_convert("UTC")
    return f"{moment.day} de {month_name(moment)}, {moment:%H:%M} UTC"


def evaluated_label(periods):
    dates = pd.PeriodIndex(periods, freq="M").sort_values()
    if dates.empty:
        return "ningún mes evaluado"
    first, last = month_name(dates[0]), month_name(dates[-1])
    if len(dates) == 1:
        return f"1 mes evaluado ({first})"
    return f"{len(dates)} meses evaluados entre {first} y {last}"
