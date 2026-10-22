import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html, no_update

from app import data
from app.theme import COLORS, GRAPH_CONFIG, build_template

LABELS = data.load_labels()
CATEGORIES = ["Vía de ingreso", "País de residencia"]
REFERENCE = data.load_series("total")
YEARS = sorted(REFERENCE.index.year.unique(), reverse=True)
DEFAULT_YEAR = int(data.aggregate(REFERENCE, "year").index.year.max())
ALL_YEARS = "all"
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]
FIRST, LAST = REFERENCE.index.min(), REFERENCE.index.max()
FULL_SPAN = f"{MONTHS[FIRST.month - 1]} de {FIRST.year} a {MONTHS[LAST.month - 1]} de {LAST.year}"
EMPTY_MESSAGE = "No hay datos para este año y grupo. Seleccione otra opción."
TEMPLATE = build_template()


def build_ranking(category, year):
    rows = []
    for key, row in LABELS[LABELS["categoria"] == category].iterrows():
        series = data.load_series(key)
        selected = (series if year == ALL_YEARS else series[series.index.year == int(year)]).dropna()
        if not selected.empty:
            rows.append({
                "key": key,
                "label": row["etiqueta"],
                "travelers": selected.sum(),
                "months": len(selected),
            })
    return pd.DataFrame(rows, columns=["key", "label", "travelers", "months"]).sort_values(
        "travelers", ascending=False,
    )


def build_figure(category, year, selected_key):
    frame = build_ranking(category, year)
    figure = go.Figure(layout={"template": TEMPLATE, "height": 360})
    if frame.empty:
        figure.add_annotation(
            text=EMPTY_MESSAGE, xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font={"size": 16, "color": COLORS["muted"]},
        )
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure, EMPTY_MESSAGE
    selected = frame["key"] == selected_key
    figure.add_trace(go.Bar(
        x=frame["travelers"],
        y=frame["label"],
        orientation="h",
        customdata=frame["key"],
        marker={
            "color": [COLORS["highlight"] if value else COLORS["observed"] for value in selected],
            "line": {"color": COLORS["text"], "width": [3 if value else 0 for value in selected]},
        },
        hovertemplate="%{y}<br><b>%{x:,.0f}</b> viajeros<extra></extra>",
    ))
    every_year = year == ALL_YEARS
    figure.update_xaxes(
        title_text="Viajeros en todo el periodo" if every_year else "Viajeros en el año",
        tickformat=",", nticks=3, automargin=True,
    )
    figure.update_yaxes(autorange="reversed", automargin=True)
    figure.update_layout(showlegend=False, clickmode="event", margin={"l": 120, "r": 20, "t": 20, "b": 60})
    months = int(frame["months"].min())
    if every_year:
        period = f"Todos los años: de {FULL_SPAN}, {months} meses."
    elif months == 12:
        period = f"{year}: año completo, 12 meses."
    else:
        period = f"{year}: periodo parcial, {months} meses disponibles. No equivale a un año completo."
    selection = (
        f" Selección: {LABELS.loc[selected_key, 'etiqueta']}, indicada en verde y con borde."
        if selected.any() else ""
    )
    note = (
        f"{period} Se comparan únicamente series del mismo grupo; no se suman países y vías."
        " Los países mostrados no representan todos los mercados de origen."
        f"{selection} El clic cambia la serie temporal, pero conserva su rango de fechas."
    )
    return figure, note


def select_series(click_data, category):
    if not click_data or not click_data.get("points"):
        return no_update
    key = click_data["points"][0].get("customdata")
    allowed = LABELS.index[LABELS["categoria"] == category]
    return key if key in allowed else no_update


def layout():
    return html.Section(
        id="ranking",
        className="card",
        children=[
            html.H2("¿Qué vías o países concentran más viajeros?", className="card-title"),
            html.P(
                "Compare las vías de ingreso o los países de residencia disponibles. "
                "Haga clic en una barra para explorar esa serie en la gráfica temporal.",
                className="card-text",
            ),
            html.Div(
                className="controls",
                children=[
                    html.Div([
                        html.Label("Grupo de comparación", htmlFor="ranking-category"),
                        dcc.Dropdown(
                            id="ranking-category",
                            options=[{"label": value, "value": value} for value in CATEGORIES],
                            value=CATEGORIES[0], clearable=False,
                        ),
                    ]),
                    html.Div([
                        html.Label("Año", htmlFor="ranking-year"),
                        dcc.Dropdown(
                            id="ranking-year",
                            options=[{"label": "Todos los años", "value": ALL_YEARS}]
                            + [{"label": str(year), "value": int(year)} for year in YEARS],
                            value=DEFAULT_YEAR, clearable=False,
                        ),
                    ]),
                ],
            ),
            dcc.Graph(id="ranking-graph", config=GRAPH_CONFIG, responsive=True, style={"height": "360px"}),
            html.P(id="ranking-note", className="note", role="status"),
            html.A("Ver la evolución de la serie seleccionada", href="#evolution", className="series-link"),
        ],
    )


def register(app):
    @app.callback(
        Output("ranking-graph", "figure"),
        Output("ranking-note", "children"),
        Input("ranking-category", "value"),
        Input("ranking-year", "value"),
        Input("series-selector", "value"),
    )
    def update(category, year, selected_key):
        return build_figure(category, year, selected_key)

    @app.callback(
        Output("series-selector", "value"),
        Input("ranking-graph", "clickData"),
        State("ranking-category", "value"),
        prevent_initial_call=True,
    )
    def select(click_data, category):
        return select_series(click_data, category)
