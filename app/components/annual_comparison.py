from textwrap import wrap

import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import data
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
EMPTY_MESSAGE = "No hay años completos para esta selección. Cambie la serie o amplíe el rango de años."


def year_options(series_key):
    series = data.monthly_series(series_key)
    first, last = int(series.index.year.min()), int(series.index.year.max())
    marks = {
        year: str(year) for year in range(first, last + 1)
        if year in (first, last) or year % 5 == 0 and first + 3 <= year <= last - 3
    }
    return first, last, marks, [first, last]


def build_figure(series_key, years):
    figure = go.Figure(layout={"template": build_template(), "height": 420})
    try:
        selected = data.select_years(data.monthly_series(series_key), years)
    except ValueError as error:
        message = str(error)
        figure.add_annotation(text="<br>".join(wrap(message, 32)), xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure, message
    yearly = data.aggregate(selected, "year")
    incomplete = data.incomplete_periods(selected, "year")
    omitted = "; ".join(f"{date.year}: {int(count)} de 12 meses válidos" for date, count in incomplete.items())
    exclusions = (
        f"Se excluyó 1 año incompleto: {omitted}. " if len(incomplete) == 1
        else f"Se excluyeron {len(incomplete)} años incompletos: {omitted}. "
    )
    note = (
        f"{LABELS.loc[series_key, 'etiqueta']} · {years[0]}–{years[1]}. "
        f"Se muestran {len(yearly)} años completos, cada uno con doce meses válidos. "
        + (exclusions if omitted else "No se excluyeron años incompletos. ")
        + "Los ceros reales cuentan como observaciones válidas. No se rellenan meses ausentes ni inválidos. "
        "Se compara una sola serie; no se suman vías de ingreso con países de residencia."
    )
    if yearly.empty:
        figure.add_annotation(text="<br>".join(wrap(EMPTY_MESSAGE, 32)), xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure, f"{EMPTY_MESSAGE} {note}"
    figure.add_trace(go.Bar(
        x=yearly.index.year.tolist(), y=yearly.tolist(), name="Total anual observado",
        marker={"color": COLORS["observed"]},
        hovertemplate="%{x}<br><b>%{y:,.0f}</b> viajeros en 12 meses<extra></extra>",
    ))
    figure.update_xaxes(
        title_text="Año", tickmode="auto", nticks=6, tickformat="d", automargin=True,
    )
    figure.update_yaxes(title_text="Viajeros por año", tickformat=",.0f", nticks=5, rangemode="tozero", automargin=True)
    figure.update_layout(showlegend=False)
    return figure, note


def layout():
    first, last, marks, years = year_options("total")
    return html.Section(
        id="annual-comparison", className="card",
        children=[
            html.H2("¿Cómo cambia el total de viajeros entre años completos?", className="card-title"),
            html.P(
                "Compare totales anuales de una misma serie. Solo aparecen años con sus doce meses válidos; "
                "la nota identifica los años excluidos.",
                className="card-text",
            ),
            html.Div(className="controls", children=[
                html.Div([
                    html.Label("Serie", htmlFor="annual-series"),
                    dcc.Dropdown(id="annual-series", options=[
                        {"label": f"{row.etiqueta} · {row.categoria}", "value": key} for key, row in LABELS.iterrows()
                    ], value="total", clearable=False, searchable=False),
                ]),
                html.Div(className="year-range", children=[
                    html.Label("Rango de años", htmlFor="annual-years"),
                    dcc.RangeSlider(
                        id="annual-years", min=first, max=last, marks=marks, step=1,
                        value=years, allowCross=False,
                    ),
                ]),
            ]),
            dcc.Graph(id="annual-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "420px"}),
            html.P(id="annual-note", className="note", role="status"),
        ],
    )


def register(app):
    @app.callback(
        Output("annual-years", "min"), Output("annual-years", "max"),
        Output("annual-years", "marks"), Output("annual-years", "value"),
        Input("annual-series", "value"),
    )
    def update_years(series_key):
        return year_options(series_key)

    @app.callback(
        Output("annual-graph", "figure"), Output("annual-note", "children"),
        Input("annual-series", "value"), Input("annual-years", "value"),
    )
    def update(series_key, years):
        return build_figure(series_key, years)
