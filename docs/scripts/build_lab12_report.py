import json
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
PAGE = "lab12_datos_observados"
LINE = "lab12_v1_evolucion"
RANKING = "lab12_v2_ranking"
GROUP = "lab12_grupo"
YEAR = "lab12_anio"
THEME = "tema_observatorio"


def field(table, name, kind="Column"):
    return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def literal(value):
    if isinstance(value, str):
        value = "'" + value.replace("'", "''") + "'"
    elif isinstance(value, bool):
        value = str(value).lower()
    else:
        value = str(value) + "D"
    return {"expr": {"Literal": {"Value": value}}}


def color(value):
    return {"solid": {"color": literal(value)}}


def projection(table, name, kind="Column", **options):
    return {
        "field": field(table, name, kind),
        "queryRef": f"{table}.{name}",
        "nativeQueryRef": name,
        **options,
    }


def categorical_filter(name, table, column, values):
    expression = field(table, column)
    condition_field = field(table, column)
    condition_field["Column"]["Expression"]["SourceRef"] = {"Source": "s"}
    return {
        "name": name,
        "field": expression,
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "s", "Entity": table, "Type": 0}],
            "Where": [{
                "Condition": {
                    "In": {
                        "Expressions": [condition_field],
                        "Values": [[literal(value)["expr"]] for value in values],
                    }
                }
            }],
        },
    }


def visual(name, visual_type, title, position, roles=None):
    result = {
        "$schema": SCHEMA + "visualContainer/2.7.0/schema.json",
        "name": name,
        "position": {
            "x": position[0], "y": position[1], "width": position[2],
            "height": position[3], "z": position[4], "tabOrder": position[4],
        },
        "visual": {
            "visualType": visual_type,
            "drillFilterOtherVisuals": False,
            "visualContainerObjects": {
                "title": [{"properties": {
                    "show": literal(True), "text": literal(title),
                    "fontFamily": literal("Arial"), "fontSize": literal(14),
                    "fontColor": color("#1B2733"), "titleWrap": literal(True),
                }}],
                "background": [{"properties": {
                    "show": literal(True), "color": color("#FFFFFF"),
                    "transparency": literal(0),
                }}],
                "general": [{"properties": {"altText": literal(title)}}],
            },
        },
    }
    if roles is not None:
        result["visual"]["query"] = {
            "queryState": {role: {"projections": items} for role, items in roles.items()}
        }
    return result


def definitions():
    line = visual(
        LINE, "lineChart", "V1 · ¿Cómo ha evolucionado el ingreso de viajeros?",
        (24, 150, 720, 500, 2),
        {
            "Category": [
                projection("Calendario", name, active=index == 0)
                for index, name in enumerate(["Año", "Trimestre", "Mes"])
            ],
            "Y": [projection("Medidas", "Viajeros serie", "Measure", format="#,0")],
        },
    )
    line["visual"]["objects"] = {
        "dataPoint": [{"properties": {"defaultColor": color("#1F4E79")}}],
        "categoryAxis": [{"properties": {"fontSize": literal(10)}}],
        "valueAxis": [{"properties": {"fontSize": literal(10)}}],
    }
    line["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"] = {
        "expr": field("Medidas", "Titulo V1", "Measure")
    }
    line["visual"]["visualContainerObjects"]["subTitle"] = [{"properties": {
        "show": literal(True),
        "text": literal("V1 · Evolución de viajeros. Clic en V2: serie seleccionada. Sin selección: Total."),
        "fontSize": literal(10),
    }}]
    line["visual"]["query"]["sortDefinition"] = {
        "sort": [{"field": field("Calendario", "Año"), "direction": "Ascending"}]
    }
    ranking = visual(
        RANKING, "clusteredBarChart", "V2 · ¿Qué vías o países concentran más viajeros?",
        (768, 150, 488, 500, 3),
        {
            "Category": [projection("DimSerie", "nombre")],
            "Y": [projection("Medidas", "Viajeros", "Measure", format="#,0")],
        },
    )
    ranking["visual"]["objects"] = {
        "dataPoint": [{"properties": {"defaultColor": color("#1F4E79")}}],
        "labels": [{"properties": {
            "show": literal(True), "fontSize": literal(10), "labelDisplayUnits": literal(1),
        }}],
        "categoryAxis": [{"properties": {"fontSize": literal(10)}}],
        "valueAxis": [{"properties": {"fontSize": literal(10)}}],
    }
    ranking["visual"]["query"]["sortDefinition"] = {
        "sort": [{"field": field("Medidas", "Viajeros", "Measure"), "direction": "Descending"}]
    }
    ranking["filterConfig"] = {"filters": [
        categorical_filter("lab12_ranking_sin_total", "DimSerie", "grupo", [
            "Vía de ingreso", "País de residencia",
        ])
    ]}
    group = visual(
        GROUP, "slicer", "Grupo del ranking", (24, 24, 400, 100, 0),
        {"Values": [projection("DimSerie", "grupo")]},
    )
    group["visual"]["objects"] = {
        "data": [{"properties": {"mode": literal("Dropdown")}}],
        "selection": [{"properties": {
            "singleSelect": literal(True), "selectAllCheckboxEnabled": literal(False),
        }}],
        "general": [{"properties": {"filter": {
            "filter": categorical_filter(
                "seleccion_grupo", "DimSerie", "grupo", ["Vía de ingreso"]
            )["filter"]
        }}}],
    }
    group["filterConfig"] = {"filters": [
        categorical_filter("lab12_grupos_disponibles", "DimSerie", "grupo", [
            "Vía de ingreso", "País de residencia",
        ])
    ]}
    year = visual(
        YEAR, "slicer", "Año del ranking", (448, 24, 296, 100, 1),
        {"Values": [projection("Calendario", "Año")]},
    )
    year["visual"]["objects"] = {
        "data": [{"properties": {"mode": literal("Dropdown")}}],
        "selection": [{"properties": {
            "singleSelect": literal(True), "selectAllCheckboxEnabled": literal(False),
        }}],
        "general": [{"properties": {"filter": {
            "filter": categorical_filter("seleccion_anio", "Calendario", "Año", [2025])["filter"]
        }}}],
    }
    page = {
        "$schema": SCHEMA + "page/2.1.0/schema.json",
        "name": PAGE, "displayName": "Datos observados",
        "displayOption": "FitToPage", "height": 720, "width": 1280,
        "visualInteractions": [
            {"source": RANKING, "target": LINE, "type": "DataFilter"},
            {"source": GROUP, "target": RANKING, "type": "DataFilter"},
            {"source": YEAR, "target": RANKING, "type": "DataFilter"},
            *[
                {"source": source, "target": target, "type": "NoFilter"}
                for source, target in [
                    (GROUP, LINE), (YEAR, LINE), (GROUP, YEAR), (YEAR, GROUP),
                    (LINE, RANKING), (LINE, GROUP), (LINE, YEAR),
                    (RANKING, GROUP), (RANKING, YEAR),
                ]
            ],
        ],
    }
    prefix = f"Report/definition/pages/{PAGE}"
    return {
        f"{prefix}/page.json": page,
        **{
            f"{prefix}/visuals/{item['name']}/visual.json": item
            for item in [line, ranking, group, year]
        },
    }


def build_report(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("El archivo PBIX de entrada está dañado.")
        entries = {item.filename: (item, archive.read(item)) for item in archive.infolist()}
    updates = definitions()
    report = json.loads(entries["Report/definition/report.json"][1])
    report["themeCollection"]["customTheme"] = {
        "name": THEME, "type": "RegisteredResources",
        "reportVersionAtImport": {"visual": "2.7.0", "page": "2.1.0", "report": "3.3.0"},
    }
    report["resourcePackages"] = [
        package for package in report["resourcePackages"] if package["name"] != "RegisteredResources"
    ] + [{
        "name": "RegisteredResources", "type": "RegisteredResources",
        "items": [{"name": THEME, "path": THEME + ".json", "type": "CustomTheme"}],
    }]
    updates["Report/definition/report.json"] = report
    pages = json.loads(entries["Report/definition/pages/pages.json"][1])
    pages["pageOrder"] = [PAGE] + [name for name in pages["pageOrder"] if name != PAGE]
    pages["activePageName"] = PAGE
    updates["Report/definition/pages/pages.json"] = pages
    for name, (_, content) in entries.items():
        if name.endswith("/page.json"):
            old_page = json.loads(content)
            if old_page["displayName"] == "Control":
                old_page["visibility"] = "HiddenInViewMode"
                updates[name] = old_page
    changes = {
        name: json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
        for name, value in updates.items()
    }
    changes[f"Report/StaticResources/RegisteredResources/{THEME}.json"] = (
        ROOT / "powerbi/tema_observatorio.json"
    ).read_bytes()
    ElementTree.register_namespace("", "http://schemas.openxmlformats.org/package/2006/content-types")
    content_types = ElementTree.fromstring(entries["[Content_Types].xml"][1])
    for item in list(content_types):
        if item.get("PartName") == "/SecurityBindings":
            content_types.remove(item)
    changes["[Content_Types].xml"] = ElementTree.tostring(
        content_types, encoding="utf-8", xml_declaration=True
    )
    backup = ROOT / "TEMP/observatorio_turismo_antes_hugo.pbix"
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    temporary = path.with_suffix(".tmp.pbix")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, (info, content) in entries.items():
                if name != "SecurityBindings":
                    archive.writestr(info, changes.pop(name, content))
            for name, content in changes.items():
                archive.writestr(name, content)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError("El archivo PBIX generado está dañado.")
            if archive.read("DataModel") != entries["DataModel"][1]:
                raise ValueError("El modelo de datos no debe modificarse.")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


if __name__ == "__main__":
    print(build_report(ROOT / "powerbi/observatorio_turismo.pbix"))
