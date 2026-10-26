from app import main
from app.main import app


def test_dashboard_serves_layout_and_linked_callbacks():
    client = app.server.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert '<html lang="es">' in response.get_data(as_text=True)
    layout = client.get("/_dash-layout")
    assert layout.status_code == 200
    body = layout.get_data(as_text=True)
    for identifier in ["time-series-graph", "ranking-graph", "ranking-year", "ranking-category"]:
        assert identifier in body
    dependencies = client.get("/_dash-dependencies").get_json()
    selection = next(item for item in dependencies if item["output"] == "series-selector.value")
    assert selection["inputs"] == [{"id": "ranking-graph", "property": "clickData"}]


def test_bar_click_updates_the_series_selector_over_http():
    client = app.server.test_client()
    response = client.post("/_dash-update-component", json={
        "output": "series-selector.value",
        "outputs": {"id": "series-selector", "property": "value"},
        "changedPropIds": ["ranking-graph.clickData"],
        "inputs": [{
            "id": "ranking-graph", "property": "clickData",
            "value": {"points": [{"customdata": "via_aerea"}]},
        }],
        "state": [{"id": "ranking-category", "property": "value", "value": "Vía de ingreso"}],
    })
    assert response.status_code == 200
    assert response.get_json()["response"]["series-selector"]["value"] == "via_aerea"


def test_selected_series_updates_the_temporal_figure_over_http():
    client = app.server.test_client()
    output = "..time-series-graph.figure...granularity-note.children.."
    response = client.post("/_dash-update-component", json={
        "output": output,
        "outputs": [
            {"id": "time-series-graph", "property": "figure"},
            {"id": "granularity-note", "property": "children"},
        ],
        "changedPropIds": ["series-selector.value"],
        "inputs": [
            {"id": "series-selector", "property": "value", "value": "via_aerea"},
            {"id": "granularity-selector", "property": "value", "value": "month"},
            {"id": "date-range", "property": "start_date", "value": "2009-01-01"},
            {"id": "date-range", "property": "end_date", "value": "2026-06-30"},
        ],
        "state": [],
    })
    assert response.status_code == 200
    figure = response.get_json()["response"]["time-series-graph"]["figure"]
    assert figure["data"][0]["name"] == "Vía Aérea"


def find(component, identifier):
    if getattr(component, "id", None) == identifier:
        return component
    children = getattr(component, "children", None)
    for child in children if isinstance(children, list) else [children]:
        found = find(child, identifier) if child is not None and not isinstance(child, str) else None
        if found is not None:
            return found
    return None


def identifiers(component):
    found = [component.id] if getattr(component, "id", None) else []
    children = getattr(component, "children", None)
    for child in children if isinstance(children, list) else [children]:
        if child is not None and not isinstance(child, str):
            found.extend(identifiers(child))
    return found


def visibility_request(observed, models):
    outputs = [{"id": section, "property": "style"} for section in main.SECTIONS]
    outputs += [{"id": f"nav-{section}", "property": "style"} for section in main.SECTIONS]
    outputs += [{"id": identifier, "property": "style"}
                for identifier in ["no-charts-message", "ranking-series-link", "ranking-series-hidden"]]
    return {
        "output": ".." + "...".join(f"{item['id']}.style" for item in outputs) + "..",
        "outputs": outputs,
        "changedPropIds": ["visible-observed.value"],
        "inputs": [
            {"id": "visible-observed", "property": "value", "value": observed},
            {"id": "visible-models", "property": "value", "value": models},
        ],
        "state": [],
    }


def test_responsive_graphs_reserve_height_in_the_layout():
    for identifier, height in [
        ("time-series-graph", "420px"), ("ranking-graph", "360px"), ("seasonality-graph", "520px"),
        ("annual-graph", "420px"), ("yoy-graph", "420px"), ("predictions-graph", "460px"),
        ("errors-graph", "420px"), ("deviations-graph", "420px"),
    ]:
        graph = find(app.layout, identifier)
        assert graph.responsive is True
        assert graph.style["height"] == height


def test_eight_charts_are_integrated_once_with_unique_ids():
    ids = identifiers(app.layout)
    assert len(ids) == len(set(ids))
    assert len(main.CHARTS) == 8
    for section in main.SECTIONS:
        assert find(app.layout, section) is not None
        assert find(app.layout, f"nav-{section}") is not None
    dependencies = app.server.test_client().get("/_dash-dependencies").get_json()
    outputs = [item["output"] for item in dependencies]
    assert len(outputs) == len(set(outputs))
    for output in ["yoy-graph.figure", "seasonality-graph.figure", "annual-graph.figure",
                   "predictions-graph.figure", "errors-graph.figure", "deviations-graph.figure"]:
        assert any(output in item for item in outputs)


def test_hiding_charts_keeps_them_mounted_and_explains_the_hidden_series():
    client = app.server.test_client()
    observed = [section for section in main.SECTIONS[:5] if section != "evolution"]
    response = client.post("/_dash-update-component", json=visibility_request(observed, ["model-errors"]))
    assert response.status_code == 200
    styles = response.get_json()["response"]
    assert styles["evolution"]["style"] == main.HIDDEN
    assert styles["predictions"]["style"] == main.HIDDEN
    assert styles["model-errors"]["style"] == main.SHOWN
    assert styles["nav-evolution"]["style"] == main.HIDDEN
    assert styles["ranking-series-link"]["style"] == main.HIDDEN
    assert styles["ranking-series-hidden"]["style"] == main.SHOWN
    assert styles["no-charts-message"]["style"] == main.HIDDEN
    assert find(app.layout, "time-series-graph") is not None
    assert test_bar_click_updates_the_series_selector_over_http() is None


def test_empty_selection_shows_message():
    styles = main.visibility([], [])
    assert styles[:len(main.SECTIONS)] == [main.HIDDEN] * len(main.SECTIONS)
    assert styles[2 * len(main.SECTIONS)] == main.SHOWN


def test_show_series_button_restores_g1_without_losing_other_choices():
    client = app.server.test_client()
    response = client.post("/_dash-update-component", json={
        "output": "visible-observed.value",
        "outputs": {"id": "visible-observed", "property": "value"},
        "changedPropIds": ["ranking-show-series.n_clicks"],
        "inputs": [{"id": "ranking-show-series", "property": "n_clicks", "value": 1}],
        "state": [{"id": "visible-observed", "property": "value", "value": ["ranking", "year-over-year"]}],
    })
    assert response.status_code == 200
    value = response.get_json()["response"]["visible-observed"]["value"]
    assert value == ["evolution", "ranking", "year-over-year"]


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
    print("ok")
