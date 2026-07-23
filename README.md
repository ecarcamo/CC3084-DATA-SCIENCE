# CC3084-DATA-SCIENCE

## Laboratorio 1 — Series de Tiempo

Análisis del ingreso histórico de viajeros internacionales a Guatemala (2009-01 a 2026-06).

### Estructura del repositorio

```
data/
├── raw/Base_Migracion_2009-2026jun.xlsx
└── processed/
    ├── base_limpia.csv
    └── series/
notebooks/
└── 01_carga_limpieza.ipynb
src/
├── carga.py
├── limpieza.py
└── series.py
informe/
├── secciones/
└── figuras/
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
