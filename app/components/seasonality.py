from textwrap import wrap

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import data
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
EMPTY_MESSAGE = "No hay datos válidos para esta selección. Cambie la serie o el rango de años."


def year_options(series_key):
    series = data.monthly_series(series_key)
    first, last = int(series.index.year.min()), int(series.index.year.max())
    marks = {
        year: str(year) for year in range(first, last + 1)
        if year in (first, last) or year % 5 == 0 and first + 3 <= year <= last - 3
    }
    return first, last, marks, [first, last]


def build_figure(series_key, years):
    figure = go.Figure(layout={"template": build_template(), "height": 520})
    try:
        selected = data.select_years(data.monthly_series(series_key), years)
        if not selected.notna().any():
            raise ValueError(EMPTY_MESSAGE)
    except ValueError as error:
        message = str(error)
        figure.add_annotation(text="<br>".join(wrap(message, 32)), xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure, message
    rows = list(range(years[0], years[1] + 1))
    matrix = selected.to_numpy().reshape(len(rows), 12)
    values = [[None if pd.isna(value) else float(value) for value in row] for row in matrix]
    figure.add_trace(go.Heatmap(
        x=list(range(1, 13)), y=rows, z=values, zmin=0,
        colorscale=[[0, "#E7EFF6"], [1, COLORS["observed"]]],
        colorbar={
            "title": {"text": "Viajeros por mes", "side": "top"},
            "orientation": "h", "y": -0.35, "len": 0.95, "nticks": 3, "tickformat": ",.0f",
        },
        xgap=2, ygap=2, hoverongaps=False,
        customdata=[MONTHS for year in rows],
        hovertemplate="%{customdata} %{y}<br><b>%{z:,.0f}</b> viajeros<extra></extra>",
    ))
    missing = selected[selected.isna()]
    if not missing.empty:
        figure.add_trace(go.Scatter(
            x=missing.index.month.tolist(), y=missing.index.year.tolist(), mode="markers",
            marker={"symbol": "x", "size": 7, "color": COLORS["muted"]}, name="Sin dato válido",
            customdata=[MONTHS[date.month - 1] for date in missing.index],
            hovertemplate="%{customdata} %{y}<br>Sin dato válido<extra></extra>", showlegend=False,
        ))
    figure.update_xaxes(
        title_text=None, tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTHS,
        tickangle=-45, fixedrange=True,
    )
    figure.update_yaxes(title_text="Año", tickmode="array", tickvals=rows, autorange="reversed", fixedrange=True)
    figure.update_layout(margin={"l": 60, "r": 15, "t": 20, "b": 160})
    note = (
        f"{LABELS.loc[series_key, 'etiqueta']} · {years[0]}–{years[1]}. "
        f"{int(selected.notna().sum())} meses con dato válido; {len(missing)} sin dato válido. "
        "Azul más intenso indica más viajeros; una × indica un mes ausente o inválido, no cero. "
        "El cero real conserva el azul más claro. La escala se ajusta a la selección, con mínimo cero; "
        "no se comparan intensidades entre selecciones distintas. "
        "El patrón describe la distribución temporal y no demuestra sus causas."
    )
    return figure, note


def layout():
    first, last, marks, years = year_options("total")
    return html.Section(
        id="seasonality", className="card",
        children=[
            html.H2("¿En qué meses se concentra el ingreso de viajeros?", className="card-title"),
            html.P(
                "Compare los meses de cada año. Pase el cursor sobre una celda para consultar su valor; "
                "los meses sin dato se marcan con una ×.",
                className="card-text",
            ),
            html.Div(className="controls", children=[
                html.Div([
                    html.Label("Serie", htmlFor="seasonality-series"),
                    dcc.Dropdown(id="seasonality-series", options=[
                        {"label": f"{row.etiqueta} · {row.categoria}", "value": key} for key, row in LABELS.iterrows()
                    ], value="total", clearable=False, searchable=False),
                ]),
                html.Div(className="year-range", children=[
                    html.Label("Rango de años", htmlFor="seasonality-years"),
                    dcc.RangeSlider(
                        id="seasonality-years", min=first, max=last, marks=marks, step=1,
                        value=years, allowCross=False,
                    ),
                ]),
            ]),
            dcc.Graph(id="seasonality-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "520px"}),
            html.P(id="seasonality-note", className="note", role="status"),
        ],
    )


def register(app):
    @app.callback(
        Output("seasonality-years", "min"), Output("seasonality-years", "max"),
        Output("seasonality-years", "marks"), Output("seasonality-years", "value"),
        Input("seasonality-series", "value"),
    )
    def update_years(series_key):
        return year_options(series_key)

    @app.callback(
        Output("seasonality-graph", "figure"), Output("seasonality-note", "children"),
        Input("seasonality-series", "value"), Input("seasonality-years", "value"),
    )
    def update(series_key, years):
        return build_figure(series_key, years)
