import json
import pytest
from pathlib import Path
from tools.data_io import list_workspace, read_result, read_csv


# ── list_workspace ─────────────────────────────────────────────────────────────

def test_list_workspace_nonexistent_subdir():
    result = list_workspace("__nonexistent_subdir_xyz__")
    assert "[INFO]" in result
    assert "does not exist" in result


def test_list_workspace_shows_file(shared_dir):
    f = shared_dir / "_lw_test.txt"
    f.write_text("hello")
    result = list_workspace()
    assert "_lw_test.txt" in result
    f.unlink()


def test_list_workspace_subdir(shared_dir):
    sub = shared_dir / "_lw_subdir"
    sub.mkdir(exist_ok=True)
    (sub / "output.json").write_text('{"ok": true}')
    result = list_workspace("_lw_subdir")
    assert "output.json" in result


def test_list_workspace_shows_size(shared_dir):
    f = shared_dir / "_lw_size.txt"
    f.write_text("abc")
    result = list_workspace()
    assert "bytes" in result
    f.unlink()


def test_list_workspace_empty_subdir(shared_dir):
    sub = shared_dir / "_lw_empty"
    sub.mkdir(exist_ok=True)
    result = list_workspace("_lw_empty")
    assert "[INFO]" in result
    assert "No files found" in result


# ── read_result ────────────────────────────────────────────────────────────────

def test_read_result_json(shared_dir):
    f = shared_dir / "_rr_result.json"
    f.write_text('{"accuracy": 0.97, "f1": 0.96}')
    result = read_result("_rr_result.json")
    parsed = json.loads(result)
    assert parsed["accuracy"] == pytest.approx(0.97)


def test_read_result_text(shared_dir):
    f = shared_dir / "_rr_notes.txt"
    f.write_text("SVM training completed in 2.3s")
    result = read_result("_rr_notes.txt")
    assert "SVM training" in result


def test_read_result_subdir_path(shared_dir):
    sub = shared_dir / "_rr_agent"
    sub.mkdir(exist_ok=True)
    (sub / "metrics.json").write_text('{"loss": 0.05}')
    result = read_result("_rr_agent/metrics.json")
    assert '"loss"' in result


def test_read_result_missing_returns_error():
    result = read_result("__file_does_not_exist__.json")
    assert result.startswith("[ERROR]")
    assert "not found" in result.lower()


# ── read_csv ───────────────────────────────────────────────────────────────────

def test_read_csv_basic(shared_dir):
    (shared_dir / "_rc_scores.csv").write_text(
        "name,score\nalice,90\nbob,85\ncarol,92\n"
    )
    result = json.loads(read_csv("_rc_scores.csv"))
    assert result["columns"] == ["name", "score"]
    assert result["shape"] == [3, 2]
    assert len(result["records"]) == 3


def test_read_csv_includes_summary(shared_dir):
    (shared_dir / "_rc_nums.csv").write_text("x,y\n1,10\n2,20\n3,30\n")
    result = json.loads(read_csv("_rc_nums.csv"))
    assert "summary" in result
    assert "dtypes" in result


def test_read_csv_max_rows_respected(shared_dir):
    rows = "\n".join(f"item{i},{i}" for i in range(50))
    (shared_dir / "_rc_big.csv").write_text("label,value\n" + rows)
    result = json.loads(read_csv("_rc_big.csv", max_rows=10))
    assert len(result["records"]) == 10


def test_read_csv_missing_returns_error():
    result = read_csv("__no_such_file__.csv")
    assert result.startswith("[ERROR]")
    assert "not found" in result.lower()


def test_read_csv_numeric_dtypes(shared_dir):
    (shared_dir / "_rc_typed.csv").write_text("a,b\n1.1,2\n3.3,4\n")
    result = json.loads(read_csv("_rc_typed.csv"))
    assert "float" in result["dtypes"]["a"]
    assert "int" in result["dtypes"]["b"]
