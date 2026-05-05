import json
from pathlib import Path
import pandas as pd
from core import mcp, SHARED_DIR, abs_shared, ensure_dir, COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS


@mcp.tool()
def list_workspace(subdir: str = "") -> str:
    """
    List files in the shared workspace (where all agents publish their results).
    subdir: optional subdirectory within shared/ (e.g. 'costaff-agent-coding')
    """
    target = Path(SHARED_DIR) / subdir if subdir else Path(SHARED_DIR)
    if not target.exists():
        return f"[INFO] Directory '{target}' does not exist."
    files = sorted(f for f in target.rglob("*") if f.is_file())
    if not files:
        return f"[INFO] No files found in {target}/"
    return "\n".join(
        f"{f.relative_to(Path(SHARED_DIR))} ({f.stat().st_size} bytes)"
        for f in files
    )


@mcp.tool()
def ensure_directory(subdir: str) -> str:
    """
    Create a kebab-case subdirectory under the BA shared slot if it does not exist.
    Idempotent — safe to call even when the directory already exists.

    subdir: kebab-case directory name (e.g. 'wine-eda-report', 'sales-analysis')
            Must be relative — never an absolute path.
    Returns: confirmation string with the resulting absolute path.

    Note: write tools (export_pdf, create_html_report, generate_chart) already
    auto-create their parent directory, so calling this first is optional.
    Use it only when you want to verify or pre-create the report directory.
    """
    if subdir.startswith("/"):
        return f"[ERROR] subdir must be relative, got absolute path: {subdir}"
    target = Path(COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS) / subdir
    ensure_dir(str(target))
    return f"Directory ready: {target}"


@mcp.tool()
def read_result(filepath: str) -> str:
    """
    Read a JSON or text result file from the shared workspace.
    filepath: relative path from shared/ root (e.g. 'costaff-agent-coding/accuracy.json')
    """
    abs_path = abs_shared(filepath)
    try:
        with open(abs_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"[ERROR] File not found: {abs_path}"
    except Exception as e:
        return f"[ERROR] {e}"


@mcp.tool()
def read_csv(filepath: str, max_rows: int = 500) -> str:
    """
    Read a CSV file from the shared workspace and return a JSON summary plus sample rows.
    filepath: relative path from shared/ root (e.g. 'costaff-agent-database/sales.csv')
    max_rows: maximum number of rows to include in the output (default 500)
    Returns: JSON string with keys: columns, shape, dtypes, summary (describe), records (sample rows)
    """
    abs_path = abs_shared(filepath)
    try:
        df = pd.read_csv(abs_path)
        result = {
            "columns": list(df.columns),
            "shape": list(df.shape),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "summary": json.loads(df.describe(include="all").fillna("").to_json()),
            "records": json.loads(df.head(max_rows).to_json(orient="records")),
        }
        return json.dumps(result, ensure_ascii=False)
    except FileNotFoundError:
        return f"[ERROR] File not found: {abs_path}"
    except Exception as e:
        return f"[ERROR] {e}"
