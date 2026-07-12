"""Orquestación del pipeline de Importación de Vehículos (Portal SAT).

Fases:
    1. Descargar los .zip del Portal SAT (2025 completo + lo transcurrido de 2026).
    2. Descomprimir los .zip y guardar los .txt en la carpeta Datos.
    3. Construir el conjunto de datos unificado (TODO).
    4. Guardar el conjunto de datos unificado en un .csv (TODO).

La fase de exploración de datos (preguntas del negocio) se hará aparte en
un notebook de Jupyter.
"""

from src.download import download_zip_from_SAT
from src.extract import extract_zips
from src.build_dataset import build_unified_dataset
from src.save_dataset import save_dataset_to_csv

YEARS = (2025, 2026)
ZIP_DIR = "Datos/zips"
RAW_DIR = "Datos/raw"
DATASET_CSV = "Datos/importacion_vehiculos.csv"


def main():
    print("== Fase 1: Descarga de .zip desde el Portal SAT ==")
    zip_paths = download_zip_from_SAT(output_dir=ZIP_DIR, years=YEARS)
    print(f"Total de .zip disponibles: {len(zip_paths)}")

    print("\n== Fase 2: Descompresión de archivos ==")
    txt_paths = extract_zips(zip_dir=ZIP_DIR, output_dir=RAW_DIR)
    print(f"Total de .txt extraídos: {len(txt_paths)}")

    print("\n== Fase 3: Construcción del dataset unificado ==")
    dataset = build_unified_dataset(raw_dir=RAW_DIR)

    print("\n== Fase 4: Guardado del dataset en .csv ==")
    save_dataset_to_csv(dataset, output_path=DATASET_CSV)


if __name__ == "__main__":
    main()
