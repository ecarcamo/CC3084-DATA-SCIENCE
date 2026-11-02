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
