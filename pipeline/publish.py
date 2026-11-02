def publish(candidate_dir, config):
    """Instala una versión candidata aceptada como versión aprobada.

    Entrada: `candidate_dir` contiene `estimates.csv`, `observed.csv`, `metrics.json`,
    `quality_report.json` y `run.json`; `config` contiene `outputs.approved_dir` y
    `outputs.history_dir`.

    Salida: identificador de la versión instalada, igual al `run_id` del candidato. La versión vigente
    se copia a `history_dir/<run_id>/` antes de reemplazarla. Si algo falla, `approved_dir` conserva la
    versión anterior completa.
    """
    raise NotImplementedError("publish pendiente: persona C")


def latest_approved(config):
    """Devuelve la carpeta de la versión aprobada vigente o `None` si todavía no existe."""
    raise NotImplementedError("latest_approved pendiente: persona C")


def restore(version_id, config):
    """Reinstala una versión del historial como versión aprobada vigente.

    Entrada: `version_id` es el nombre de una carpeta en `outputs.history_dir`; `config` contiene las
    rutas de salida.

    Salida: identificador de la versión restaurada. La versión vigente pasa al historial antes del
    reemplazo.
    """
    raise NotImplementedError("restore pendiente: persona C")
