import re

from app import data
from app.theme import COLORS, FONT_FAMILY, build_template


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(linear, [0.2126, 0.7152, 0.0722]))


def contrast_ratio(first, second):
    light, dark = sorted([luminance(first), luminance(second)], reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_required_palette_keys_are_preserved():
    assert set(COLORS) >= {
        "background", "surface", "text", "muted", "grid",
        "observed", "forecast", "alert", "highlight",
    }


def test_text_contrast_on_page_and_cards():
    for background in ["background", "surface"]:
        for foreground in ["text", "muted", "observed", "forecast", "alert", "highlight"]:
            assert contrast_ratio(COLORS[foreground], COLORS[background]) >= 4.5


def test_series_contrast_on_cards():
    for foreground in ["observed", "forecast", "alert", "highlight"]:
        assert contrast_ratio(COLORS[foreground], COLORS["surface"]) >= 3


def test_css_palette_matches_plotly():
    css = (data.ROOT / "app" / "assets" / "style.css").read_text(encoding="utf-8")
    variables = dict(re.findall(r"--([a-z]+):\s*(#[0-9A-Fa-f]{6})", css))
    assert variables == COLORS


def test_plotly_typography_and_surfaces():
    template = build_template()
    assert template.layout.font.family == FONT_FAMILY
    assert template.layout.font.size >= 14
    assert template.layout.hoverlabel.font.size >= 14
    assert template.layout.paper_bgcolor == COLORS["surface"]
    assert template.layout.plot_bgcolor == COLORS["surface"]


def test_contrast_reference_values():
    assert contrast_ratio("#000000", "#FFFFFF") == 21
    assert contrast_ratio("#FFFFFF", "#FFFFFF") == 1


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
    print("ok")
