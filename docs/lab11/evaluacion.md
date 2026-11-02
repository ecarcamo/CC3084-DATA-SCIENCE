# Laboratorio 11: evaluación y regla de aceptación

## 5.1 Evaluación con meses ocultos

`pipeline/evaluation.py` oculta cada mes entre `periods.evaluation_start` y `periods.evaluation_end`, de julio de 2025 a junio de 2026, y lo estima como si no estuviera disponible. Para cada mes ajusta Holt-Winters solo con los meses desde `periods.fit_start` hasta el mes anterior al evaluado, según `model.evaluation_horizon`, que vale 1. Ningún valor del mes evaluado ni de meses posteriores interviene en su estimación.

Los meses sin valor observado no se evalúan y no se convierten en cero. Si falta un mes dentro de la ventana de ajuste, el ajuste se detiene con un error que nombra el mes faltante.

### Limitaciones frente a enero y febrero de 2026

- La base disponible llega a junio de 2026. No se conserva la versión de la fuente que existía a inicios de 2026, por lo que la evaluación usa valores que pudieron revisarse o completarse después.
- Con horizonte de un mes, febrero de 2026 se estima con enero ya observado. Si en la situación original ambos meses faltaban a la vez, febrero requería un horizonte de dos meses y su error real tiende a ser mayor que el medido.
- Si la base no contiene valores observados comparables para enero y febrero de 2026, con la misma definición de visitantes y la misma cobertura, esos meses quedan fuera de `evaluated_periods` y no se calculan errores para ellos.
- El factor de reparto vale 1, de modo que la evaluación mide la serie nacional y no el error que tendría un destino con reparto.

## 5.2 Métricas

Sobre los meses evaluados se calculan tres métricas con la diferencia entre estimado y observado:

- MAE: error absoluto medio, en visitantes por mes.
- RMSE: raíz del error cuadrático medio, en visitantes por mes. Penaliza más los meses con errores grandes.
- MAPE: error absoluto medio como porcentaje del observado.

Los meses con observado igual a cero se excluyen del MAPE porque el error porcentual no está definido, pero siguen en MAE y RMSE. Si todos los observados son cero, `mape_pct` vale `null`. Esta regla se guarda en `mape_zero_rule` dentro de `metrics.json`. Sin meses evaluados, las tres métricas valen `null`.

## 5.3 Referencia

La referencia es el estacional ingenuo con rezago de 12 meses, definido en `baseline`: estima cada mes con el valor observado del mismo mes del año anterior. Ese valor siempre es anterior al mes evaluado y sale del mismo historial truncado que recibe Holt-Winters.

Ambos procedimientos se evalúan sobre los mismos meses. Si falta el observado o el valor de referencia de un mes, ese mes se excluye para los dos. `metrics.json` guarda las métricas de cada uno en `procedure` y `baseline`.

## 5.4 Regla de aceptación

`accept` rechaza una versión candidata si se cumple cualquiera de estas condiciones:

1. Algún control de calidad tiene estado `stop`.
2. `estimates.csv` no tiene todas las columnas de `outputs.estimate_columns` o alguna tiene valores vacíos.
3. El pronóstico no tiene exactamente `acceptance.expected_forecast_months` meses, de `periods.forecast_start` a `periods.forecast_end`.
4. Hay estimaciones no finitas o negativas.
5. El MAPE del procedimiento supera `acceptance.max_mape_pct` o no puede calcularse.
6. La razón entre el MAE del procedimiento y el de la referencia supera `acceptance.max_mae_ratio_to_baseline` o no puede calcularse.

Los umbrales son inclusivos: un valor igual al máximo se acepta. La decisión es `{"accepted": bool, "reasons": [...]}`, con un motivo por cada criterio incumplido, y se guarda en `acceptance` dentro de `run.json`. Las advertencias de calidad no rechazan la versión por sí solas.

### Umbrales fijados

Los umbrales están en `acceptance` dentro de `config/pipeline.yaml` y quedan fijados con este documento antes de ejecutar la evaluación con la base institucional. No se modifican después de conocer ese resultado. Un cambio posterior exige una nueva `model.procedure_version` y se aplica solo a ejecuciones nuevas.

| Umbral | Valor | Justificación |
|---|---|---|
| `max_mape_pct` | 10 % | La serie nacional está en el orden de cientos de miles de visitantes por mes. Como referencia de escala, la serie total de viajeros de `insumos/series/`, con otra definición, varía entre unos 190 000 y 390 000 por mes desde 2023, con promedio cercano a 290 000. Un 10 % equivale a unos 29 000 visitantes por mes. En esa serie, la variación absoluta promedio entre meses consecutivos ronda 15 % y el estacional ingenuo logra cerca de 4 % entre julio de 2025 y junio de 2026. El umbral deja margen por la diferencia de definición y por los pocos meses evaluados, pero rechaza un error cercano a la variación mensual típica, que ya no permitiría distinguir los movimientos estacionales. |
| `max_mae_ratio_to_baseline` | 1.5 | El punto 5.5 no exige superar a la referencia. Con 12 meses evaluados, un solo mes atípico mueve mucho el MAE, por lo que se tolera hasta un 50 % más de error que el estacional ingenuo. Holt-Winters aporta una tendencia amortiguada para seis meses que la referencia no tiene. Por encima de 1.5, el procedimiento es claramente peor que repetir el año anterior y no se justifica publicarlo. |
| `expected_forecast_months` | 6 | El tablero muestra de julio a diciembre de 2026. Una versión incompleta dejaría meses sin estimación. |
| `require_non_negative_estimates` | sí | La variable es un conteo de visitantes y no admite valores negativos. |
| `require_finite_estimates` | sí | Un valor infinito o vacío no puede mostrarse ni compararse. |

Ambos criterios de desempeño deben cumplirse a la vez. El MAPE limita el error frente a la escala de la serie y la razón de MAE lo limita frente a una alternativa trivial.

## 5.5 Aplicación de la regla

Resultado con la base institucional `data/raw/base_migracion_2009_2026jun.xlsx` (huella SHA-256 `cdaba779…3846`), ejecutado con `docker compose run --rm pipeline`. Se evaluaron los 12 meses de julio de 2025 a junio de 2026; todos tienen valor observado y valor de referencia, y ninguno es cero.

| Procedimiento | MAE | RMSE | MAPE |
|---|---|---|---|
| Holt-Winters | 16 670 | 20 068 | 6,39 % |
| Estacional ingenuo | 12 027 | 15 232 | 4,47 % |

Errores por mes (estimado menos observado, en visitantes):

| Mes | Observado | Holt-Winters | Error HW | Referencia | Error referencia |
|---|---|---|---|---|---|
| 2025-07 | 283 389 | 287 191 | 3 803 | 266 975 | -16 414 |
| 2025-08 | 293 781 | 299 116 | 5 335 | 282 102 | -11 679 |
| 2025-09 | 218 070 | 237 062 | 18 993 | 215 659 | -2 411 |
| 2025-10 | 255 921 | 226 402 | -29 519 | 249 666 | -6 255 |
| 2025-11 | 310 586 | 305 354 | -5 231 | 302 674 | -7 911 |
| 2025-12 | 365 573 | 375 856 | 10 283 | 361 750 | -3 823 |
| 2026-01 | 300 664 | 315 360 | 14 696 | 289 544 | -11 120 |
| 2026-02 | 236 844 | 268 826 | 31 982 | 254 429 | 17 585 |
| 2026-03 | 291 160 | 313 540 | 22 379 | 278 538 | -12 622 |
| 2026-04 | 260 951 | 299 719 | 38 768 | 300 288 | 39 337 |
| 2026-05 | 241 312 | 251 226 | 9 914 | 247 982 | 6 670 |
| 2026-06 | 245 688 | 254 828 | 9 140 | 254 190 | 8 503 |

Holt-Winters no supera a la referencia. Su error es menor en julio, agosto y noviembre de 2025, pero sobreestima nueve de los doce meses, sobre todo en 2026. La ventana de ajuste empieza en enero de 2023, de modo que al inicio de la evaluación solo hay 30 meses, dos años y medio, para estimar el nivel, la tendencia y doce índices estacionales. La tendencia amortiguada todavía arrastra el crecimiento de 2023 y 2024, mientras que 2026 se mantuvo cerca de 2025. El estacional ingenuo, en cambio, repite un año que ya refleja ese nivel. Abril de 2026 es el mayor error de ambos procedimientos: Semana Santa cayó en abril en 2025 y entre marzo y abril en 2026, y ninguno de los dos lo modela.

Decisión de la regla, con los umbrales fijados antes de la ejecución y sin cambiarlos:

| Criterio | Valor | Umbral | Cumple |
|---|---|---|---|
| Controles críticos | 6 de 6 en `ok` | ningún `stop` | sí |
| Integridad de `estimates.csv` | 6 meses, de 2026-07 a 2026-12, columnas completas | 6 meses | sí |
| Estimaciones finitas y no negativas | entre 230 737 y 371 750 | todas | sí |
| MAPE de Holt-Winters | 6,39 % | ≤ 10 % | sí |
| Razón de MAE frente a la referencia | 16 670 / 12 027 = 1,39 | ≤ 1,5 | sí |

La versión se acepta y se publica. Como permite el punto 5.5, la regla no exige superar a la referencia: el error de Holt-Winters equivale a un 6 % del mes promedio de 264 790 visitantes desde 2023 y queda dentro del margen fijado. El resultado se informa tal cual en el tablero (G7) y se deja como mejora para una versión futura, con una nueva `model.procedure_version`, revisar la ventana de ajuste o la tendencia.

La validación con la fuente sintética de `tests/synthetic_source.py`, sin estacionalidad, sigue en las pruebas automáticas y no describe la serie real.
