# Entrega de Ernesto: G5, revisión de G2 e integración final

## Recepción de las partes anteriores

El trabajo parte de `3c2591e`, último commit publicado de Hugo en `lab10`, después de actualizar la rama local con un avance rápido sin conflictos.

| Parte | Commits recibidos | Componentes | Estado al recibir |
|---|---|---|---|
| Diego | `27de746` (y el boceto `a659f04`) | `app/model_results.py`, G7, G8 | Archivos y pruebas presentes |
| Esteban | `06e49c6`, `d325379`, `65a9e55` | G6, revisión de G1, `data.incomplete_periods` | Archivos y pruebas presentes |
| Hugo | `cf8a623`, `230ea01`, `3c2591e` | G3, G4, `data.monthly_series`, `data.select_years` | Archivos y pruebas presentes |

Antes de integrar se ejecutaron las 75 pruebas existentes y todas se aprobaron. No faltaba ningún componente ni identificador de los registrados en los tres documentos de entrega. Esto acredita disponibilidad técnica, no la aceptación personal de cada parte: las fechas y horas de aceptación siguen sin registrarse.

## Inventario final

| Gráfica | Archivo | Sección | Controles propios | Responsable del componente y su texto |
|---|---|---|---|---|
| G1 | `time_series.py` | `evolution` | `series-selector`, `granularity-selector`, `date-range` | Esteban (revisión) |
| G2 | `ranking.py` | `ranking` | `ranking-category`, `ranking-year`; clic en barra | Ernesto (revisión) |
| G3 | `seasonality.py` | `seasonality` | `seasonality-series`, `seasonality-years` | Hugo |
| G4 | `annual_comparison.py` | `annual-comparison` | `annual-series`, `annual-years` | Hugo |
| G5 | `year_over_year.py` | `year-over-year` | `yoy-series`, `yoy-dates` | Ernesto |
| G6 | `predictions.py` | `predictions` | `predictions-series`, `predictions-models`, `predictions-dates` | Esteban |
| G7 | `model_errors.py` | `model-errors` | `errors-series`, `errors-metric` | Diego |
| G8 | `model_deviations.py` | `model-deviations` | `deviations-series`, `deviations-model`, `deviations-dates` | Diego |

Son ocho gráficas distintas, cada una con su propio tipo de figura, pregunta y controles. Ningún cambio de filtro se cuenta como otra gráfica. Las notas, los controles, el menú y la selección de gráficas visibles son elementos complementarios.

## G5: variación interanual mensual

`app/components/year_over_year.py` expone `layout()`, `register(app)`, `year_over_year(series)`, `select_dates(frame, start, end)` y `build_figure(series_key, start, end)`, que devuelve figura y nota.

- **Cálculo:** `(viajeros del mes ÷ viajeros del mismo mes del año anterior − 1) × 100`. El mes anterior se busca por fecha (`shift` con `DateOffset(years=1)`), no por posición, de modo que un hueco en la serie no compara meses distintos.
- **Fuente:** `data.monthly_series`, la lectura validada de Hugo. Valores ausentes, no numéricos, negativos o infinitos quedan sin dato válido; el cero real se conserva.
- **Casos sin base válida:** sin dato en el mes, sin dato del mismo mes del año anterior o con cero viajeros en ese mes anterior. No se calcula ni se reemplaza por 0 %. Se marcan con una × gris, como en G3, y la nota indica cuántos son y por qué, con los cuatro primeros meses y el número restante.
- **Selección:** serie y rango de fechas. El rango filtra los meses mostrados; la base del año anterior se toma de la serie completa, aunque quede fuera del rango. Por defecto empieza en enero de 2010, primer mes con base de comparación.
- **Mensajes:** rango sin meses, fechas invertidas o inválidas, serie desconocida y selecciones donde ningún mes tiene base válida (por ejemplo, solo 2009).

Comprobación manual: en la serie total, enero de 2025 registra 306.596 viajeros y enero de 2024, 333.491. `(306.596 ÷ 333.491 − 1) × 100 = −8,06 %`, el mismo valor que calcula el componente.

Con las fuentes actuales, Vía Marítima tiene 27 meses cuyo mes anterior registró cero viajeros, y las tres series de países tienen ceros en 2020. Esos meses aparecen con × y no como 0 %. En la serie total, los meses de 2021 y 2022 llegan a +800 % porque el año anterior tuvo muy pocos viajeros. La nota lo advierte y el cursor muestra los valores absolutos de ambos meses.

## Revisión de G2

| Revisión | Resultado | Cambio |
|---|---|---|
| Vías y países por separado | Cada grupo se ordena y se suma por separado; el total no entra en el ranking. | Ninguno. |
| Periodos parciales | 2026 se rotula como periodo parcial de 6 meses; «Todos los años» indica de enero de 2009 a junio de 2026. | Ninguno. |
| Enlace con `series-selector` | El clic cambia la serie de G1 y no escribe en `date-range` ni en `granularity-selector`. | Ninguno en el cálculo. |
| Selección con G1 oculta | El enlace «Ver la evolución…» apuntaba a una sección que podía estar oculta. | Con G1 oculta se cambia por un aviso y el botón «Mostrar la serie temporal», que vuelve a marcar G1 sin desmarcar otras gráficas. |

## Integración y navegación final

`app/main.py` define dos grupos, `OBSERVED` (G1 a G5) y `MODELS` (G6 a G8). La distribución final es una sola página:

1. Encabezado con el propósito del tablero y un menú de enlaces agrupado en «Datos observados» y «Predicciones y modelos».
2. Tarjeta «Gráficas visibles», con una casilla por gráfica en los mismos dos grupos. Todas están marcadas al inicio.
3. Las ocho tarjetas en orden, de G1 a G8. Cada título empieza con su número (por ejemplo, «G5 · ¿Cuánto cambió…?») para relacionarlo con el menú y las casillas.

Desmarcar una casilla oculta la tarjeta con `display: none` y retira su enlace del menú. Los componentes siguen montados: sus callbacks y selecciones se conservan y la gráfica reaparece como se dejó. Si no queda ninguna marcada, aparece «No hay gráficas seleccionadas…». Cada componente se registra una sola vez y no hay salidas duplicadas.

Se descartaron las pestañas del boceto del avance porque la serie temporal debía aparecer en dos pestañas a la vez, y un componente de Dash no puede repetirse en la página. El boceto `docs/figuras/boceto_tablero.png` se regeneró con `python -m docs.scripts.draw_wireframe` y muestra la distribución implementada.

Capturas del tablero integrado, a 1440 × 900: `docs/figuras/04_ernesto_navegacion.jpg` (menú y selección) y `docs/figuras/04_ernesto_g5.jpg` (G5 con Vía Marítima y meses sin base válida).

## Verificación de requisitos

| Requisito | Resultado | Evidencia |
|---|---|---|
| Ocho gráficas interactivas distintas | Cumplido | Inventario anterior; `test_eight_charts_are_integrated_once_with_unique_ids` |
| G5 coincide con un cálculo manual y explica los casos sin base | Cumplido | Ejemplo de enero de 2025; `tests/test_year_over_year.py` |
| Clic en G2 cambia G1 y conserva el rango de fechas | Cumplido | Pruebas HTTP de `tests/test_app.py`; en el navegador, con G1 oculta, el clic en Vía Aérea cambió G1 y mantuvo sus 210 meses |
| Gráficas ocultas sin errores y que pueden volver a mostrarse | Cumplido | `test_hiding_charts_keeps_them_mounted…`, `test_show_series_button…`; en el navegador se ocultaron y restauraron las ocho, que recuperaron su ancho de 1110 px |
| Selección explícita de gráficas visibles | Cumplido | Tarjeta «Gráficas visibles» |
| G1 aumenta y disminuye el detalle y explica los periodos incompletos | Cumplido (Esteban) | Niveles mensual, trimestral y anual; nota de periodos omitidos |
| Al menos tres modelos comparables, sin entrenar modelos nuevos | Cumplido: cinco modelos | G6 ofrece los cinco (tres marcados al inicio), G7 compara los cinco y G8 permite elegir cualquiera |
| Interacciones, enlaces, selecciones sin datos y legibilidad revisados | Cumplido en este alcance | Ver «Pruebas» |
| Documento Word con las ocho gráficas y las secciones exigidas | **Pendiente** | El Word del equipo no está en el repositorio; los textos de G2 y G5 están abajo |
| Documento y boceto coinciden con la aplicación | Boceto: cumplido. Word: **pendiente** | — |
| PDF final legible y con datos personales confirmados | **Pendiente** | — |
| Entrega del avance e inscripción en el grupo de Canvas | **Sin verificar** | — |
| Historial con contribuciones de los cuatro | Commits publicados de BARHUG0, ecarcamo, Diego y AscencioSIUU en `lab10`; esta entrega aún no está confirmada ni publicada | `git shortlog -sne origin/lab10` |

## Pruebas

Desde la raíz, con el entorno del proyecto:

```bash
python -m unittest tests.test_design tests.test_predictions tests.test_model_results tests.test_model_components tests.test_year_over_year
python -m tests.test_data && python -m tests.test_theme && python -m tests.test_ranking && python -m tests.test_app && python -m tests.test_wireframe
```

Resultado: 87 pruebas aprobadas, 75 existentes y 12 nuevas.

- `tests/test_year_over_year.py` (8): cálculo manual con la fuente, primer año sin base, ceros y faltantes no rellenados, alineación por fecha con un hueco, ceros reales de Vía Marítima, barras iguales al cálculo, mensajes de selecciones inválidas o sin datos y callback HTTP.
- `tests/test_app.py` (4 nuevas): ocho gráficas con identificadores y salidas únicos, alturas reservadas, ocultación con el enlace de G2 activo, mensaje sin gráficas y botón que restaura G1 sin perder otras selecciones.
- `tests/test_wireframe.py`: se adaptó al nuevo tamaño del boceto y a la posición de la barra seleccionada.

Revisión en Chrome, 25 de octubre de 2026, a 1440 × 900 y con ventana estrecha de 500 píxeles, el mínimo que permitió el navegador:

- Las ocho gráficas se dibujan con su ancho completo y no hay desplazamiento horizontal.
- G5 con el total y con Vía Marítima: 171 barras y 27 meses marcados con ×.
- G1 oculta, clic en la barra de Vía Aérea en G2, aviso con botón y G1 restaurada con la serie elegida y las fechas sin cambios.
- Todas las gráficas ocultas muestran el mensaje; al marcarlas de nuevo reaparecen.
- No se registraron errores en la consola.

No se revisó en dispositivos físicos ni con lectores de pantalla. No se probaron todas las combinaciones de filtros de los componentes recibidos.

## Texto para Word de G2

La gráfica de barras horizontales responde a la pregunta «¿Qué vías o países concentran más viajeros?». Suma los viajeros registrados de cada vía de ingreso, o de cada país de residencia disponible, para el año elegido o para todo el periodo, a partir de `insumos/series/`. Las barras horizontales ordenadas de mayor a menor permiten comparar magnitudes y leer los nombres completos sin girarlos.

El directivo elige el grupo de comparación y el año. Las vías y los países nunca se mezclan ni se suman entre sí, y la nota advierte que los tres países no representan todos los mercados de origen. Si el año está incompleto, como 2026, que llega hasta junio, la nota lo identifica como periodo parcial para no compararlo con años completos. Al hacer clic en una barra, la serie temporal G1 muestra esa vía o ese país y conserva el rango de fechas y el nivel de detalle elegidos; la barra seleccionada se marca en verde y con borde, para no depender solo del color. Si G1 está oculta, la gráfica lo indica y ofrece un botón para mostrarla.

La gráfica ayuda a identificar dónde se concentra la demanda y a pasar de esa comparación al detalle temporal de una serie. Describe volúmenes registrados; no explica por qué una vía o un país concentra más viajeros ni anticipa su comportamiento futuro.

## Texto para Word de G5

La gráfica de barras responde a la pregunta «¿Cuánto cambió cada mes frente al mismo mes del año anterior?». Para cada mes calcula la variación porcentual respecto al mismo mes del año previo: (viajeros del mes ÷ viajeros del mismo mes del año anterior − 1) × 100. Comparar con el mismo mes evita que la temporada se confunda con un crecimiento o una caída. Las barras sobre y bajo la línea de 0 % muestran de un vistazo si cada mes superó o no al año anterior; el color azul conserva el significado de dato observado, y la dirección de la barra no depende del color.

El directivo elige la serie y el rango de fechas, y al pasar el cursor ve el porcentaje y los viajeros de ambos meses. Cuando no hay dato del mes, no hay dato del año anterior o el año anterior registró cero viajeros, el porcentaje no puede calcularse: el mes se marca con una × y la nota indica cuántos meses están en esa situación y por qué. Nunca se muestran como 0 %, que significaría «sin cambio». Con los datos actuales, el primer año, 2009, no tiene base de comparación.

La gráfica ayuda a detectar meses de recuperación o caída frente al año anterior y a revisar si un cambio es reciente o sostenido. Cuando el año anterior tuvo muy pocos viajeros, como en 2020, el porcentaje puede ser muy grande aunque el volumen sea pequeño; por eso conviene leerla junto con G1 y G4. Describe el cambio registrado y no demuestra sus causas.

## Texto para Word sobre navegación y alcance

El tablero es una sola página. El encabezado explica su propósito y ofrece un menú con enlaces a cada gráfica, agrupados en «Datos observados» (G1 a G5) y «Predicciones y modelos» (G6 a G8). Debajo, la tarjeta «Gráficas visibles» permite marcar o desmarcar cada gráfica; ocultarla no borra sus selecciones y su enlace desaparece del menú. Cada gráfica tiene sus propios controles, una nota de lectura y un mensaje cuando la selección no tiene datos. G2 está enlazada con G1: el clic en una barra cambia la serie de G1 sin modificar su rango de fechas.

El alcance comprende siete series mensuales observadas (total, tres vías de ingreso y tres países de residencia), de enero de 2009 a junio de 2026, y las estimaciones existentes del Laboratorio 1 de cinco modelos (SARIMA, Holt-Winters, SES, Seasonal Naive y Prophet), de abril de 2021 a junio de 2026. No se entrenaron modelos nuevos, las estimaciones corresponden a meses ya registrados y no incluyen intervalos de confianza.

## Pendientes explícitos

- **Word:** el documento de diseño es un archivo privado del equipo y no está en el repositorio. Falta incorporar los bloques de G1, G3, G4, G6, G7 y G8 (en los entregables 01 a 03), los de G2 y G5 y el de navegación y alcance anteriores. También falta reemplazar el boceto y la navegación del avance por los actuales. El Word revisado menciona cinco modelos: el tablero muestra los cinco, por lo que ese alcance se mantiene.
- **Portada:** nombres y carnés deben confirmarlos los cuatro integrantes. No se infieren de los nombres de usuario de Git.
- **Código del curso:** el Word dice CC3084 y el PDF del enunciado, CC3066. El encabezado de `docs/Laboratorio_10_Visualizacion_interactiva_2026.docx` también dice «CC3066 – Data Science», mientras que el repositorio se llama CC3084-DATA-SCIENCE. Aquí no se resuelve: debe confirmarse con el curso.
- **Planificación:** conservar tareas, responsables y fechas, y registrar su estado real sin inventar fechas de realización.
- **PDF final:** generarlo desde el Word, revisar cada página y acordar su nombre y ubicación.
- **Canvas:** verificar que se entregó el avance completo del 22 de octubre y que los cuatro están inscritos en el grupo. Sin esa verificación, el estado es «sin verificar».
- **Aceptaciones:** registrar la fecha y hora reales de aceptación de cada parte y del cierre.
- **Publicación:** estos cambios son locales. Antes de publicar, ejecutar `git pull --rebase origin lab10`, revisar los archivos incluidos y hacer `git push` sin forzar. Distinguir **preparado** (este estado), **publicado** (tras el push) y **entregado en Canvas**.
