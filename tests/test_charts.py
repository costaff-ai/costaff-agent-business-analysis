import json
import pytest
from pathlib import Path
from tools.charts import generate_chart


def j(data: dict) -> str:
    return json.dumps(data)


# ── individual chart types ─────────────────────────────────────────────────────

def test_bar_chart(agent_dir):
    data = j({"labels": ["Q1", "Q2", "Q3"], "values": [100, 120, 110]})
    result = generate_chart(data, "bar", "Revenue by Quarter", "tc_bar.png")
    assert result.startswith("[OK]")
    assert (agent_dir / "tc_bar.png").exists()


def test_line_chart(agent_dir):
    data = j({"x": [1, 2, 3, 4, 5], "y": [10, 15, 12, 18, 20]})
    result = generate_chart(data, "line", "Trend Line", "tc_line.png", xlabel="Month", ylabel="Value")
    assert result.startswith("[OK]")
    assert (agent_dir / "tc_line.png").exists()


def test_area_chart(agent_dir):
    data = j({"x": ["Jan", "Feb", "Mar"], "y": [50, 70, 65]})
    result = generate_chart(data, "area", "Area Chart", "tc_area.png")
    assert result.startswith("[OK]")


def test_pie_chart(agent_dir):
    data = j({"labels": ["Electronics", "Clothing", "Food"], "values": [45, 30, 25]})
    result = generate_chart(data, "pie", "Category Share", "tc_pie.png")
    assert result.startswith("[OK]")


def test_scatter_chart(agent_dir):
    data = j({"x": [1, 2, 3, 4, 5], "y": [2, 4, 1, 5, 3]})
    result = generate_chart(data, "scatter", "Scatter Plot", "tc_scatter.png")
    assert result.startswith("[OK]")


def test_scatter_with_point_labels(agent_dir):
    data = j({"x": [1, 2, 3], "y": [3, 1, 2], "labels": ["P1", "P2", "P3"]})
    result = generate_chart(data, "scatter", "Labeled Scatter", "tc_scatter_lbl.png")
    assert result.startswith("[OK]")


def test_histogram_chart(agent_dir):
    import random
    values = [random.gauss(50, 10) for _ in range(200)]
    data = j({"values": values, "bins": 20})
    result = generate_chart(data, "histogram", "Score Distribution", "tc_hist.png")
    assert result.startswith("[OK]")


def test_box_chart(agent_dir):
    data = j({"groups": {
        "GroupA": [10, 12, 11, 14, 9, 13],
        "GroupB": [20, 22, 18, 25, 19, 21],
    }})
    result = generate_chart(data, "box", "Box Plot Comparison", "tc_box.png")
    assert result.startswith("[OK]")


def test_multi_bar_chart(agent_dir):
    data = j({
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "series": {
            "Sales": [100, 120, 110, 140],
            "Costs": [80, 85, 90, 95],
        }
    })
    result = generate_chart(data, "multi_bar", "Sales vs Costs", "tc_mbar.png")
    assert result.startswith("[OK]")


def test_multi_line_chart(agent_dir):
    data = j({
        "x": ["Jan", "Feb", "Mar", "Apr"],
        "series": {
            "Revenue": [200, 220, 210, 250],
            "Profit": [50, 60, 55, 75],
        }
    })
    result = generate_chart(data, "multi_line", "Revenue & Profit", "tc_mline.png")
    assert result.startswith("[OK]")


def test_heatmap_chart(agent_dir):
    data = j({
        "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "row_labels": ["R1", "R2", "R3"],
        "col_labels": ["C1", "C2", "C3"],
    })
    result = generate_chart(data, "heatmap", "Correlation Matrix", "tc_heatmap.png")
    assert result.startswith("[OK]")


def test_confusion_matrix_chart(agent_dir):
    data = j({
        "matrix": [[50, 5, 0], [3, 42, 2], [1, 1, 44]],
        "labels": ["Cat", "Dog", "Fish"],
    })
    result = generate_chart(data, "confusion_matrix", "SVM Confusion Matrix", "tc_cm.png")
    assert result.startswith("[OK]")


# ── error handling ─────────────────────────────────────────────────────────────

def test_unknown_chart_type_returns_error(agent_dir):
    data = j({"x": [1, 2], "y": [3, 4]})
    result = generate_chart(data, "donut_chart", "Unknown", "tc_unknown.png")
    assert result.startswith("[ERROR]")
    assert "Unknown chart_type" in result


def test_invalid_json_returns_error(agent_dir):
    result = generate_chart("not json at all", "bar", "Bad Input", "tc_bad.png")
    assert result.startswith("[ERROR]")


# ── output path is returned in result ─────────────────────────────────────────

def test_result_contains_output_path(agent_dir):
    data = j({"labels": ["A", "B"], "values": [1, 2]})
    result = generate_chart(data, "bar", "Path Test", "tc_path_check.png")
    assert "tc_path_check.png" in result
