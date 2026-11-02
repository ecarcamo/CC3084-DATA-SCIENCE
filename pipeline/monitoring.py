def run_monitoring(series, estimates, previous_approved_dir, config):
    """Ejecuta las verificaciones de actualización, calidad y resultados.

    Entrada: `series` es la serie mensual de `prepare_series`; `estimates` es el DataFrame de
    `estimates.csv`; `previous_approved_dir` es la carpeta de la versión aprobada vigente, que puede
    no existir; `config` contiene `monitoring` y `periods`.

    Salida: lista de `pipeline.checks.CheckResult` con estado `ok` o `warning`. El monitoreo genera
    alertas para revisión y no usa `stop`. Se guarda en `run.json` bajo `monitoring`.
    """
    raise NotImplementedError("run_monitoring pendiente: persona B")
