import json
from core import mcp


@mcp.tool()
def analyze_data(data_json: str) -> str:
    """
    Perform a statistical summary on numeric data and detect basic patterns.

    data_json: JSON object. Accepted shapes:
      - {"series": [1, 2, 3, ...]}               — single numeric series
      - {"labels": [...], "values": [...]}         — labeled series
      - {"columns": {...}, "records": [...]}        — tabular (from read_csv)

    Returns: JSON with min, max, mean, median, std, trend direction, and top/bottom values.
    """
    import numpy as np
    try:
        data = json.loads(data_json)
        results = {}

        def _stats(name: str, values: list) -> None:
            arr = np.array(
                [v for v in values if v is not None and str(v).replace(".", "").lstrip("-").isdigit()],
                dtype=float,
            )
            if arr.size == 0:
                return
            trend = "upward" if arr[-1] > arr[0] else ("downward" if arr[-1] < arr[0] else "flat")
            results[name] = {
                "count": int(arr.size),
                "min": round(float(arr.min()), 4),
                "max": round(float(arr.max()), 4),
                "mean": round(float(arr.mean()), 4),
                "median": round(float(np.median(arr)), 4),
                "std": round(float(arr.std()), 4),
                "trend": trend,
            }
            if "labels" in data and len(data["labels"]) == len(values):
                sorted_pairs = sorted(
                    zip(data["labels"], values),
                    key=lambda x: x[1] if x[1] is not None else 0,
                )
                results[name]["bottom3"] = [str(p[0]) for p in sorted_pairs[:3]]
                results[name]["top3"] = [str(p[0]) for p in sorted_pairs[-3:]]

        if "series" in data:
            _stats("series", data["series"])
        elif "values" in data:
            _stats("values", data["values"])
        elif "records" in data and isinstance(data["records"], list) and data["records"]:
            for col in data["records"][0]:
                col_values = [row.get(col) for row in data["records"]]
                _stats(col, col_values)

        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"[ERROR] analyze_data failed: {e}"
