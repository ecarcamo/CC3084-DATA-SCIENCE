import plotly.graph_objects as go

COLORS = {
    "background": "#F4F6F8",
    "surface": "#FFFFFF",
    "text": "#1B2733",
    "muted": "#5B6B7A",
    "grid": "#DDE3E9",
    "observed": "#1F4E79",
    "forecast": "#A65E16",
    "alert": "#B3261E",
    "highlight": "#20745A",
}

FONT_FAMILY = "Arial, Helvetica, sans-serif"
GRAPH_CONFIG = {
    "displaylogo": False,
    "locale": "es",
    "locales": {
        "es": {
            "dictionary": {
                "Download plot as a PNG": "Descargar gráfica como PNG",
                "Share chart...": "Compartir gráfica",
                "Zoom": "Acercar",
                "Pan": "Desplazar",
                "Box Select": "Seleccionar área",
                "Lasso Select": "Selección libre",
                "Zoom in": "Aumentar zoom",
                "Zoom out": "Reducir zoom",
                "Autoscale": "Ajustar escala",
                "Reset axes": "Restablecer ejes",
                "Double-click to zoom back out": "Doble clic para restablecer la vista",
            },
            "format": {
                "days": ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
                "shortDays": ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
                "months": [
                    "enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
                ],
                "shortMonths": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
                "decimal": ",",
                "thousands": ".",
                "grouping": [3],
            },
        },
    },
}


def build_template():
    return go.layout.Template(
        layout=go.Layout(
            font={"family": FONT_FAMILY, "size": 14, "color": COLORS["text"]},
            paper_bgcolor=COLORS["surface"],
            plot_bgcolor=COLORS["surface"],
            colorway=[COLORS["observed"], COLORS["forecast"], COLORS["highlight"], COLORS["alert"]],
            xaxis={"gridcolor": COLORS["grid"], "linecolor": COLORS["muted"], "zeroline": False},
            yaxis={"gridcolor": COLORS["grid"], "linecolor": COLORS["muted"], "zeroline": False},
            margin={"l": 70, "r": 20, "t": 30, "b": 50},
            hoverlabel={"font": {"family": FONT_FAMILY, "size": 14}},
        )
    )
