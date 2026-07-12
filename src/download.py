"""Descarga de los archivos .zip de Importación de Vehículos del Portal SAT.

Fuente: https://portal.sat.gob.gt/portal/alza-e-importacion-vehiculos/
Esa página lista, entre otras cosas, una tabla "Importación de Vehículos"
con un enlace de descarga por mes/año. Cada enlace apunta directamente a un
.zip (Content-Type: application/octet-stream, Content-Disposition indica el
nombre real del archivo).
"""

import re
from pathlib import Path

import requests

LISTING_URL = "https://portal.sat.gob.gt/portal/alza-e-importacion-vehiculos/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Solo nos interesan los enlaces de "importacion-de-vehiculos" (no los de
# "alza-de-importacion-de-vehiculos", que es otra tabla de la misma página).
LINK_PATTERN = re.compile(
    r'href="(https://portal\.sat\.gob\.gt/portal/descarga/\d+/importacion-de-vehiculos/'
    r'\d+/importacion_de_vehiculos_(\d{4})_([a-z]+))"'
)

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def get_available_downloads(years):
    """Consulta la página del Portal SAT y devuelve los enlaces de descarga
    disponibles para los años indicados.

    Devuelve una lista de dicts: {"year": int, "month": int, "url": str}
    """
    response = requests.get(LISTING_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    seen_urls = set()
    downloads = []
    for url, year_str, mes_nombre in LINK_PATTERN.findall(response.text):
        # Cada fila de la tabla tiene dos <a> (ícono + botón) con el mismo href.
        if url in seen_urls:
            continue
        seen_urls.add(url)

        year = int(year_str)
        if year not in years:
            continue
        month = MESES.get(mes_nombre)
        if month is None:
            continue
        downloads.append({"year": year, "month": month, "url": url})

    downloads.sort(key=lambda d: (d["year"], d["month"]))
    return downloads


def download_zip_from_SAT(output_dir="Datos/zips", years=(2025, 2026)):
    """Descarga los .zip de Importación de Vehículos del Portal SAT para los
    años indicados y los guarda en output_dir.

    Devuelve la lista de rutas (Path) de los .zip descargados/existentes.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    downloads = get_available_downloads(years)
    zip_paths = []

    for item in downloads:
        filename = f"importacion_vehiculos_{item['year']}_{item['month']:02d}.zip"
        zip_path = output_path / filename

        if zip_path.exists():
            print(f"[download] Ya existe {filename}, se omite.")
            zip_paths.append(zip_path)
            continue

        print(f"[download] Descargando {filename} ...")
        resp = requests.get(item["url"], headers=HEADERS, timeout=60)
        resp.raise_for_status()
        zip_path.write_bytes(resp.content)
        zip_paths.append(zip_path)

    return zip_paths


if __name__ == "__main__":
    paths = download_zip_from_SAT()
    print(f"Descargados {len(paths)} archivos .zip")
