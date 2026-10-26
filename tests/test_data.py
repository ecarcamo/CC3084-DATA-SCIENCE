import math

import pandas as pd

from app import data
from app.components import time_series


def test_load_series_covers_full_period():
    series = data.load_series("total")
    assert series.index.min() == pd.Timestamp("2009-01-01")
    assert series.index.max() == pd.Timestamp("2026-06-01")
    assert len(series) == 210


def test_yearly_aggregate_keeps_only_complete_years():
    yearly = data.aggregate(data.load_series("total"), "year")
    assert yearly.index.max() == pd.Timestamp("2025-01-01")
    assert len(yearly) == 17


def test_quarterly_aggregate_keeps_only_complete_quarters():
    quarterly = data.aggregate(data.load_series("total"), "quarter")
    assert quarterly.index.max() == pd.Timestamp("2026-04-01")


def test_empty_selection_shows_message():
    figure = time_series.build_figure("total", "year", "2026-01-01", "2026-06-30")
    assert figure.layout.annotations[0].text == time_series.EMPTY_MESSAGE


def test_every_series_builds_a_figure():
    for key in time_series.LABELS.index:
        figure = time_series.build_figure(key, "month", "2009-01-01", "2026-06-30")
        assert len(figure.data) == 1


def test_yearly_selection_excludes_months_outside_the_date_range():
    figure = time_series.build_figure("total", "year", "2025-01-01", "2025-06-30")
    assert not figure.data
    assert figure.layout.annotations[0].text == time_series.EMPTY_MESSAGE


def test_quarterly_selection_keeps_only_complete_selected_quarters():
    figure = time_series.build_figure("total", "quarter", "2025-02-01", "2025-08-31")
    assert list(figure.data[0].x) == [pd.Timestamp("2025-04-01")]


def test_aggregated_totals_keep_their_unit_and_period_labels():
    monthly = data.load_series("total").loc["2025"]
    quarterly = time_series.build_figure("total", "quarter", "2025-01-01", "2025-12-31")
    yearly = time_series.build_figure("total", "year", "2025-01-01", "2025-12-31")
    assert list(quarterly.data[0].customdata) == [
        "T1 2025 (ene–mar)", "T2 2025 (abr–jun)", "T3 2025 (jul–sep)", "T4 2025 (oct–dic)",
    ]
    assert math.isclose(quarterly.data[0].y[1], monthly.loc["2025-04":"2025-06"].sum())
    assert quarterly.layout.yaxis.title.text == "Viajeros por trimestre"
    assert list(yearly.data[0].customdata) == ["2025"]
    assert math.isclose(yearly.data[0].y[0], monthly.sum())
    assert "viajeros por año" in yearly.data[0].hovertemplate


def test_note_reports_complete_and_incomplete_periods():
    complete = time_series.build_note("total", "year", "2015-01-01", "2020-12-31")
    assert "Todos los años del rango elegido están completos" in complete
    partial_year = time_series.build_note("total", "year", "2009-01-01", "2026-06-30")
    assert "Se omitió 1 año incompleto" in partial_year
    assert "2026, 6 de 12 meses" in partial_year
    partial_quarters = time_series.build_note("total", "quarter", "2025-02-01", "2025-08-31")
    assert "Se omitieron 2 trimestres incompletos" in partial_quarters
    assert "T1 2025 (ene–mar), 2 de 3 meses" in partial_quarters
    assert "T3 2025 (jul–sep), 2 de 3 meses" in partial_quarters
    assert "un mes" in time_series.build_note("total", "month", "2025-01-01", "2025-12-31")


def test_incomplete_periods_count_missing_months():
    series = data.load_series("total").loc["2024-02":"2024-12"].drop(pd.Timestamp("2024-08-01"))
    incomplete = data.incomplete_periods(series, "quarter")
    assert incomplete.to_dict() == {pd.Timestamp("2024-01-01"): 2, pd.Timestamp("2024-07-01"): 2}
    assert data.incomplete_periods(series, "month").empty
    assert list(data.aggregate(series, "quarter").index) == [pd.Timestamp("2024-04-01"), pd.Timestamp("2024-10-01")]


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
    print("ok")
