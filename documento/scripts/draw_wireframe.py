import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

output_path = sys.argv[1]
BG, JADE, SALVIA, TXT, ACH = "#F4F0E6", "#1E4D45", "#8DA197", "#26292B", "#C4552D"
plt.rcParams["font.family"] = "Liberation Sans"

W, H = 11, 17
fig = plt.figure(figsize=(7.6, 6.2), dpi=220)
ax = fig.add_axes([0.0, 0.0, 0.52, 1.0])
ax.set_xlim(-0.6, W + 0.6)
ax.set_ylim(-0.6, H + 0.6)
ax.set_aspect("equal")
ax.axis("off")
ax.add_patch(Rectangle((0, 0), W, H, facecolor=BG, edgecolor="#BDB6A6", lw=0.8))


def draw_block(x, y, w, h, label, subtitle, fill=None, edge=SALVIA, color=TXT):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                facecolor=fill or "none", edgecolor=edge, lw=0.9))
    ax.text(x + 0.25, y + h - 0.35, label, fontsize=6.2, fontweight="bold", color=color, va="top")
    ax.text(x + 0.25, y + h - 0.85, subtitle, fontsize=4.8, color=color, va="top", linespacing=1.25)


margin, gap = 0.5, 0.3
draw_block(margin, 15.1, W - 2 * margin, 1.5, "1  Titular y subtítulo", "Pregunta guía como titular periodístico", fill=JADE, edge=JADE, color=BG)
card_w = (W - 2 * margin - 3 * gap) / 4
for i, kpi in enumerate(["52.3 M", "4.69 M", "−97.5 %", "61 %"]):
    x = margin + i * (card_w + gap)
    ax.add_patch(FancyBboxPatch((x, 13.3), card_w, 1.5, boxstyle="round,pad=0,rounding_size=0.12",
                                facecolor="none", edgecolor=SALVIA, lw=0.9))
    ax.text(x + card_w / 2, 14.2, kpi, fontsize=8, fontweight="bold", ha="center",
            color=ACH if i == 2 else JADE)
    ax.text(x + card_w / 2, 13.6, "KPI", fontsize=4.6, ha="center", color=TXT)
draw_block(margin, 10.1, W - 2 * margin, 2.9, "2  Panorama 2009–2026", "Línea mensual con anotaciones de eventos")
ax.plot([1.0, 3.2, 5.6, 6.2, 6.6, 7.6, 10.0], [10.9, 11.4, 12.1, 10.35, 10.5, 11.8, 11.5], color=JADE, lw=1.2)
ax.add_patch(Rectangle((6.1, 10.25), 1.0, 2.2, facecolor=ACH, alpha=0.15, edgecolor="none"))
half_w = (W - 2 * margin - gap) / 2
draw_block(margin, 6.9, half_w, 2.9, "3a  Estacionalidad", "Índice mensual\n(diciembre, Semana Santa,\njulio, septiembre)")
draw_block(margin + half_w + gap, 6.9, half_w, 2.9, "3b  Cuadrante comparativo", "2 × 2: estacionalidad,\ncrecimiento, volatilidad,\ngolpe de la pandemia")
draw_block(margin, 3.7, half_w, 2.9, "4a  Desempeño de modelos", "MAE y RMSE de los 5\nmodelos (serie total)")
draw_block(margin + half_w + gap, 3.7, half_w, 2.9, "4b  Pronóstico ganador", "Real vs. SES con banda\n80 % / 95 % «Estimación»", edge=ACH)
draw_block(margin, 1.15, W - 2 * margin, 2.25, "5  Recomendaciones para INGUAT", "3 a 5 tarjetas de acción numeradas")
ax.text(margin, 0.5, "Ficha técnica · Fuente: Base de Migración 2009–2026 (INGUAT/IGM) · Autores", fontsize=4.6, color=TXT)

ax.annotate("", xy=(W + 0.35, 1.2), xytext=(W + 0.35, 16.5),
            arrowprops=dict(arrowstyle="-|>", color=TXT, lw=0.8))
ax.text(W + 0.5, 8.8, "lectura", rotation=270, fontsize=5, color=TXT, va="center")

sx = fig.add_axes([0.58, 0.18, 0.4, 0.64])
sx.axis("off")
sx.set_xlim(0, 1)
sx.set_ylim(0, 1)
swatches = [(BG, "Fondo", "#F4F0E6 · hueso"), (JADE, "Dominante", "#1E4D45 · jade profundo"),
      (SALVIA, "Mediador", "#8DA197 · salvia gris"), (TXT, "Texto", "#26292B · grafito"),
      (ACH, "Acento", "#C4552D · achiote")]
for i, (color, role, label) in enumerate(swatches):
    y = 0.86 - i * 0.19
    sx.add_patch(Rectangle((0.0, y), 0.22, 0.13, facecolor=color, edgecolor="#BDB6A6", lw=0.6))
    sx.text(0.27, y + 0.085, role, fontsize=7, fontweight="bold", color=TXT, va="center")
    sx.text(0.27, y + 0.03, label, fontsize=6, color=TXT, va="center")

fig.savefig(output_path, facecolor="white", bbox_inches="tight", pad_inches=0.04)
