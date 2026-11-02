import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app import model_results
from app.model_results import month_name, number
from app.theme import COLORS, GRAPH_CONFIG, build_template

KIND_STYLES = {
    "observado": {
        "name": "Observado (dato registrado)", "mode": "lines",
        "line": {"color": COLORS["observed"], "width": 3, "dash": "solid"},
    },
    "estimado": {
        "name": "Estimado (versión aprobada)", "mode": "lines+markers",
        "line": {"color": COLORS["forecast"], "width": 3, "dash": "dot"}, "marker": {"size": 7},
    },
}
HISTORY_OPTIONS = [
    {"label": "12 meses", "value": 12}, {"label": "24 meses", "value": 24},
    {"label": "36 meses", "value": 36}, {"label": "Todo el historial", "value": 0},
]
DEFAULT_HISTORY = 24
LISTED_MONTHS = 4
SHOWN, HIDDEN = {}, {"display": "none"}


def _history(value):
    return value if value in {option["value"] for option in HISTORY_OPTIONS} else DEFAULT_HISTORY


def _plotted(series):
    return [None if pd.isna(value) else float(value) for value in series]


def build_figure(version, history_months):
    observed = model_results.monthly(version["observed"])
    months = _history(history_months)
    sources = [(version["observed"], observed.iloc[-months:] if months else observed),
               (version["estimates"], model_results.monthly(version["estimates"]))]
    unit = version["estimates"]["unit"].iloc[0]
    figure = go.Figure(layout={"template": build_template(), "height": 460})
    for frame, series in sources:
        kind = frame["kind"].iloc[0]
        style = KIND_STYLES[kind]
        figure.add_trace(go.Scatter(
            x=series.index.tolist(), y=_plotted(series), connectgaps=False, **style,
            hovertemplate=f"<b>%{{y:,.0f}}</b> {unit}<extra>{kind.capitalize()}</extra>",
        ))
    figure.update_yaxes(title_text=unit.capitalize(), tickformat=",", rangemode="tozero", automargin=True)
    figure.update_xaxes(title_text=None, hoverformat="%b %Y", automargin=True)
    figure.update_layout(
        hovermode="x unified", showlegend=True,
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.12, "yanchor": "top", "title": {"text": "Líneas: "}},
        margin={"l": 70, "r": 20, "t": 30, "b": 90},
    )
    return figure


def build_note(version, history_months):
    observed = model_results.monthly(version["observed"])
    months = _history(history_months)
    shown = observed.iloc[-months:] if months else observed
    estimates = model_results.monthly(version["estimates"])
    destination = version["estimates"]["destination"].iloc[0].replace("_", " ").title()
    return (
        f"{destination}: {shown.notna().sum()} meses registrados de {month_name(shown.index.min())} a "
        f"{month_name(shown.index.max())} y {len(estimates)} meses estimados de {month_name(estimates.index.min())} "
        f"a {month_name(estimates.index.max())}. Cambiar el historial mostrado no vuelve a calcular las estimaciones."
    )


def validation_summary(metrics, unit):
    score = metrics["procedure"]
    periods = model_results.evaluated_label(metrics["evaluated_periods"])
    if score.get("mape_pct") is not None:
        value, name = f"{number(score['mape_pct'], 1)} %", "error porcentual medio, MAPE"
    elif score.get("mae") is not None:
        value, name = f"{number(score['mae'])} {unit}", "error absoluto medio, MAE"
    else:
        return f"No hay métrica de validación disponible ({periods})."
    return (f"Precisión en la validación: en promedio, cada estimación mensual se alejó {value} de lo registrado "
            f"({name}), en {periods}. G7 la compara con una referencia.")


def build_details(version):
    estimates = version["estimates"]
    row = estimates.iloc[0]
    procedure = model_results.procedure_label(version["metrics"]["procedure"]["name"])
    return [
        html.P([
            html.Strong(f"Actualizado el {model_results.updated_label(row['generated_at'])}"),
            f" · versión {row['run_id']} · procedimiento {procedure} ({row['procedure_version']}).",
        ], className="note"),
        html.P(validation_summary(version["metrics"], row["unit"]), className="note"),
    ]


def build_warning(version):
    observed = model_results.monthly(version["observed"])
    estimates = model_results.monthly(version["estimates"])
    unit = version["estimates"]["unit"].iloc[0]
    missing = observed.index[observed.isna()]
    if missing.empty:
        coverage = "El historial no tiene meses sin registro."
    else:
        listed = ", ".join(month_name(date) for date in missing[:LISTED_MONTHS])
        extra = f" y {len(missing) - LISTED_MONTHS} más" if len(missing) > LISTED_MONTHS else ""
        coverage = (f"{len(missing)} meses del historial no tienen registro ({listed}{extra}); "
                    "se ven como cortes en la línea y no se rellenan.")
    return [
        html.Strong("Antes de usar estas cifras: "),
        f"son estimaciones puntuales de {unit} de {month_name(estimates.index.min())} a "
        f"{month_name(estimates.index.max())}, sin margen de error; cuanto más lejano el mes, mayor la incertidumbre. "
        "Se basan en lo registrado y no anticipan cambios bruscos como crisis, cierres de frontera o grandes eventos. "
        f"{coverage} La serie mide {unit}, una definición distinta de la de G1 a G5, por eso sus cifras no coinciden. "
        "Los parámetros y el detalle de cada ejecución están en MLflow y en la documentación del pipeline.",
    ]


def build_view(version, history_months):
    if version is None:
        return go.Figure(), "", [], [], HIDDEN, SHOWN
    return (
        build_figure(version, history_months), build_note(version, history_months),
        build_details(version), build_warning(version), SHOWN, HIDDEN,
    )


def layout():
    return html.Section(
        id="predictions", className="card",
        children=[
            html.H2("G6 · ¿Cuántos visitantes se esperan en los próximos meses?", className="card-title"),
            html.P(model_results.UNAVAILABLE_MESSAGE, id="predictions-unavailable", className="card-text",
                   role="status", style=HIDDEN),
            html.Div(id="predictions-content", style=HIDDEN, children=[
                html.P(
                    "La línea azul continua muestra los visitantes registrados; la naranja punteada, lo que estima la "
                    "versión aprobada para los meses siguientes. Pase el cursor sobre un mes para ver su valor.",
                    className="card-text",
                ),
                html.Div(className="controls", children=[
                    html.Div([
                        html.Label("Historial observado", htmlFor="predictions-history"),
                        dcc.RadioItems(
                            id="predictions-history", options=HISTORY_OPTIONS, value=DEFAULT_HISTORY, inline=True,
                            className="radio",
                        ),
                    ]),
                ]),
                dcc.Graph(id="predictions-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "460px"}),
                html.P(id="predictions-note", className="note", role="status"),
                html.Div(id="predictions-details"),
                html.P(id="predictions-warning", className="warning", role="note"),
            ]),
        ],
    )


def register(app):
    @app.callback(
        Output("predictions-graph", "figure"), Output("predictions-note", "children"),
        Output("predictions-details", "children"), Output("predictions-warning", "children"),
        Output("predictions-content", "style"), Output("predictions-unavailable", "style"),
        Input("predictions-history", "value"),
    )
    def update(history_months):
        return build_view(model_results.current_version(), history_months)
