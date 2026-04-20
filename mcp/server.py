import os
import json
import base64
import traceback
from pathlib import Path
from datetime import datetime

import markdown as md_parser
from mcp.server.fastmcp import FastMCP

WORKSPACE_DIR = os.getenv("CODING_WORKSPACE_DIR", "/app/data/coding_workspace")
REPORTS_DIR = os.getenv("REPORTS_DIR", "/app/data/reports")

mcp = FastMCP("viz-report-mcp", host="0.0.0.0", port=int(os.getenv("MCP_VIZ_PORT", "8083")))

def _ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def _abs_workspace(filename: str) -> str:
    return str(Path(WORKSPACE_DIR) / filename)

def _abs_reports(filename: str) -> str:
    return str(Path(REPORTS_DIR) / filename)


@mcp.tool()
def list_workspace(subdir: str = "shared") -> str:
    """
    List files in the coding workspace (default: shared/ subdirectory).
    Use this to discover result files produced by coding-agent.
    """
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
    Read a result file from the coding workspace.
    filepath: relative path from workspace root (e.g. 'shared/accuracy.json')
    """
    abs_path = _abs_workspace(filepath)
    try:
        with open(abs_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"[ERROR] File not found: {abs_path}"
    except Exception as e:
        return f"[ERROR] {e}"


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
      - 'bar': bar chart (data: {"labels": [...], "values": [...]})
      - 'confusion_matrix': heatmap (data: {"matrix": [[...]], "labels": [...]})
      - 'line': line chart (data: {"x": [...], "y": [...]})
      - 'pie': pie chart (data: {"labels": [...], "values": [...]})

    output_filename: saved under /app/data/reports/ (e.g. 'accuracy_bar.png')
    Returns: absolute path to saved PNG.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np

    # Register Noto Sans CJK TC directly from file path for Traditional Chinese support
    _noto_tc = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    _noto_serif_tc = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
    for _fp in [_noto_tc, _noto_serif_tc]:
        if os.path.exists(_fp):
            fm.fontManager.addfont(_fp)
    _prop = fm.FontProperties(fname=_noto_tc) if os.path.exists(_noto_tc) else None
    if _prop:
        plt.rcParams["font.family"] = _prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False

    _ensure_dir(REPORTS_DIR)
    data = json.loads(data_json)
    fig, ax = plt.subplots(figsize=(8, 6))

    try:
        if chart_type == "bar":
            labels = data["labels"]
            values = data["values"]
            bars = ax.bar(labels, values, color="#4F86C6", edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.4f", padding=3, fontsize=10)
            ax.set_ylim(0, max(values) * 1.15)

        elif chart_type == "confusion_matrix":
            matrix = np.array(data["matrix"])
            labels = data.get("labels", [str(i) for i in range(matrix.shape[0])])
            im = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
            fig.colorbar(im, ax=ax)
            ax.set_xticks(range(len(labels)))
            ax.set_yticks(range(len(labels)))
            ax.set_xticklabels(labels)
            ax.set_yticklabels(labels)
            thresh = matrix.max() / 2.0
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    ax.text(j, i, str(matrix[i, j]),
                            ha="center", va="center",
                            color="white" if matrix[i, j] > thresh else "black",
                            fontsize=12, fontweight="bold")
            ax.set_xlabel("Predicted Label")
            ax.set_ylabel("True Label")

        elif chart_type == "line":
            ax.plot(data["x"], data["y"], marker="o", color="#4F86C6", linewidth=2)
            ax.fill_between(data["x"], data["y"], alpha=0.1, color="#4F86C6")

        elif chart_type == "pie":
            ax.pie(data["values"], labels=data["labels"], autopct="%1.1f%%",
                   startangle=90, colors=["#4F86C6", "#F4845F", "#6DBE72", "#F7C948", "#9B7FD4"])
            ax.axis("equal")

        else:
            return f"[ERROR] Unknown chart_type: {chart_type}"

        ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
        if xlabel: ax.set_xlabel(xlabel)
        if ylabel: ax.set_ylabel(ylabel)

        plt.tight_layout()
        out_path = _abs_reports(output_filename)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return f"[OK] Chart saved: {out_path}"

    except Exception as e:
        plt.close(fig)
        return f"[ERROR] Chart generation failed: {e}\n{traceback.format_exc()}"


@mcp.tool()
def create_html_report(
    title: str,
    sections_json: str,
    output_filename: str,
) -> str:
    """
    Create a formatted HTML report combining text and charts.

    sections_json: JSON array of section objects:
      [
        {"type": "heading", "text": "Results Summary"},
        {"type": "text", "text": "The model achieved..."},
        {"type": "metric", "label": "Accuracy", "value": "97.22%"},
        {"type": "image", "path": "/app/data/reports/confusion_matrix.png", "caption": "Confusion Matrix"}
      ]

    output_filename: saved under /app/data/reports/ (e.g. 'wine_svm_report.html')
    Returns: absolute path to saved HTML.
    """
    _ensure_dir(REPORTS_DIR)
    sections = json.loads(sections_json)

    def img_to_base64(path: str) -> str:
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return ""

    body_parts = []
    for sec in sections:
        t = sec.get("type", "text")
        if t == "heading":
            body_parts.append(f'<h2 class="section-heading">{sec["text"]}</h2>')
        elif t == "text":
            rendered = md_parser.markdown(
                sec["text"],
                extensions=["fenced_code", "tables", "nl2br"]
            )
            body_parts.append(f'<div class="body-text">{rendered}</div>')
        elif t == "metric":
            body_parts.append(f'''
            <div class="metric-card">
                <div class="metric-label">{sec["label"]}</div>
                <div class="metric-value">{sec["value"]}</div>
            </div>''')
        elif t == "image":
            b64 = img_to_base64(sec["path"])
            caption = sec.get("caption", "")
            if b64:
                body_parts.append(f'''
                <figure class="chart-figure">
                    <img src="data:image/png;base64,{b64}" alt="{caption}" />
                    <figcaption>{caption}</figcaption>
                </figure>''')
            else:
                body_parts.append(f'<p class="error">[Image not found: {sec["path"]}]</p>')
        elif t == "divider":
            body_parts.append('<hr class="divider" />')

    body_html = "\n".join(body_parts)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<style>
  :root {{ --blue: #4F86C6; --dark: #1e293b; --light: #f8fafc; --border: #e2e8f0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans", sans-serif;
          background: var(--light); color: var(--dark); padding: 2rem; }}
  .report-container {{ max-width: 900px; margin: 0 auto; }}
  .report-header {{ background: var(--blue); color: white; border-radius: 1rem;
                    padding: 2.5rem; margin-bottom: 2rem; }}
  .report-header h1 {{ font-size: 2rem; font-weight: 800; letter-spacing: -0.5px; }}
  .report-header .meta {{ font-size: 0.8rem; opacity: 0.8; margin-top: 0.5rem; }}
  .section-heading {{ font-size: 1.25rem; font-weight: 700; color: var(--blue);
                      margin: 2rem 0 1rem; padding-bottom: 0.5rem;
                      border-bottom: 2px solid var(--border); }}
  .body-text {{ line-height: 1.8; color: #475569; margin-bottom: 1rem; }}
  .body-text h1, .body-text h2, .body-text h3 {{
    font-weight: 700; color: var(--blue); margin: 1.25rem 0 0.5rem; }}
  .body-text h1 {{ font-size: 1.2rem; }}
  .body-text h2 {{ font-size: 1.05rem; }}
  .body-text h3 {{ font-size: 0.95rem; }}
  .body-text p {{ margin-bottom: 0.75rem; }}
  .body-text pre {{ background: #1e293b; color: #7dd3fc; font-family: monospace;
    font-size: 0.8rem; padding: 1rem 1.25rem; border-radius: 0.5rem;
    overflow-x: auto; margin: 0.75rem 0; line-height: 1.6; }}
  .body-text code {{ font-family: monospace; background: #f1f5f9;
    padding: 0.1em 0.35em; border-radius: 0.25rem; font-size: 0.85em; }}
  .body-text pre code {{ background: none; padding: 0; color: inherit; }}
  .body-text table {{ width: 100%; border-collapse: collapse; margin: 0.75rem 0;
    font-size: 0.85rem; }}
  .body-text th {{ background: var(--blue); color: white; padding: 0.5rem 0.75rem;
    text-align: left; }}
  .body-text td {{ padding: 0.4rem 0.75rem; border-bottom: 1px solid var(--border); }}
  .body-text tr:nth-child(even) td {{ background: #f8fafc; }}
  .metric-card {{ display: inline-block; background: white; border: 1px solid var(--border);
                  border-radius: 0.75rem; padding: 1.25rem 2rem; margin: 0.5rem 0.5rem 0.5rem 0;
                  box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .metric-label {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
                   letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 0.25rem; }}
  .metric-value {{ font-size: 2rem; font-weight: 800; color: var(--blue); }}
  .chart-figure {{ margin: 1.5rem 0; text-align: center; }}
  .chart-figure img {{ max-width: 100%; border-radius: 0.75rem;
                        border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .chart-figure figcaption {{ font-size: 0.8rem; color: #94a3b8; margin-top: 0.75rem; }}
  .divider {{ border: none; border-top: 1px solid var(--border); margin: 2rem 0; }}
  .error {{ color: #ef4444; font-size: 0.85rem; }}
  .report-footer {{ text-align: center; font-size: 0.75rem; color: #94a3b8;
                    margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="report-container">
  <div class="report-header">
    <h1>{title}</h1>
    <p class="meta">Generated by Mateclaw Viz-Report Agent &nbsp;·&nbsp; {generated_at}</p>
  </div>
  {body_html}
  <div class="report-footer">Mateclaw AI Platform · Auto-generated Report</div>
</div>
</body>
</html>"""

    out_path = _abs_reports(output_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return f"[OK] Report saved: {out_path}"


_NOTO_CSS = """
<style>
* { font-family: "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans", Arial, sans-serif !important; }
body { font-family: "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans", Arial, sans-serif !important; }
</style>
"""

def _inject_noto_font(html_content: str) -> str:
    """Inject Noto CJK font override into any HTML before PDF export."""
    if "Noto Sans CJK" in html_content:
        return html_content  # already has Noto, skip
    if "</head>" in html_content:
        return html_content.replace("</head>", _NOTO_CSS + "</head>", 1)
    # No <head> tag — prepend style block
    return _NOTO_CSS + html_content


@mcp.tool()
def export_pdf(html_filename: str, output_filename: str) -> str:
    """
    Convert an HTML report to PDF using WeasyPrint.

    html_filename: filename of the HTML report. Searched in /app/data/reports/ first,
                   then /app/data/coding_workspace/ (any subdirectory).
    output_filename: output PDF filename under /app/data/reports/ (e.g. 'wine_svm_report.pdf')
    Returns: absolute path to saved PDF.
    """
    try:
        from weasyprint import HTML
    except ImportError:
        return "[ERROR] weasyprint is not installed."

    # Search for the HTML file: reports dir first, then anywhere in workspace
    html_path = _abs_reports(html_filename)
    if not Path(html_path).exists():
        matches = list(Path(WORKSPACE_DIR).rglob(html_filename))
        if matches:
            html_path = str(matches[0])
        else:
            return f"[ERROR] HTML file not found: {html_filename}"

    pdf_path = _abs_reports(output_filename)

    try:
        _ensure_dir(REPORTS_DIR)
        raw_html = Path(html_path).read_text(encoding="utf-8")
        patched_html = _inject_noto_font(raw_html)
        HTML(string=patched_html, base_url=str(Path(html_path).parent)).write_pdf(pdf_path)
        return f"[OK] PDF saved: {pdf_path}"
    except Exception as e:
        return f"[ERROR] PDF export failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
