import sys
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

output_path, figure_path = sys.argv[1], sys.argv[2]
FONT = "Times New Roman"
BODY_SIZE = 12
TITLE_SIZE = 12
SMALL_SIZE = 10.5
TITLE = "Resiliencia y futuro del turismo en Guatemala: decisiones de diseño de la infografía"

doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
for margin in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(section, margin, Inches(1))

normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(BODY_SIZE)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.line_spacing = 2.0
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(0)


def add_page_number(sec):
    p = sec.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    run.font.name = FONT
    run.font.size = Pt(BODY_SIZE)


def add_runs(p, text, bold=False, italic=False, size=None):
    for i, part in enumerate(text.split("*")):
        if not part:
            continue
        run = p.add_run(part)
        run.bold = bold
        run.italic = italic or (i % 2 == 1)
        if size:
            run.font.size = Pt(size)
    return p


def paragraph(text="", bold=False, italic=False, align=None, indent=True, spacing=None, size=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if indent and align is None:
        p.paragraph_format.first_line_indent = Inches(0.5)
    if spacing is not None:
        p.paragraph_format.line_spacing = spacing
    if text:
        add_runs(p, text, bold, italic, size)
    return p


def heading(text):
    p = paragraph(text, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.paragraph_format.keep_with_next = True
    return p


def title(text):
    p = paragraph(text, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=TITLE_SIZE, spacing=2.0)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(0)
    return p


def set_borders(cell, edges):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        if edge in edges:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "6")
            el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")
        borders.append(el)
    tc_pr.append(borders)


def table(number, caption, header, rows, widths, note=None):
    p = paragraph(f"Tabla {number}", bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False)
    p.paragraph_format.keep_with_next = True
    p = paragraph(caption, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False)
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, width in enumerate(widths):
        t.columns[i].width = Inches(width)
    for i, col in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        col.set(qn("w:w"), str(int(widths[i] * 1440)))
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for r, values in enumerate([header] + rows):
        for c, value in enumerate(values):
            cell = t.rows[r].cells[c]
            cell.width = Inches(widths[c])
            cp = cell.paragraphs[0]
            cp.paragraph_format.line_spacing = 1.0
            cp.paragraph_format.space_before = Pt(2)
            cp.paragraph_format.space_after = Pt(2)
            cp.paragraph_format.keep_with_next = r == 0
            add_runs(cp, value, size=SMALL_SIZE)
            edges = ["top", "bottom"] if r == 0 else []
            if r == len(rows):
                edges.append("bottom")
            set_borders(cell, edges)
    if note:
        p = paragraph(align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, spacing=1.0)
        p.paragraph_format.space_before = Pt(4)
        add_runs(p, "*Nota.* " + note, size=SMALL_SIZE)
    paragraph(spacing=1.0)


add_page_number(section)

for _ in range(3):
    paragraph(align=WD_ALIGN_PARAGRAPH.CENTER)
title(TITLE)
paragraph(align=WD_ALIGN_PARAGRAPH.CENTER)
for line in ["Hugo Daniel Barillas (23556), Esteban Cárcamo (23016) y Ernesto Ascencio (23009)",
             "Departamento de Ciencias de la Computación, Universidad del Valle de Guatemala",
             "CC3084 Data Science, Sección 20",
             "Msc. Lynette García",
             "15 de octubre de 2026"]:
    paragraph(line, align=WD_ALIGN_PARAGRAPH.CENTER)
paragraph("Laboratorio 9: Visualización estática (avance)", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)

title(TITLE)
paragraph("La infografía responde una sola pregunta para un directivo de INGUAT que no es estadístico: "
          "¿qué enseñan 17 años de datos migratorios sobre el turismo en Guatemala y qué debemos anticipar? "
          "Todas las cifras salen del Laboratorio 1 del grupo (Barillas et al., 2026), sin recalcular nada "
          "fuera de ese análisis.")

heading("Orden y recorrido de lectura")
paragraph("La página se lee de arriba hacia abajo, en un patrón Z dentro de cada fila de dos columnas "
          "(Figura 1). El orden va de lo general a lo accionable: contexto (titular y KPI), historia "
          "(2009–2026), patrones (estacionalidad y comparación de series), pronóstico y, al final, qué hacer. "
          "Los KPI van arriba y en el mayor tamaño porque el tamaño y el color se perciben de forma "
          "preatencional, antes de leer (Ware, 2012).")

p = paragraph("Figura 1", bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, spacing=1.0)
p.paragraph_format.space_before = Pt(12)
p.paragraph_format.space_after = Pt(6)
p.paragraph_format.keep_with_next = True
p = paragraph("Boceto de la página (11 × 17 in) y paleta de color", italic=True,
              align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, spacing=1.0)
p.paragraph_format.space_after = Pt(6)
p.paragraph_format.keep_with_next = True
p = paragraph(align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.0)
p.add_run().add_picture(figure_path, width=Inches(4.3))
p.paragraph_format.keep_with_next = True
p = paragraph(align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, spacing=1.0)
add_runs(p, "*Nota.* La flecha indica el recorrido de lectura. Elaboración propia.", size=SMALL_SIZE)
p.paragraph_format.space_after = Pt(12)

doc.save(output_path)
