# Entrega de Diego resultados y comparación de modelos

## Alcance realizado

Se incorporan la lectura compartida de resultados existentes, G7 (comparación de errores entre modelos) y G8 (desviación observado menos estimado). Los componentes tienen una vista de revisión independiente. Su integración definitiva en `app/main.py` corresponde a Ernesto, conforme al reparto Diego → Esteban → Hugo → Ernesto.

El punto de partida fue `a659f04c654c29479b8c4f8d4f65c77dbe5de249`, en la rama `lab10`. No se entrenan modelos, no se alteran los CSV y no se modifica el documento compartido: los dos textos para incorporarlo están al final de este archivo, para la integración asignada a Ernesto.

## Validación de fuentes

La validación reproducible está en [01_diego_validacion.json](01_diego_validacion.json), generada mediante `python -m docs.scripts.audit_model_results`. Registra rutas, columnas, fechas, conteos y huellas SHA-256 de las fuentes mensuales y de las métricas.

| Serie | Observaciones mensuales | Modelos con archivo | Meses comunes de comparación |
|---|---:|---:|---:|
| Total | 210 | 5 | 63 |
| Vía Aérea | 210 | 5 | 63 |
| Vía Terrestre | 210 | 5 | 63 |
| Vía Marítima | 210 | 5 | 63 |
| El Salvador | 210 | 5 | 63 |
| Estados Unidos | 210 | 5 | 63 |
| Honduras | 210 | 5 | 63 |

- Las siete series cubren enero de 2009 a junio de 2026. Sus columnas son `fecha,viajeros`.
- Los 35 archivos de predicciones cubren abril de 2021 a junio de 2026, con 63 filas cada uno. Sus columnas son `fecha,prediccion`.
- Los cinco modelos identificados son `sarima`, `holt_winters`, `ses`, `seasonal_naive` y `prophet`.
- En los 42 archivos mensuales no se encontraron fechas inválidas o repetidas, huecos mensuales, valores faltantes, valores no numéricos ni infinitos.
- `metricas_modelos.csv` contiene 35 combinaciones serie/modelo sin duplicados y sin faltantes en MAE, RMSE o MAPE. Los vacíos en `order`, AIC o BIC no se rellenan y esos campos no se usan para ordenar los cinco modelos.
- Se recalcularon las tres métricas para las 35 combinaciones: las 105 coinciden con el CSV dentro de una tolerancia relativa de `1e-9` y absoluta de `1e-8`.
- Para cada serie quedan 147 observaciones anteriores a la cobertura de las predicciones. No se inventan estimaciones para ellas ni se rellenan con cero.
- No hay observaciones iguales a cero en los 63 meses comparados de las fuentes actuales. El código contempla ese caso: las excluye solo de MAPE y comunica cuántas se excluyeron.

La revisión acredita consistencia de los archivos del repositorio. No verifica su procedencia externa ni demuestra una separación entre entrenamiento y evaluación independiente, porque esa separación no está documentada en estos CSV. La interfaz presenta una comparación histórica, sin garantía de precisión futura ni atribución causal.

## Cálculo y alcance comparables

G7 recalcula MAE, RMSE y MAPE con las predicciones existentes. No copia una métrica global y la presenta como si respondiera a filtros distintos. Todos los modelos se comparan sobre la intersección de fechas con valores válidos del observado y de cada predicción.

Sea `e = observado - predicho`:

- MAE: promedio de `abs(e)`, en viajeros.
- RMSE: raíz del promedio de `e²`, en viajeros; da mayor peso a las equivocaciones grandes.
- MAPE: promedio de `abs(e / observado) × 100`, únicamente donde observado es distinto de cero. Si no queda ninguna observación válida, no se muestra un porcentaje numérico.

G8 utiliza los pares válidos de una serie y un modelo en el rango elegido. Una fecha sin ambos valores no genera una desviación. Si falta un mes entre dos puntos, la línea deja un hueco: no se interpola.

Ejemplo contrastado en el total, con SES, para abril de 2021: observado `82.067,87`, estimado `105.145,05`, diferencia `-23.077,18` viajeros, redondeados a dos decimales. El signo negativo indica que el modelo estimó más que lo registrado. La comprobación automatizada utiliza los valores completos.

Para el total, sobre los 63 meses comunes, SES tiene MAE `175.088,44`, RMSE `194.790,81` y MAPE `58,11 %`. Esta comparación describe ese periodo y esa serie; no se generaliza a todos los modelos, series o fechas futuras.

## Interfaz compartida para Esteban

Módulo: `app/model_results.py`. Las claves de serie son las de `app/data.py`; las claves de modelo y sus etiquetas están en `MODEL_LABELS`.

| Función | Argumentos | Resultado |
|---|---|---|
| `load_observations` | `series_key` | `pandas.Series` llamada `observed`, índice mensual `DatetimeIndex` llamado `date`, ordenado y sin fechas repetidas. |
| `load_predictions` | `series_key, model_key` | `pandas.Series` llamada `predicted`, con el mismo tipo de índice. |
| `available_models` | `series_key` | Lista de claves reconocidas cuyos archivos existen; no sustituye la validación de su contenido. |
| `load_metrics` | `series_key=None` | `DataFrame` con las columnas originales del CSV, validado y opcionalmente filtrado por serie. |
| `align_models` | `series_key, model_keys=None, start=None, end=None` | `DataFrame` con columna `observed` y una por clave de modelo, sobre las mismas fechas válidas. `attrs['models']` conserva las claves seleccionadas. |
| `align_observations` | `series_key, model_key, start=None, end=None` | `DataFrame` con `observed`, `predicted` y `error`, índice `date`. |
| `calculate_errors` | `series_key, model_keys=None, start=None, end=None` | `DataFrame` con índice `model` y columnas `mae,rmse,mape,count,mape_excluded,start,end`. |

`model_keys` es una lista de claves. `None` selecciona todos los modelos reconocidos con archivo. `start` y `end` aceptan fechas ISO o `pandas.Timestamp`; `None` deja abierto ese extremo y el filtro es inclusivo.

Los datos ausentes se conservan como ausentes hasta eliminar los pares incompletos para la comparación. No se convierten en ceros. Un periodo válido sin coincidencias devuelve un resultado vacío. Claves desconocidas, archivos ilegibles, columnas necesarias ausentes, fechas inválidas o duplicadas, valores no numéricos o infinitos y rangos invertidos generan `ModelDataError`, con mensaje en español. Los componentes capturan esta excepción y muestran un mensaje claro.

G7 y G8 usan controles propios. No escriben en `series-selector` ni cambian los filtros de los componentes existentes. G7 compara toda la intersección disponible; el rango de fechas de G8 afecta exclusivamente a G8.

## Componentes y registro para Ernesto

| Componente | Archivo | Identificadores |
|---|---|---|
| G7 | `app/components/model_errors.py` | Sección `model-errors`; controles `errors-series`, `errors-metric`; salidas `errors-graph`, `errors-note`. |
| G8 | `app/components/model_deviations.py` | Sección `model-deviations`; controles `deviations-series`, `deviations-model`, `deviations-dates`; salidas `deviations-graph`, `deviations-note`. |

Ambos exponen `layout()` y `register(app)`. `build_figure(...)` devuelve `(figure, note)` para facilitar su comprobación. En G8, `model_options(series_key, selected_model=None)` devuelve las opciones disponibles y conserva el modelo seleccionado cuando sigue disponible.

La integración debe añadir ambos `layout()` a la distribución final y llamar una vez a cada `register(app)`. Debe conservar los otros seis componentes que entregue el equipo y sus identificadores. No se ha sustituido ni modificado `app/main.py`.

## Ejecución y comprobaciones

Desde la raíz del repositorio, con las dependencias de `requirements.txt` instaladas:

```bash
python -m docs.scripts.audit_model_results
python -m unittest tests.test_model_results tests.test_model_components -v
python -m docs.scripts.preview_model_results
```

La vista de revisión se abre en `http://127.0.0.1:8051/`. Es una comprobación independiente de G7 y G8; no reemplaza el arranque del tablero principal ni la integración final.

Resultados de verificación:

- 14 pruebas nuevas aprobadas: intersección de fechas comparable entre modelos, cálculo contrastado, exclusión de ceros en MAPE, rechazo de duplicados y valores inválidos, tratamiento de faltantes, huecos en la línea, selecciones sin datos y callbacks HTTP.
- 27 pruebas existentes aprobadas en `tests.test_data`, `tests.test_ranking`, `tests.test_theme`, `tests.test_app` y `tests.test_wireframe`.
- En Edge se revisaron el renderizado de las dos gráficas, cambios de métrica MAE/MAPE, cambios de serie, selección de SES, rango de enero a diciembre de 2025 y periodo sin predicciones entre 2009 y 2010. Las selecciones produjeron los resultados y mensajes correspondientes.
- Las solicitudes de layout y callbacks respondieron con HTTP 200. No se observaron errores o advertencias en la consola del navegador durante la revisión.
- Se revisó la presentación de escritorio. No se declara una auditoría de dispositivos móviles; la revisión visual general corresponde a la parte de Hugo.

## Texto para Word G7 comparación de errores entre modelos

La gráfica de barras horizontales responde a la pregunta «¿Qué modelo se equivoca menos para esta serie?». Cada barra muestra el error de uno de los cinco modelos existentes. Se elige este tipo de gráfica porque permite comparar magnitudes y reconocer el orden de los modelos dentro de una misma serie. El usuario selecciona la serie y la medida de error. No se suman vías de ingreso y países de residencia.

El error absoluto medio, MAE, indica la distancia media entre lo observado y lo estimado, en viajeros. RMSE también se expresa en viajeros y da más peso a las equivocaciones grandes. MAPE expresa la distancia media como porcentaje de lo observado y excluye los meses cuyo valor observado es cero. La interfaz explica cada medida y señala las fechas y el número de meses utilizados. Las barras se ordenan de menor a mayor error y se usa el naranja del tema para identificar resultados relacionados con las estimaciones.

Los errores se recalculan sobre las mismas fechas coincidentes de todos los modelos, a partir de las series y predicciones de los laboratorios anteriores. En las fuentes revisadas son 63 meses, de abril de 2021 a junio de 2026. Esta comparación ayuda a decidir qué estimación consultar con mayor cautela para una serie. Un error menor describe mayor cercanía en ese periodo; no garantiza precisión futura ni demuestra una evaluación independiente del entrenamiento. Si faltan datos comparables, se muestra un mensaje en lugar de un ranking incompleto sin explicación.

## Texto para Word G8 desviación entre observado y estimado

La gráfica temporal responde a la pregunta «¿En qué meses se alejó el modelo de lo observado?». Muestra la diferencia entre viajeros observados y estimados para una serie y un modelo, en fechas coincidentes. Se elige una línea temporal porque permite localizar los meses en que las desviaciones crecen, disminuyen o cambian de signo. Los puntos identifican las observaciones mensuales y el usuario puede seleccionar la serie, el modelo y el rango de fechas.

Una línea horizontal marca el cero, donde observado y estimado coinciden. Un valor positivo indica que el modelo estimó menos viajeros de los registrados; uno negativo indica que estimó más. El signo describe la dirección del error y no una cantidad negativa de viajeros. El eje expresa la diferencia en viajeros, y la nota indica el modelo, la serie y los meses efectivamente comparados.

La línea utiliza el naranja reservado a las estimaciones y conserva la tipografía, las etiquetas y los controles del tablero. Los meses sin un par válido no se rellenan ni se interpolan; una selección sin coincidencias muestra un mensaje que invita a cambiar las fechas o el modelo. La gráfica ayuda a reconocer cuándo conviene ampliar los márgenes al planificar con una estimación, sin atribuir causas ni garantizar que el patrón histórico se repita.
