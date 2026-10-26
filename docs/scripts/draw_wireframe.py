import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from app.theme import COLORS

OUTPUT = ROOT / 'figuras' / 'boceto_tablero.png'
FONT_ROOT = Path('C:/Windows/Fonts')
SIZE = (1800, 2720)
CARD_HEIGHT = 230
CARD_GAP = 18
OBSERVED_TOP = 600
MODELS_TOP = 1890


def card_top(index):
    start, position = (OBSERVED_TOP, index) if index < 5 else (MODELS_TOP, index - 5)
    return start + position * (CARD_HEIGHT + CARD_GAP)


def selected_bar_point():
    return 200, card_top(1) + 118 + 53


def draw_wireframe(output=OUTPUT):
    image = Image.new('RGB', SIZE, COLORS['background'])
    draw = ImageDraw.Draw(image)

    def font(size, bold=False):
        candidates = [
            str(FONT_ROOT / ('arialbd.ttf' if bold else 'arial.ttf')),
            'Arial Bold.ttf' if bold else 'Arial.ttf',
            'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
            '/System/Library/Fonts/Supplemental/' + ('Arial Bold.ttf' if bold else 'Arial.ttf'),
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                pass
        return ImageFont.load_default(size=size)

    def text(x, y, value, size=34, color='text', bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=COLORS.get(color, color))

    def box(bounds, fill='surface', outline='grid', width=3, radius=12):
        draw.rounded_rectangle(bounds, radius=radius, fill=COLORS.get(fill, fill), outline=COLORS.get(outline, outline), width=width)

    def dashed(start, end, y, color, width=4, step=34):
        for x in range(start, end, step):
            draw.line((x, y, min(x + step // 2, end), y), fill=COLORS[color], width=width)

    def checkbox(x, y, label):
        box((x, y, x + 30, y + 30), 'observed', 'observed', radius=4)
        draw.line((x + 7, y + 15, x + 13, y + 22, x + 24, y + 8), fill=COLORS['surface'], width=4)
        text(x + 42, y - 1, label, 28)

    def card(index, title, controls):
        top = card_top(index)
        box((50, top, 1750, top + CARD_HEIGHT))
        text(85, top + 14, title, 34, bold=True)
        step = 1630 / len(controls)
        for position, label in enumerate(controls):
            left = int(85 + position * step)
            box((left, top + 62, int(left + step - 16), top + 108), 'background', radius=8)
            text(left + 14, top + 71, label, 26)
        box((85, top + 118, 1715, top + CARD_HEIGHT - 14), 'background', radius=8)
        return top + 118, top + CARD_HEIGHT - 14

    text(60, 28, 'Observatorio de turismo sostenible de Guatemala', 52, bold=True)
    text(60, 98, 'Boceto de la distribución final · espacios ilustrativos sin datos reales', 32, 'muted')

    box((50, 160, 1750, 300))
    text(85, 175, 'Menú de secciones (enlaces a cada gráfica visible)', 30, 'muted', True)
    text(85, 215, 'Datos observados:  G1 Evolución · G2 Vía o país · G3 Meses · G4 Totales anuales · G5 Variación', 28, 'observed')
    text(85, 255, 'Predicciones y modelos:  G6 Observado y estimado · G7 Error · G8 Desviación por mes', 28, 'observed')

    box((50, 320, 1750, 540))
    text(85, 334, 'Gráficas visibles', 36, bold=True)
    text(85, 382, 'Datos observados', 26, 'muted', True)
    for position, label in enumerate(['G1', 'G2', 'G3', 'G4', 'G5']):
        checkbox(330 + position * 150, 380, label)
    text(85, 440, 'Predicciones y modelos', 26, 'muted', True)
    for position, label in enumerate(['G6', 'G7', 'G8']):
        checkbox(410 + position * 150, 438, label)
    text(85, 492, 'Ocultar una gráfica conserva sus selecciones y callbacks.', 26, 'muted')

    text(60, 556, 'Datos observados', 32, 'muted', True)
    top, bottom = card(0, 'G1 · ¿Cómo ha evolucionado el ingreso de viajeros?', ['Serie', 'Nivel: mes / trimestre / año', 'Fechas: desde / hasta'])
    draw.line([(130 + x * 60, bottom - 20 - (x * 37 % 55)) for x in range(26)], fill=COLORS['observed'], width=5)

    top, bottom = card(1, 'G2 · ¿Qué vías o países concentran más viajeros?', ['Grupo: vías / países', 'Año: todos o uno'])
    for row, width in enumerate([480, 330, 160]):
        selected = row == 1
        draw.rectangle(
            (125, top + 12 + row * 30, 125 + width, top + 34 + row * 30),
            fill=COLORS['highlight' if selected else 'observed'], outline=COLORS['text'] if selected else None, width=3,
        )
    text(700, top + 18, 'Clic en una barra: G1 muestra esa serie y conserva sus fechas.', 28, 'highlight', True)
    text(700, top + 56, 'Si G1 está oculta: aviso y botón «Mostrar la serie temporal».', 26, 'muted')
    arrow_x = 1775
    draw.line((arrow_x, top + 40, arrow_x, card_top(0) + 160), fill=COLORS['highlight'], width=5)
    draw.polygon([(arrow_x - 12, card_top(0) + 178), (arrow_x + 12, card_top(0) + 178), (arrow_x, card_top(0) + 156)], fill=COLORS['highlight'])

    top, bottom = card(2, 'G3 · ¿En qué meses se concentra el ingreso de viajeros?', ['Serie', 'Rango de años'])
    shades = ['#E7EFF6', '#B9CDE0', '#7FA3C4', COLORS['observed']]
    for row in range(3):
        for column in range(12):
            left = 125 + column * 70
            draw.rectangle((left, top + 10 + row * 24, left + 64, top + 30 + row * 24), fill=shades[(row + column * 2) % 4])
    text(1000, top + 30, '× = mes sin dato; el cero real conserva el azul claro.', 26, 'muted')

    top, bottom = card(3, 'G4 · ¿Cómo cambia el total de viajeros entre años completos?', ['Serie', 'Rango de años'])
    for column in range(17):
        height = 20 + (column * 23 % 55)
        draw.rectangle((125 + column * 50, bottom - 10 - height, 160 + column * 50, bottom - 10), fill=COLORS['observed'])
    text(1000, top + 30, 'Solo años con doce meses válidos; la nota lista los excluidos.', 26, 'muted')

    top, bottom = card(4, 'G5 · ¿Cuánto cambió cada mes frente al mismo mes del año anterior?', ['Serie', 'Fechas: desde / hasta'])
    zero = (top + bottom) // 2
    dashed(125, 940, zero, 'muted', 3)
    for column in range(26):
        change = ((column * 17) % 31) - 12
        draw.rectangle((130 + column * 30, min(zero, zero - change), 150 + column * 30, max(zero, zero - change)), fill=COLORS['observed'])
    text(1000, top + 18, '(mes ÷ mismo mes del año anterior − 1) × 100', 26, 'observed', True)
    text(1000, top + 54, 'Sin base válida o con base cero: ×, nunca 0 %.', 26, 'muted')

    text(60, MODELS_TOP - 44, 'Predicciones y modelos (resultados existentes, sin reentrenar)', 32, 'muted', True)
    top, bottom = card(5, 'G6 · ¿Qué estimaron los modelos frente a lo que se registró?', ['Serie', 'Modelos: casillas', 'Periodo'])
    draw.line([(130 + x * 60, bottom - 25 - (x * 29 % 45)) for x in range(14)], fill=COLORS['observed'], width=5)
    dashed(130, 910, bottom - 40, 'forecast', 5)
    text(1000, top + 30, 'Azul continua: observado · naranja discontinua: estimado', 26, 'muted')

    top, bottom = card(6, 'G7 · ¿Qué modelo se equivoca menos para esta serie?', ['Serie', 'Medida: MAE / RMSE / MAPE'])
    for row, width in enumerate([220, 330, 450]):
        draw.rectangle((125, top + 12 + row * 26, 125 + width, top + 30 + row * 26), fill=COLORS['forecast'])
    text(1000, top + 30, 'Mismos meses coincidentes para todos los modelos.', 26, 'muted')

    top, bottom = card(7, 'G8 · ¿En qué meses se alejó el modelo de lo observado?', ['Serie', 'Modelo', 'Fechas'])
    zero = (top + bottom) // 2
    dashed(125, 940, zero, 'muted', 3)
    draw.line([(130 + x * 60, zero - ((x * 19) % 37) + 14) for x in range(14)], fill=COLORS['forecast'], width=5)
    text(1000, top + 30, 'Positivo: estimó menos; negativo: estimó más.', 26, 'muted')

    text(60, 2650, 'Una sola página: el menú lleva a cada gráfica y «Gráficas visibles» decide cuáles se muestran.', 30, 'muted')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, dpi=(240, 240))
    return output


if __name__ == "__main__":
    print(draw_wireframe())
