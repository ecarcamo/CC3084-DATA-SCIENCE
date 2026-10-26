# Entrega de Esteban: predicciones y revisión de la serie temporal

## Alcance realizado

Se incorpora G6, la comparación interactiva entre los datos observados y las predicciones existentes, y se revisa G1, la serie temporal. El trabajo parte de `27de746` en la rama `lab10`, último commit publicado de la entrega de Diego, y utiliza su interfaz compartida de `app/model_results.py` sin modificarla. No se entrena ningún modelo, no se alteran los CSV y no se modifica `app/main.py`: la integración definitiva corresponde a Ernesto, conforme al reparto Diego → Esteban → Hugo → Ernesto.

## Dependencia de entrada

Se recibieron de Diego `app/model_results.py`, su contrato de funciones (sección «Interfaz compartida para Esteban» de `01_diego_resultados.md`) y el inventario de `01_diego_validacion.json`. Antes de construir G6 se ejecutaron sus 14 pruebas y las 27 existentes; todas se aprobaron.

La condición de partida se cumple: hay resultados utilizables de **cinco modelos** para **las siete series**, por encima del mínimo de tres. No se registra ningún bloqueo.

## Modelos efectivamente disponibles

| Serie | Clave | SARIMA | Holt-Winters | SES | Seasonal Naive | Prophet | Meses comparables |
|---|---|:-:|:-:|:-:|:-:|:-:|---:|
| Total | `total` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |
| Vía Aérea | `via_aerea` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |
| Vía Terrestre | `via_terrestre` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |
| Vía Marítima | `via_maritima` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |
| El Salvador | `pais_el_salvador` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |
| Estados Unidos | `pais_estados_unidos` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |
| Honduras | `pais_honduras` | ✓ | ✓ | ✓ | ✓ | ✓ | 63 |

La disponibilidad no se fija en el código: `predictions.model_options` consulta `model_results.available_models` para cada serie, de modo que si falta un archivo, ese modelo deja de ofrecerse y, si estaba elegido, la gráfica lo informa con un mensaje.

## Alcance temporal

- **Observaciones (G1):** enero de 2009 a junio de 2026, 210 meses por serie.
- **Predicciones (G6):** abril de 2021 a junio de 2026, 63 meses por serie y modelo. El selector de periodo de G6 se limita a esa cobertura, que se calcula a partir de los archivos y no se escribe a mano.
- G6 muestra solo los meses en que existen a la vez el dato observado y la estimación de **todos** los modelos elegidos (`model_results.align_models`, unión interna). Si faltara un mes, la línea se corta y no se interpola.
- Las 147 observaciones anteriores a abril de 2021 no tienen estimación y no se muestran en G6; tampoco se rellenan con cero.
- Los archivos son resultados históricos del Laboratorio 1: cubren meses ya registrados. La interfaz no los presenta como un pronóstico futuro y no muestra intervalos de confianza, porque los CSV no los contienen.

## Uso de la interfaz compartida

G6 utiliza sin cambios `MODEL_LABELS`, `ModelDataError`, `available_models`, `load_observations`, `load_predictions` y `align_models`. **No hay cambios de contrato**, de modo que G7 y G8 no se ven afectadas; sus 6 pruebas de componentes siguen aprobándose.

En `app/data.py` se añade la función `incomplete_periods(series, granularity)`, que devuelve el número de meses con dato de cada trimestre o año incompleto. Es una adición: `aggregate`, `load_series`, `slice_range` y `GRANULARITY` no cambian, y el ranking los sigue utilizando igual.

## Identificadores

| Componente | Archivo | Sección | Controles | Salidas |
|---|---|---|---|---|
| G1 | `app/components/time_series.py` | `evolution` | `series-selector`, `granularity-selector`, `date-range` | `time-series-graph`, `granularity-note` |
| G6 | `app/components/predictions.py` | `predictions` | `predictions-series`, `predictions-models`, `predictions-dates` | `predictions-graph`, `predictions-note` |

- G1 conserva `series-selector`, en el que escribe el clic sobre una barra del ranking.
- G6 usa controles propios: no escribe en `series-selector` ni en los controles de G7 y G8.
- La nota de lectura de G6 enlaza con `#model-errors`, la sección de G7, para remitir a la comparación de errores.
- Ambos módulos exponen `layout()` y `register(app)`. `predictions.build_figure(series_key, model_keys, start, end)` devuelve `(figure, note)`; `time_series.build_figure` mantiene su firma y se añade `time_series.build_note(series_key, granularity, start, end)`.
- Para integrarlos, Ernesto debe añadir `predictions.layout()` a la distribución y llamar una vez a `predictions.register(app)`. G1 ya está registrada en `app/main.py`.

## G6: decisiones de diseño

- **Selección:** serie (lista desplegable), modelos (casillas; por defecto SARIMA, Holt-Winters y SES) y periodo de comparación. Cada cambio vuelve a calcular la gráfica; al cambiar de serie se conservan los modelos elegidos que sigan disponibles.
- **Observado frente a estimado:** el dato registrado es una línea **continua azul** (`COLORS["observed"]`) con puntos y la etiqueta «Observado (dato registrado)». Cada estimación es una línea **discontinua** de la familia naranja reservada a las estimaciones (`COLORS["forecast"]` y cuatro tonos de la misma familia, todos con contraste de 3:1 o más sobre blanco), con un patrón de trazo distinto por modelo y la etiqueta «Estimado · <modelo>». La diferencia no depende solo del color.
- **Leyenda y lectura:** la leyenda identifica todas las curvas; al pasar el cursor se ven, para un mismo mes, el valor registrado y el de cada modelo.
- **Mensajes:** sin modelos elegidos, con un periodo sin coincidencias, con un modelo sin archivo para la serie o con fechas invertidas se muestra un mensaje en la gráfica y en la nota, sin trazos.
- **Origen y periodo:** la nota indica la serie, los modelos, el número de meses y las fechas comparadas, la carpeta de origen (`insumos/resultados/predicciones`, Laboratorio 1) y que no se entrenó ningún modelo nuevo.

## G1: revisión y cambios justificados

| Revisión | Resultado | Cambio |
|---|---|---|
| Selección de serie y conservación de `series-selector` | Correcta; el ranking sigue actualizándola. | Ninguno. |
| Selección de fechas | Correcta; el rango se aplica antes de agregar. | Ninguno. |
| Niveles mensual, trimestral y anual | Correctos; las sumas solo incluyen periodos con todos sus meses. | Ninguno en el cálculo. |
| Significado de la unidad al agregar | El eje decía «Viajeros por trimestre» o «por año», pero el cursor mostraba la fecha de inicio («abr 2025», «ene 2025»), que podía leerse como el dato de un solo mes. | El cursor muestra el periodo: «T2 2025 (abr–jun)» o «2025». |
| Periodos incompletos | No se sumaban, pero la nota era fija: siempre mencionaba 2026 y no decía qué se omitía en otros rangos (por ejemplo, de febrero a agosto de 2025 en trimestral se omitían dos trimestres sin aviso). | La nota se calcula con el rango elegido y enumera los periodos omitidos y cuántos meses tenían. |
| Mensaje sin datos | Correcto (por ejemplo, anual entre enero y junio de 2026). | Ninguno. |
| Legibilidad del eje | En el nivel anual, el título del eje Y se superponía a las cifras de millones. | Margen automático del eje Y. |

## Comprobaciones

Desde la raíz del repositorio, con las dependencias de `requirements.txt`:

```bash
python -m unittest tests.test_predictions tests.test_model_results tests.test_model_components -v
python -m tests.test_data
python -m tests.test_app
python -m tests.test_ranking
python -m tests.test_theme
python -m tests.test_wireframe
python -m docs.scripts.preview_predictions
```

La vista de revisión de G1 y G6 se abre en `http://127.0.0.1:8052/`. Es una comprobación independiente; no reemplaza el tablero principal ni la integración final.

Resultados:

- **11 pruebas nuevas de G6** (`tests/test_predictions.py`), aprobadas: cinco modelos y 63 meses idénticos en todas las curvas de las siete series; diferencia de etiqueta, trazo y color entre observado y estimado; valores trazados iguales a los de los CSV; uso exclusivo de las fechas comunes a observado y modelos; cortes sin interpolación; mensajes ante selecciones sin datos, modelos desconocidos, archivos ausentes y fechas invertidas; conservación de modelos al cambiar de serie; y callbacks HTTP que cambian la gráfica al modificar modelos, periodo y serie.
- **3 pruebas nuevas de G1** (`tests/test_data.py`), aprobadas: etiquetas y sumas trimestrales y anuales; notas con un periodo completo (2015–2020 anual) y con periodos incompletos (2026 con 6 de 12 meses; T1 y T3 de 2025 con 2 de 3 meses); y conteo de meses ausentes.
- **41 pruebas previas**, aprobadas sin cambios: `tests.test_data`, `tests.test_app` (incluido el enlace del ranking con `series-selector`), `tests.test_ranking`, `tests.test_theme`, `tests.test_wireframe`, `tests.test_model_results` y `tests.test_model_components`.
- **Revisión en el navegador** de la vista local: G6 se dibuja con la leyenda completa; marcar Prophet añade su curva; el cursor muestra los cinco valores de un mes (septiembre de 2023); al desmarcar todos los modelos aparece «Seleccione al menos un modelo…». En G1, el nivel anual informa «Se omitió 1 año incompleto… 2026, 6 de 12 meses», el trimestral informa que todos sus trimestres están completos y el cursor muestra «T4 2022 (oct–dic)». No hubo errores en la consola.

## Limitaciones pendientes para Hugo

- **Distancia grande entre estimaciones y datos.** Desde enero de 2022, las estimaciones quedan por debajo de lo registrado en el 93 % al 100 % de los meses, según la serie y el modelo; para el total, el MAPE va de 58 % (SES) a 93 % (Prophet). La estimación de SES es constante en las siete series y, en cuatro de ellas, igual al valor observado de marzo de 2021, lo que es coherente con predicciones elaboradas con datos hasta ese mes; sin embargo, los CSV no documentan el periodo de entrenamiento y no se da por confirmado. La gráfica muestra los resultados tal como existen; no se corrigen ni se reentrenan. Conviene que la revisión de textos lo trate con cuidado y sin atribuir causas.
- **Sin intervalos de confianza.** Los archivos no los incluyen y la gráfica no los inventa.
- **Revisión visual en escritorio.** No se declara una auditoría en dispositivos móviles; la revisión visual general corresponde a Hugo.
- **Integración pendiente.** G6 no está en `app/main.py`; su incorporación y la navegación final corresponden a Ernesto.

## Texto para Word G1 serie temporal

La gráfica de líneas responde a la pregunta «¿Cómo ha evolucionado el ingreso de viajeros y en qué épocas del año sube o baja?». Muestra los viajeros internacionales registrados en Guatemala de enero de 2009 a junio de 2026, a partir de los archivos `insumos/series/serie_<clave>.csv`. Se elige una gráfica temporal porque el dato es una secuencia mensual: la línea permite reconocer la tendencia, la estacionalidad, la caída de 2020 y la recuperación posterior, algo que una tabla o unas barras sueltas no muestran con la misma claridad.

El usuario elige la serie (total, vía de ingreso o país de residencia), el rango de fechas y el nivel de detalle mensual, trimestral o anual, y puede acercarse a un periodo arrastrando sobre la gráfica. Al hacer clic en una barra del comparativo por grupo, la serie elegida se abre en esta gráfica. La línea azul representa siempre datos registrados, el mismo significado que tiene ese color en todo el tablero; el eje indica si cada punto son viajeros por mes, por trimestre o por año, y al pasar el cursor se lee el periodo exacto, por ejemplo «T2 2025 (abr–jun)».

Al agregar, cada punto suma los viajeros de un trimestre o un año completo. Los periodos con meses faltantes dentro del rango no se muestran, para no presentar un total parcial como si fuera completo, y la nota indica cuáles se omitieron: con los datos actuales, 2026 aparece solo en los niveles mensual y trimestral, porque llega hasta junio. Si una selección no tiene periodos completos, se muestra un mensaje. La gráfica apoya decisiones de planificación por temporada y la comparación entre años; describe lo registrado y no explica por sí sola las causas de los cambios.

## Texto para Word G6 datos observados y predicciones

La gráfica de líneas responde a la pregunta «¿Qué estimó cada modelo frente a lo que realmente se registró?». Compara, mes a mes, los viajeros registrados con las estimaciones existentes de cinco modelos (SARIMA, Holt-Winters, suavizamiento exponencial simple, referencia estacional y Prophet), tomadas de los resultados del Laboratorio 1 en `insumos/resultados/predicciones` y de las series de `insumos/series`. No se entrenó ningún modelo nuevo. Se elige una gráfica temporal porque tanto los datos como las estimaciones son secuencias mensuales: superponerlas en el mismo eje permite ver en qué periodos cada estimación se acerca o se aleja de lo observado.

El usuario selecciona la serie, uno o varios modelos (por defecto tres) y el periodo de comparación; cada cambio actualiza la gráfica. La línea continua azul con puntos representa los datos registrados y cada línea discontinua naranja, con un trazo distinto, la estimación de un modelo; la leyenda identifica todas las curvas y, al pasar el cursor, se leen todos los valores de un mismo mes. El naranja mantiene en todo el tablero el significado de «estimación», y el tipo de trazo distingue los modelos sin depender solo del color.

Solo se muestran los meses en que existen a la vez el dato registrado y la estimación de todos los modelos elegidos; con los archivos actuales son 63 meses, de abril de 2021 a junio de 2026. Son estimaciones para meses ya registrados, no un pronóstico de meses futuros, y no incluyen intervalos de confianza porque los archivos no los contienen. Que una curva se vea cercana no demuestra que el modelo sea preciso ni que lo será en el futuro: para comparar el tamaño del error, la nota remite a la gráfica «¿Qué modelo se equivoca menos para esta serie?». Si una selección no tiene datos, se muestra un mensaje. La gráfica ayuda al directivo a decidir con qué cautela consultar cada estimación; con los datos actuales, desde 2022 casi todas las estimaciones quedan por debajo de lo registrado.

## Paso a Hugo

- **Commits:** los de esta parte publicados en `lab10` después de `27de746`.
- **Modelos y fechas comprobados:** cinco modelos en las siete series; predicciones de abril de 2021 a junio de 2026 (63 meses); observaciones de enero de 2009 a junio de 2026.
- **Identificadores:** los de la tabla de identificadores; `series-selector` se conserva.
- **Resultados de revisión:** 14 pruebas nuevas y 41 previas aprobadas; revisión local en el navegador sin errores de consola.
- **Limitaciones abiertas:** las de la sección anterior; no se dan por resueltas.
- **Fecha y hora de aceptación:** por acordar y registrar.
