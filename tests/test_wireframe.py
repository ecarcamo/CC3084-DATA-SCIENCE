from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageColor

from app.theme import COLORS
from docs.scripts.draw_wireframe import SIZE, draw_wireframe, selected_bar_point


def test_wireframe_is_saved_with_the_dashboard_palette():
    with TemporaryDirectory() as folder:
        output = Path(folder) / "figuras" / "boceto.png"
        assert draw_wireframe(output) == output
        with Image.open(output) as image:
            assert image.size == SIZE
            assert image.mode == "RGB"
            assert image.getpixel((0, 0)) == ImageColor.getrgb(COLORS["background"])
            assert image.getpixel(selected_bar_point()) == ImageColor.getrgb(COLORS["highlight"])


if __name__ == "__main__":
    test_wireframe_is_saved_with_the_dashboard_palette()
    print("ok")
