import json
import pytest
from pathlib import Path
from tools.reports import (
    create_report_from_markdown,
    create_html_report,
    export_pdf,
    export_pptx,
)

try:
    import weasyprint
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

try:
    import pptx  # noqa: F401
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False


# ── create_report_from_markdown ────────────────────────────────────────────────

def test_markdown_report_creates_file(agent_dir):
    result = create_report_from_markdown(
        title="Test Report",
        markdown_content="## Section\n\nHello world.",
        output_filename="tr_basic.html",
    )
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_basic.html").exists()


def test_markdown_report_contains_title(agent_dir):
    create_report_from_markdown("My Title", "## Body\n\nContent.", "tr_title.html")
    content = (agent_dir / "tr_title.html").read_text()
    assert "My Title" in content


def test_markdown_report_renders_code_blocks(agent_dir):
    md = "## Code\n\n```python\ndef hello():\n    return 42\n```"
    create_report_from_markdown("Code Report", md, "tr_code.html")
    content = (agent_dir / "tr_code.html").read_text()
    assert "<code" in content


def test_markdown_report_renders_tables(agent_dir):
    md = "| Col A | Col B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    create_report_from_markdown("Table Report", md, "tr_table.html")
    content = (agent_dir / "tr_table.html").read_text()
    assert "<table" in content


def test_markdown_report_result_contains_path(agent_dir):
    result = create_report_from_markdown("Path Check", "Hello.", "tr_pathcheck.html")
    assert "tr_pathcheck.html" in result


# ── create_html_report ─────────────────────────────────────────────────────────

def test_html_report_creates_file(agent_dir):
    sections = json.dumps([{"type": "heading", "text": "Summary"}])
    result = create_html_report("HTML Test", sections, "tr_html.html")
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_html.html").exists()


def test_html_report_heading_section(agent_dir):
    sections = json.dumps([{"type": "heading", "text": "Results Summary"}])
    create_html_report("Heading Test", sections, "tr_heading.html")
    content = (agent_dir / "tr_heading.html").read_text()
    assert "Results Summary" in content


def test_html_report_metric_section(agent_dir):
    sections = json.dumps([{"type": "metric", "label": "Accuracy", "value": "97.22%"}])
    create_html_report("Metric Test", sections, "tr_metric.html")
    content = (agent_dir / "tr_metric.html").read_text()
    assert "97.22%" in content
    assert "Accuracy" in content


def test_html_report_text_section(agent_dir):
    sections = json.dumps([{"type": "text", "text": "The model performed well."}])
    create_html_report("Text Test", sections, "tr_text.html")
    content = (agent_dir / "tr_text.html").read_text()
    assert "model performed well" in content


def test_html_report_divider_section(agent_dir):
    sections = json.dumps([{"type": "divider"}])
    create_html_report("Divider Test", sections, "tr_divider.html")
    content = (agent_dir / "tr_divider.html").read_text()
    assert "divider" in content


def test_html_report_missing_image_shows_placeholder(agent_dir):
    sections = json.dumps([
        {"type": "image", "path": "/nonexistent/chart.png", "caption": "Missing Chart"}
    ])
    create_html_report("Image Test", sections, "tr_img.html")
    content = (agent_dir / "tr_img.html").read_text()
    assert "Image not found" in content


def test_html_report_image_embedded_as_base64(agent_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Generate a real PNG so img_to_base64 runs its read path
    png_path = agent_dir / "tr_real_chart.png"
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.bar(["A", "B"], [1, 2])
    fig.savefig(str(png_path), dpi=50)
    plt.close(fig)

    sections = json.dumps([
        {"type": "image", "path": str(png_path), "caption": "Real Chart"}
    ])
    create_html_report("Embedded Image", sections, "tr_img_b64.html")
    content = (agent_dir / "tr_img_b64.html").read_text()
    assert "data:image/png;base64," in content
    assert "Real Chart" in content


def test_html_report_multiple_sections(agent_dir):
    sections = json.dumps([
        {"type": "heading", "text": "Overview"},
        {"type": "metric", "label": "F1 Score", "value": "0.96"},
        {"type": "text", "text": "Strong performance across all classes."},
        {"type": "divider"},
        {"type": "metric", "label": "AUC", "value": "0.99"},
    ])
    result = create_html_report("Multi Section", sections, "tr_multi.html")
    assert result.startswith("[OK]")
    content = (agent_dir / "tr_multi.html").read_text()
    assert "F1 Score" in content
    assert "AUC" in content


# ── export_pdf ─────────────────────────────────────────────────────────────────

def test_export_pdf_html_not_found(agent_dir):
    result = export_pdf("__nonexistent__.html", "out.pdf")
    assert result.startswith("[ERROR]")
    # when weasyprint is installed: "HTML file not found: ..."
    # when weasyprint is absent: "weasyprint is not installed"
    # either way we expect an [ERROR] return


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="weasyprint not installed")
def test_export_pdf_creates_file(agent_dir):
    create_report_from_markdown("PDF Test", "## Section\n\nContent.", "tr_pdf_src.html")
    result = export_pdf("tr_pdf_src.html", "tr_output.pdf")
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_output.pdf").exists()


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="weasyprint not installed")
def test_export_pdf_result_contains_path(agent_dir):
    create_report_from_markdown("PDF Path", "Hello.", "tr_pdf2.html")
    result = export_pdf("tr_pdf2.html", "tr_output2.pdf")
    assert "tr_output2.pdf" in result


# ── export_pptx ────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_creates_file(agent_dir):
    slides = json.dumps([
        {"type": "title", "title": "Q3 Report", "subtitle": "CoStaff BI"},
        {"type": "content", "title": "Key Metrics", "bullets": ["Accuracy: 97%", "F1: 0.96"]},
    ])
    result = export_pptx("Test Deck", slides, "tr_deck.pptx")
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_deck.pptx").exists()


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_title_slide(agent_dir):
    slides = json.dumps([{"type": "title", "title": "My Deck", "subtitle": "Subtitle"}])
    result = export_pptx("Title Only", slides, "tr_title_only.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_content_slide(agent_dir):
    slides = json.dumps([
        {"type": "content", "title": "Findings", "bullets": ["Point A", "Point B", "Point C"]},
    ])
    result = export_pptx("Content Deck", slides, "tr_content.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_result_contains_path(agent_dir):
    slides = json.dumps([{"type": "title", "title": "Path Check"}])
    result = export_pptx("Path Deck", slides, "tr_path_deck.pptx")
    assert "tr_path_deck.pptx" in result


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_image_slide(agent_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    png_path = agent_dir / "tr_pptx_chart.png"
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.plot([1, 2, 3], [3, 1, 2])
    fig.savefig(str(png_path), dpi=50)
    plt.close(fig)

    slides = json.dumps([
        {"type": "image", "title": "Revenue Trend", "image_path": str(png_path), "note": "Strong Q3."},
    ])
    result = export_pptx("Image Deck", slides, "tr_img_deck.pptx")
    assert result.startswith("[OK]")


# ── new layout types (section / two_column / quote / kpi / chart / closing) ────

@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_section_slide(agent_dir):
    slides = json.dumps([
        {"type": "section", "title": "Part 2: Recommendations", "subtitle": "Three actionable steps"},
    ])
    result = export_pptx("Section", slides, "tr_section.pptx")
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_section.pptx").exists()


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_two_column_bullets(agent_dir):
    slides = json.dumps([
        {"type": "two_column", "title": "Before vs After",
         "left":  {"heading": "Before", "bullets": ["Slow",  "Manual", "Error-prone"]},
         "right": {"heading": "After",  "bullets": ["Fast",  "Auto",   "Reliable"]}},
    ])
    result = export_pptx("Two Col", slides, "tr_two_col.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_two_column_image_right(agent_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    png_path = agent_dir / "tr_2col.png"
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.bar(["a", "b"], [1, 2])
    fig.savefig(str(png_path), dpi=50); plt.close(fig)
    slides = json.dumps([
        {"type": "two_column", "title": "Findings",
         "left":  {"heading": "Insight", "bullets": ["Up 22%", "Region: north"]},
         "right": {"image_path": str(png_path)}},
    ])
    result = export_pptx("Two Col Img", slides, "tr_two_col_img.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_quote_slide(agent_dir):
    slides = json.dumps([
        {"type": "quote", "text": "We saw revenue jump 30% in Q3.",
         "attribution": "CFO, internal review 2026"},
    ])
    result = export_pptx("Quote", slides, "tr_quote.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_kpi_slide(agent_dir):
    slides = json.dumps([
        {"type": "kpi", "title": "Q3 Highlights", "kpis": [
            {"value": "$2.4M", "label": "Revenue", "change": "+18%"},
            {"value": "1,250", "label": "New Customers", "change": "+22%"},
            {"value": "87%",   "label": "Retention",     "change": "+3pt"},
        ]},
    ])
    result = export_pptx("KPI", slides, "tr_kpi.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_chart_native(agent_dir):
    slides = json.dumps([
        {"type": "chart", "title": "Quarterly Revenue", "chart_type": "column",
         "categories": ["Q1", "Q2", "Q3", "Q4"],
         "series": [
             {"name": "2025", "values": [100, 110, 95, 130]},
             {"name": "2026", "values": [115, 130, 145, 160]},
         ],
         "note": "Source: internal finance dashboard."},
    ])
    result = export_pptx("Chart", slides, "tr_chart.pptx")
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_chart.pptx").exists()


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_chart_pie(agent_dir):
    slides = json.dumps([
        {"type": "chart", "title": "Market Share", "chart_type": "pie",
         "categories": ["Us", "Competitor A", "Competitor B", "Others"],
         "series": [{"name": "Share", "values": [42, 28, 18, 12]}]},
    ])
    result = export_pptx("Pie", slides, "tr_pie.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_closing_slide(agent_dir):
    slides = json.dumps([
        {"type": "closing", "title": "Thank you", "subtitle": "Questions?",
         "contact": "ba@costaff.app"},
    ])
    result = export_pptx("Closing", slides, "tr_closing.pptx")
    assert result.startswith("[OK]")


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
@pytest.mark.parametrize("theme_name", ["dark", "light", "corporate"])
def test_export_pptx_themes(agent_dir, theme_name):
    slides = json.dumps([
        {"type": "title", "title": f"{theme_name} theme"},
        {"type": "content", "title": "Bullets", "bullets": ["A", "B"]},
    ])
    result = export_pptx(f"Theme {theme_name}", slides, f"tr_theme_{theme_name}.pptx",
                         theme=theme_name)
    assert result.startswith("[OK]")
    assert (agent_dir / f"tr_theme_{theme_name}.pptx").exists()


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_export_pptx_full_deck(agent_dir):
    """End-to-end: a 9-slide deck exercising every layout in one go."""
    slides = json.dumps([
        {"type": "title", "title": "Q3 Sales", "subtitle": "FY2026 Review"},
        {"type": "section", "title": "Highlights"},
        {"type": "kpi", "title": "Headline numbers",
         "kpis": [
             {"value": "$2.4M", "label": "Revenue", "change": "+18%"},
             {"value": "1,250", "label": "Customers", "change": "+22%"},
         ]},
        {"type": "content", "title": "What worked", "bullets": ["A", "B", "C"]},
        {"type": "two_column", "title": "Compare",
         "left":  {"heading": "Plan",   "bullets": ["x", "y"]},
         "right": {"heading": "Actual", "bullets": ["a", "b"]}},
        {"type": "chart", "title": "Monthly trend", "chart_type": "line",
         "categories": ["Jul", "Aug", "Sep"],
         "series": [{"name": "Revenue", "values": [800, 900, 1100]}]},
        {"type": "quote", "text": "Best quarter we've ever shipped.",
         "attribution": "CEO"},
        {"type": "section", "title": "Next steps"},
        {"type": "closing", "title": "Thank you", "contact": "ba@costaff.app"},
    ])
    result = export_pptx("Full Deck", slides, "tr_full_deck.pptx")
    assert result.startswith("[OK]")
    assert (agent_dir / "tr_full_deck.pptx").exists()
    assert (agent_dir / "tr_img_deck.pptx").exists()
