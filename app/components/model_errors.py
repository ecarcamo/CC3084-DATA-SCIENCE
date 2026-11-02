import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import model_results
from app.theme import COLORS, GRAPH_CONFIG, build_template

METRICS = {
    "mae": ("Error absoluto medio (MAE)", "Distancia media entre lo estimado y lo registrado en cada mes."),
    "rmse": ("Raíz del error cuadrático medio (RMSE)", "Como el MAE, pero da más peso a los errores grandes."),
    "mape_pct": ("Error porcentual absoluto medio (MAPE)", "Distancia media expresada como porcentaje de lo registrado."),
}
SCORES = [("procedure", "{} (versión aprobada)", COLORS["forecast"]), ("baseline", "{}", COLORS["muted"])]
SHOWN, HIDDEN = {}, {"display": "none"}


def _message(figure, message):
    figure.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure, message


def build_figure(version, metric):
    figure = go.Figure(layout={"template": build_template(), "height": 420})
    if metric not in METRICS:
        return _message(figure, "Seleccione una métrica disponible.")
    metrics = version["metrics"]
    title, explanation = METRICS[metric]
    bars = [(label.format(model_results.procedure_label(metrics[key]["name"])), metrics[key].get(metric), color)
            for key, label, color in SCORES]
    bars = [bar for bar in bars if bar[1] is not None]
    if not bars:
        reason = "no hay meses evaluados con valor registrado distinto de cero" if metric == "mape_pct" else "no hay meses evaluados"
        return _message(figure, f"No se puede calcular el {title[0].lower()}{title[1:]}: {reason}.")
    unit = "%" if metric == "mape_pct" else version["estimates"]["unit"].iloc[0]
    figure.add_trace(go.Bar(
        x=[value for _, value, _ in bars], y=[label for label, _, _ in bars], orientation="h",
        marker={"color": [color for _, _, color in bars]},
        hovertemplate=f"%{{y}}<br><b>%{{x:,.2f}}</b> {unit}<extra></extra>",
    ))
    figure.update_xaxes(title_text=f"Error ({unit})", tickformat=".1f" if metric == "mape_pct" else ",.0f",
                        nticks=4, rangemode="tozero", automargin=True)
    figure.update_yaxes(autorange="reversed", automargin=True)
    figure.update_layout(showlegend=False, margin={"l": 20, "r": 30, "t": 20, "b": 70})
    rule = " Los meses registrados en cero no entran en este porcentaje." if metric == "mape_pct" else ""
    note = (
        f"{title}: {explanation} Calculado con {model_results.evaluated_label(metrics['evaluated_periods'])}: cada "
        "mes se estimó solo con datos anteriores a él. Menor error indica mayor cercanía. La referencia estacional "
        "repite el valor del mismo mes del año anterior; sirve para comprobar que el procedimiento aporta más que "
        f"la estacionalidad.{rule} Estos errores describen meses ya registrados y no garantizan el desempeño futuro."
    )
    return figure, note


def build_view(version, metric):
    if version is None:
        return go.Figure(), "", HIDDEN, SHOWN
    return (*build_figure(version, metric), SHOWN, HIDDEN)


def layout():
    return html.Section(
        id="model-errors", className="card",
        children=[
            html.H2("G7 · ¿Qué tan cerca estuvo la estimación de lo registrado?", className="card-title"),
            html.P(model_results.UNAVAILABLE_MESSAGE, id="errors-unavailable", className="card-text", role="status",
                   style=HIDDEN),
            html.Div(id="errors-content", style=HIDDEN, children=[
                html.P(
                    "Compare el error de validación del procedimiento aprobado con el de una referencia sencilla, "
                    "en los mismos meses ocultos.",
                    className="card-text",
                ),
                html.Div(className="controls", children=[
                    html.Div([
                        html.Label("Medida de error", htmlFor="errors-metric"),
                        dcc.Dropdown(id="errors-metric", options=[
                            {"label": spec[0], "value": key} for key, spec in METRICS.items()
                        ], value="mape_pct", clearable=False, searchable=False),
                    ]),
                ]),
                dcc.Graph(id="errors-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "420px"}),
                html.P(id="errors-note", className="note", role="status"),
            ]),
        ],
    )


def register(app):
    @app.callback(
        Output("errors-graph", "figure"), Output("errors-note", "children"),
        Output("errors-content", "style"), Output("errors-unavailable", "style"),
        Input("errors-metric", "value"),
    )
    def update(metric):
        return build_view(model_results.current_version(), metric)
