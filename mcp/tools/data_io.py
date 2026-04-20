import json
from core import mcp, WORKSPACE_DIR, abs_workspace


@mcp.tool()
def list_workspace(subdir: str = "shared") -> str:
    """
    List files in the data workspace (default: shared/ subdirectory).
    Use this to discover result files produced by other agents.
    """
    from pathlib import Path
    target = Path(WORKSPACE_DIR) / subdir
    if not target.exists():
        return f"[INFO] Directory '{subdir}' does not exist in workspace."
    files = list(target.rglob("*"))
    if not files:
        return f"[INFO] No files found in {subdir}/"
    return "\n".join(
        f"{f.relative_to(Path(WORKSPACE_DIR))} ({f.stat().st_size} bytes)"
        for f in sorted(files) if f.is_file()
    )


@mcp.tool()
def read_result(filepath: str) -> str:
    """
    Read a JSON or text result file from the workspace.
    filepath: relative path from workspace root (e.g. 'shared/accuracy.json')
    """
    abs_path = abs_workspace(filepath)
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
    Read a CSV file from the workspace and return a JSON summary plus sample rows.
    filepath: relative path from workspace root (e.g. 'shared/sales.csv')
    max_rows: maximum number of rows to include in the output (default 500)
    Returns: JSON string with keys: columns, shape, dtypes, summary (describe), records (sample rows)
    """
    import pandas as pd
    abs_path = abs_workspace(filepath)
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
