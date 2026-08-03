# Laboratorio 2 — Material a entregar

CC3084 Data Science, Semestre II 2026 — Universidad del Valle de Guatemala

**Integrantes:** Hugo Daniel Barillas (23556), Esteban Cárcamo (23016), Ernesto Ascencio (23009)

**Repositorio:** https://github.com/ecarcamo/CC3084-DATA-SCIENCE/tree/lab2

## Contenido

- `Informe_Final_Lab2.pdf` — informe completo: metodología LSTM, modelado de la serie total y de
  vía aérea, comparativo contra el Laboratorio 1, y caracterización de las siete series con
  catch22 (PCA, clustering, heatmap, correlaciones, distancias, interpretación y un LSTM con
  características catch22 de ventana móvil).
- `notebooks/` — cuadernos con el código y las explicaciones, en el orden en que se ejecutan:
  - `08_lstm_preparacion.ipynb` — valida ventaneo, escalado y protocolo de validación.
  - `09_lstm_total.ipynb` — tuneo, selección y predicción LSTM de la serie total.
  - `10_lstm_via_aerea.ipynb` — lo mismo para la vía aérea.
  - `11_comparativo_lstm.ipynb` — comparación LSTM contra los modelos del Laboratorio 1.
  - `12_catch22_caracteristicas.ipynb` — extracción catch22, PCA, clustering, interpretación
    (incisos 2.1 a 2.14) y el LSTM con características de ventana móvil.
- `scripts/` — los mismos cuadernos exportados a `.py`, para reproducibilidad sin Jupyter.
- `resultados/` — CSV producidos por los notebooks anteriores (tuneo, métricas, predicciones,
  matrices catch22 y comparaciones).

## Reproducir

Requiere Python con las dependencias de `requirements-lab2.txt` del repositorio (incluye
`pycatch22`, `tensorflow`/`keras`, `scikit-learn`). Los notebooks se ejecutan en el orden 08 a 12
desde la raíz del repositorio, con `data/processed/series/` ya generado por el Laboratorio 1.
