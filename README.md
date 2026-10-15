# CC3084-DATA-SCIENCE

## Laboratorio 9: Visualización Estática

Infografía de una página que comunica a un directivo de INGUAT los hallazgos del Laboratorio 1
(series de tiempo del ingreso de viajeros internacionales a Guatemala, 2009-01 a 2026-06).

### Estructura del repositorio

```
instructions/
└── Laboratorio 09. Visualización Estática. 2026.pdf
documento/
├── Avance_Lab9_Decisiones_de_Diseno.pdf   (avance: decisiones de diseño, APA)
├── Avance_Lab9_Decisiones_de_Diseno.docx  (versión editable para Google Docs)
├── figuras/boceto_paleta.png
└── scripts/
    ├── draw_wireframe.py    (boceto de la página y paleta)
    └── build_document.py    (genera el .docx; el PDF se exporta con LibreOffice)
insumos/
├── series/          (las 7 series mensuales completas del Lab 1: fecha, viajeros)
└── resultados/
    ├── comparativo_series.csv   (Fs, Ft, pendiente, CV, caída y recuperación por serie)
    ├── diagnostico_series.csv   (ADF y factores estacionales por serie)
    ├── metricas_modelos.csv     (MAE, RMSE, MAPE, AIC/BIC de los 5 modelos por serie)
    ├── modelos_arima.csv        (rejilla SARIMA seleccionada)
    ├── maritima_anual.csv
    └── predicciones/            (predicción sobre el test de cada modelo y serie)
```

Los archivos de `insumos/` son copia literal de la rama `lab1`
(`data/processed/series/` y `resultados/`). Las cifras de la infografía deben salir de ahí para
que coincidan con el informe del Lab 1.

### Entregables

| Fecha | Entregable |
|---|---|
| Jueves 15 de octubre (avance) | Documento de explicación de las decisiones de diseño (PDF) |
| Domingo 18 de octubre | Infografía PNG (mínimo 1200x2400 px) y PDF de una página 11x17 in vertical |
| Domingo 18 de octubre | Script de Python de las visualizaciones, link del documento y del diseño, link del repositorio |

### Datos y publicación

Los datos se comparten con fines estrictamente académicos y la infografía no debe publicarse en
repositorios públicos sin consulta previa. Por eso `infografia/` está en `.gitignore`: los PNG y
PDF finales se entregan por Canvas, no se suben aquí.
