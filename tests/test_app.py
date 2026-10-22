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


def test_responsive_graphs_reserve_height_in_the_layout():
    sections = app.layout.children[1].children
    for section, identifier, height in [
        (sections[0], "time-series-graph", "420px"),
        (sections[1], "ranking-graph", "360px"),
    ]:
        graph = next(child for child in section.children if getattr(child, "id", None) == identifier)
        assert graph.responsive is True
        assert graph.style["height"] == height


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
    print("ok")
