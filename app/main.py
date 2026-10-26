from dash import Dash, Input, Output, State, dcc, html

from app.components import (
    annual_comparison, model_deviations, model_errors, predictions, ranking, seasonality, time_series,
    year_over_year,
)

OBSERVED = [
    ("evolution", "G1 · Evolución temporal", time_series),
    ("ranking", "G2 · Comparación por vía o país", ranking),
    ("seasonality", "G3 · Meses de mayor ingreso", seasonality),
    ("annual-comparison", "G4 · Totales anuales", annual_comparison),
    ("year-over-year", "G5 · Variación interanual", year_over_year),
]
MODELS = [
    ("predictions", "G6 · Observado y estimado", predictions),
    ("model-errors", "G7 · Error de los modelos", model_errors),
    ("model-deviations", "G8 · Desviación por mes", model_deviations),
]
CHARTS = OBSERVED + MODELS
SECTIONS = [section for section, _, _ in CHARTS]
SHOWN, HIDDEN = {}, {"display": "none"}
NO_CHARTS_MESSAGE = "No hay gráficas seleccionadas. Marque al menos una en «Gráficas visibles»."


def nav_group(title, charts):
    links = [html.A(label, href=f"#{section}", id=f"nav-{section}", className="section-link")
             for section, label, _ in charts]
    return html.P(className="nav-group", children=[html.Span(f"{title}:", className="nav-title"), *links])


def picker_group(title, charts, identifier):
    return html.Div(className="picker-group", children=[
        html.Span(title, className="nav-title"),
        dcc.Checklist(
            id=identifier, options=[{"label": label, "value": section} for section, label, _ in charts],
            value=[section for section, _, _ in charts], inline=True, className="radio",
        ),
    ])


def visibility(observed, models):
    visible = set(observed or []) | set(models or [])
    sections = [SHOWN if section in visible else HIDDEN for section in SECTIONS]
    linked = "evolution" in visible
    return [
        *sections, *sections, HIDDEN if visible else SHOWN,
        SHOWN if linked else HIDDEN, HIDDEN if linked else SHOWN,
    ]


app = Dash(__name__, title="Observatorio de turismo - Guatemala")
app.index_string = app.index_string.replace("<html>", '<html lang="es">')
app.layout = html.Div(
    className="page",
    children=[
        html.Header(
            className="header",
            children=[
                html.H1("Observatorio de turismo sostenible de Guatemala"),
                html.P(
                    "Explore el ingreso de viajeros internacionales registrado de enero de 2009 a junio de 2026 y "
                    "compare lo que estimaron cinco modelos existentes con lo que se registró."
                ),
                html.Nav(
                    [nav_group("Datos observados", OBSERVED), nav_group("Predicciones y modelos", MODELS)],
                    **{"aria-label": "Secciones del tablero"},
                ),
            ],
        ),
        html.Section(
            id="chart-picker", className="card",
            children=[
                html.H2("Gráficas visibles", className="card-title"),
                html.P(
                    "Desmarque las gráficas que no necesite. Ocultarlas no borra sus selecciones: "
                    "al marcarlas de nuevo aparecen como las dejó.",
                    className="card-text",
                ),
                picker_group("Datos observados", OBSERVED, "visible-observed"),
                picker_group("Predicciones y modelos", MODELS, "visible-models"),
            ],
        ),
        html.Main(children=[
            *[module.layout() for _, _, module in CHARTS],
            html.P(NO_CHARTS_MESSAGE, id="no-charts-message", className="card", role="status", style=HIDDEN),
        ]),
    ],
)
for _, _, module in CHARTS:
    module.register(app)


@app.callback(
    *[Output(section, "style") for section in SECTIONS],
    *[Output(f"nav-{section}", "style") for section in SECTIONS],
    Output("no-charts-message", "style"),
    Output("ranking-series-link", "style"),
    Output("ranking-series-hidden", "style"),
    Input("visible-observed", "value"),
    Input("visible-models", "value"),
)
def update_visibility(observed, models):
    return visibility(observed, models)


@app.callback(
    Output("visible-observed", "value"),
    Input("ranking-show-series", "n_clicks"),
    State("visible-observed", "value"),
    prevent_initial_call=True,
)
def show_linked_series(_, observed):
    return [section for section, _, _ in OBSERVED if section in (observed or []) or section == "evolution"]


server = app.server

if __name__ == "__main__":
    app.run(debug=True)
