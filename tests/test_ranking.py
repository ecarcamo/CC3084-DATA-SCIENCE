import pandas as pd
from dash import no_update

from app import data
from app.components import ranking
from app.theme import COLORS


def test_ranking_keeps_comparison_groups_separate():
    for category in ranking.CATEGORIES:
        frame = ranking.build_ranking(category, 2025)
        assert len(frame) == 3
        assert set(ranking.LABELS.loc[frame["key"], "categoria"]) == {category}
        assert "total" not in frame["key"].values
        assert frame["travelers"].is_monotonic_decreasing


def test_ranking_totals_match_source():
    frame = ranking.build_ranking("Vía de ingreso", 2025).set_index("key")
    source = data.load_series("via_aerea")
    assert frame.loc["via_aerea", "travelers"] == source[source.index.year == 2025].sum()
    assert frame["months"].eq(12).all()


def test_partial_year_is_labeled():
    frame = ranking.build_ranking("Vía de ingreso", 2026)
    assert frame["months"].eq(6).all()
    figure, note = ranking.build_figure("Vía de ingreso", 2026, "total")
    assert len(figure.data) == 1
    assert "periodo parcial, 6 meses" in note
    assert "No equivale a un año completo" in note


def test_empty_ranking_shows_message():
    figure, note = ranking.build_figure("Vía de ingreso", 2008, "total")
    assert not figure.data
    assert figure.layout.annotations[0].text == ranking.EMPTY_MESSAGE
    assert note == ranking.EMPTY_MESSAGE


def test_selected_bar_has_color_and_noncolor_cues():
    frame = ranking.build_ranking("Vía de ingreso", 2025)
    figure, note = ranking.build_figure("Vía de ingreso", 2025, "via_aerea")
    position = list(frame["key"]).index("via_aerea")
    assert figure.data[0].marker.color[position] == COLORS["highlight"]
    assert figure.data[0].marker.line.width[position] == 3
    assert "Selección: Vía Aérea" in note


def test_click_selects_only_a_series_from_the_current_group():
    click = {"points": [{"customdata": "via_aerea"}]}
    assert ranking.select_series(click, "Vía de ingreso") == "via_aerea"
    assert ranking.select_series(click, "País de residencia") is no_update
    assert ranking.select_series(None, "Vía de ingreso") is no_update
    assert ranking.select_series({"points": []}, "Vía de ingreso") is no_update
    assert ranking.select_series({"points": [{}]}, "Vía de ingreso") is no_update


def test_complete_year_is_labeled_and_excludes_unrelated_selection():
    figure, note = ranking.build_figure("País de residencia", 2025, "via_aerea")
    assert "año completo, 12 meses" in note
    assert "Selección:" not in note
    assert set(figure.data[0].marker.color) == {COLORS["observed"]}


def test_all_available_years_build_both_groups():
    for year in ranking.YEARS:
        for category in ranking.CATEGORIES:
            frame = ranking.build_ranking(category, year)
            assert len(frame) == 3
            assert pd.notna(frame["travelers"]).all()


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
    print("ok")
