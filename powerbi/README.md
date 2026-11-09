# Laboratorio 12 · Informe de Power BI del observatorio de turismo

Segunda versión del tablero del Laboratorio 10 (Dash), construida como informe de Power BI Desktop. Usa los mismos CSV y resultados de modelos del Laboratorio 10; no entrena modelos nuevos.

- **Archivo:** `powerbi/observatorio_turismo.pbix`, versión **v1.0** (SHA-256 `b4cfc732…f76d54`, ver `powerbi/version_informe.json`).
- **Power BI Desktop:** 2.159.1231.0 de 64 bits (octubre de 2026) o posterior. Solo se ejecuta en **Windows** (10 / Server 2016 o posterior, x64). Un `.pbix` guardado en una versión nueva no abre en una anterior.
- **Licencia:** basta con Desktop gratuito. No se publicó en el servicio de Power BI ni se usan funciones de pago.
- **Documento final:** `docs/lab12/Lab12_PowerBI_Final.pdf` (fuente `docs/lab12/informe_final.md`).

## Estructura de carpetas

```
powerbi/
├── observatorio_turismo.pbix     informe final (v1.0)
├── version_informe.json          versión, SHA-256 y estado del .pbix
├── tema_observatorio.json        tema de colores y fuente (Vista > Temas > Examinar temas)
├── medidas_hugo.json             medidas DAX de V1–V5 y del detalle
└── medidas_diego.json            medidas DAX de V6–V8
insumos/
├── series/serie_<clave>.csv                          observado: fecha, viajeros (7 series × 210 meses)
└── resultados/
    ├── predicciones/<serie>_<modelo>.csv             estimado: fecha, prediccion (35 archivos × 63 meses)
    └── metricas_modelos.csv                          MAE, RMSE y MAPE por serie y modelo (35 filas)
docs/lab12/                       documento de diseño, comparación, pruebas y evidencia JSON
docs/figuras/lab12_*.png          capturas de ambas versiones
docs/scripts/                     generadores PBIR, valores de referencia y cronómetro de las pruebas
tests/test_lab12_design.py, tests/test_lab12_models.py   pruebas automatizadas del informe
```

## Abrir el informe

1. Clonar la rama `lab12` en Windows: `git clone -b lab12 https://github.com/ecarcamo/CC3084-DATA-SCIENCE.git`.
2. Abrir `powerbi/observatorio_turismo.pbix` con Power BI Desktop. Los datos ya están importados: se puede revisar sin actualizar.
3. El informe abre en **Inicio**. Los botones superiores llevan a Datos observados, Estacionalidad y años, Predicciones y modelos y Detalle de serie. En Desktop los botones se activan con **Ctrl + clic**. «Restablecer vista» vuelve al estado inicial de cada página.

## Cambiar la ruta de origen y actualizar

El parámetro `RutaInsumos` guarda la ruta absoluta del equipo donde se construyó el informe. En otro equipo hay que cambiarlo antes de actualizar:

1. **Inicio > Transformar datos > Editar parámetros.**
2. En `RutaInsumos`, escribir la ruta absoluta de la carpeta `insumos` del clon, **terminada en `\`**. Ejemplo: `C:\Users\<usuario>\CC3084-DATA-SCIENCE\insumos\`.
3. **Aceptar > Aplicar cambios** y luego **Inicio > Actualizar**.
4. Conservar las subcarpetas `series` y `resultados\predicciones`. Las consultas fijan la configuración regional `en-US`, así que el punto decimal se lee bien en cualquier idioma de Windows.
5. Comprobar los conteos de control (la página oculta **Control** los muestra; se ve con clic derecho en las pestañas > Mostrar): **1.470** observaciones, **2.205** predicciones y **35** métricas; Total 2025 = **3.597.238** viajeros.

Diego probó este procedimiento con una copia de `insumos` en otra carpeta y se conservaron los mismos conteos (`docs/lab12/01_diego_datos.md`, «Prueba de actualización desde otra carpeta»).

## Tablas del modelo

Modelo estrella en modo Import. Las dimensiones filtran a los hechos en una sola dirección y no hay relaciones entre hechos, de modo que lo observado no se repite por cada modelo.

| Tabla | Tipo | Columnas | Relación |
|---|---|---|---|
| `Observaciones` | Hecho | `serie_clave`, `fecha`, `viajeros` | `DimSerie[clave]`, `Calendario[Date]` |
| **`Predicciones`** | Hecho | `serie_clave`, `modelo_clave`, `fecha`, `prediccion` | `DimSerie[clave]`, `DimModelo[clave]`, `Calendario[Date]` |
| **`Metricas`** | Hecho | `serie_clave`, `modelo_clave`, `mae`, `rmse`, `mape`, `mape_excluidos`, `mejor` | `DimSerie[clave]`, `DimModelo[clave]`; **sin** relación con `Calendario` (métricas de los 63 meses completos) |
| `DimSerie` | Dimensión | `clave`, `nombre`, `grupo`, `orden` | 7 series: Total, 3 vías, 3 países |
| `DimModelo` | Dimensión | `clave`, `nombre`, `orden` | SARIMA, Holt-Winters, SES, Seasonal Naive, Prophet |
| `Calendario` | Dimensión | `Date`, `Año`, `Trimestre`, `MesNum`, `Mes` | Diario, 2009-01-01 a 2026-12-31 |
| `Medidas` | Medidas | `Viajeros`, `Viajeros serie`, `Estimado`, `Diferencia`, medidas de V3–V8 | Sin relaciones |

- **Predicciones:** abril de 2021 a junio de 2026, 63 meses por serie y modelo. Son estimaciones de meses ya registrados, sin intervalos de confianza.
- **Metricas:** MAE y RMSE en viajeros; MAPE ya en porcentaje (58,11 significa 58,11 %). `mape_excluidos` cuenta meses con observado 0 (11 en Vía Marítima). La fila «Total» de la tabla complementaria de la página de modelos suma métricas entre modelos y no se usa para comparar.

## Reproducir las tres pruebas

El protocolo está en `docs/lab12/03_esteban_gestion_y_comparacion.md` §3 y los resultados en `docs/lab12/05_diego_pruebas.md`.

| Prueba | Power BI | Dash (Lab 10) | Resultado esperado |
|---|---|---|---|
| T1 · Pregunta con filtros | Datos observados: grupo «Vía de ingreso», año 2025; leer V2 | G2: grupo «Vía de ingreso», año 2025 | Vía Terrestre, 2.401.323 |
| T2 · General → detalle → regreso | V1: clic derecho en 2025 > Explorar en profundidad hasta T4 y meses; luego Rastrear agrupando dos veces | G1: Anual → Trimestral → Mensual → Anual | 2025 = 3.597.238; T4 = 997.817; diciembre = 392.087 |
| T3 · Predicciones y modelos | Predicciones y modelos: serie Total, SARIMA, Holt-Winters y SES en V6; V7 con MAE, RMSE y MAPE | G6 y G7 con los mismos modelos y métricas | SES: MAE 175.088,44; RMSE 194.790,81; MAPE 58,11 % |

Valores de referencia recalculados desde los CSV (cualquier sistema operativo):

```bash
python -m docs.scripts.lab12_valores_referencia
```

## Abrir la versión del Laboratorio 10 (Dash)

```bash
git worktree add ../lab10-tablero lab10
cd ../lab10-tablero
python -m venv .venv && source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Abrir http://127.0.0.1:8050. La comparación se hace siempre contra `lab10` (`b605afc`), no contra `lab11`, que cambió G6 y G7 y retiró G8. Al terminar: `git worktree remove ../lab10-tablero`.

## Versiones del informe

Obtenidas con `git log --format='%h %an %s' -- powerbi/observatorio_turismo.pbix`.

| Versión | Commit | Autor | Contenido |
|---|---|---|---|
| v0.1 | `f43b181` | Diego | Importación de series, predicciones y métricas; modelo y página Control |
| v0.2 | `f4eb7b0` | Hugo | Tema, V1 y V2 enlazadas (avance del 5-nov) |
| v0.3 | `d022104` | Hugo | V3–V5, cinco páginas, navegación, marcadores y drillthrough |
| v1.0 | `a3d5706` | Diego | V6–V8 y página de modelos; congelada en `44eab4e` (`version_informe.json`) |
