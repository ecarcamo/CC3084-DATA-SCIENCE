from dash import Dash, html

from app.components import ranking, time_series

app = Dash(__name__, title="Observatorio de turismo - Guatemala")
app.index_string = app.index_string.replace("<html>", '<html lang="es">')
app.layout = html.Div(
    className="page",
    children=[
        html.Header(
            className="header",
            children=[
                html.H1("Observatorio de turismo sostenible de Guatemala"),
                html.P("Avance: explore el ingreso de viajeros. Las predicciones se incorporarán en la entrega final."),
                html.Nav(
                    [html.A("Evolución temporal", href="#evolution", className="section-link"), " | ",
                     html.A("Comparación por grupo", href="#ranking", className="section-link")],
                    **{"aria-label": "Secciones del tablero"},
                ),
            ],
        ),
        html.Main(children=[time_series.layout(), ranking.layout()]),
    ],
)
time_series.register(app)
ranking.register(app)
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
