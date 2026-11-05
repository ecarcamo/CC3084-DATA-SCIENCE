import json
import zipfile
from pathlib import Path

from PIL import Image, ImageColor

from docs.scripts import build_lab12_report
from docs.scripts.build_lab12_report import GROUP, LINE, PAGE, RANKING, YEAR, definitions
from docs.scripts.draw_lab12_wireframe import COLORS, SIZE, draw_wireframe

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
        assert pages["activePageName"] == PAGE
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
