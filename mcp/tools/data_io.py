import json
from core import mcp, SHARED_DIR, abs_shared


@mcp.tool()
def list_workspace(subdir: str = "") -> str:
    """
    List files in the shared workspace (where all agents publish their results).
    subdir: optional subdirectory within shared/ (e.g. 'costaff-agent-coding')
    """
    from pathlib import Path
    target = Path(SHARED_DIR) / subdir if subdir else Path(SHARED_DIR)
    if not target.exists():
        return f"[INFO] Directory '{target}' does not exist."
    files = list(target.rglob("*"))
    if not files:
        return f"[INFO] No files found in {target}/"
    return "\n".join(
        f"{f.relative_to(Path(SHARED_DIR))} ({f.stat().st_size} bytes)"
        for f in sorted(files) if f.is_file()
    )


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
    import pandas as pd
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
