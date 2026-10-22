import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import data
from app.theme import COLORS, build_template

LABELS = data.load_labels()
SERIES_OPTIONS = [
    {"label": f"{row.etiqueta} ({row.categoria})", "value": key}
    for key, row in LABELS.iterrows()
]
GRANULARITY_OPTIONS = [
    {"label": spec["label"], "value": key} for key, spec in data.GRANULARITY.items()
]
TEMPLATE = build_template()
EMPTY_MESSAGE = "No hay datos para esta selección. Amplíe el rango de fechas o elija otro nivel de detalle."


def build_figure(series_key, granularity, start, end):
    series = data.aggregate(data.load_series(series_key), granularity)
    series = data.slice_range(series, start, end)
    label = LABELS.loc[series_key, "etiqueta"]
    figure = go.Figure(layout={"template": TEMPLATE, "height": 420})
    if series.empty:
        figure.add_annotation(
            text=EMPTY_MESSAGE, xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font={"size": 16, "color": COLORS["muted"]},
        )
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure
    unit = {"month": "mes", "quarter": "trimestre", "year": "año"}[granularity]
    figure.add_trace(
        go.Scatter(
            x=series.index, y=series.values, mode="lines+markers" if granularity == "year" else "lines",
            name=label, line={"color": COLORS["observed"], "width": 2.5},
            hovertemplate=f"%{{x|%b %Y}}<br><b>%{{y:,.0f}}</b> viajeros por {unit}<extra></extra>",
        )
    )
    figure.update_yaxes(title_text=f"Viajeros por {unit}", tickformat=",")
    figure.update_xaxes(title_text=None)
    figure.update_layout(showlegend=False)
    return figure


def layout():
    return html.Section(
        className="card",
        children=[
            html.H2("¿Cómo ha evolucionado el ingreso de viajeros?", className="card-title"),
            html.P(
                "Datos observados de ingreso de viajeros internacionales a Guatemala (enero 2009 a junio 2026). "
                "Elija la serie y el nivel de detalle; arrastre sobre la gráfica para acercarse a un periodo.",
                className="card-text",
            ),
            html.Div(
                className="controls",
                children=[
                    html.Div([
                        html.Label("Serie", htmlFor="series-selector"),
                        dcc.Dropdown(id="series-selector", options=SERIES_OPTIONS, value="total", clearable=False),
                    ]),
                    html.Div([
                        html.Label("Nivel de detalle", htmlFor="granularity-selector"),
                        dcc.RadioItems(
                            id="granularity-selector", options=GRANULARITY_OPTIONS, value="month",
                            inline=True, className="radio",
                        ),
                    ]),
                    html.Div([
                        html.Label("Rango de fechas", htmlFor="date-range"),
                        dcc.DatePickerRange(
                            id="date-range", min_date_allowed="2009-01-01", max_date_allowed="2026-06-30",
                            start_date="2009-01-01", end_date="2026-06-30", display_format="MMM YYYY",
                            minimum_nights=0,
                        ),
                    ]),
                ],
            ),
            dcc.Graph(id="time-series-graph", config={"displaylogo": False, "locale": "es"}),
            html.P(id="granularity-note", className="note"),
        ],
    )


def register(app):
    @app.callback(
        Output("time-series-graph", "figure"),
        Output("granularity-note", "children"),
        Input("series-selector", "value"),
        Input("granularity-selector", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    )
    def update(series_key, granularity, start, end):
        note = ""
        if granularity != "month":
            note = "Solo se muestran periodos completos; el año 2026 aún no aparece porque llega hasta junio."
        return build_figure(series_key, granularity, start or "2009-01-01", end or "2026-06-30"), note
