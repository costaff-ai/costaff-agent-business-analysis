import json
import pytest
from tools.analysis import analyze_data


def _parse(data) -> dict:
    return json.loads(analyze_data(json.dumps(data)))


# ── series format ──────────────────────────────────────────────────────────────

def test_series_basic_stats():
    s = _parse({"series": [1, 2, 3, 4, 5]})["series"]
    assert s["count"] == 5
    assert s["min"] == 1.0
    assert s["max"] == 5.0
    assert s["mean"] == 3.0
    assert s["median"] == 3.0
    assert s["std"] > 0


def test_series_upward_trend():
    assert _parse({"series": [1, 2, 3, 4, 5]})["series"]["trend"] == "upward"


def test_series_downward_trend():
    assert _parse({"series": [5, 4, 3, 2, 1]})["series"]["trend"] == "downward"


def test_series_flat_trend():
    assert _parse({"series": [7, 7, 7]})["series"]["trend"] == "flat"


def test_series_single_element():
    s = _parse({"series": [42]})["series"]
    assert s["count"] == 1
    assert s["min"] == s["max"] == s["mean"] == 42.0


def test_series_scientific_notation():
    s = _parse({"series": [1e3, 2e3, 3e3]})["series"]
    assert s["min"] == 1000.0
    assert s["max"] == 3000.0


# ── labels + values format ────────────────────────────────────────────────────

def test_labeled_values_stats():
    s = _parse({"labels": ["A", "B", "C"], "values": [10, 30, 20]})["values"]
    assert s["min"] == 10.0
    assert s["max"] == 30.0
    assert s["mean"] == 20.0


def test_labeled_values_top_bottom():
    s = _parse({"labels": ["A", "B", "C", "D"], "values": [10, 40, 20, 30]})["values"]
    assert "top3" in s
    assert "bottom3" in s
    assert s["top3"][-1] == "B"   # highest value
    assert s["bottom3"][0] == "A"  # lowest value


# ── records / tabular format (from read_csv) ──────────────────────────────────

def test_records_tabular():
    records = [
        {"price": 100, "qty": 5},
        {"price": 200, "qty": 3},
        {"price": 150, "qty": 8},
    ]
    result = _parse({"records": records})
    assert "price" in result
    assert "qty" in result
    assert result["price"]["min"] == 100.0
    assert result["price"]["max"] == 200.0
    assert result["qty"]["mean"] == pytest.approx(16 / 3, rel=1e-4)


def test_records_skips_non_numeric_columns():
    records = [{"name": "alice", "score": 90}, {"name": "bob", "score": 85}]
    result = _parse({"records": records})
    # "name" column has no numeric values → should be absent
    assert "name" not in result
    assert "score" in result


# ── edge cases ────────────────────────────────────────────────────────────────

def test_filters_non_numeric_values():
    s = _parse({"series": [1, "N/A", None, "—", 5]})["series"]
    assert s["count"] == 2
    assert s["min"] == 1.0
    assert s["max"] == 5.0


def test_empty_series_returns_empty():
    assert _parse({"series": []}) == {}


def test_empty_records_returns_empty():
    assert _parse({"records": []}) == {}


def test_invalid_json_returns_error():
    result = analyze_data("this is not json")
    assert result.startswith("[ERROR]")
