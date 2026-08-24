"""Ensambla las secciones del informe de la Parte 2 en un solo PDF.

Une los archivos de `informe/secciones/` en orden, convierte el markdown a HTML con
el formato pedido por el enunciado (texto negro de 12 pt, títulos de 16 pt centrados,
encabezado con los integrantes del grupo) e imprime el resultado con Chromium en modo
headless. Uso:  python informe/construir_pdf.py
"""

import base64
import subprocess
import tempfile
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parents[1]
SECCIONES = RAIZ / "informe" / "secciones"
FIGURAS = RAIZ / "informe" / "figuras"
SALIDA = RAIZ / "INFORME_PARTE2.pdf"

CURSO = "CC3084 &mdash; Data Science &mdash; Semestre II 2026"
UNIVERSIDAD = "Universidad del Valle de Guatemala &mdash; Facultad de Ingenier&iacute;a"
TITULO = "Laboratorio 4, Parte 2<br>An&aacute;lisis de modelos usando datos geoespaciales"
INTEGRANTES = [
    ("Hugo Barillas", "23556"),
    ("Esteban C&aacute;rcamo", "23016"),
    ("Ernesto Ascencio", "23009"),
]

# Texto negro de 12 pt y títulos de 16 pt centrados, según el formato pedido. Las tablas
# y el código heredan un tamaño ligeramente menor para que las tablas anchas de métricas
# quepan en el ancho de página sin desbordarse.
CSS = """
@page { size: letter; margin: 2cm 2.2cm; }
body { font-family: "Liberation Serif", "Times New Roman", serif; font-size: 12pt;
       color: #000000; line-height: 1.45; }
h1, h2, h3, h4 { font-size: 16pt; text-align: center; color: #000000;
                 font-weight: bold; margin: 1.1em 0 0.6em 0; page-break-after: avoid; }
h1 { page-break-before: always; }
p, li { font-size: 12pt; color: #000000; text-align: justify; }
table { border-collapse: collapse; margin: 0.8em auto; font-size: 10pt; }
th, td { border: 1px solid #000000; padding: 3px 7px; color: #000000; }
th { font-weight: bold; }
code { font-family: "Liberation Mono", monospace; font-size: 10.5pt; color: #000000; }
img { display: block; margin: 0.8em auto; max-width: 96%; page-break-inside: avoid; }
.portada { text-align: center; page-break-after: always; padding-top: 5cm; }
.portada h1 { page-break-before: avoid; font-size: 16pt; }
.portada p { text-align: center; }
.integrantes { margin-top: 2.5cm; }
.encabezado { text-align: center; font-size: 12pt; margin-bottom: 0.4cm; }
"""


def incrustar_figuras(html: str) -> str:
    """Reemplaza las rutas relativas de las figuras por data URIs.

    Chromium en modo headless no carga rutas relativas fuera del archivo temporal, y
    embeber las imágenes evita depender de la ubicación desde donde se ejecute el script.
    """
    for figura in FIGURAS.glob("*.png"):
        ruta = f"../figuras/{figura.name}"
        if ruta not in html:
            continue
        datos = base64.b64encode(figura.read_bytes()).decode()
        html = html.replace(ruta, f"data:image/png;base64,{datos}")
    return html


def quitar_indice_de_figuras(texto: str) -> str:
    """Elimina las secciones "Figuras generadas" del markdown de cada inciso.

    Esas listas enumeran rutas de archivo; son útiles como referencia dentro del
    repositorio, pero en el PDF las figuras ya van embebidas donde corresponde y la
    lista solo agrega ruido.
    """
    lineas = texto.splitlines()
    salida, saltando = [], False
    for linea in lineas:
        if linea.startswith("## Figuras generadas"):
            saltando = True
            continue
        if saltando:
            if linea.startswith("#"):
                saltando = False
            else:
                continue
        salida.append(linea)
    return "\n".join(salida)


def portada() -> str:
    filas = "\n".join(
        f"<p>{nombre} &mdash; carn&eacute; {carne}</p>" for nombre, carne in INTEGRANTES
    )
    return f"""
<div class="portada">
  <p class="encabezado">{UNIVERSIDAD}</p>
  <p class="encabezado">{CURSO}</p>
  <h1>{TITULO}</h1>
  <div class="integrantes">
    <p><b>Integrantes</b></p>
    {filas}
  </div>
</div>
"""


def construir_html() -> str:
    secciones = sorted(SECCIONES.glob("p2_*.md"))
    if not secciones:
        raise SystemExit(f"No se encontraron secciones en {SECCIONES}")

    cuerpo = markdown.markdown(
        "\n\n".join(quitar_indice_de_figuras(s.read_text(encoding="utf-8")) for s in secciones),
        extensions=["tables", "sane_lists"],
    )
    cuerpo = incrustar_figuras(cuerpo)
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Laboratorio 4 Parte 2 - Datos Geoespaciales</title>
<style>{CSS}</style></head>
<body>{portada()}{cuerpo}</body></html>"""


def main() -> None:
    html = construir_html()
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
        tmp.write(html)
        ruta_html = Path(tmp.name)

    subprocess.run(
        ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", f"--print-to-pdf={SALIDA}", ruta_html.as_uri()],
        check=True, capture_output=True,
    )
    ruta_html.unlink()
    print(f"{SALIDA} generado ({SALIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
