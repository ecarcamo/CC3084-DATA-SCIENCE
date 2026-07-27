# CC3084-DATA-SCIENCE

## Laboratorio 1: Series de Tiempo

Análisis del ingreso histórico de viajeros internacionales a Guatemala (2009-01 a 2026-06).

### Estructura del repositorio

```
data/
├── raw/Base_Migracion_2009-2026jun.xlsx
└── processed/
    ├── base_limpia.csv
    └── series/
notebooks/
├── 01_carga_limpieza.ipynb
├── 02_eda.ipynb
├── 03_series_preliminar.ipynb
├── 04_diagnostico_series.ipynb
├── 05_modelos_arima.ipynb
├── 06_prediccion_evaluacion.ipynb
└── 07_comparativo.ipynb
scripts/
└── (notebooks 01-07 exportados a .py con jupyter nbconvert)
src/
├── carga.py
├── limpieza.py
├── series.py
├── diagnostico.py
├── modelos.py
├── evaluacion.py
├── comparativo.py
└── utils.py
resultados/
├── diagnostico_series.csv
├── metricas_modelos.csv
├── modelos_arima.csv
├── comparativo_series.csv
├── maritima_anual.csv
└── predicciones/
informe/
├── secciones/
├── figuras/
├── informe_final.md
└── Informe_Final_Lab1.pdf
```

### Convenciones del equipo

- Python + pandas, matplotlib, statsmodels. Sin seaborn.
- Toda serie se guarda como CSV con exactamente dos columnas: `fecha` (formato `YYYY-MM-01`) y
  `viajeros` (float).
- Índice mensual completo y sin huecos; si un mes no tiene registros, va con 0, no ausente.
- Las figuras se guardan en `informe/figuras/` a 150 dpi.
- Cada quien escribe su sección en `informe/secciones/` en un archivo propio para no chocar en
  git.

### Datos

Ver [`informe/secciones/01_datos_y_limpieza.md`](informe/secciones/01_datos_y_limpieza.md) para
el origen de los datos, las decisiones de limpieza y el criterio del split 70/30.

### Cómo reproducir el análisis

1. Crear un entorno virtual e instalar dependencias: `pip install -r requirements.txt`.
2. Correr los notebooks en orden, cada uno depende de los artefactos que deja el anterior
   (`data/processed/`, `resultados/*.csv`, `informe/figuras/`):

   | Orden | Notebook | Qué produce |
   |---|---|---|
   | 1 | `01_carga_limpieza.ipynb` | `data/processed/base_limpia.csv` y las series por vía/país |
   | 2 | `02_eda.ipynb` | Figuras `eda_*.png` del análisis exploratorio |
   | 3 | `03_series_preliminar.ipynb` | Diagnóstico preliminar de la serie total y vía aérea |
   | 4 | `04_diagnostico_series.ipynb` | `resultados/diagnostico_series.csv`, ADF y factores estacionales de las 7 series |
   | 5 | `05_modelos_arima.ipynb` | Rejilla SARIMA, `auto_arima` y `resultados/modelos_arima.csv` |
   | 6 | `06_prediccion_evaluacion.ipynb` | Predicciones fuera de muestra y `resultados/metricas_modelos.csv` |
   | 7 | `07_comparativo.ipynb` | `resultados/comparativo_series.csv` y las figuras `comp_*.png` |

3. El informe consolidado está en [`informe/informe_final.md`](informe/informe_final.md) y su
   versión exportada en [`informe/Informe_Final_Lab1.pdf`](informe/Informe_Final_Lab1.pdf). Para
   regenerar el PDF:
   ```
   pandoc informe/informe_final.md -o informe/Informe_Final_Lab1.pdf \
     --resource-path=informe --toc --pdf-engine=xelatex -V geometry:margin=2.5cm
   ```
4. Los `.py` en `scripts/` son la exportación literal de los notebooks (`jupyter nbconvert
   --to script notebooks/*.ipynb --output-dir=scripts/`), incluidos para el corrector según lo
   pedido en el enunciado.

### Contribuciones por integrante

- **Esteban Cárcamo (23016):** carga y limpieza de la base (`01_carga_limpieza`), construcción de
  series y utilidades compartidas, análisis exploratorio (`02_eda`), diagnóstico de
  estacionariedad de las 7 series (`04_diagnostico_series`), ajuste de modelos SARIMA con rejilla
  manual y `auto_arima`, algoritmos alternativos (Holt-Winters, SES, seasonal naive, Prophet), y
  el fix posterior que descartó especificaciones SARIMA con pronóstico desbordado
  (`05_modelos_arima`, `06_prediccion_evaluacion`). Autor de las secciones 4 y 5 del informe.
- **Hugo Daniel Barillas (23556):** análisis preliminar de la serie total y vía aérea
  (`03_series_preliminar`), y el análisis comparativo completo entre las 7 series: métricas de
  estacionalidad, tendencia, volatilidad e impacto pandémico (`07_comparativo`), con los
  descubrimientos para INGUAT. Autor de la sección 6 del informe.
- **Ernesto Ascencio (23009):** armado y entrega del informe final: consolidación de las 6
  secciones en `informe/informe_final.md` con portada e índice, revisión de coherencia entre
  secciones (numeración, figuras, cifras), exportación a PDF, generación de `requirements.txt` y
  de los scripts en `scripts/`, y esta actualización del README.
