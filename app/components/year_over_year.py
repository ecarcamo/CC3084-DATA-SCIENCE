from textwrap import wrap

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import data
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
REFERENCE = data.monthly_series("total")
FIRST, LAST = REFERENCE.index.min(), REFERENCE.index.max()
DEFAULT_START = FIRST + pd.DateOffset(years=1)
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]
REASONS = {
    "missing_current": "sin dato válido en el mes",
    "missing_previous": "sin dato válido del mismo mes del año anterior",
    "zero_previous": "el mismo mes del año anterior registró cero viajeros",
}
LISTED_MONTHS = 4
EMPTY_MESSAGE = (
    "No se puede calcular la variación interanual para ningún mes de esta selección. "
    "Elija fechas posteriores al primer año de la serie o cambie la serie."
)


def month_name(date):
    return f"{MONTHS[date.month - 1]} de {date.year}"


def year_over_year(series):
    previous = series.shift(freq=pd.DateOffset(years=1)).reindex(series.index)
    frame = pd.DataFrame({"current": series, "previous": previous})
    frame["reason"] = None
    frame.loc[frame["previous"] == 0, "reason"] = "zero_previous"
    frame.loc[frame["previous"].isna(), "reason"] = "missing_previous"
    frame.loc[frame["current"].isna(), "reason"] = "missing_current"
    valid = frame["reason"].isna()
    frame["variation"] = (frame["current"] / frame["previous"].where(valid) - 1) * 100
    return frame


def select_dates(frame, start, end):
    try:
        first, last = pd.Timestamp(start or DEFAULT_START), pd.Timestamp(end or LAST)
    except (TypeError, ValueError) as error:
        raise ValueError("Seleccione un rango de fechas válido.") from error
    if pd.isna(first) or pd.isna(last):
        raise ValueError("Seleccione un rango de fechas válido.")
    if first > last:
        raise ValueError("La fecha inicial debe ser anterior o igual a la fecha final.")
    return frame.loc[first:last]


def _empty_figure(figure, message, note=None):
    figure.add_annotation(
        text="<br>".join(wrap(message, 48)), xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
        font={"size": 16, "color": COLORS["muted"]},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure, note or message


def build_note(series_key, frame):
    computed = frame.dropna(subset=["variation"])
    missing = frame[frame["variation"].isna()]
    note = (
        f"{LABELS.loc[series_key, 'etiqueta']} · {month_name(frame.index.min())} a {month_name(frame.index.max())}. "
        f"{len(computed)} meses con variación calculada como (viajeros del mes ÷ viajeros del mismo mes del año "
        "anterior − 1) × 100. Un valor positivo indica más viajeros que un año antes; uno negativo, menos."
    )
    if missing.empty:
        note += " Todos los meses del rango tienen una base válida de comparación."
    else:
        listed = [f"{month_name(date)}: {REASONS[reason]}" for date, reason in missing["reason"].items()]
        if len(listed) > LISTED_MONTHS:
            listed = listed[:LISTED_MONTHS] + [f"y {len(missing) - LISTED_MONTHS} más"]
        note += (
            f" {len(missing)} meses no se pueden calcular y se marcan con una ×, no con cero: {'; '.join(listed)}."
        )
    return (
        f"{note} Cuando el año anterior tuvo pocos viajeros, como en 2020, el porcentaje puede ser muy grande; "
        "el cursor muestra los valores de ambos meses. La variación describe el cambio registrado y no explica sus causas."
    )


def build_figure(series_key, start, end):
    figure = go.Figure(layout={"template": build_template(), "height": 420})
    try:
        frame = select_dates(year_over_year(data.monthly_series(series_key)), start, end)
    except ValueError as error:
        return _empty_figure(figure, str(error))
    if frame.empty:
        return _empty_figure(figure, "No hay meses en el rango elegido. Amplíe las fechas.")
    if frame["variation"].isna().all():
        return _empty_figure(figure, EMPTY_MESSAGE, f"{EMPTY_MESSAGE} {build_note(series_key, frame)}")
    computed = frame.dropna(subset=["variation"])
    figure.add_trace(go.Bar(
        x=computed.index.tolist(), y=computed["variation"].tolist(), name="Variación interanual",
        marker={"color": COLORS["observed"]},
        customdata=[[month_name(date), current, previous]
                    for date, current, previous in zip(computed.index, computed["current"], computed["previous"])],
        hovertemplate=(
            "%{customdata[0]}<br><b>%{y:+,.1f} %</b> respecto al año anterior<br>"
            "%{customdata[1]:,.0f} viajeros frente a %{customdata[2]:,.0f}<extra></extra>"
        ),
    ))
    missing = frame[frame["variation"].isna()]
    if not missing.empty:
        figure.add_trace(go.Scatter(
            x=missing.index.tolist(), y=[0] * len(missing), mode="markers", name="Sin base válida",
            marker={"symbol": "x", "size": 8, "color": COLORS["muted"]},
            customdata=[[month_name(date), REASONS[reason]] for date, reason in missing["reason"].items()],
            hovertemplate="%{customdata[0]}<br>No se puede calcular: %{customdata[1]}<extra></extra>",
        ))
    figure.add_hline(y=0, line_dash="dash", line_color=COLORS["muted"])
    figure.update_yaxes(title_text="Variación interanual (%)", ticksuffix=" %", tickformat=",.0f", automargin=True)
    figure.update_xaxes(title_text=None, automargin=True)
    figure.update_layout(showlegend=False, bargap=0.15)
    return figure, build_note(series_key, frame)


def layout():
    return html.Section(
        id="year-over-year", className="card",
        children=[
            html.H2("G5 · ¿Cuánto cambió cada mes frente al mismo mes del año anterior?", className="card-title"),
            html.P(
                "Cada barra compara un mes con el mismo mes del año anterior, por lo que la temporada no "
                "distorsiona la comparación. La línea discontinua marca 0 %: igual que un año antes. "
                "Elija la serie y el periodo; pase el cursor para ver ambos valores.",
                className="card-text",
            ),
            html.Div(className="controls", children=[
                html.Div([
                    html.Label("Serie", htmlFor="yoy-series"),
                    dcc.Dropdown(id="yoy-series", options=[
                        {"label": f"{row.etiqueta} ({row.categoria})", "value": key} for key, row in LABELS.iterrows()
                    ], value="total", clearable=False, searchable=False),
                ]),
                html.Div([
                    html.Label("Rango de fechas", htmlFor="yoy-dates"),
                    dcc.DatePickerRange(
                        id="yoy-dates", min_date_allowed=FIRST.date(), max_date_allowed=LAST.date(),
                        start_date=DEFAULT_START.date(), end_date=LAST.date(), display_format="DD/MM/YYYY",
                        start_date_placeholder_text="Fecha inicial", end_date_placeholder_text="Fecha final",
                        minimum_nights=0,
                    ),
                ]),
            ]),
            dcc.Graph(id="yoy-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "420px"}),
            html.P(id="yoy-note", className="note", role="status"),
        ],
    )


def register(app):
    @app.callback(
        Output("yoy-graph", "figure"), Output("yoy-note", "children"),
        Input("yoy-series", "value"), Input("yoy-dates", "start_date"), Input("yoy-dates", "end_date"),
    )
    def update(series_key, start, end):
        return build_figure(series_key, start, end)
