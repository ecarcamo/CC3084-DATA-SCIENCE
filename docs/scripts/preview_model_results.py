import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dash import Dash, html

from app.components import model_deviations, model_errors


def build_app():
    app = Dash(__name__, title="Predicciones y desempeño de modelos", assets_folder=str(ROOT / "app" / "assets"))
    app.index_string = app.index_string.replace("<html>", '<html lang="es">')
    app.layout = html.Div(className="page", children=[
        html.Header(className="header", children=[
            html.H1("Predicciones y desempeño de modelos"),
            html.P("Compare los errores y explore las desviaciones de las estimaciones existentes."),
        ]),
        html.Main(children=[model_errors.layout(), model_deviations.layout()]),
    ])
    model_errors.register(app)
    model_deviations.register(app)
    return app


if __name__ == "__main__":
    build_app().run(debug=False, port=8051)
