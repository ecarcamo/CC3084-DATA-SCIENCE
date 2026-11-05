from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/figuras/lab12_hugo_boceto.png"
SIZE = (1800, 2440)
PAGES = [
    "Inicio", "Datos observados", "Estacionalidad y años",
    "Predicciones y modelos", "Detalle de serie",
]
COLORS = {
    "background": "#F4F6F8", "surface": "#FFFFFF", "text": "#1B2733",
    "muted": "#5B6B7A", "grid": "#DDE3E9", "observed": "#1F4E79",
    "forecast": "#A65E16", "selection": "#20745A", "alert": "#B3261E",
}


def draw_wireframe(output=OUTPUT):
    image = Image.new("RGB", SIZE, COLORS["background"])
    draw = ImageDraw.Draw(image)

    def font(size, bold=False):
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)

    def text(x, y, value, size=24, color="text", bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=COLORS[color])

    def box(bounds, fill="surface", outline="grid"):
        draw.rounded_rectangle(
            bounds, radius=10, fill=COLORS[fill], outline=COLORS[outline], width=2
        )

    def wrapped(x, y, value, width, size=24, color="muted"):
        words = value.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and draw.textbbox((0, 0), candidate, font=font(size))[2] > width:
                text(x, y, line, size, color)
                y += size + 9
                line = word
            else:
                line = candidate
        text(x, y, line, size, color)

    def panel(index, title, help_text):
        top = 155 + index * 438
        box((35, top, 1765, top + 414))
        text(60, top + 15, title, 32, bold=True)
        x = 60
        for position, label in enumerate(PAGES):
            width = [125, 260, 305, 345, 250][position]
            selected = position == index
            box(
                (x, top + 66, x + width, top + 112),
                "selection" if selected else "background",
                "selection" if selected else "grid",
            )
            text(x + 10, top + 76, label, 22, "surface" if selected else "text")
            x += width + 9
        box((1490, top + 66, 1735, top + 112), "background")
        text(1505, top + 78, "Restablecer vista", 22)
        wrapped(60, top + 355, help_text, 1660, 23)
        return top

    def chart(left, top, width, label, description, color="observed"):
        box((left, top, left + width, top + 194), "background")
        text(left + 18, top + 15, label, 25, color, True)
        wrapped(left + 18, top + 58, description, width - 36, 23)

    text(45, 24, "Observatorio de turismo · Power BI", 44, bold=True)
    text(45, 84, "Boceto de navegación final · no es una captura de Power BI ni representa datos reales", 25, "muted")

    top = panel(0, "1. Inicio", "Los botones llevan a páginas de análisis. Las pestañas verdes identifican la página activa con texto y color.")
    chart(60, top + 138, 520, "Propósito", "Examinar viajeros registrados y estimaciones históricas. Cobertura: ene. 2009 a jun. 2026.")
    chart(600, top + 138, 560, "Cómo leer el informe", "Azul: observado. Naranja: estimado. Verde: selección. Rojo y mensaje: alerta o sin datos.")
    chart(1180, top + 138, 555, "Accesos por pregunta", "Evolución y ranking → Datos observados. Meses y años → Estacionalidad. Errores → Modelos.")

    top = panel(1, "2. Datos observados · V1 y V2 en el avance", "Clic en V2 → filtra V1. Sin selección → Total. Grupo y año filtran solo V2, como en Lab 10. V5 queda para sesión 2.")
    chart(60, top + 138, 785, "V1 · Evolución de viajeros", "Líneas azules. Explorar Año > Trimestre > Mes. La serie seleccionada conserva toda su historia.")
    draw.line([(90 + i * 26, top + 310 - (i * 17 % 42)) for i in range(27)], fill=COLORS["observed"], width=4)
    chart(870, top + 138, 520, "V2 · Ranking por vía o país", "Grupo único: vías. Año: 2025. Barras ordenadas de mayor a menor.")
    for index, width in enumerate([220, 150, 55]):
        draw.rectangle(
            (895, top + 268 + index * 19, 895 + width, top + 280 + index * 19),
            fill=COLORS["selection" if index == 1 else "observed"],
        )
    draw.line((865, top + 315, 840, top + 315), fill=COLORS["selection"], width=5)
    draw.polygon([(840, top + 315), (851, top + 307), (851, top + 323)], fill=COLORS["selection"])
    chart(1410, top + 138, 325, "V5 · Cambio %", "Variación mensual interanual. Cero base o sin dato: × y explicación.")

    top = panel(2, "3. Estacionalidad y años · sesión 2", "Se conserva la pregunta de G3, pero el mapa de calor se sustituye por una matriz con formato condicional.")
    chart(60, top + 138, 820, "V3 · Concentración por mes", "Matriz Año × Mes. Escala azul claro → azul oscuro. × = mes sin dato; no equivale a cero.")
    for row in range(2):
        for column in range(12):
            left = 85 + column * 57
            draw.rectangle(
                (left, top + 278 + row * 22, left + 48, top + 295 + row * 22),
                fill=["#E7EFF6", "#B9CDE0", "#7FA3C4", "#1F4E79"][(column + row) % 4],
            )
    chart(905, top + 138, 830, "V4 · Totales de años completos", "Columnas por año. Solo se comparan años con doce meses válidos. Los excluidos se indican por escrito.")

    top = panel(3, "4. Predicciones y modelos · sesión 2", "Serie única. Evaluación: abr. 2021 a jun. 2026. No son pronósticos futuros. Las métricas importadas no cambian por fecha.")
    chart(60, top + 138, 540, "V6 · Observado y estimado", "Azul continuo y cinco modelos naranjas con trazos distintos. Modelos identificados por nombre.", "forecast")
    chart(620, top + 138, 540, "V7 · Error por modelo", "Barras de MAE, RMSE o MAPE. Menor error histórico no garantiza precisión futura.", "forecast")
    chart(1180, top + 138, 555, "V8 · Desviación mensual", "Línea de observado menos estimado. Referencia en cero. Tabla de modelos como apoyo, no como V9.", "forecast")

    top = panel(4, "5. Detalle de serie · sesión 2", "Acceso con clic derecho desde V2 o V7. Se conserva la serie y el contexto recibido. Regresar vuelve al origen.")
    chart(60, top + 138, 540, "Serie recibida", "Campo de obtención de detalles: DimSerie[nombre]. Encabezado con nombre y período.")
    chart(620, top + 138, 540, "Historia de la serie", "Evolución de viajeros. Mensaje visible si el contexto no contiene observaciones.")
    chart(1180, top + 138, 555, "Regresar", "Botón de regreso al origen. Restablecer vista recupera el estado inicial de cada página.")

    text(45, 2370, "Navegación, marcadores y páginas finales: propuesta. Avance PBIR: Datos observados y Control oculta.", 25, "muted")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, dpi=(180, 180))
    return output


if __name__ == "__main__":
    print(draw_wireframe())
