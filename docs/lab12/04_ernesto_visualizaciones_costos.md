# Lab 12 · Visualizaciones V1–V8, especificación V3–V8 y costos

**Responsable:** Ernesto. **Fecha:** 7 de noviembre de 2026. **Alcance:** 4.3, especificación de V3–V8 para Hugo y Diego, y 5.2.

El comportamiento se tomó del código de la rama `lab10` (`app/components/*.py` y `app/model_results.py`), no de `lab11`. Los valores esperados provienen de [`docs/scripts/lab12_valores_referencia.py`](../scripts/lab12_valores_referencia.py), que lee los CSV de `insumos/` y comprueba con `assert` conteos, duplicados, cobertura y las 35 métricas recalculadas:

```bash
python -m docs.scripts.lab12_valores_referencia
```

El DAX de este documento se escribió sin Power BI Desktop (equipo macOS). **Todas las medidas están marcadas como no probadas en Desktop**: Hugo y Diego las validan contra los valores esperados de cada ficha y corrigen aquí cualquier ajuste.

## 1. Tipo y equivalencia de las ocho visualizaciones (4.3)

| V | Lab 10 | Pregunta | Tipo en Dash | Tipo en Power BI | Por qué ese tipo responde la pregunta | Sustitución y motivo |
|---|---|---|---|---|---|---|
| V1 | G1 | ¿Cómo ha evolucionado el ingreso de viajeros? | Líneas con selector de serie y de granularidad (mes, trimestre, año) | Gráfico de líneas, eje Año > Trimestre > Mes | La línea muestra continuidad temporal, tendencia y épocas de alza o baja | Selector de granularidad → exploración jerárquica nativa (bajar/subir). Selector de serie → clic en V2 y `[Viajeros serie]` (Total por defecto) |
| V2 | G2 | ¿Qué vías o países concentran más viajeros? | Barras horizontales con selector de grupo y año | Gráfico de barras agrupadas horizontal | La longitud ordenada compara magnitudes entre categorías | Desplegables → segmentadores. Se conserva el clic ranking → serie temporal (`DataFilter`) |
| V3 | G3 | ¿En qué meses se concentra el ingreso de viajeros? | Mapa de calor año × mes, escala `#E7EFF6` → `#1F4E79` | Matriz Año × Mes con formato condicional de fondo | La intensidad por celda permite comparar meses dentro y entre años | Power BI no trae mapa de calor nativo; la matriz con degradado conserva la escala y muestra además el valor. Las × de meses sin dato pasan a celdas vacías, explicadas en la nota |
| V4 | G4 | ¿Cómo cambia el total de viajeros entre años completos? | Barras verticales por año, solo años con 12 meses, nota de excluidos | Gráfico de columnas agrupadas + tarjeta con la nota | Las columnas comparan totales de una misma magnitud anual | Ninguna en el tipo; la nota pasa a una medida de texto |
| V5 | G5 | ¿Cuánto cambió cada mes frente al mismo mes del año anterior? | Barras por mes de variación %, línea 0 % discontinua, × en meses sin base | Gráfico de columnas por mes + línea constante 0 % | Las columnas positivas y negativas alrededor de 0 muestran el signo y la magnitud del cambio | Las × no existen de forma nativa: los meses sin base no se dibujan y se cuentan en la nota. Selector de fechas → segmentador «Entre» |
| V6 | G6 | ¿Qué estimaron los modelos frente a lo que se registró? | Líneas: observado azul continuo, cada modelo naranja con trazo propio; casillas de modelos | Gráfico de líneas con una medida por modelo | Superponer las líneas en el mismo eje permite ver dónde coinciden y dónde se separan | Casillas → segmentador de modelos de selección múltiple. Color y trazo se fijan por medida, no por paleta automática |
| V7 | G7 | ¿Qué modelo se equivoca menos para esta serie? | Barras horizontales ordenadas por error; selector MAE/RMSE/MAPE | Gráfico de barras horizontal + tabla desconectada `MetricaV7` y `SWITCH` | Ordenar de menor a mayor error responde directamente «cuál se equivoca menos» | Selector → segmentador de una tabla desconectada. Se usa `Metricas` importada (ver decisión V7) |
| V8 | G8 | ¿En qué meses se alejó el modelo de lo observado? | Línea con marcadores de observado − estimado, línea 0 «Observado = estimado» | Gráfico de líneas con marcadores + línea constante 0 | La distancia a 0 mes a mes localiza las desviaciones y su signo | Desplegable de modelo → segmentador de selección única. El selector de fechas se comparte con V6 |

La página única de Lab 10 con casillas «Gráficas visibles» se sustituye por páginas temáticas con navegador. Segmentadores, tarjetas, botones, tablas y textos de ayuda no cuentan como visualizaciones.

### Capturas del Lab 10

Evidencia de la versión Dash para comparar con Power BI. Tablero de la rama `lab10` (`b605afc`) en http://127.0.0.1:8050, macOS, Chrome, ventana de 1920 px; capturas tomadas el 7-nov-2026 con Claude in Chrome en el **estado inicial** de cada gráfica, sin interacción previa.

| Captura | Muestra | Selección inicial | Comprobación |
|---|---|---|---|
| [G1](../figuras/lab12_ernesto_lab10_g1.png) | Serie mensual completa | Total, mensual, 01/01/2009–30/06/2026 | Caída de 2020 y pico de dic-2022 |
| [G2](../figuras/lab12_ernesto_lab10_g2.png) | Ranking de vías | Vía de ingreso, 2025 | Terrestre > Aérea > Marítima (2.401.323 / 1.188.971 / 6.944) |
| [G3](../figuras/lab12_ernesto_lab10_g3.png) | Mapa de calor año × mes | Total, 2009–2026 | Nota: 210 meses con dato, 6 sin dato (× en jul–dic 2026) |
| [G4](../figuras/lab12_ernesto_lab10_g4.png) | Totales de años completos | Total, 2009–2026 | 17 años; nota «2026: 6 de 12 meses válidos» |
| [G5](../figuras/lab12_ernesto_lab10_g5.png) | Variación interanual mensual | Total, 01/01/2010–01/06/2026 | Nota: 198 meses calculados; todos con base válida |
| [G6](../figuras/lab12_ernesto_lab10_g6.png) | Observado frente a estimados | Total; SARIMA, Holt-Winters, SES; 01/04/2021–01/06/2026 | Nota: 63 meses; SES es una línea constante |
| [G7](../figuras/lab12_ernesto_lab10_g7.png) | Error por modelo | Total, MAE | SES < Holt-Winters < Seasonal Naive < SARIMA < Prophet; 63 meses |
| [G8](../figuras/lab12_ernesto_lab10_g8.png) | Observado − estimado por mes | Total, SARIMA, 01/04/2021–01/06/2026 | Pico en dic-2022; casi todos los meses por encima de 0 |

Las notas de G3, G4, G5 y G6 confirman los conteos que el script y las fichas de §2 esperan en Power BI.

## 2. Especificación de V3–V8

### 2.1 Medidas compartidas

Todas van en la tabla `Medidas`. Ninguna suma grupos distintos: igual que `[Viajeros serie]`, si no hay exactamente una serie se usa Total.

```dax
Serie elegida =
IF ( HASONEVALUE ( DimSerie[nombre] ), SELECTEDVALUE ( DimSerie[nombre] ), "Total" )

Meses con dato serie =
IF (
    HASONEVALUE ( DimSerie[clave] ),
    COUNT ( Observaciones[viajeros] ),
    CALCULATE ( COUNT ( Observaciones[viajeros] ), REMOVEFILTERS ( DimSerie ), DimSerie[clave] = "total" )
)

Estimado serie =
IF (
    HASONEVALUE ( DimSerie[clave] ),
    [Estimado],
    CALCULATE ( [Estimado], REMOVEFILTERS ( DimSerie ), DimSerie[clave] = "total" )
)
```

| Medida | Finalidad | Usada en |
|---|---|---|
| `Serie elegida` | Nombre de la serie en títulos y notas | V3–V8 |
| `Meses con dato serie` | Meses válidos; decide si un año es completo | V3, V4 |
| `Estimado serie` | `[Estimado]` con el mismo respaldo a Total que `[Viajeros serie]` | V6 |

**Mensajes «sin datos».** Cada gráfica tiene una tarjeta (o cuadro de texto con valor dinámico) encima del área del gráfico con su medida `Mensaje Vn`, fuente Arial 12, color `#B3261E`. La medida devuelve `""` cuando hay datos para que la tarjeta no muestre «(En blanco)». El texto es el mismo de Lab 10.

### 2.2 V3 · Estacionalidad y años: matriz Año × Mes

- **Página:** Estacionalidad y años. **Objeto:** Matriz.
- **Filas:** `Calendario[Año]`. **Columnas:** `Calendario[Mes]` (ordenado por `MesNum`). **Valores:** `[Viajeros serie]`, formato `#,0`.
- Totales de fila y de columna **desactivados** (un total de 2026 mezclaría 6 meses con años de 12).
- **Formato condicional → Color de fondo → Degradado:** mínimo `#E7EFF6` (valor más bajo), máximo `#1F4E79` (valor más alto). Celdas vacías: sin formato.
- **Color de fuente → Reglas:** si el valor es ≥ 55 % y ≤ 100 % (porcentaje) → `#FFFFFF`; en otro caso `#1B2733`. Así el número se lee sobre los azules oscuros.
- **Segmentadores de la página (filtran V3 y V4):** `DimSerie[nombre]` de selección única, Total por defecto; `Calendario[Año]` «Entre», 2009–2026.
- **Título:** «¿En qué meses se concentra el ingreso de viajeros?»; subtítulo con `[Serie elegida]`.

```dax
Nota V3 =
VAR Meses = COUNTROWS ( VALUES ( Calendario[Año] ) ) * 12
VAR ConDato = [Meses con dato serie]
RETURN
    [Serie elegida] & " · " & MIN ( Calendario[Año] ) & "–" & MAX ( Calendario[Año] ) & ". "
        & ConDato & " meses con dato válido; " & ( Meses - ConDato ) & " sin dato (celda vacía, no cero). "
        & "Azul más intenso indica más viajeros. El patrón describe la distribución temporal y no demuestra sus causas."

Mensaje V3 =
IF ( ISBLANK ( [Viajeros serie] ), "No hay datos válidos para esta selección. Cambie la serie o el rango de años.", "" )
```

**Valores esperados (Total):** dic-2025 = **392.087**, el mes de mayor valor de 2025. Con 2009–2026 la nota dice **210 meses con dato válido; 6 sin dato** (jul–dic 2026).

### 2.3 V4 · Estacionalidad y años: totales de años completos

- **Página:** Estacionalidad y años. **Objeto:** Gráfico de columnas agrupadas.
- **Eje X:** `Calendario[Año]` (categórico, ascendente). **Eje Y:** `[Total año completo]`, formato `#,0`, inicio en 0. Color `#1F4E79`. «Mostrar elementos sin datos» desactivado.
- Usa los mismos segmentadores de serie y años que V3.
- **Título:** «¿Cómo cambia el total de viajeros entre años completos?». Tarjeta de texto debajo con `[Nota V4]`.

```dax
Total año completo =
IF ( [Meses con dato serie] = 12, [Viajeros serie] )

Nota V4 =
VAR Excluidos =
    FILTER ( VALUES ( Calendario[Año] ), VAR m = [Meses con dato serie] RETURN m > 0 && m < 12 )
VAR Completos =
    COUNTROWS ( FILTER ( VALUES ( Calendario[Año] ), [Meses con dato serie] = 12 ) )
RETURN
    [Serie elegida] & ". Se muestran " & Completos & " años completos, cada uno con doce meses válidos. "
        & IF (
            ISEMPTY ( Excluidos ),
            "No se excluyeron años incompletos.",
            "Se excluyen por estar incompletos: "
                & CONCATENATEX ( Excluidos, Calendario[Año] & " (" & [Meses con dato serie] & " de 12 meses)", "; ", Calendario[Año], ASC )
                & "."
        )
        & " No se suman vías de ingreso con países de residencia."

Mensaje V4 =
IF (
    ISEMPTY ( FILTER ( VALUES ( Calendario[Año] ), [Meses con dato serie] = 12 ) ),
    "No hay años completos para esta selección. Cambie la serie o amplíe el rango de años.",
    ""
)
```

**Valores esperados (Total, 2009–2026):** 17 años completos (2009–2025); 2024 = **3.593.876**; 2025 = **3.597.238**; nota «2026 (6 de 12 meses)».

### 2.4 V5 · Datos observados: variación interanual por mes

- **Página:** Datos observados (debajo de V1 y V2). **Objeto:** Gráfico de columnas agrupadas.
- **Eje X:** `Calendario[Año]` y `Calendario[Mes]`, expandido al nivel Mes («Expandir todo un nivel hacia abajo»), sin botones de exploración. **Eje Y:** `[Variación interanual %]`, formato `0.0 %`. Color `#1F4E79`.
- **Análisis → Línea Y constante** en 0, discontinua, `#5B6B7A`.
- **Segmentador propio:** `Calendario[Date]` «Entre», por defecto 01/01/2010–30/06/2026 (como `DEFAULT_START` de G5).
- **Interacciones (Formato → Editar interacciones):** V2 → V5 **Filtrar** (el clic en una vía o país cambia la serie); segmentadores de grupo y año de V2 → V5 **Ninguno**; segmentador de fechas de V5 → V1 y V2 **Ninguno**.
- **Título:** «¿Cuánto cambió cada mes frente al mismo mes del año anterior?» + `[Serie elegida]`. Tarjeta con `[Nota V5]`.

```dax
Viajeros año anterior =
CALCULATE ( [Viajeros serie], SAMEPERIODLASTYEAR ( Calendario[Date] ) )

Variación interanual % =
VAR Actual = [Viajeros serie]
VAR Anterior = [Viajeros año anterior]
RETURN
    IF (
        HASONEVALUE ( Calendario[Año] ) && HASONEVALUE ( Calendario[MesNum] )
            && NOT ISBLANK ( Actual ) && NOT ISBLANK ( Anterior ) && Anterior <> 0,
        DIVIDE ( Actual - Anterior, Anterior )
    )

Meses con variación =
COUNTROWS (
    FILTER ( SUMMARIZE ( Calendario, Calendario[Año], Calendario[MesNum] ), NOT ISBLANK ( [Variación interanual %] ) )
)

Nota V5 =
VAR Meses = COUNTROWS ( SUMMARIZE ( Calendario, Calendario[Año], Calendario[MesNum] ) )
VAR Calculados = [Meses con variación]
RETURN
    [Serie elegida] & ". " & Calculados & " meses con variación = (viajeros del mes ÷ mismo mes del año anterior − 1). "
        & "Positivo: más viajeros que un año antes; negativo: menos. "
        & IF ( Meses > Calculados, ( Meses - Calculados ) & " meses sin base válida no se dibujan (no son cero). ", "" )
        & "Si el año anterior tuvo pocos viajeros, como en 2020, el porcentaje puede ser muy grande."

Mensaje V5 =
IF (
    [Meses con variación] = 0,
    "No se puede calcular la variación interanual para ningún mes de esta selección. Elija fechas posteriores al primer año de la serie o cambie la serie.",
    ""
)
```

La condición `HASONEVALUE` impide comparar un 2026 de 6 meses con un 2025 de 12 si alguien sube al nivel Año. `Anterior <> 0` reproduce la regla de G5 (sin base si el año anterior registró cero; ocurre en Vía Marítima).

**Valores esperados (Total):** ene-2025 = **−8,06 %**; jun-2026 = **−5,27 %**; abr-2021 = **+717,49 %**. Con el periodo por defecto: **198 meses** calculados y ninguno sin base.

### 2.5 V6 · Predicciones y modelos: observado frente a estimados

- **Página:** Predicciones y modelos. **Objeto:** Gráfico de líneas.
- **Eje X:** `Calendario[Date]`, tipo **Continuo**, formato `mmm yyyy`. **Eje Y:** `[Observado V6]` y las cinco medidas `Estimado <modelo>` (sin campo de leyenda), formato `#,0`.
- **Colores y trazos por serie** (Formato → Líneas, aplicar a cada serie):

| Medida | Leyenda | Color | Trazo | Grosor |
|---|---|---|---|---|
| `Observado V6` | Observado (dato registrado) | `#1F4E79` | Continuo + marcadores | 3 |
| `Estimado SARIMA` | Estimado · SARIMA | `#A65E16` | Discontinuo | 2 |
| `Estimado Holt-Winters` | Estimado · Holt-Winters | `#6B3A0C` | Punteado | 2 |
| `Estimado SES` | Estimado · SES | `#C46A12` | Personalizado (guion y punto) | 2 |
| `Estimado Seasonal Naive` | Estimado · Seasonal Naive | `#8A4B12` | Personalizado (guion largo) | 2 |
| `Estimado Prophet` | Estimado · Prophet | `#D07A1E` | Personalizado (guion largo y punto) | 2 |

- **Segmentadores de la página:** `DimSerie[nombre]` selección única, Total; `DimModelo[nombre]` selección múltiple, SARIMA + Holt-Winters + SES; `Calendario[Date]` «Entre», 01/04/2021–30/06/2026 (cobertura de las predicciones).
- Información sobre herramientas: modo «x unificado» (todas las líneas del mes).
- **Título:** «¿Qué estimaron los modelos frente a lo que se registró?» + `[Serie elegida]`. Tarjeta con `[Nota V6]`.

```dax
Observado V6 =
IF ( NOT ISEMPTY ( Predicciones ), [Viajeros serie] )

Estimado SARIMA = CALCULATE ( [Estimado serie], KEEPFILTERS ( DimModelo[clave] = "sarima" ) )
Estimado Holt-Winters = CALCULATE ( [Estimado serie], KEEPFILTERS ( DimModelo[clave] = "holt_winters" ) )
Estimado SES = CALCULATE ( [Estimado serie], KEEPFILTERS ( DimModelo[clave] = "ses" ) )
Estimado Seasonal Naive = CALCULATE ( [Estimado serie], KEEPFILTERS ( DimModelo[clave] = "seasonal_naive" ) )
Estimado Prophet = CALCULATE ( [Estimado serie], KEEPFILTERS ( DimModelo[clave] = "prophet" ) )

Nota V6 =
VAR Meses = COUNTROWS ( FILTER ( VALUES ( Calendario[Date] ), NOT ISBLANK ( [Observado V6] ) ) )
VAR Modelos = CONCATENATEX ( VALUES ( DimModelo[nombre] ), DimModelo[nombre], ", ", DimModelo[orden], ASC )
RETURN
    [Serie elegida] & " · " & Modelos & ". " & Meses & " meses con dato registrado y estimación. "
        & "Las estimaciones son resultados existentes (insumos/resultados/predicciones); no se entrenó ningún modelo. "
        & "Corresponden a meses ya registrados: no son un pronóstico de meses futuros ni incluyen intervalos de confianza."

Mensaje V6 =
IF (
    ISBLANK ( [Observado V6] ),
    "No hay meses con dato registrado y estimación en este periodo. Amplíe las fechas o cambie los modelos.",
    ""
)
```

`KEEPFILTERS` respeta el segmentador de modelos: un modelo no seleccionado queda en blanco y su línea no se dibuja. `Observado V6` solo muestra meses con estimación, como la unión interna de `align_models`. En Power BI un segmentador sin selección equivale a «todos», así que el mensaje de G6 «Seleccione al menos un modelo» no aplica: con ninguno marcado se ven los cinco.

**Valores esperados (Total/SES):** abr-2021 observado **82.067,87**, estimado **105.145,05**; dic-2025 observado **392.087**, estimado **105.145,05** (SES estima un nivel constante). La nota dice **63 meses**.

### 2.6 V7 · Predicciones y modelos: error por modelo

**Decisión: usar `Metricas` importada, no recalcular.** En `lab10`, G7 llama a `calculate_errors(series_key)` sin fechas: siempre usa los 63 meses comunes (abr-2021 a jun-2026) y no tiene selector de periodo. El script recalculó MAE, RMSE y MAPE de las 35 combinaciones y coinciden con `metricas_modelos.csv` (`rtol = 1e-9`), incluido `mape_excluidos`. Por eso la tabla importada reproduce G7 sin DAX adicional y V7 no responde al segmentador de fechas (`Metricas` no se relaciona con `Calendario`).

- **Objeto:** Gráfico de barras agrupadas horizontal. **Eje Y:** `DimModelo[nombre]`. **Eje X:** `[Error modelo]`, inicio en 0. Orden ascendente por `[Error modelo]` (menor error arriba). Color `#A65E16`. Etiquetas de datos activadas.
- **Tabla desconectada** (Modelado → Nueva tabla) y segmentador `MetricaV7[Metrica]` de selección única, MAE por defecto, ordenado por `Orden`:

```dax
MetricaV7 =
DATATABLE (
    "Metrica", STRING, "Orden", INTEGER, "Unidad", STRING, "Explicacion", STRING,
    {
        { "MAE", 1, "viajeros", "Distancia media entre lo observado y lo estimado." },
        { "RMSE", 2, "viajeros", "Da más peso a las equivocaciones grandes." },
        { "MAPE", 3, "%", "Distancia media expresada como porcentaje de lo observado." }
    }
)

Error modelo =
VAR Metrica = SELECTEDVALUE ( MetricaV7[Metrica], "MAE" )
VAR Serie = IF ( HASONEVALUE ( DimSerie[clave] ), SELECTEDVALUE ( DimSerie[clave] ), "total" )
RETURN
    CALCULATE (
        SWITCH ( Metrica, "MAE", SUM ( Metricas[mae] ), "RMSE", SUM ( Metricas[rmse] ), "MAPE", SUM ( Metricas[mape] ) ),
        REMOVEFILTERS ( DimSerie ),
        DimSerie[clave] = Serie
    )

Subtitulo V7 =
VAR Metrica = SELECTEDVALUE ( MetricaV7[Metrica], "MAE" )
VAR Excluidos = CALCULATE ( MAX ( Metricas[mape_excluidos] ), REMOVEFILTERS ( DimModelo ) )
RETURN
    Metrica & " en " & SELECTEDVALUE ( MetricaV7[Unidad], "viajeros" ) & " · "
        & [Serie elegida] & " · 63 meses coincidentes, abr-2021 a jun-2026. "
        & SELECTEDVALUE ( MetricaV7[Explicacion], "" ) & " Menor error indica mayor cercanía en ese periodo."
        & IF ( Metrica = "MAPE" && Excluidos > 0, " El porcentaje excluye " & Excluidos & " meses con observado igual a cero.", "" )

Mensaje V7 =
IF ( ISBLANK ( [Error modelo] ), "No hay datos coincidentes para comparar los modelos de esta selección.", "" )
```

- **Formato dinámico** de `[Error modelo]` (Herramientas de medición → Formato → Dinámico): `IF ( SELECTEDVALUE ( MetricaV7[Metrica], "MAE" ) = "MAPE", "0.00 \%", "#,0.00" )`. MAPE ya viene en porcentaje (58,11 = 58,11 %), por eso el `%` va escapado y no multiplica por 100.
- **Título:** «¿Qué modelo se equivoca menos para esta serie?»; **subtítulo** con `[Subtitulo V7]` (identifica métrica, unidad y conjunto de evaluación). Nunca se mezclan dos métricas en el mismo eje.
- **Interacciones:** serie → V7 Filtrar; modelos (múltiple) → V7 **Ninguno** (G7 compara siempre los cinco); fechas → V7 Ninguno. V7 → V6 y V8: Ninguno.
- Obtención de detalles hacia «Detalle de serie»: V7 no lleva `DimSerie` en sus campos; activar «Conservar todos los filtros» en la página de detalle para que reciba la serie del segmentador.

**Valores esperados (Total, orden de V7):**

| Modelo | MAE | RMSE | MAPE % |
|---|---:|---:|---:|
| SES | 175.088,44 | 194.790,81 | 58,11 |
| Holt-Winters | 196.956,01 | 216.457,08 | 65,30 |
| Seasonal Naive | 235.730,91 | 253.203,39 | 83,86 |
| SARIMA | 250.722,71 | 274.289,54 | 83,48 |
| Prophet | 264.527,13 | 282.313,48 | 92,50 |

Con MAPE el orden cambia: SARIMA (83,48) queda antes que Seasonal Naive (83,86). Vía Marítima excluye **11 meses** con observado 0 en MAPE.

### 2.7 V8 · Predicciones y modelos: diferencia por mes

- **Objeto:** Gráfico de líneas con marcadores (mismo tipo que G8). **Eje X:** `Calendario[Date]` continuo, `mmm yyyy`. **Eje Y:** `[Diferencia]` (medida existente), formato `#,0`. Color `#A65E16`, grosor 2,5.
- **Análisis → Línea Y constante** en 0, discontinua, `#5B6B7A`, etiqueta «Observado = estimado».
- **Segmentador propio** `DimModelo[nombre]` de **selección única**, SARIMA por defecto (como G8, primer modelo disponible). Usa los segmentadores de serie y fechas de la página.
- **Interacciones:** segmentador de modelos múltiple → V8 **Ninguno**; segmentador único de V8 → V6, V7 y al segmentador múltiple **Ninguno**; serie y fechas → V8 Filtrar.
- **Título:** «¿En qué meses se alejó el modelo de lo observado?» + `[Serie elegida]` + modelo. Texto fijo debajo: «Positivo: el modelo estimó menos viajeros de los registrados; negativo: estimó más. Cerca de 0 = menor desviación. No demuestra causas ni garantiza el desempeño futuro.»

```dax
Titulo V8 =
"¿En qué meses se alejó el modelo de lo observado? · " & [Serie elegida] & " · "
    & SELECTEDVALUE ( DimModelo[nombre], "elija un modelo" )

Mensaje V8 =
IF (
    ISBLANK ( [Diferencia] ),
    "No hay datos observados y estimados coincidentes para esta selección. Amplíe las fechas o cambie el modelo.",
    ""
)
```

`[Diferencia]` ya devuelve vacío sin una serie y un modelo únicos y no convierte ausencias en cero. Con el segmentador de serie de selección única siempre hay una serie.

**Valores esperados (Total):** vista inicial SARIMA abr-2021 = **11.927,75**; mayor desviación SARIMA dic-2022 = **500.354,56**. SES abr-2021 = **−23.077,18**; mayor desviación SES dic-2022 = **421.044,95**; SES queda por debajo de lo observado en 58 de 63 meses.

### 2.8 Complementarios de la página Predicciones y modelos (no cuentan como visualización)

- Tabla `DimModelo[nombre]`, `Metricas[mae]`, `Metricas[rmse]`, `Metricas[mape]`, `Metricas[mejor]` para la serie elegida.
- Glosario breve: **Estimado:** valor que un modelo calculó para un mes ya registrado. **MAE:** error medio en viajeros. **RMSE:** como MAE, pero castiga más los errores grandes. **MAPE:** error medio en porcentaje de lo observado.
- Limitaciones: meses ya registrados, sin intervalos de confianza; los CSV no documentan una evaluación independiente del entrenamiento; menor error histórico no garantiza precisión futura.
- Marcador «Inicial – Predicciones y modelos» con Total, SARIMA + Holt-Winters + SES, MAE, SARIMA en V8 y fechas abr-2021–jun-2026.

### 2.9 Comprobación en Desktop

| Medida o visual | Comprobar | Esperado |
|---|---|---|
| V3 | Total, dic-2025 | 392.087 |
| V4 | Total 2024 / 2025; nota | 3.593.876 / 3.597.238; 2026 excluido (6 de 12) |
| V5 | Total ene-2025 | −8,06 % |
| V6 | Total/SES abr-2021 | 82.067,87 y 105.145,05 |
| V7 | Total, MAE SES | 175.088,44 |
| V8 | Total/SARIMA abr-2021; Total/SES abr-2021 | 11.927,75; −23.077,18 |

Si una medida no da el valor esperado, corregir aquí la fórmula y anotar el cambio.

## 3. Costos y acceso (5.2)

Solo fuentes oficiales, **consultadas el 7 de noviembre de 2026**. Los precios son los publicados en dólares estadounidenses. Microsoft aclara que son referenciales y que el precio final depende de la moneda, el país y la región. Hay precios académicos, de gobierno y de organizaciones sin fines de lucro que no se cotizaron.

| Aspecto | Power BI | Dash (Plotly) |
|---|---|---|
| Sistema operativo para desarrollar | Power BI Desktop solo para **Windows** (Windows 10 / Server 2016 o posterior, x64; en ARM requiere la actualización 2025-09). No hay versión para macOS. Admite Azure Virtual Desktop y Windows 365; no admite otros entornos VDI [1] | Python en Windows, macOS o Linux (`pip install dash`) [5] |
| Licencia para desarrollar | Desktop gratuito [1] | Dash de código abierto, licencia **MIT** (© Plotly Technologies Inc.) [4] |
| Compartir sin publicar | Enviar el `.pbix`: quien lo recibe necesita Desktop, es decir, Windows | Enviar el repositorio: quien lo recibe necesita Python y las dependencias de `requirements.txt` |
| Publicar y compartir en la organización | Servicio Power BI. Licencia gratuita (Fabric Free): solo contenido propio, sin compartir. **Pro: USD 14 por usuario al mes**, pago anual; publica, comparte y consume contenido de otros Pro. **Premium por usuario: USD 24** por usuario al mes, pago anual; solo comparte con otros PPU [2][3] | Requiere un servidor propio o un alojamiento. Plotly Cloud: **Free USD 0** (10 apps, URL personalizada, marca Plotly, 3 lectores privados); **Pro USD 29** por creador al mes o USD 290 al año (apps ilimitadas, 10 lectores privados, dominio propio); **Enterprise** con precio a convenir (SSO/OAuth, en la nube propia o de Plotly) [6] |
| Consumidores sin licencia por usuario | Solo si el contenido está en una capacidad **Fabric F64 o superior** o Premium P1+; la capacidad tiene precio variable (reserva anual o pago por uso) y publicar en ella sigue exigiendo Pro [2][3] | Cualquiera con un navegador y acceso a la URL; el control de acceso lo pone el alojamiento o el código (el código abierto no trae autenticación) [5][6] |
| Público en internet | «Publicar en la web»: **cualquiera** en internet ve el informe y sus datos de detalle, sin autenticación. Requiere licencia Power BI (Pro o PPU desde áreas de trabajo) y que el administrador del inquilino habilite la opción. Caché de 1 hora; no admite seguridad de nivel de fila, DirectQuery, conexión dinámica ni visuales R/Python [7] | Desplegar la app en un servidor público (el repositorio ya tiene `Dockerfile` y `docker-compose.yml`); el costo y el mantenimiento del servidor son del equipo |
| Mantenimiento | Desktop se actualiza cada mes y solo la última versión tiene soporte; un `.pbix` guardado en una versión nueva no abre en una anterior [1] | Dependencias de Python fijadas en `requirements.txt`; actualizarlas y mantener el servidor es responsabilidad propia |

### Implicaciones para el laboratorio

- **Desarrollar gratis no implica distribuir gratis.** Ambas herramientas son gratuitas para construir el tablero, pero compartirlo con otros cuesta: en Power BI, licencias Pro para quien publica y para quien consume (o una capacidad F64+); en Dash, un servidor o un plan de alojamiento y su mantenimiento.
- La restricción de sistema operativo fue un costo real del equipo: solo 2 de 4 integrantes (Diego y Hugo, con Windows) pudieron editar el `.pbix`. Ernesto y Esteban, con macOS, trabajaron en especificación, documentación y comparación. El Lab 10 lo desarrollaron los cuatro.
- El enunciado no exige publicar el informe. Se entrega el `.pbix` y el repositorio público, por lo que el laboratorio no generó costos de licencia.
- «Publicar en la web» no es apto para datos confidenciales. Los datos de este observatorio son agregados públicos, pero la opción depende de un administrador del inquilino y de una cuenta organizacional.

### Fuentes (consultadas el 7-nov-2026)

1. Microsoft Learn, *Download Power BI Desktop* (actualizada 13-oct-2026): <https://learn.microsoft.com/power-bi/fundamentals/desktop-get-the-desktop>
2. Microsoft, *Power BI pricing*: <https://www.microsoft.com/power-platform/products/power-bi/pricing>
3. Microsoft Learn, *Power BI service features by license type* (actualizada 31-ago-2026): <https://learn.microsoft.com/power-bi/fundamentals/service-features-license-type>
4. Plotly, licencia de Dash (MIT): <https://github.com/plotly/dash/blob/dev/LICENSE>
5. Plotly, *Dash*: <https://plotly.com/dash/>
6. Plotly, *Pricing*: <https://plotly.com/pricing/>
7. Microsoft Learn, *Publish to web from Power BI* (actualizada 1-abr-2026): <https://learn.microsoft.com/power-bi/collaborate-share/service-publish-to-web>
