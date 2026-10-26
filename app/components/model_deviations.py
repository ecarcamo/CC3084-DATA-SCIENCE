import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from app import data, model_results
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
EMPTY_MESSAGE = "No hay datos observados y estimados coincidentes para esta selección. Amplíe las fechas o cambie el modelo."


def model_options(series_key, selected_model=None):
    try:
        keys = model_results.available_models(series_key)
    except model_results.ModelDataError:
        keys = []
    options = [{"label": model_results.MODEL_LABELS[key], "value": key} for key in keys]
    selected = selected_model if selected_model in keys else (keys[0] if keys else None)
    return options, selected


def build_figure(series_key, model_key, start, end):
    figure = go.Figure(layout={"template": build_template(), "height": 420})
    try:
        frame = model_results.align_observations(series_key, model_key, start, end)
        if frame.empty:
            raise model_results.ModelDataError(EMPTY_MESSAGE)
    except model_results.ModelDataError as error:
        message = str(error)
        figure.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure, message
    plotted = frame.reindex(pd.date_range(frame.index.min(), frame.index.max(), freq="MS"))
    values = plotted["error"].where(plotted["error"].notna(), None).astype(object)
    values = [None if pd.isna(value) else float(value) for value in values]
    figure.add_trace(go.Scatter(
        x=plotted.index.tolist(), y=values, mode="lines+markers", connectgaps=False,
        name="Observado menos estimado", line={"color": COLORS["forecast"], "width": 2.5},
        hovertemplate="%{x|%b %Y}<br><b>%{y:,.2f}</b> viajeros de diferencia<extra></extra>",
    ))
    figure.add_hline(
        y=0, line_dash="dash", line_color=COLORS["muted"],
        annotation_text="Observado = estimado", annotation_position="top left",
    )
    figure.update_yaxes(title_text="Diferencia de viajeros", tickformat=",.0f", nticks=5, automargin=True)
    figure.update_xaxes(title_text="Mes", automargin=True)
    figure.update_layout(showlegend=False)
    note = (
        f"{LABELS.loc[series_key, 'etiqueta']} · {model_results.MODEL_LABELS[model_key]}. "
        f"{len(frame)} meses coincidentes del {frame.index.min():%d/%m/%Y} al {frame.index.max():%d/%m/%Y}. "
        "Un valor positivo indica que el modelo estimó menos viajeros; uno negativo, que estimó más. "
        "La cercanía a cero indica menor desviación. Los meses sin pares válidos no se rellenan ni se interpolan. "
        "Esta comparación histórica no demuestra una causa ni garantiza el desempeño futuro."
    )
    return figure, note


def layout():
    reference = model_results.load_observations("total")
    options, selected = model_options("total")
    predictions = model_results.load_predictions("total", selected) if selected else reference
    first = predictions.index.min() if not predictions.empty else reference.index.min()
    last = predictions.index.max() if not predictions.empty else reference.index.max()
    return html.Section(
        id="model-deviations", className="card",
        children=[
            html.H2("¿En qué meses se alejó el modelo de lo observado?", className="card-title"),
            html.P("Explore cuándo la estimación quedó por encima o por debajo de los datos registrados.", className="card-text"),
            html.Div(className="controls", children=[
                html.Div([
                    html.Label("Serie", htmlFor="deviations-series"),
                    dcc.Dropdown(id="deviations-series", options=[
                        {"label": row.etiqueta, "value": key} for key, row in LABELS.iterrows()
                    ], value="total", clearable=False, searchable=False),
                ]),
                html.Div([
                    html.Label("Modelo", htmlFor="deviations-model"),
                    dcc.Dropdown(id="deviations-model", options=options, value=selected, clearable=False, searchable=False),
                ]),
                html.Div([
                    html.Label("Rango de fechas", htmlFor="deviations-dates"),
                    dcc.DatePickerRange(
                        id="deviations-dates", min_date_allowed=reference.index.min().date(),
                        max_date_allowed=reference.index.max().date(), start_date=first.date(), end_date=last.date(),
                        display_format="DD/MM/YYYY", start_date_placeholder_text="Fecha inicial",
                        end_date_placeholder_text="Fecha final", minimum_nights=0,
                    ),
                ]),
            ]),
            dcc.Graph(id="deviations-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "420px"}),
            html.P(id="deviations-note", className="note", role="status"),
        ],
    )


def register(app):
    @app.callback(
        Output("deviations-model", "options"), Output("deviations-model", "value"),
        Input("deviations-series", "value"), State("deviations-model", "value"),
    )
    def update_models(series_key, selected_model):
        return model_options(series_key, selected_model)

    @app.callback(
        Output("deviations-graph", "figure"), Output("deviations-note", "children"),
        Input("deviations-series", "value"), Input("deviations-model", "value"),
        Input("deviations-dates", "start_date"), Input("deviations-dates", "end_date"),
    )
    def update(series_key, model_key, start, end):
        return build_figure(series_key, model_key, start, end)
