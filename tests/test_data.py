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


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
    print("ok")
