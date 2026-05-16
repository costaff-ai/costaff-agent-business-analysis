"""BA's own tools as native function tools (httpx → BA MCP server's HTTP shim).

Same tools as before, same server (costaff-mcp-business-analysis) — only
the transport changes: httpx.post instead of ADK McpToolset. The MCP
server keeps all the real logic (matplotlib / weasyprint / pandas); this
file is just thin wrappers so the BA agent process holds ZERO MCP
streamable-http client → the anyio CancelScope race cannot occur.
"""
import os

from ._http import call_shim

_BASE = os.getenv("MCP_BA_HTTP_URL", "http://costaff-mcp-business-analysis:8083")


def list_workspace(subdir: str = "") -> str:
    """List files in the shared workspace (where all agents publish results).

    subdir: optional subdirectory within shared/ (e.g. 'costaff-agent-coding').
    """
    return call_shim(_BASE, "list_workspace", subdir=subdir)


def ensure_directory(subdir: str) -> str:
    """Create a kebab-case subdirectory under the BA shared slot (idempotent).

    subdir: relative kebab-case dir name (e.g. 'wine-eda-report'). Never absolute.
    """
    return call_shim(_BASE, "ensure_directory", subdir=subdir)


def read_result(filepath: str) -> str:
    """Read a JSON or text result file from the shared workspace.

    filepath: relative path from shared/ root
      (e.g. 'costaff-agent-coding/wine-eda/results.json').
    """
    return call_shim(_BASE, "read_result", filepath=filepath)


def read_csv(filepath: str, max_rows: int = 500) -> str:
    """Read a CSV from the shared workspace; return JSON summary + sample rows.

    filepath: relative path from shared/ root.
    max_rows: max rows to include (default 500).
    Returns JSON with keys: columns, shape, dtypes, summary, records.
    """
    return call_shim(_BASE, "read_csv", filepath=filepath, max_rows=max_rows)


def analyze_data(data_json: str) -> str:
    """Statistical summary + basic pattern detection on numeric data.

    data_json: JSON. Accepted shapes: {"series":[...]}, {"labels":[...],
    "values":[...]}, or {"records":[...]} (from read_csv).
    Returns JSON with min/max/mean/median/std/trend and top/bottom values.
    """
    return call_shim(_BASE, "analyze_data", data_json=data_json)


def generate_chart(
    data_json: str,
    chart_type: str,
    title: str,
    output_filename: str,
    xlabel: str = "",
    ylabel: str = "",
) -> str:
    """Generate a chart from JSON data and save as PNG.

    chart_type: bar | line | area | pie | scatter | histogram | box |
      multi_bar | multi_line | heatmap | confusion_matrix.
    output_filename: path under the BA shared slot
      (e.g. 'wine-eda-report/dist.png').
    Returns the absolute saved path.
    """
    return call_shim(
        _BASE, "generate_chart",
        data_json=data_json, chart_type=chart_type, title=title,
        output_filename=output_filename, xlabel=xlabel, ylabel=ylabel,
    )


def generate_distribution_plots(
    csv_path: str,
    features: list,
    output_subdir: str,
    include_boxplot: bool = True,
    bins: int = 30,
) -> str:
    """Batch histogram (+optional boxplot) for multiple numeric CSV columns.

    Prefer over generate_chart when the task is "distribution plots for
    these N features" — one call instead of N round-trips.

    csv_path: absolute path to the input CSV.
    features: column names to plot.
    output_subdir: kebab-case <report-name>/ under the BA shared slot.
    Returns JSON {"ok":true,"paths":[...],"errors":[...]}.
    """
    return call_shim(
        _BASE, "generate_distribution_plots",
        csv_path=csv_path, features=features, output_subdir=output_subdir,
        include_boxplot=include_boxplot, bins=bins,
    )


def create_report_from_markdown(
    title: str, markdown_content: str, output_filename: str
) -> str:
    """Create a formatted report from plain Markdown.

    Use when the body has code snippets/backslashes (avoids JSON escaping).
    output_filename: end with .html for HTML, .pdf for PDF (HTML auto-made).
    Image src must be a bare filename, a path relative to the BA shared
    root, or an absolute /app/data/ path — never an http(s) URL.
    Returns the absolute saved path.
    """
    return call_shim(
        _BASE, "create_report_from_markdown",
        title=title, markdown_content=markdown_content,
        output_filename=output_filename,
    )


def create_html_report(title: str, sections_json: str, output_filename: str) -> str:
    """Create a formatted report from a JSON array of section objects.

    sections_json: [{"type":"heading"|"text"|"metric"|"image"|"divider", ...}].
    output_filename: end with .html for HTML, .pdf for PDF (HTML auto-made).
    Returns the absolute saved path.
    """
    return call_shim(
        _BASE, "create_html_report",
        title=title, sections_json=sections_json, output_filename=output_filename,
    )


def export_pdf(html_filename: str, output_filename: str) -> str:
    """Convert an existing HTML report to PDF (WeasyPrint).

    html_filename: HTML filename (searched in BA shared slot then workspace).
    output_filename: output PDF filename under the BA shared slot.
    Returns the absolute saved PDF path.
    """
    return call_shim(
        _BASE, "export_pdf",
        html_filename=html_filename, output_filename=output_filename,
    )


def export_pptx(title: str, slides_json: str, output_filename: str) -> str:
    """Generate a PowerPoint deck (.pptx).

    slides_json: [{"type":"title"|"content"|"image", ...}].
    output_filename: .pptx filename under the BA shared slot.
    Returns the absolute saved path.
    """
    return call_shim(
        _BASE, "export_pptx",
        title=title, slides_json=slides_json, output_filename=output_filename,
    )


def load_ba_tools() -> list:
    """Return BA's own tools as native ADK function tools (httpx-backed)."""
    return [
        list_workspace, ensure_directory, read_result, read_csv,
        analyze_data, generate_chart, generate_distribution_plots,
        create_report_from_markdown, create_html_report,
        export_pdf, export_pptx,
    ]
