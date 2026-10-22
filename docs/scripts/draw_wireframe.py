from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.theme import COLORS

OUTPUT = Path(__file__).resolve().parents[1] / "figuras" / "boceto_tablero.png"


def draw_wireframe(output=OUTPUT):
    image = Image.new("RGB", (1440, 1500), COLORS["background"])
    draw = ImageDraw.Draw(image)
    fonts = {size: ImageFont.truetype("arial.ttf", size) for size in [20, 24, 30, 38]}

    def text(position, value, size=24, color="text"):
        draw.text(position, value, fill=COLORS[color], font=fonts[size])

    def box(bounds, label):
        draw.rounded_rectangle(bounds, radius=6, fill=COLORS["surface"], outline=COLORS["muted"], width=2)
        text((bounds[0] + 12, bounds[1] + 12), label, 20)

    text((50, 28), "Observatorio de turismo sostenible de Guatemala", 38)
    text((50, 84), "Avance: exploración de datos observados. No incluye predicciones.", 24, "muted")
    text((50, 128), "Evolución temporal   |   Comparación por grupo", 24, "observed")
    for bounds in [(40, 190, 1400, 785), (40, 815, 1400, 1380)]:
        draw.rounded_rectangle(bounds, radius=10, fill=COLORS["surface"], outline=COLORS["grid"], width=2)
    text((65, 210), "1. ¿Cómo ha evolucionado el ingreso de viajeros?", 30)
    text((65, 258), "Serie, fechas y nivel de detalle. Arrastre sobre la gráfica para acercarse.", 24, "muted")
    box((65, 310, 435, 365), "Serie: Total  v")
    box((460, 310, 825, 365), "Mensual | Trimestral | Anual")
    box((850, 310, 1370, 365), "Rango: ene. 2009 — jun. 2026")
    draw.line([(165, 410), (165, 680), (1310, 680)], fill=COLORS["muted"], width=2)
    draw.line(
        [(165, 625), (290, 580), (415, 610), (540, 520), (665, 585),
         (790, 660), (915, 590), (1040, 500), (1165, 450), (1310, 425)],
        fill=COLORS["observed"], width=5,
    )
    text((70, 390), "Viajeros", 20, "muted")
    text((570, 700), "Tiempo", 20, "muted")
    text((65, 745), "Nota: agregaciones completas y mensajes cuando no hay datos.", 20, "muted")
    text((65, 835), "2. ¿Qué vías o países concentran más viajeros?", 30)
    text((65, 883), "Compare dentro de un grupo. El clic en una barra selecciona la serie de arriba.", 24, "muted")
    box((65, 935, 650, 990), "Grupo: Vía de ingreso / País de residencia  v")
    box((675, 935, 1020, 990), "Año: 2025  v")
    for y, width, label, selected in [
        (1040, 850, "Vía Terrestre", False),
        (1110, 560, "Vía Aérea", True),
        (1180, 230, "Vía Marítima", False),
    ]:
        text((70, y + 8), label, 24)
        draw.rectangle(
            (280, y, 280 + width, y + 48),
            fill=COLORS["highlight"] if selected else COLORS["observed"],
            outline=COLORS["text"] if selected else COLORS["observed"],
            width=4 if selected else 1,
        )
    text((65, 1255), "Selección: Vía Aérea, en verde y con borde. El rango temporal se conserva.", 20, "muted")
    text((65, 1300), "Ver la evolución de la serie seleccionada ↑", 24, "observed")
    text((50, 1420), "Bosquejo del avance. Las formas ilustran la navegación, no resultados numéricos.", 20, "muted")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output


if __name__ == "__main__":
    print(draw_wireframe())
