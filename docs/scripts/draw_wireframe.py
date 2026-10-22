import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from app.theme import COLORS

OUTPUT = ROOT / 'figuras' / 'boceto_tablero.png'
FONT_ROOT = Path('C:/Windows/Fonts')


def draw_wireframe(output=OUTPUT):
    image = Image.new('RGB', (1800, 2170), COLORS['background'])
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

    def box(bounds, fill='surface', outline='grid', width=3):
        draw.rounded_rectangle(bounds, radius=12, fill=COLORS.get(fill, fill), outline=COLORS.get(outline, outline), width=width)

    def panel(y, title, active, controls, note):
        box((50, y, 1750, y + 610))
        text(85, y + 20, title, 43, bold=True)
        tabs = [('Panorama', 85, 445), ('Detalle por vía y país', 460, 1020), ('Predicciones y modelos', 1035, 1715)]
        for index, (label, left, right) in enumerate(tabs):
            selected = index == active
            box((left, y + 85, right, y + 149), 'observed' if selected else 'background')
            text(left + 18, y + 100, label, 32, 'surface' if selected else 'muted', selected)
        count = len(controls)
        step = 1630 / count
        for index, label in enumerate(controls):
            left = int(85 + index * step)
            box((left, y + 175, int(left + step - 16), y + 244), 'background')
            text(left + 15, y + 194, label, 31)
        text(85, y + 555, note, 29, 'muted')

    def chart(bounds, label, subtitle=None):
        box(bounds, 'background')
        left, top, right, bottom = bounds
        text(left + 20, top + 14, label, 33, bold=True)
        if subtitle:
            text(left + 20, top + 58, subtitle, 27, 'muted')
        return left, top, right, bottom

    text(60, 28, 'Tablero de viajeros de Guatemala', 54, bold=True)
    text(60, 100, 'Boceto de navegación · espacios ilustrativos sin datos reales', 32, 'muted')

    panel(175, 'Panorama · vista de entrada', 0, ['Serie: total', 'Fechas: desde / hasta', 'Nivel: mensual'], 'Cambiar la serie, el periodo o el nivel temporal para explorar los datos.')
    chart((85, 445, 1715, 705), 'Serie temporal observada', 'Nivel mensual, trimestral o anual')
    draw.line([(150, 650), (1650, 650)], fill=COLORS['grid'], width=3)
    draw.line([(150, 540), (150, 650)], fill=COLORS['grid'], width=3)
    text(630, 595, 'Espacio de la gráfica', 35, 'observed')

    panel(820, 'Detalle por vía y país · selección enlazada', 1, ['Grupo: vías / países', 'Año: todos o uno'], 'Elegir una barra cambia la serie temporal; el rango de fechas se conserva.')
    chart((85, 1090, 805, 1350), 'Ranking del grupo', 'Vías y países se comparan por separado')
    for offset, width, color in [(0, 400, 'observed'), (1, 310, 'highlight'), (2, 220, 'observed')]:
        draw.rectangle((125, 1205 + offset * 42, 125 + width, 1230 + offset * 42), fill=COLORS[color], outline=COLORS['text'] if color == 'highlight' else None, width=3)
    text(550, 1241, 'Selección', 26, 'highlight')
    chart((840, 1090, 1715, 1350), 'Serie temporal enlazada', 'La selección se identifica por nombre y borde')
    text(1040, 1230, 'Espacio de la gráfica', 35, 'observed')

    panel(1465, 'Predicciones y modelos · propuesta para la entrega final', 2, ['Serie: seleccionar', 'Modelo: seleccionar', 'Fechas: desde / hasta'], 'Sin datos: “No hay datos para esta selección”. Ajustar o limpiar los filtros.')
    chart((85, 1735, 1060, 1995), 'Observado y predicción', 'Comparación en fechas coincidentes')
    draw.line((125, 1870, 315, 1870), fill=COLORS['observed'], width=6)
    text(340, 1850, 'Observado', 30, 'observed')
    for x in range(125, 315, 38):
        draw.line((x, 1930, x + 20, 1930), fill=COLORS['forecast'], width=6)
    text(340, 1910, 'Predicción', 30, 'forecast')
    chart((1095, 1735, 1715, 1995), 'Error de los modelos', 'Indicador y explicación breve')
    text(1150, 1850, 'Espacio de comparación', 31, 'muted')
    text(1150, 1900, 'de errores', 31, 'muted')

    text(60, 2120, 'Cada vista conserva el menú y usa la misma paleta, tipografía y etiquetas.', 31, 'muted')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, dpi=(240, 240))
    return output


if __name__ == "__main__":
    print(draw_wireframe())
