from dash import Dash, html

from app.components import time_series

app = Dash(__name__, title="Observatorio de turismo - Guatemala")
app.layout = html.Div(
    className="page",
    children=[
        html.Header(
            className="header",
            children=[
                html.H1("Observatorio de turismo sostenible de Guatemala"),
                html.P("Tablero para explorar el ingreso de viajeros y consultar las predicciones con sus límites."),
            ],
        ),
        html.Main(children=[time_series.layout()]),
    ],
)
time_series.register(app)
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
