def log_run(metadata, config, artifacts_dir):
    """Registra una ejecución en MLflow Tracking.

    Entrada: `metadata` es el contenido de `run.json`; `config` contiene la sección `mlflow`;
    `artifacts_dir` es la carpeta candidata con los archivos generados hasta el momento.

    Salida: identificador del run de MLflow. Registra el estado, el commit de Git, la huella de la
    fuente, los períodos, los parámetros, los controles y los archivos existentes. Si
    `metadata["metrics"]` es `None`, la ejecución se detuvo antes de la evaluación y no registra
    métricas; registra la causa desde `metadata["errors"]`.
    """
    raise NotImplementedError("log_run pendiente: persona B")
