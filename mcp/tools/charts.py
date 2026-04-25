import os
import json
import traceback
import numpy as np
from pathlib import Path
from core import mcp, COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS as AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR, ensure_dir

PALETTE = ["#4F86C6", "#F4845F", "#6DBE72", "#F7C948", "#9B7FD4", "#4CC9C9", "#E07DB3", "#A0A0A0"]


def _auto_xaxis(ax, labels: list, max_ticks: int = 15, rotation_hint: int = -1):
    """Thin and rotate x-axis labels to prevent overlap.

    Labels are the full list of strings for the x-axis. If there are more than
    max_ticks, only every N-th label is shown. Rotation is applied automatically
    based on visible label count and max character length.
    """
    import matplotlib.pyplot as _plt
    n = len(labels)
    str_labels = [str(l) for l in labels]

    if n > max_ticks:
        step = max(1, round(n / max_ticks))
        shown = [str_labels[i] if i % step == 0 else "" for i in range(n)]
        ax.set_xticks(range(n))
        ax.set_xticklabels(shown)
        visible = [l for l in shown if l]
    else:
        visible = str_labels

    max_len = max((len(l) for l in visible), default=0)
    n_vis = len(visible)

    if rotation_hint >= 0:
        angle = rotation_hint
    elif n_vis > 10 or max_len > 8:
        angle = 60
    elif n_vis > 6 or max_len > 5:
        angle = 45
    elif n_vis > 4 or max_len > 3:
        angle = 30
    else:
        angle = 0

    if angle > 0:
        _plt.setp(ax.get_xticklabels(), rotation=angle, ha="right",
                  fontsize=max(6, 9 - max(0, n_vis - 8) // 4))


def _setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    noto_tc = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if os.path.exists(noto_tc):
        fm.fontManager.addfont(noto_tc)
        prop = fm.FontProperties(fname=noto_tc)
        plt.rcParams["font.family"] = prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False
    return plt


_plt_cache = None


def _get_plt():
    global _plt_cache
    if _plt_cache is None:
        _plt_cache = _setup_matplotlib()
    return _plt_cache


@mcp.tool()
def generate_chart(
    data_json: str,
    chart_type: str,
    title: str,
    output_filename: str,
    xlabel: str = "",
    ylabel: str = "",
) -> str:
    """
    Generate a chart from JSON data and save as PNG.

    chart_type options:
      - 'bar'             : {"labels": [...], "values": [...]}
      - 'line'            : {"x": [...], "y": [...]}
      - 'area'            : {"x": [...], "y": [...]}
      - 'pie'             : {"labels": [...], "values": [...]}
      - 'scatter'         : {"x": [...], "y": [...], "labels": [...] (optional)}
      - 'histogram'       : {"values": [...], "bins": 20 (optional)}
      - 'box'             : {"groups": {"GroupA": [...], "GroupB": [...]}}
      - 'multi_bar'       : {"labels": [...], "series": {"SeriesA": [...], "SeriesB": [...]}}
      - 'multi_line'      : {"x": [...], "series": {"SeriesA": [...], "SeriesB": [...]}}
      - 'heatmap'         : {"matrix": [[...]], "row_labels": [...], "col_labels": [...]}
      - 'confusion_matrix': {"matrix": [[...]], "labels": [...]}

    output_filename: saved under /app/data/reports/
    Returns: absolute path to saved PNG.
    """
    plt = _get_plt()
    ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)

    try:
        data = json.loads(data_json)
    except Exception as e:
        return f"[ERROR] Invalid JSON input: {e}"
    fig, ax = plt.subplots(figsize=(9, 6))

    try:
        if chart_type == "bar":
            labels, values = data["labels"], data["values"]
            x_pos = range(len(labels))
            bars = ax.bar(x_pos, values, color=PALETTE[0], edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.3g", padding=3, fontsize=9)
            ax.set_ylim(0, max(values) * 1.18)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels)
            _auto_xaxis(ax, labels)

        elif chart_type == "line":
            x_data, y_data = data["x"], data["y"]
            x_pos = range(len(x_data))
            marker = "o" if len(x_data) <= 30 else ""
            ax.plot(x_pos, y_data, marker=marker, color=PALETTE[0], linewidth=2)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_data)
            _auto_xaxis(ax, x_data)

        elif chart_type == "area":
            x_data, y_data = data["x"], data["y"]
            x_pos = range(len(x_data))
            ax.plot(x_pos, y_data, color=PALETTE[0], linewidth=2)
            ax.fill_between(x_pos, y_data, alpha=0.25, color=PALETTE[0])
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_data)
            _auto_xaxis(ax, x_data)

        elif chart_type == "pie":
            ax.pie(data["values"], labels=data["labels"], autopct="%1.1f%%",
                   startangle=90, colors=PALETTE)
            ax.axis("equal")

        elif chart_type == "scatter":
            xs, ys = data["x"], data["y"]
            ax.scatter(xs, ys, color=PALETTE[0], alpha=0.7, edgecolors="white", linewidth=0.4)
            if "labels" in data:
                for lbl, x, y in zip(data["labels"], xs, ys):
                    ax.annotate(str(lbl), (x, y), textcoords="offset points",
                                xytext=(4, 4), fontsize=8, color="#475569")

        elif chart_type == "histogram":
            bins = data.get("bins", 20)
            ax.hist(data["values"], bins=bins, color=PALETTE[0], edgecolor="white", linewidth=0.4)

        elif chart_type == "box":
            groups = data["groups"]
            ax.boxplot(
                list(groups.values()),
                tick_labels=list(groups.keys()),
                patch_artist=True,
                boxprops=dict(facecolor=PALETTE[0], alpha=0.6),
                medianprops=dict(color="#1e293b", linewidth=2),
            )

        elif chart_type == "multi_bar":
            labels = data["labels"]
            series = data["series"]
            n_series = len(series)
            x = np.arange(len(labels))
            width = 0.7 / n_series
            for i, (name, values) in enumerate(series.items()):
                offset = (i - (n_series - 1) / 2) * width
                ax.bar(x + offset, values, width, label=name,
                       color=PALETTE[i % len(PALETTE)], edgecolor="white", linewidth=0.3)
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend(fontsize=9)
            _auto_xaxis(ax, labels)

        elif chart_type == "multi_line":
            x_data = data["x"]
            x_pos = range(len(x_data))
            for i, (name, values) in enumerate(data["series"].items()):
                marker = "o" if len(x_data) <= 30 else ""
                ax.plot(x_pos, values, marker=marker, label=name,
                        color=PALETTE[i % len(PALETTE)], linewidth=2)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_data)
            ax.legend(fontsize=9)
            _auto_xaxis(ax, x_data)

        elif chart_type in ("heatmap", "confusion_matrix"):
            matrix = np.array(data["matrix"])
            row_labels = data.get("row_labels") or data.get("labels", [str(i) for i in range(matrix.shape[0])])
            col_labels = data.get("col_labels") or data.get("labels", [str(i) for i in range(matrix.shape[1])])
            cmap = "Blues" if chart_type == "confusion_matrix" else "YlOrRd"
            im = ax.imshow(matrix, interpolation="nearest", cmap=cmap)
            fig.colorbar(im, ax=ax)
            ax.set_xticks(range(len(col_labels)))
            ax.set_yticks(range(len(row_labels)))
            ax.set_xticklabels(col_labels, rotation=30, ha="right")
            ax.set_yticklabels(row_labels)
            thresh = matrix.max() / 2.0
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    ax.text(j, i, f"{matrix[i, j]:.3g}",
                            ha="center", va="center",
                            color="white" if matrix[i, j] > thresh else "black",
                            fontsize=10, fontweight="bold")
            if chart_type == "confusion_matrix":
                ax.set_xlabel("Predicted")
                ax.set_ylabel("Actual")

        else:
            plt.close(fig)
            return f"[ERROR] Unknown chart_type: {chart_type}"

        ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)

        plt.tight_layout()
        out_path = str(Path(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR) / output_filename)
        ensure_dir(str(Path(out_path).parent))
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return f"[OK] Chart saved: {out_path}"

    except Exception as e:
        plt.close(fig)
        return f"[ERROR] Chart generation failed: {e}\n{traceback.format_exc()}"
