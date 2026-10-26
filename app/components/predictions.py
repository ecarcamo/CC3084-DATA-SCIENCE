import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from app import data, model_results
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
SHORT_LABELS = {**model_results.MODEL_LABELS, "ses": "SES", "seasonal_naive": "Seasonal Naive"}
MODEL_STYLES = {
    "sarima": {"color": COLORS["forecast"], "dash": "dash"},
    "holt_winters": {"color": "#6B3A0C", "dash": "dot"},
    "ses": {"color": "#C46A12", "dash": "dashdot"},
    "seasonal_naive": {"color": "#8A4B12", "dash": "longdash"},
    "prophet": {"color": "#D07A1E", "dash": "longdashdot"},
}
DEFAULT_MODEL_COUNT = 3
OBSERVED_NAME = "Observado (dato registrado)"
SOURCE = "insumos/resultados/predicciones"
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]
NO_MODELS_MESSAGE = "Seleccione al menos un modelo para comparar sus estimaciones con lo observado."
EMPTY_MESSAGE = (
    "No hay meses con dato registrado y estimación de todos los modelos elegidos en este periodo. "
    "Amplíe las fechas o cambie los modelos."
)


def month_name(date):
    return f"{MONTHS[date.month - 1]} de {date.year}"


def estimate_name(model_key):
    return f"Estimado · {SHORT_LABELS[model_key]}"


def prediction_coverage():
    first, last = [], []
    for series_key in LABELS.index:
        for model_key in model_results.available_models(series_key):
            predictions = model_results.load_predictions(series_key, model_key).dropna()
            if not predictions.empty:
                first.append(predictions.index.min())
                last.append(predictions.index.max())
    if not first:
        reference = model_results.load_observations("total")
        return reference.index.min(), reference.index.max()
    return min(first), max(last)


def model_options(series_key, selected_models=None):
    try:
        keys = model_results.available_models(series_key)
    except model_results.ModelDataError:
        keys = []
    options = [{"label": model_results.MODEL_LABELS[key], "value": key} for key in keys]
    if selected_models is None:
        return options, keys[:DEFAULT_MODEL_COUNT]
    return options, [key for key in keys if key in selected_models]


def _empty_figure(figure, message):
    figure.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
        font={"size": 16, "color": COLORS["muted"]},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure, message


def _selected_models(series_key, model_keys):
    if not model_keys:
        raise model_results.ModelDataError(NO_MODELS_MESSAGE)
    unknown = [key for key in model_keys if key not in model_results.MODEL_LABELS]
    if unknown:
        raise model_results.ModelDataError("Seleccione un modelo disponible.")
    available = model_results.available_models(series_key)
    missing = [SHORT_LABELS[key] for key in model_keys if key not in available]
    if missing:
        raise model_results.ModelDataError(
            f"No hay estimaciones de {', '.join(missing)} para esta serie. Elija otro modelo."
        )
    return [key for key in model_results.MODEL_LABELS if key in model_keys]


def _plotted_values(series):
    return [None if pd.isna(value) else float(value) for value in series]


def build_figure(series_key, model_keys, start, end):
    figure = go.Figure(layout={"template": build_template(), "height": 460})
    try:
        keys = _selected_models(series_key, model_keys)
        frame = model_results.align_models(series_key, keys, start, end)
        if frame.empty:
            raise model_results.ModelDataError(EMPTY_MESSAGE)
    except model_results.ModelDataError as error:
        return _empty_figure(figure, str(error))
    plotted = frame.reindex(pd.date_range(frame.index.min(), frame.index.max(), freq="MS"))
    dates = plotted.index.tolist()
    figure.add_trace(go.Scatter(
        x=dates, y=_plotted_values(plotted["observed"]), name=OBSERVED_NAME, mode="lines+markers",
        connectgaps=False, line={"color": COLORS["observed"], "width": 3, "dash": "solid"}, marker={"size": 5},
        hovertemplate="<b>%{y:,.0f}</b> viajeros registrados<extra>Observado</extra>",
    ))
    for key in keys:
        style = MODEL_STYLES[key]
        figure.add_trace(go.Scatter(
            x=dates, y=_plotted_values(plotted[key]), name=estimate_name(key), mode="lines",
            connectgaps=False, line={"color": style["color"], "width": 2, "dash": style["dash"]},
            hovertemplate=f"%{{y:,.0f}} viajeros estimados<extra>{SHORT_LABELS[key]}</extra>",
        ))
    figure.update_yaxes(title_text="Viajeros por mes", tickformat=",", automargin=True)
    figure.update_xaxes(title_text=None, hoverformat="%b %Y", automargin=True)
    figure.update_layout(
        hovermode="x unified", showlegend=True,
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.16, "yanchor": "top", "title": {"text": "Líneas: "}},
        margin={"l": 70, "r": 20, "t": 30, "b": 110},
    )
    count = len(frame)
    names = ", ".join(SHORT_LABELS[key] for key in keys)
    note = (
        f"{LABELS.loc[series_key, 'etiqueta']} · {names}. {count} meses con dato registrado y estimación de "
        f"{'cada modelo elegido' if len(keys) > 1 else 'el modelo elegido'}, de {month_name(frame.index.min())} "
        f"a {month_name(frame.index.max())}. Las estimaciones provienen de los resultados existentes del "
        f"Laboratorio 1 ({SOURCE}); no se entrenó ningún modelo nuevo. Corresponden a meses ya registrados: "
        "no son un pronóstico de meses futuros ni incluyen intervalos de confianza."
    )
    return figure, note


def layout():
    first, last = prediction_coverage()
    options, selected = model_options("total")
    return html.Section(
        id="predictions", className="card",
        children=[
            html.H2("¿Qué estimaron los modelos frente a lo que se registró?", className="card-title"),
            html.P(
                "La línea azul continua muestra los viajeros registrados; cada línea naranja discontinua, lo que "
                "estimó un modelo para esos mismos meses. Elija la serie, los modelos y el periodo; pase el cursor "
                "sobre un mes para ver todos los valores.",
                className="card-text",
            ),
            html.Div(className="controls", children=[
                html.Div([
                    html.Label("Serie", htmlFor="predictions-series"),
                    dcc.Dropdown(id="predictions-series", options=[
                        {"label": f"{row.etiqueta} ({row.categoria})", "value": key} for key, row in LABELS.iterrows()
                    ], value="total", clearable=False, searchable=False),
                ]),
                html.Div([
                    html.Label("Modelos", htmlFor="predictions-models"),
                    dcc.Checklist(
                        id="predictions-models", options=options, value=selected, inline=True, className="radio",
                    ),
                ]),
                html.Div([
                    html.Label("Periodo de comparación", htmlFor="predictions-dates"),
                    dcc.DatePickerRange(
                        id="predictions-dates", min_date_allowed=first.date(), max_date_allowed=last.date(),
                        start_date=first.date(), end_date=last.date(), display_format="DD/MM/YYYY",
                        start_date_placeholder_text="Fecha inicial", end_date_placeholder_text="Fecha final",
                        minimum_nights=0,
                    ),
                ]),
            ]),
            dcc.Graph(id="predictions-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "460px"}),
            html.P(id="predictions-note", className="note", role="status"),
            html.P(
                [
                    "Cómo leerla: cuanto más se acerca una línea discontinua a la azul, más se pareció esa estimación "
                    "a lo registrado en ese periodo. Que una curva se vea cercana no demuestra que el modelo sea "
                    "preciso ni que lo será en el futuro; para comparar el tamaño del error, consulte ",
                    html.A("«¿Qué modelo se equivoca menos para esta serie?»", href="#model-errors", className="section-link"),
                    ".",
                ],
                className="note",
            ),
        ],
    )


def register(app):
    @app.callback(
        Output("predictions-models", "options"), Output("predictions-models", "value"),
        Input("predictions-series", "value"), State("predictions-models", "value"),
    )
    def update_models(series_key, selected_models):
        return model_options(series_key, selected_models)

    @app.callback(
        Output("predictions-graph", "figure"), Output("predictions-note", "children"),
        Input("predictions-series", "value"), Input("predictions-models", "value"),
        Input("predictions-dates", "start_date"), Input("predictions-dates", "end_date"),
    )
    def update(series_key, model_keys, start, end):
        return build_figure(series_key, model_keys, start, end)
