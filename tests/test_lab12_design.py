import json
import zipfile
from pathlib import Path

from PIL import Image, ImageColor

from docs.scripts import build_lab12_report
from docs.scripts.build_lab12_report import GROUP, LINE, PAGE, RANKING, YEAR, definitions
from docs.scripts.draw_lab12_wireframe import COLORS, SIZE, draw_wireframe
from docs.scripts.lab12_final_pages import HOME, PAGES, SEASONAL, DETAIL, V3, V4, V5, DATES

ROOT = Path(__file__).resolve().parents[1]


def contrast(first, second):
    def luminance(value):
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return sum(channel * weight for channel, weight in zip(linear, [0.2126, 0.7152, 0.0722]))

    light, dark = sorted([luminance(first), luminance(second)], reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_theme_preserves_palette_and_readable_text():
    theme = json.loads((ROOT / "powerbi/tema_observatorio.json").read_text(encoding="utf-8"))
    assert theme["dataColors"] == [
        "#1F4E79", "#A65E16", "#6B3A0C", "#C46A12",
        "#8A4B12", "#D07A1E", "#20745A", "#B3261E",
    ]
    assert theme["minimum"] == "#E7EFF6"
    assert theme["maximum"] == "#1F4E79"
    for text_class in theme["textClasses"].values():
        assert text_class["fontFace"] == "Arial"
        assert text_class["fontSize"] >= 10
        for background in ["#FFFFFF", "#F4F6F8"]:
            assert contrast(text_class["color"], background) >= 4.5


def test_report_links_ranking_to_history_without_slicer_side_effects():
    files = definitions()
    page = files[f"Report/definition/pages/{PAGE}/page.json"]
    interactions = {
        (item["source"], item["target"]): item["type"]
        for item in page["visualInteractions"]
    }
    assert interactions[RANKING, LINE] == "DataFilter"
    for slicer in [GROUP, YEAR]:
        assert interactions[slicer, LINE] == "NoFilter"
        assert interactions[slicer, RANKING] == "DataFilter"
    prefix = f"Report/definition/pages/{PAGE}/visuals"
    line = files[f"{prefix}/{LINE}/visual.json"]["visual"]
    categories = line["query"]["queryState"]["Category"]["projections"]
    assert [item["field"]["Column"]["Property"] for item in categories] == ["Año", "Trimestre", "Mes"]
    assert line["query"]["queryState"]["Y"]["projections"][0]["queryRef"] == "Medidas.Viajeros serie"
    assert line["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Measure"]["Property"] == "Titulo V1"
    ranking = files[f"{prefix}/{RANKING}/visual.json"]
    assert ranking["visual"]["query"]["sortDefinition"]["sort"][0]["direction"] == "Descending"
    allowed = ranking["filterConfig"]["filters"][0]["filter"]["Where"][0]["Condition"]["In"]["Values"]
    assert allowed == [
        [{"Literal": {"Value": "'Vía de ingreso'"}}],
        [{"Literal": {"Value": "'País de residencia'"}}],
    ]
    group = files[f"{prefix}/{GROUP}/visual.json"]["visual"]
    assert group["objects"]["selection"][0]["properties"]["singleSelect"]["expr"]["Literal"]["Value"] == "true"


def test_saved_report_contains_the_definitions_and_theme():
    def assert_contains(actual, expected):
        if isinstance(expected, dict):
            for key, value in expected.items():
                if key not in {"$schema", "drillFilterOtherVisuals"}:
                    if key == "visualInteractions" and not value:
                        assert not actual.get(key, [])
                    elif key == "version" and "sections" in expected:
                        assert actual[key].startswith("1.")
                    elif key == "options":
                        assert_contains({**dict.fromkeys(value, False), **actual.get(key, {})}, value)
                    elif key == "filters" and value == {"byExpr": []}:
                        assert_contains(actual.get(key, value), value)
                    elif key == "acceptsFilterContext" and value == "Default":
                        assert actual.get(key, "Default") == value
                    else:
                        assert_contains(actual[key], value)
        elif isinstance(expected, list):
            if expected and all(isinstance(item, dict) and "name" in item for item in expected):
                actual_by_name = {item["name"]: item for item in actual}
                expected_names = {item["name"] for item in expected}
                assert all(not item.get("filter") for item in actual if item["name"] not in expected_names)
                for item in expected:
                    assert_contains(actual_by_name[item["name"]], item)
            else:
                assert len(actual) == len(expected)
                for actual_item, expected_item in zip(actual, expected):
                    assert_contains(actual_item, expected_item)
        else:
            assert actual == expected

    with zipfile.ZipFile(ROOT / "powerbi/observatorio_turismo.pbix") as archive:
        assert archive.testzip() is None
        assert b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"' in archive.read("[Content_Types].xml")
        for name, value in definitions().items():
            assert_contains(json.loads(archive.read(name)), value)
        pages = json.loads(archive.read("Report/definition/pages/pages.json"))
        assert pages["activePageName"] == HOME
        assert pages["pageOrder"][:5] == list(PAGES)
        embedded_theme = archive.read("Report/StaticResources/RegisteredResources/tema_observatorio.json")
        assert json.loads(embedded_theme) == json.loads((ROOT / "powerbi/tema_observatorio.json").read_bytes())
        control = json.loads(archive.read("Report/definition/pages/08325135a3a754e1a190/page.json"))
        assert control["visibility"] == "HiddenInViewMode"


def test_build_report_preserves_the_model_and_first_backup(tmp_path, monkeypatch):
    original = (ROOT / "powerbi/observatorio_turismo.pbix").read_bytes()
    source = tmp_path / "report.pbix"
    source.write_bytes(original)
    theme = tmp_path / "powerbi/tema_observatorio.json"
    theme.parent.mkdir()
    theme.write_bytes((ROOT / "powerbi/tema_observatorio.json").read_bytes())
    monkeypatch.setattr(build_lab12_report, "ROOT", tmp_path)
    for _ in range(2):
        assert build_lab12_report.build_report(source) == source
        assert (tmp_path / "TEMP/observatorio_turismo_antes_hugo.pbix").read_bytes() == original
        with zipfile.ZipFile(source) as generated:
            assert generated.testzip() is None
            with zipfile.ZipFile(ROOT / "powerbi/observatorio_turismo.pbix") as reference:
                assert generated.read("DataModel") == reference.read("DataModel")


def test_wireframe_has_the_expected_palette_and_dimensions(tmp_path):
    output = draw_wireframe(tmp_path / "boceto.png")
    with Image.open(output) as image:
        assert image.size == SIZE
        assert image.mode == "RGB"
        assert image.getpixel((0, 0)) == ImageColor.getrgb(COLORS["background"])
        assert image.getpixel((65, 230)) == ImageColor.getrgb(COLORS["selection"])


def test_final_pages_have_active_navigation_and_reset_bookmarks():
    files = definitions()
    for page in PAGES:
        prefix = f"Report/definition/pages/{page}/visuals"
        for target in PAGES:
            item = files[f"{prefix}/nav_{target}/visual.json"]["visual"]
            action = item["visualContainerObjects"]["visualLink"][0]["properties"]
            assert action["navigationSection"] == build_lab12_report.literal(target)
            expected_color = "#20745A" if page == target else "#FFFFFF"
            assert item["objects"]["fill"][0]["properties"]["show"] == build_lab12_report.literal(True)
            for state in item["objects"]["fill"][1:]:
                assert state["properties"]["fillColor"] == build_lab12_report.color(expected_color)
        bookmark = files[f"Report/definition/bookmarks/inicial_{page}.bookmark.json"]
        assert bookmark["explorationState"]["activeSection"] == page
        assert all(value is False for value in bookmark["options"].values())
        for name, state in bookmark["explorationState"]["sections"][page]["visualContainers"].items():
            assert state["highlight"]["selection"] == []
            source = files[f"{prefix}/{name}/visual.json"]
            for entry in source.get("filterConfig", {}).get("filters", []):
                if "filter" in entry:
                    assert entry["howCreated"] == "User"
                    assert any(saved["filter"] == entry["filter"] and saved["howCreated"] == 1
                               for saved in state["filters"]["byExpr"])
        reset = files[f"{prefix}/reset_{page}/visual.json"]["visual"]
        assert reset["visualContainerObjects"]["visualLink"][0]["properties"]["bookmark"] == build_lab12_report.literal("inicial_" + page)


def test_seasonal_visuals_use_shared_slicers_and_no_mixed_totals():
    files = definitions()
    prefix = f"Report/definition/pages/{SEASONAL}"
    matrix = files[f"{prefix}/visuals/{V3}/visual.json"]["visual"]
    assert matrix["visualType"] == "pivotTable"
    roles = matrix["query"]["queryState"]
    assert roles["Rows"]["projections"][0]["queryRef"] == "Calendario.Año"
    assert roles["Columns"]["projections"][0]["queryRef"] == "Calendario.Mes"
    assert matrix["objects"]["subTotals"][0]["properties"] == {
        "rowSubtotals": build_lab12_report.literal(False),
        "columnSubtotals": build_lab12_report.literal(False),
    }
    annual = files[f"{prefix}/visuals/{V4}/visual.json"]["visual"]
    assert annual["query"]["queryState"]["Y"]["projections"][0]["queryRef"] == "Medidas.Total año completo"
    interactions = {(i["source"], i["target"]): i["type"] for i in files[f"{prefix}/page.json"]["visualInteractions"]}
    for source in ["serie_estacional", "anios_estacional"]:
        for target in [V3, V4, "nota_v3", "nota_v4", "mensaje_v3", "mensaje_v4"]:
            assert interactions[source, target] == "DataFilter"
    assert interactions[V3, V4] == "NoFilter"
    bookmark = files[f"Report/definition/bookmarks/inicial_{PAGE}.bookmark.json"]
    states = bookmark["explorationState"]["sections"][PAGE]["visualContainers"]
    assert states[RANKING]["singleVisual"]["orderBy"] == [{
        "Expression": build_lab12_report.field("Medidas", "Viajeros", "Measure"), "Direction": 2,
    }]
    assert states[V5]["singleVisual"]["isDrillDisabled"] is True
    ranking = files[f"Report/definition/pages/{PAGE}/visuals/{RANKING}/visual.json"]
    fixed_filter = ranking["filterConfig"]["filters"][0]
    reset_filter = states[RANKING]["filters"]["byExpr"][0]
    assert reset_filter["filter"] == fixed_filter["filter"]
    assert reset_filter["expression"] == fixed_filter["field"]
    assert reset_filter["howCreated"] == 1
    assert fixed_filter["howCreated"] == "User"


def test_yoy_date_slicer_is_isolated_and_ranking_changes_its_series():
    files = definitions()
    prefix = f"Report/definition/pages/{PAGE}"
    interactions = {(i["source"], i["target"]): i["type"] for i in files[f"{prefix}/page.json"]["visualInteractions"]}
    assert interactions[RANKING, V5] == "DataFilter"
    assert interactions[DATES, V5] == "DataFilter"
    for target in [LINE, RANKING, GROUP, YEAR]:
        assert interactions[DATES, target] == "NoFilter"
    for source in [GROUP, YEAR]:
        assert interactions[source, V5] == "NoFilter"
    yoy = files[f"{prefix}/visuals/{V5}/visual.json"]["visual"]
    assert [p["queryRef"] for p in yoy["query"]["queryState"]["Category"]["projections"]] == ["Calendario.Año", "Calendario.Mes"]
    assert yoy["objects"]["y1AxisReferenceLine"][0]["properties"]["value"] == build_lab12_report.literal(0)
    assert "start" not in yoy["objects"]["valueAxis"][0]["properties"]
    assert all(value == build_lab12_report.literal(False)
               for value in yoy["visualContainerObjects"]["visualHeader"][0]["properties"].values())
    assert yoy["visualContainerObjects"]["subTitle"][0]["properties"]["text"]["expr"] == build_lab12_report.field("Medidas", "Serie elegida", "Measure")
    message = files[f"{prefix}/visuals/mensaje_v5/visual.json"]["visual"]
    assert all(value == build_lab12_report.literal(4)
               for value in message["visualContainerObjects"]["padding"][0]["properties"].values())


def test_detail_page_binds_series_and_has_back_action():
    files = definitions()
    prefix = f"Report/definition/pages/{DETAIL}"
    page = files[f"{prefix}/page.json"]
    assert page["type"] == "Drillthrough"
    assert page["pageBinding"]["parameters"][0]["fieldExpr"] == build_lab12_report.field("DimSerie", "nombre")
    assert page["pageBinding"]["acceptsFilterContext"] == "Default"
    assert page["filterConfig"]["filters"][0]["howCreated"] == "Drillthrough"
    back = files[f"{prefix}/visuals/atras_detalle/visual.json"]["visual"]
    assert back["visualContainerObjects"]["visualLink"][0]["properties"]["type"] == build_lab12_report.literal("Back")


def test_required_measures_and_empty_selection_messages_are_reproducible():
    measures = json.loads((ROOT / "powerbi/medidas_hugo.json").read_text(encoding="utf-8"))
    assert measures["Variación interanual %"]["formatString"] == "0.0 %"
    for number in [3, 4, 5]:
        assert f"Nota V{number}" in measures
        assert f"Mensaje V{number}" in measures
        assert '\"\"' in measures[f"Mensaje V{number}"]["expression"]
    assert "Anterior <> 0" in measures["Variación interanual %"]["expression"]
    assert "= 12" in measures["Total año completo"]["expression"]
    assert "REMOVEFILTERS ( Calendario )" in measures["Total último año completo"]["expression"]
    for name in ["Meses con dato serie", "Meses con variación", "Nota V4"]:
        assert "COALESCE" in measures[name]["expression"]


def test_final_layout_does_not_overlap_or_exceed_canvas():
    files = definitions()
    for page in PAGES:
        prefix = f"Report/definition/pages/{page}/"
        definition = files[prefix + "page.json"]
        positions = [value["position"] for name, value in files.items()
                     if name.startswith(prefix + "visuals/")]
        for index, first in enumerate(positions):
            assert first["x"] >= 0 and first["y"] >= 0
            assert first["x"] + first["width"] <= definition["width"]
            assert first["y"] + first["height"] <= definition["height"]
            for second in positions[index + 1:]:
                overlap_x = min(first["x"] + first["width"], second["x"] + second["width"]) - max(first["x"], second["x"])
                overlap_y = min(first["y"] + first["height"], second["y"] + second["height"]) - max(first["y"], second["y"])
                assert overlap_x <= 0 or overlap_y <= 0
