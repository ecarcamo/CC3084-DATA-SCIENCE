# Entrega de Hugo: estacionalidad y comparación anual

## Alcance y dependencias

La entrega incorpora G3, mapa de calor mensual, y G4, comparación de totales anuales. También registra la revisión visual de G1, G2, G6, G7 y G8 recibidas de Diego y Esteban. El punto de partida es `65a9e55`, en `lab10`. El enunciado suministrado está disponible como texto en `TEMP/lab10`.

Los archivos de las entregas anteriores existen y sus pruebas pasan. Esto acredita su disponibilidad técnica, no una aceptación personal del equipo. La fecha y hora de aceptación de Esteban y del paso a Ernesto siguen por acordar.

No se modifica `app/main.py`, no se alteran los CSV y no se entrenan modelos. La vista de revisión contiene siete gráficas. No acredita el mínimo de ocho visualizaciones ni la navegación y selección de secciones de la entrega final. G5 y la integración definitiva corresponden al trabajo restante del equipo.

## Datos y reglas de selección

La comprobación de las siete series encontró 210 observaciones por serie, de enero de 2009 a junio de 2026. No encontró fechas inválidas, meses repetidos, huecos interiores ni valores ausentes, no numéricos, negativos o infinitos en estos archivos.

Las opciones se calculan desde las fechas reales de cada serie. Ambos componentes tienen controles propios de serie y rango inclusivo de años. Al cambiar la serie, el rango vuelve a toda su cobertura. Los números de los extremos también se pueden editar; el cambio se confirma al salir del campo, por ejemplo con Tab.

`app/data.py` añade dos funciones sin cambiar los contratos existentes:

| Función | Resultado |
|---|---|
| `monthly_series(key)` | Serie ordenada, con una observación como máximo por mes y fechas al inicio del mes. Rechaza claves desconocidas, archivos ilegibles y fechas inválidas o repetidas. Los valores ausentes, no numéricos, negativos o infinitos quedan sin dato válido. El cero se conserva. |
| `select_years(series, years)` | Calendario mensual de los años seleccionados, con doce posiciones por año. Las posiciones sin observación quedan vacías. No inventa valores ni modifica la fuente. Rechaza rangos invertidos o fuera de cobertura. |

G3 conserva esas posiciones vacías y las marca con una ×. El valor real de cero tiene el azul más claro y un valor numérico en el cursor. El mapa siempre presenta enero a diciembre y años en orden ascendente, de arriba hacia abajo.

G4 reutiliza `aggregate` e `incomplete_periods` sobre ese calendario validado. Un año solo aparece si tiene doce meses distintos con valor válido. La nota enumera cada año excluido y sus meses válidos, incluso si falta un año entero dentro de la cobertura.

Con las fuentes actuales, G4 presenta 17 años completos, de 2009 a 2025. Excluye 2026 con el mensaje de seis meses válidos de doce. G3 muestra esos seis meses de 2026 y marca los seis restantes sin dato. El total de la serie general para 2025 coincide con la suma mensual, aproximadamente 3.597.238 viajeros. Las pruebas comparan los valores completos con tolerancia para aritmética decimal.

Cada selección utiliza una sola serie. Los países de residencia no se suman con las vías de ingreso ni se tratan como categorías mutuamente excluyentes de estas.

## Componentes para Ernesto

| Gráfica | Archivo | Sección | Controles | Salidas |
|---|---|---|---|---|
| G3 | `app/components/seasonality.py` | `seasonality` | `seasonality-series`, `seasonality-years` | `seasonality-graph`, `seasonality-note` |
| G4 | `app/components/annual_comparison.py` | `annual-comparison` | `annual-series`, `annual-years` | `annual-graph`, `annual-note` |

Ambos módulos exponen `layout()` y `register(app)`. Sus funciones `build_figure(series_key, years)` devuelven figura y nota. `years` contiene el año inicial y el final. `year_options(series_key)` devuelve mínimo, máximo, marcas y rango inicial según la cobertura real.

La integración debe incorporar cada `layout()` y llamar una vez a cada `register(app)`. Los identificadores son únicos y ninguno de los componentes escribe en `series-selector`. No hay cambios de interfaz para Diego o Esteban.

## Revisión visual y correcciones

La revisión se realizó el 25 de octubre de 2026 en Chromium, con ventanas de 1440 × 900 y 390 × 844. Se esperó al renderizado de las siete gráficas y al ajuste de sus dimensiones antes de tomar capturas.

| Elemento revisado | Resultado y corrección |
|---|---|
| G3, meses y escala | Las etiquetas y el título de la escala se superponían en la ventana estrecha. Se separó la escala, se giraron los nombres de los meses y se amplió el margen inferior. |
| G3 y G4, rango de años | Las marcas próximas a los extremos se amontonaban. Se redujeron las marcas y se dio ancho flexible a los controles. |
| G4, eje anual | Las etiquetas de los 17 años resultaban demasiado próximas en una ventana estrecha. El eje ahora calcula hasta seis marcas orientativas; todas las barras conservan su año en el cursor. |
| G3 y G4, controles | El rango usaba el violeta predeterminado de Dash. Los rangos, sus tiradores y el foco de los campos numéricos usan ahora el azul del tema, con estilos limitados a `.year-range`. |
| G3 y G4, selecciones vacías | Un mensaje largo se recortaba dentro de G4. Los mensajes de ambas gráficas ahora tienen saltos de línea. En 390 × 844 se comprobó que la anotación vacía queda dentro de los 340 píxeles de la gráfica. |
| G1 y G2 | Se conservaron sus ejes, controles y significados de color. Los tests HTTP del clic y un evento `plotly_click` simulado en el navegador comprobaron el enlace del ranking con la serie temporal. No se cambiaron estos módulos. |
| G6 | Se revisaron observado y estimaciones, los controles y la leyenda con tres y cinco modelos. Con cinco modelos aparecen seis curvas. La leyenda se mantiene dentro del espacio de la gráfica en la ventana estrecha. No se cambió el componente. |
| G7 y G8 | Se revisaron los títulos, ejes, controles y notas en ambas dimensiones. Se conservó el naranja de las estimaciones y la referencia de desviación cero. No se cambiaron estos módulos. |
| Desbordamiento horizontal | La página y las siete gráficas se ajustaron al ancho de 390 píxeles después de terminar el redimensionado. |

Las capturas están en `docs/figuras/`:

- `03_hugo_escritorio.png`
- `03_hugo_estrecho.png`
- `03_hugo_g3_estrecho.png`
- `03_hugo_g4_sin_datos.png`
- `03_hugo_predicciones_estrecho.png`

### Paleta y tipografía verificadas

No cambia ningún valor ni significado de `app/theme.py`. El azul `#1F4E79` identifica observaciones; el naranja `#A65E16`, resultados relacionados con estimaciones; el verde `#20745A`, la selección del ranking; y el rojo `#B3261E`, las alertas. Se mantienen el fondo `#F4F6F8`, las tarjetas blancas, el texto `#1B2733`, el texto secundario `#5B6B7A` y la cuadrícula `#DDE3E9`.

G3 añade únicamente una escala secuencial propia, de `#E7EFF6` al azul observado. La intensidad representa cantidad, no una categoría nueva. Su mínimo es cero y su máximo se ajusta a la selección. La nota advierte que los tonos de selecciones distintas no deben compararse directamente. La × permite reconocer los meses sin dato sin depender solo del color.

La familia sigue siendo Arial, Helvetica y sans-serif. Las figuras reutilizan la plantilla de 14 píxeles y los textos de las tarjetas mantienen las reglas existentes. Las pruebas de contraste del tema, de correspondencia entre CSS y Plotly y de tipografía siguen pasando. No se declara una certificación de accesibilidad, una evaluación con lectores de pantalla ni una revisión en dispositivos físicos.

## Comprobaciones reproducibles

Desde la raíz, con el entorno académico existente:

```powershell
& ..\.venv\Scripts\python.exe -m unittest tests.test_design tests.test_predictions tests.test_model_results tests.test_model_components -v
& ..\.venv\Scripts\python.exe -m tests.test_data
& ..\.venv\Scripts\python.exe -m tests.test_theme
& ..\.venv\Scripts\python.exe -m tests.test_ranking
& ..\.venv\Scripts\python.exe -m tests.test_app
& ..\.venv\Scripts\python.exe -m tests.test_wireframe
& ..\.venv\Scripts\python.exe -m docs.scripts.preview_design
```

La vista de revisión se abre en `http://127.0.0.1:8053/`. No sustituye el tablero final.

Resultado final: 75 pruebas aprobadas, 20 nuevas y 55 existentes. Las nuevas comprueban integridad mensual, meses ausentes frente a ceros, sumas anuales, años enteros ausentes, rangos y claves inválidos, fechas repetidas, orden de las dimensiones, mensajes, filtros HTTP, límites derivados de la fuente e identificadores únicos.

En el navegador se verificaron los cambios de serie a Vía Aérea en G3 y G4, los rangos de 2024 a 2026 y de 2024 a 2025, y G4 limitada a 2026 sin años completos. Los campos numéricos se confirmaron con Tab. La revisión final no registró errores de JavaScript. La simulación del evento enlazado complementa las pruebas HTTP; no acredita una prueba física del clic en una pantalla táctil.

## Texto para Word de G3

La visualización responde a la pregunta "¿En qué meses se concentra el ingreso de viajeros?". Utiliza las siete series mensuales disponibles en `insumos/series/`, que cubren enero de 2009 a junio de 2026. El mapa de calor cruza años y meses porque permite reconocer concentraciones y diferencias entre temporadas sin superponer muchas líneas.

El directivo selecciona una serie y un rango de años. Los meses aparecen de enero a diciembre y los años en orden cronológico. Un azul más intenso indica más viajeros y la escala expresa viajeros por mes. El cursor permite consultar el valor de cada celda. Una × identifica un mes sin dato válido, mientras que un cero real conserva el azul más claro. La escala parte de cero y ajusta su máximo a la selección, por lo que no conviene comparar tonos entre selecciones distintas.

La gráfica ayuda a localizar temporadas para revisar la planificación de servicios y recursos. Describe la distribución temporal registrada y no explica por sí sola las causas de los cambios. Tampoco garantiza que una concentración histórica se repita. Los meses ausentes no se completan ni se convierten en ceros.

## Texto para Word de G4

La visualización responde a la pregunta "¿Cómo cambia el total de viajeros entre años completos?". Utiliza las mismas fuentes mensuales y presenta barras con la suma de los doce meses válidos de cada año de una sola serie. Las barras permiten comparar magnitudes anuales sobre una base común de cero.

El directivo selecciona la serie y el rango de años. El eje vertical expresa viajeros por año y el cursor identifica el año y su total. La gráfica conserva el azul de los datos observados. Solo incluye años con sus doce meses distintos y válidos; la nota identifica los años excluidos y cuántos meses válidos contienen. Con las fuentes actuales se comparan 2009 a 2025 y se excluye 2026, que llega hasta junio. Un cero real cuenta como una observación válida.

La comparación ayuda a revisar cambios de volumen anual sin confundir seis meses con un año completo. El total anual oculta las diferencias entre meses, por lo que G3 aporta el detalle estacional. Ninguna gráfica combina países con vías de ingreso ni demuestra causas o predice por sí sola el resultado del año siguiente.

## Paso a Ernesto y límites pendientes

- Incorporar G3 y G4 a la integración y navegación final, sin duplicar sus callbacks.
- Incorporar los bloques anteriores al Word y conservar las advertencias sobre cobertura, escala y años incompletos.
- Completar G5 y verificar los ocho componentes y los controles de selección de gráficas del enunciado.
- Registrar las fechas y horas de aceptación reales. Este registro no las sustituye.
- Revisar de nuevo las dimensiones y los estados vacíos después de la integración. La revisión de los componentes recibidos no cubre todas las combinaciones de filtros ni todos sus estados vacíos.
- Conservar las advertencias de Esteban sobre errores de los modelos, ausencia de intervalos y falta de documentación del periodo de entrenamiento. No se corrigieron ni reentrenaron estimaciones.

No se ejecutó `git pull --rebase origin lab10` porque existían cambios ajenos sin confirmar. Se preservaron `README.md`, los informes, la infografía y las capturas previas. La actualización remota debe coordinarse sin descartar ese trabajo. Los commits de esta entrega son locales; no se ejecuta `git push` por las instrucciones del repositorio. La publicación y la confirmación de accesos personales siguen pendientes.
