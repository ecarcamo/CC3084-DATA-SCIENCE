"""Descompresión de los .zip de Importación de Vehículos del Portal SAT.

Cada .zip contiene un único archivo de texto delimitado por "|" (encoding
ISO-8859-1) cuyo nombre interno no identifica el mes/año (ej.
"web_imp_08072026.txt"). Por eso, al extraer, el archivo se renombra
usando el año/mes que ya conocemos por el nombre del .zip.
"""

import re
import zipfile
from pathlib import Path

ZIP_NAME_PATTERN = re.compile(r"importacion_vehiculos_(\d{4})_(\d{2})\.zip")


def extract_zips(zip_dir="Datos/zips", output_dir="Datos/raw"):
    """Descomprime todos los .zip de zip_dir y guarda el .txt resultante en
    output_dir, renombrado como importacion_vehiculos_<year>_<month>.txt.

    Devuelve la lista de rutas (Path) de los .txt extraídos.
    """
    zip_path = Path(zip_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_paths = []

    for zip_file in sorted(zip_path.glob("importacion_vehiculos_*.zip")):
        match = ZIP_NAME_PATTERN.match(zip_file.name)
        if not match:
            print(f"[extract] Nombre inesperado, se omite: {zip_file.name}")
            continue

        year, month = match.groups()
        txt_name = f"importacion_vehiculos_{year}_{month}.txt"
        txt_path = output_path / txt_name

        if txt_path.exists():
            print(f"[extract] Ya existe {txt_name}, se omite.")
            txt_paths.append(txt_path)
            continue

        with zipfile.ZipFile(zip_file) as zf:
            members = zf.namelist()
            if len(members) != 1:
                print(
                    f"[extract] Aviso: {zip_file.name} contiene {len(members)} "
                    "archivos, se usará el primero."
                )
            with zf.open(members[0]) as source, open(txt_path, "wb") as dest:
                dest.write(source.read())

        print(f"[extract] {zip_file.name} -> {txt_name}")
        txt_paths.append(txt_path)

    return txt_paths


if __name__ == "__main__":
    paths = extract_zips()
    print(f"Extraídos {len(paths)} archivos .txt")
