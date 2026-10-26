import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import data
from app.theme import COLORS, GRAPH_CONFIG, build_template

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
SHORT_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
UNITS = {"month": ("mes", "meses"), "quarter": ("trimestre", "trimestres"), "year": ("año", "años")}
LISTED_PERIODS = 4


def period_label(date, granularity):
    if granularity == "year":
        return str(date.year)
    if granularity == "quarter":
        return f"T{date.quarter} {date.year} ({SHORT_MONTHS[date.month - 1]}–{SHORT_MONTHS[date.month + 1]})"
    return f"{SHORT_MONTHS[date.month - 1]} {date.year}"


def build_note(series_key, granularity, start, end):
    if granularity == "month":
        return "Cada punto es el número de viajeros registrados en un mes."
    singular, plural = UNITS[granularity]
    series = data.slice_range(data.load_series(series_key), start, end)
    incomplete = data.incomplete_periods(series, granularity)
    months = data.GRANULARITY[granularity]["months"]
    note = f"Cada punto suma los viajeros de un {singular} completo ({months} meses con dato)."
    if incomplete.empty:
        return f"{note} Todos los {plural} del rango elegido están completos."
    listed = [f"{period_label(date, granularity)}, {count} de {months} meses" for date, count in incomplete.items()]
    if len(listed) > LISTED_PERIODS:
        listed = listed[:LISTED_PERIODS] + [f"y {len(incomplete) - LISTED_PERIODS} más"]
    noun = singular if len(incomplete) == 1 else plural
    omitted = "Se omitió" if len(incomplete) == 1 else "Se omitieron"
    adjective = "incompleto" if len(incomplete) == 1 else "incompletos"
    return (
        f"{note} {omitted} {len(incomplete)} {noun} {adjective} para no presentar un total parcial como completo: "
        f"{'; '.join(listed)}."
    )


def build_figure(series_key, granularity, start, end):
    series = data.slice_range(data.load_series(series_key), start, end)
    series = data.aggregate(series, granularity)
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
    unit = UNITS[granularity][0]
    figure.add_trace(
        go.Scatter(
            x=series.index, y=series.values, mode="lines+markers" if granularity == "year" else "lines",
            name=label, line={"color": COLORS["observed"], "width": 2.5},
            customdata=[period_label(date, granularity) for date in series.index],
            hovertemplate=f"%{{customdata}}<br><b>%{{y:,.0f}}</b> viajeros por {unit}<extra></extra>",
        )
    )
    figure.update_yaxes(title_text=f"Viajeros por {unit}", tickformat=",", automargin=True)
    figure.update_xaxes(title_text=None)
    figure.update_layout(showlegend=False)
    return figure


def layout():
    return html.Section(
        id="evolution",
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
                            start_date="2009-01-01", end_date="2026-06-30", display_format="DD/MM/YYYY",
                            start_date_placeholder_text="Fecha inicial", end_date_placeholder_text="Fecha final",
                            minimum_nights=0,
                        ),
                    ]),
                ],
            ),
            dcc.Graph(id="time-series-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "420px"}),
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
        start, end = start or "2009-01-01", end or "2026-06-30"
        return build_figure(series_key, granularity, start, end), build_note(series_key, granularity, start, end)
