"""Ensambla el informe final del Laboratorio 4 (Partes I y II) en un solo PDF.

Une el informe de la Parte I (`INFORME.md`) con las diez secciones de la Parte II
(`informe/secciones/`), convierte el markdown a HTML con el formato pedido por el
enunciado (texto negro de 12 pt, títulos de 16 pt centrados, encabezado con los
integrantes del grupo) e imprime el resultado con Chromium en modo headless.

Uso:  python informe/construir_pdf.py
"""

import base64
import re
import subprocess
import tempfile
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parents[1]
PARTE1 = RAIZ / "INFORME.md"
SECCIONES = RAIZ / "informe" / "secciones"
FIGURAS = RAIZ / "informe" / "figuras"
SALIDA = RAIZ / "INFORME_FINAL.pdf"

CURSO = "CC3084 &mdash; Data Science &mdash; Semestre II 2026"
UNIVERSIDAD = "Universidad del Valle de Guatemala &mdash; Facultad de Ingenier&iacute;a"
TITULO = (
    "Laboratorio 4<br>Monitoreo satelital de cianobacteria "
    "en los lagos de Atitl&aacute;n y Amatitl&aacute;n"
)
SUBTITULO = "Parte I: an&aacute;lisis de datos geoespaciales<br>Parte II: modelos de Machine Learning"
REPOSITORIO = "https://github.com/ecarcamo/CC3084-DATA-SCIENCE"
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
.portada { text-align: center; page-break-after: always; padding-top: 4cm; }
.portada h1 { page-break-before: avoid; font-size: 16pt; }
.portada p { text-align: center; }
.integrantes { margin-top: 2.2cm; }
.encabezado { text-align: center; font-size: 12pt; margin-bottom: 0.4cm; }
.repo { margin-top: 1.6cm; font-size: 11pt; }
"""

# Enlace markdown a una figura .png, en cualquiera de las dos formas que usan los
# informes: "informe/figuras/x.png" (Parte I) o "../figuras/x.png" (Parte II).
ENLACE_FIGURA = re.compile(r"\[([^\]]*)\]\((?:informe|\.\.)/figuras/([A-Za-z0-9_.\-]+\.png)\)")
ENLACE_MAPA_HTML = re.compile(r"\[([^\]]*)\]\((?:informe|\.\.)/figuras/[A-Za-z0-9_.\-]+\.html\)")


def embeber_figuras_enlazadas(texto: str) -> str:
    """Convierte los enlaces a figuras de la Parte I en imágenes embebidas.

    La Parte I menciona sus figuras como enlaces dentro del párrafo ("ver `x.png`"),
    lo cual es inservible en un PDF: el lector no puede abrir el archivo. Aquí cada
    enlace se reduce a su texto y la figura se inserta como imagen justo después del
    párrafo que la menciona, conservando el orden y sin repetir una misma figura.
    Los mapas interactivos (.html) no son embebibles y quedan solo como mención.
    """
    parrafos = texto.split("\n\n")
    salida = []
    for parrafo in parrafos:
        figuras = []
        for nombre in ENLACE_FIGURA.findall(parrafo):
            if nombre[1] not in figuras:
                figuras.append(nombre[1])
        parrafo = ENLACE_FIGURA.sub(r"\1", parrafo)
        parrafo = ENLACE_MAPA_HTML.sub(r"\1", parrafo)
        salida.append(parrafo)
        for figura in figuras:
            salida.append(f"![{figura}](../figuras/{figura})")
    return "\n\n".join(salida)


def incrustar_datos_imagen(html: str) -> str:
    """Reemplaza las rutas de las figuras por data URIs.

    Chromium en modo headless no carga rutas relativas fuera del archivo temporal, y
    embeber las imágenes evita depender de la ubicación desde donde se ejecute el script.
    """
    for figura in FIGURAS.glob("*.png"):
        datos = None
        for ruta in (f"../figuras/{figura.name}", f"informe/figuras/{figura.name}"):
            if ruta not in html:
                continue
            if datos is None:
                datos = base64.b64encode(figura.read_bytes()).decode()
            html = html.replace(ruta, f"data:image/png;base64,{datos}")
    return html


def quitar_indice_de_figuras(texto: str) -> str:
    """Elimina las secciones "Figuras generadas" del markdown de cada inciso.

    Esas listas enumeran rutas de archivo; son útiles como referencia dentro del
    repositorio, pero en el PDF las figuras ya van embebidas donde corresponde y la
    lista solo agrega ruido.
    """
    salida, saltando = [], False
    for linea in texto.splitlines():
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


def markdown_parte1() -> str:
    """Contenido de la Parte I, sin su portada propia (ya está en la del informe final)."""
    texto = PARTE1.read_text(encoding="utf-8")
    inicio = texto.index("## 1. Contexto y objetivo")
    return "# Parte I. Análisis de los datos geoespaciales\n\n" + embeber_figuras_enlazadas(
        texto[inicio:]
    )


def markdown_parte2() -> str:
    """Las diez secciones de la Parte II, en orden de inciso."""
    secciones = sorted(SECCIONES.glob("p2_*.md"))
    if not secciones:
        raise SystemExit(f"No se encontraron secciones en {SECCIONES}")
    cuerpo = "\n\n".join(
        quitar_indice_de_figuras(s.read_text(encoding="utf-8")) for s in secciones
    )
    return "# Parte II. Modelos de Machine Learning\n\n" + cuerpo


def portada() -> str:
    filas = "\n".join(
        f"<p>{nombre} &mdash; carn&eacute; {carne}</p>" for nombre, carne in INTEGRANTES
    )
    return f"""
<div class="portada">
  <p class="encabezado">{UNIVERSIDAD}</p>
  <p class="encabezado">{CURSO}</p>
  <h1>{TITULO}</h1>
  <p>{SUBTITULO}</p>
  <div class="integrantes">
    <p><b>Integrantes</b></p>
    {filas}
  </div>
  <p class="repo">Repositorio: {REPOSITORIO}</p>
</div>
"""


def construir_html() -> str:
    cuerpo = markdown.markdown(
        markdown_parte1() + "\n\n" + markdown_parte2(),
        extensions=["tables", "sane_lists"],
    )
    cuerpo = incrustar_datos_imagen(cuerpo)
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Laboratorio 4 - Monitoreo satelital de cianobacteria</title>
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
