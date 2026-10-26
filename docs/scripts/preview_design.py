import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dash import Dash, html

from app.components import annual_comparison, model_deviations, model_errors, predictions, ranking, seasonality, time_series

COMPONENTS = [time_series, ranking, seasonality, annual_comparison, predictions, model_errors, model_deviations]


def build_app():
    app = Dash(__name__, title="Revisión visual de Hugo", assets_folder=str(ROOT / "app" / "assets"))
    app.index_string = app.index_string.replace("<html>", '<html lang="es">')
    app.layout = html.Div(className="page", children=[
        html.Header(className="header", children=[
            html.H1("Revisión visual del tablero"),
            html.P("Vista de comprobación de los componentes recibidos y de G3 y G4. No es la integración final."),
        ]),
        html.Main(children=[component.layout() for component in COMPONENTS]),
    ])
    for component in COMPONENTS:
        component.register(app)
    return app


if __name__ == "__main__":
    build_app().run(debug=False, host="127.0.0.1", port=8053)
