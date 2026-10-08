"""Versión ESTÁTICA del mismo dashboard (imagen fija). Ejecutar: python static.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.express as px

df = px.data.gapminder()
fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5.5))

d = df[df.year == 2007]
for cont, g in d.groupby("continent"):
    a.scatter(g.gdpPercap, g.lifeExp, s=g["pop"] / 2e6, alpha=0.6, label=cont)
a.set_xscale("log")
a.set(title="2007: ingreso vs. esperanza de vida", xlabel="PIB per cápita (log)", ylabel="Esperanza de vida")
a.legend(title="Continente")

for cont, g in df.groupby("continent"):
    m = g.groupby("year").lifeExp.mean()
    b.plot(m.index, m.values, marker="o", label=cont)
b.set(title="Esperanza de vida media por continente", xlabel="Año", ylabel="Años")
b.legend()

fig.suptitle("Gapminder — dashboard estático", fontweight="bold")
fig.tight_layout()
out = Path(__file__).resolve().parent.parent / "img" / "dashboard_estatico.png"
fig.savefig(out, dpi=150)
print(out)
