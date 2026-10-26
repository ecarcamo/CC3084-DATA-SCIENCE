import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import data, model_results
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
METRICS = {
    "mae": ("Error absoluto medio (MAE)", "Viajeros", "Distancia media entre lo observado y lo estimado."),
    "rmse": ("Raíz del error cuadrático medio (RMSE)", "Viajeros", "Da más peso a las equivocaciones grandes."),
    "mape": ("Error porcentual absoluto medio (MAPE)", "%", "Distancia media expresada como porcentaje de lo observado."),
}
SHORT_LABELS = {**model_results.MODEL_LABELS, "ses": "SES", "seasonal_naive": "Seasonal Naive"}
EMPTY_MESSAGE = "No hay datos coincidentes para comparar los modelos de esta selección."


def build_figure(series_key, metric):
    figure = go.Figure(layout={"template": build_template(), "height": 420})
    try:
        if metric not in METRICS:
            raise model_results.ModelDataError("Seleccione una métrica disponible.")
        errors = model_results.calculate_errors(series_key)
        available = errors.dropna(subset=[metric]).sort_values(metric)
        if available.empty:
            message = (
                "No se puede calcular el error porcentual: no hay observaciones distintas de cero."
                if metric == "mape" and not errors.empty else EMPTY_MESSAGE
            )
            raise model_results.ModelDataError(message)
    except model_results.ModelDataError as error:
        message = str(error)
        figure.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure, message
    title, unit, explanation = METRICS[metric]
    figure.add_trace(go.Bar(
        x=available[metric].tolist(),
        y=[SHORT_LABELS[key] for key in available.index],
        orientation="h",
        marker={"color": COLORS["forecast"]},
        hovertemplate=f"%{{y}}<br><b>%{{x:,.2f}}</b> {unit}<extra></extra>",
    ))
    figure.update_xaxes(title_text=f"Error ({unit})", tickformat=".1f" if metric == "mape" else ",.0f", nticks=4, rangemode="tozero", automargin=True)
    figure.update_yaxes(autorange="reversed", automargin=True)
    figure.update_layout(showlegend=False, margin={"l": 20, "r": 30, "t": 20, "b": 70})
    first = available.iloc[0]
    exclusions = (
        f" El porcentaje excluye {int(first['mape_excluded'])} meses con observado igual a cero."
        if metric == "mape" else ""
    )
    note = (
        f"{LABELS.loc[series_key, 'etiqueta']}: {len(available)} modelos comparados sobre "
        f"los mismos {int(first['count'])} meses coincidentes, del {first['start']:%d/%m/%Y} "
        f"al {first['end']:%d/%m/%Y}. {title}: {explanation} Menor error indica mayor cercanía en ese periodo."
        f"{exclusions} Los errores se recalculan con resultados existentes; "
        "no garantizan el desempeño futuro ni demuestran una evaluación independiente del entrenamiento."
    )
    return figure, note


def layout():
    return html.Section(
        id="model-errors", className="card",
        children=[
            html.H2("¿Qué modelo se equivoca menos para esta serie?", className="card-title"),
            html.P("Compare el tamaño del error de los modelos en un mismo periodo observado.", className="card-text"),
            html.Div(className="controls", children=[
                html.Div([
                    html.Label("Serie", htmlFor="errors-series"),
                    dcc.Dropdown(id="errors-series", options=[
                        {"label": row.etiqueta, "value": key} for key, row in LABELS.iterrows()
                    ], value="total", clearable=False, searchable=False),
                ]),
                html.Div([
                    html.Label("Medida de error", htmlFor="errors-metric"),
                    dcc.Dropdown(id="errors-metric", options=[
                        {"label": spec[0], "value": key} for key, spec in METRICS.items()
                    ], value="mae", clearable=False, searchable=False),
                ]),
            ]),
            dcc.Graph(id="errors-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "420px"}),
            html.P(id="errors-note", className="note", role="status"),
        ],
    )


def register(app):
    @app.callback(
        Output("errors-graph", "figure"), Output("errors-note", "children"),
        Input("errors-series", "value"), Input("errors-metric", "value"),
    )
    def update(series_key, metric):
        return build_figure(series_key, metric)
