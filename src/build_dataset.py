"""Fase 3: construcción del dataset unificado de Importación de Vehículos.

Cada .txt en Datos/raw/ es un archivo mensual delimitado por "|", en
encoding ISO-8859-1 (latin-1), con 17 columnas nombradas en el encabezado
pero 18 campos por fila de datos (el último siempre vacío, por un "|"
final). Si se lee con pandas sin index_col=False, ese desfase hace que
pandas tome la primera columna como índice y desalinee todo el resto —
por eso index_col=False es obligatorio aquí.

Además, un puñado de filas (5, todas en 2025_07, para el mismo tipo de
maquinaria pesada "BUSH HOG LOADCRAFT") traen un "|" adicional dentro del
campo de Centímetros Cúbicos (formato de medida de neumático, ej.
"12R2D4.75"), lo que rompe el conteo de columnas esperado.

Probamos on_bad_lines="skip" de pandas para esas filas, pero con el motor
"python" no las descarta: las trunca y desplaza el resto de los valores en
esa fila (el Impuesto real termina en la columna Valor_CIF, Distintivo se
pierde), es decir corrompe en silencio en vez de saltarlas. Por eso el
filtrado de filas malformadas se hace a mano, línea por línea, antes de
pasarle el texto a pandas.
"""

import re
from io import StringIO
from pathlib import Path

import pandas as pd

RAW_FILENAME_PATTERN = re.compile(r"importacion_vehiculos_(\d{4})_(\d{2})\.txt")

COLUMN_RENAME = {
    "Pais de Proveniencia": "Pais_Proveniencia",
    "Aduana de Ingreso": "Aduana_Ingreso",
    "Fecha de la Poliza": "Fecha_Poliza",
    "Partida Arancelaria": "Partida_Arancelaria",
    "Modelo del Vehiculo": "Modelo_Vehiculo",
    "Marca": "Marca",
    "Linea": "Linea",
    "Centimetros Cubicos": "Centimetros_Cubicos",
    "Distintivo": "Distintivo",
    "Tipo de Vehiculo": "Tipo_Vehiculo",
    "Tipo de Importador": "Tipo_Importador",
    "Tipo Combustible": "Tipo_Combustible",
    "Asientos": "Asientos",
    "Puertas": "Puertas",
    "Tonelaje": "Tonelaje",
    "Valor CIF": "Valor_CIF",
    "Impuesto": "Impuesto",
}

NUMERIC_COLUMNS = [
    "Modelo_Vehiculo",
    "Centimetros_Cubicos",
    "Asientos",
    "Puertas",
    "Tonelaje",
    "Valor_CIF",
    "Impuesto",
]

TEXT_COLUMNS = [
    "Pais_Proveniencia",
    "Aduana_Ingreso",
    "Partida_Arancelaria",
    "Marca",
    "Linea",
    "Distintivo",
    "Tipo_Vehiculo",
    "Tipo_Importador",
    "Tipo_Combustible",
]


def _read_month_file(txt_path):
    with open(txt_path, encoding="latin-1") as fh:
        lines = fh.read().splitlines()

    header, *data_lines = lines
    expected_pipes = header.count("|") + 1  # cada fila de datos trae un "|" final extra

    good_lines = []
    dropped = 0
    for line in data_lines:
        if not line:
            continue
        if line.count("|") == expected_pipes:
            good_lines.append(line)
        else:
            dropped += 1

    if dropped:
        print(f"[build_dataset]   {txt_path.name}: {dropped} fila(s) malformada(s) descartada(s)")

    csv_text = "\n".join([header, *good_lines])
    df = pd.read_csv(StringIO(csv_text), sep="|", index_col=False)
    df.columns = [col.strip() for col in df.columns]
    df = df.rename(columns=COLUMN_RENAME)
    return df


def build_unified_dataset(raw_dir="Datos/raw"):
    """Lee todos los .txt de raw_dir y devuelve un único DataFrame limpio,
    con una fila por vehículo importado.
    """
    raw_path = Path(raw_dir)
    frames = []

    for txt_file in sorted(raw_path.glob("importacion_vehiculos_*.txt")):
        match = RAW_FILENAME_PATTERN.match(txt_file.name)
        if not match:
            print(f"[build_dataset] Nombre inesperado, se omite: {txt_file.name}")
            continue

        print(f"[build_dataset] Leyendo {txt_file.name} ...")
        frames.append(_read_month_file(txt_file))

    if not frames:
        raise FileNotFoundError(f"No se encontraron .txt en {raw_dir}")

    df = pd.concat(frames, ignore_index=True)

    for col in TEXT_COLUMNS:
        # Algunas columnas (ej. Partida_Arancelaria) son numéricas en meses
        # donde todos los valores son puramente dígitos; se fuerzan a texto
        # antes de aplicar .str.strip().
        df[col] = df[col].astype("string").str.strip()

    df["Fecha_Poliza"] = pd.to_datetime(
        df["Fecha_Poliza"].str.strip(), format="%d/%m/%Y", errors="coerce"
    )
    df["Anio"] = df["Fecha_Poliza"].dt.year
    df["Mes"] = df["Fecha_Poliza"].dt.month

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"[build_dataset] Dataset unificado: {len(df):,} filas, {df.shape[1]} columnas")
    return df


if __name__ == "__main__":
    dataset = build_unified_dataset()
    print(dataset.head())
