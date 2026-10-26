import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dash import Dash, html

from app.components import predictions, time_series


def build_app():
    app = Dash(__name__, title="Serie temporal y predicciones", assets_folder=str(ROOT / "app" / "assets"))
    app.index_string = app.index_string.replace("<html>", '<html lang="es">')
    app.layout = html.Div(className="page", children=[
        html.Header(className="header", children=[
            html.H1("Serie temporal y predicciones"),
            html.P("Explore lo registrado y compárelo con las estimaciones existentes de los modelos."),
        ]),
        html.Main(children=[time_series.layout(), predictions.layout()]),
    ])
    time_series.register(app)
    predictions.register(app)
    return app


if __name__ == "__main__":
    build_app().run(debug=False, port=8052)
