import plotly.graph_objects as go

COLORS = {
    "background": "#F4F6F8",
    "surface": "#FFFFFF",
    "text": "#1B2733",
    "muted": "#5B6B7A",
    "grid": "#DDE3E9",
    "observed": "#1F4E79",
    "forecast": "#D9822B",
    "alert": "#B3261E",
    "highlight": "#2E8B6E",
}

FONT_FAMILY = "Arial, Helvetica, sans-serif"


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
