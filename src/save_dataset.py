"""Fase 4: guardado del dataset unificado en un archivo .csv."""

from pathlib import Path


def save_dataset_to_csv(dataset, output_path="Datos/importacion_vehiculos.csv"):
    """Guarda el DataFrame unificado en output_path como .csv (utf-8, sin
    índice). Devuelve la ruta (Path) del archivo generado.
    """
    csv_path = Path(output_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    dataset.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[save_dataset] Dataset guardado en {csv_path} ({len(dataset):,} filas)")
    return csv_path
