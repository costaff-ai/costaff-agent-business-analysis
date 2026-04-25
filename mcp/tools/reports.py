import json
import re
import traceback
from datetime import datetime
from pathlib import Path
import markdown as md_parser
from core import mcp, COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS as AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR, SHARED_DIR as WORKSPACE_DIR, ensure_dir, abs_my_shared as abs_reports
from .template import render_html, inject_noto_font, img_to_base64, MARKDOWN_CSS, SECTIONS_CSS


def _html_to_pdf(html_content: str, html_path: str, pdf_path: str) -> str:
    """Write HTML to disk and convert to PDF via WeasyPrint. Returns '[OK] PDF saved: <path>' or '[ERROR] ...'."""
    try:
        from weasyprint import HTML as WeasyprintHTML
    except ImportError:
        return "[ERROR] weasyprint is not installed."
    try:
        Path(html_path).write_text(html_content, encoding="utf-8")
        patched = inject_noto_font(html_content)
        WeasyprintHTML(string=patched, base_url=str(Path(html_path).parent)).write_pdf(pdf_path)
        return f"[OK] PDF saved: {pdf_path}"
    except Exception as e:
        return f"[ERROR] PDF export failed: {e}"


@mcp.tool()
def create_report_from_markdown(
    title: str,
    markdown_content: str,
    output_filename: str,
) -> str:
    """
    Create a formatted report from plain Markdown content.

    Use this tool whenever the report body contains code snippets, backslashes, or
    any content that would be hard to embed safely inside a JSON string.
    markdown_content: the full report body as a Markdown string (headings, lists, code blocks, tables).
    output_filename: filename under the BA shared dir.
      - End with '.html' to get an HTML file.
      - End with '.pdf'  to get a PDF directly (HTML is created automatically as an intermediate step).
    Returns: absolute path to the saved file.
    """
    ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body_html = md_parser.markdown(
        markdown_content,
        extensions=["fenced_code", "tables", "nl2br", "toc"]
    )
    wrapped_body = f'<div class="report-body">\n{body_html}\n  </div>'
    html = render_html(title, wrapped_body, generated_at, MARKDOWN_CSS)

    stem = Path(output_filename).stem
    if output_filename.lower().endswith(".pdf"):
        html_path = abs_reports(f"{stem}.html")
        pdf_path  = abs_reports(output_filename)
        return _html_to_pdf(html, html_path, pdf_path)

    out_path = abs_reports(output_filename)
    Path(out_path).write_text(html, encoding="utf-8")
    return f"[OK] Report saved: {out_path}"


@mcp.tool()
def create_html_report(
    title: str,
    sections_json: str,
    output_filename: str,
) -> str:
    """
    Create a formatted HTML report combining text and charts.

    IMPORTANT: If the report body contains code snippets or backslashes, use
    create_report_from_markdown() instead — it accepts plain Markdown and avoids
    JSON escape issues entirely.

    sections_json: JSON array of section objects:
      [
        {"type": "heading", "text": "Results Summary"},
        {"type": "text", "text": "The model achieved..."},
        {"type": "metric", "label": "Accuracy", "value": "97.22%"},
        {"type": "image", "path": "/app/data/reports/confusion_matrix.png", "caption": "Confusion Matrix"}
      ]

    output_filename: filename under the BA shared dir.
      - End with '.html' to get an HTML file.
      - End with '.pdf'  to get a PDF directly (HTML is created automatically as an intermediate step).
    Returns: absolute path to the saved file.
    """
    ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
    try:
        sections = json.loads(sections_json)
    except json.JSONDecodeError:
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', sections_json)
        sections = json.loads(fixed)

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
            body_parts.append(
                f'<div class="metric-card">'
                f'<div class="metric-label">{sec["label"]}</div>'
                f'<div class="metric-value">{sec["value"]}</div>'
                f'</div>'
            )
        elif t == "image":
            b64 = img_to_base64(sec["path"])
            caption = sec.get("caption", "")
            if b64:
                body_parts.append(
                    f'<figure class="chart-figure">'
                    f'<img src="data:image/png;base64,{b64}" alt="{caption}" />'
                    f'<figcaption>{caption}</figcaption>'
                    f'</figure>'
                )
            else:
                body_parts.append(f'<p class="error">[Image not found: {sec["path"]}]</p>')
        elif t == "divider":
            body_parts.append('<hr class="divider" />')

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = render_html(title, "\n".join(body_parts), generated_at, SECTIONS_CSS)

    stem = Path(output_filename).stem
    if output_filename.lower().endswith(".pdf"):
        html_path = abs_reports(f"{stem}.html")
        pdf_path  = abs_reports(output_filename)
        return _html_to_pdf(html, html_path, pdf_path)

    out_path = abs_reports(output_filename)
    Path(out_path).write_text(html, encoding="utf-8")
    return f"[OK] Report saved: {out_path}"


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

    html_path = abs_reports(html_filename)
    if not Path(html_path).exists():
        matches = list(Path(WORKSPACE_DIR).rglob(html_filename))
        if matches:
            html_path = str(matches[0])
        else:
            return f"[ERROR] HTML file not found: {html_filename}"

    pdf_path = abs_reports(output_filename)

    try:
        ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
        raw_html = Path(html_path).read_text(encoding="utf-8")
        patched_html = inject_noto_font(raw_html)
        HTML(string=patched_html, base_url=str(Path(html_path).parent)).write_pdf(pdf_path)
        return f"[OK] PDF saved: {pdf_path}"
    except Exception as e:
        return f"[ERROR] PDF export failed: {e}"


@mcp.tool()
def export_pptx(
    title: str,
    slides_json: str,
    output_filename: str,
) -> str:
    """
    Generate a PowerPoint slide deck (.pptx).

    slides_json: JSON array of slide objects:
      [
        {"type": "title",   "title": "Q3 Sales Report", "subtitle": "CoStaff BI"},
        {"type": "content", "title": "Key Metrics",     "bullets": ["Revenue: $2M", "Growth: +18%"]},
        {"type": "image",   "title": "Revenue Trend",   "image_path": "/app/data/reports/trend.png",
                             "note": "Q3 saw a strong recovery in the North region."}
      ]

    output_filename: saved under /app/data/reports/ (e.g. 'q3_report.pptx')
    Returns: absolute path to saved PPTX.
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        return "[ERROR] python-pptx is not installed."

    try:
        slides = json.loads(slides_json)
        prs = Presentation()
        prs.core_properties.title = title
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)

        DARK = RGBColor(0x1e, 0x29, 0x3b)
        BLUE = RGBColor(0x4F, 0x86, 0xC6)
        WHITE = RGBColor(0xFF, 0xFF, 0xFF)
        GRAY = RGBColor(0x94, 0xA3, 0xB8)

        blank_layout = prs.slide_layouts[6]

        for idx, slide_data in enumerate(slides, start=1):
            slide = prs.slides.add_slide(blank_layout)

            bg = slide.background
            fill = bg.fill
            fill.solid()
            fill.fore_color.rgb = DARK

            stype = slide_data.get("type", "content")
            slide_title = slide_data.get("title", "")

            if stype == "title":
                txBox = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11.33), Inches(1.5))
                tf = txBox.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                run = p.add_run()
                run.text = slide_title
                run.font.size = Pt(44)
                run.font.bold = True
                run.font.color.rgb = WHITE

                subtitle = slide_data.get("subtitle", "")
                if subtitle:
                    txBox2 = slide.shapes.add_textbox(Inches(1), Inches(4.2), Inches(11.33), Inches(0.8))
                    tf2 = txBox2.text_frame
                    p2 = tf2.paragraphs[0]
                    p2.alignment = PP_ALIGN.CENTER
                    run2 = p2.add_run()
                    run2.text = subtitle
                    run2.font.size = Pt(20)
                    run2.font.color.rgb = GRAY

                line = slide.shapes.add_shape(1, Inches(4.67), Inches(4.0), Inches(4.0), Inches(0.04))
                line.fill.solid()
                line.fill.fore_color.rgb = BLUE
                line.line.fill.background()

            elif stype == "content":
                title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(10), Inches(0.7))
                tf = title_box.text_frame
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = slide_title
                run.font.size = Pt(24)
                run.font.bold = True
                run.font.color.rgb = WHITE

                bullets = slide_data.get("bullets", [])
                if bullets:
                    body_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.4), Inches(11.5), Inches(5.5))
                    tf2 = body_box.text_frame
                    tf2.word_wrap = True
                    for i, bullet in enumerate(bullets):
                        p2 = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
                        p2.space_before = Pt(6)
                        run2 = p2.add_run()
                        run2.text = f"  •  {bullet}"
                        run2.font.size = Pt(18)
                        run2.font.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)

            elif stype == "image":
                title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(10), Inches(0.7))
                tf = title_box.text_frame
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = slide_title
                run.font.size = Pt(24)
                run.font.bold = True
                run.font.color.rgb = WHITE

                img_path = slide_data.get("image_path", "")
                if img_path and Path(img_path).exists():
                    slide.shapes.add_picture(img_path, Inches(1.5), Inches(1.3), Inches(10.3), Inches(5.2))

                note = slide_data.get("note", "")
                if note:
                    note_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.8), Inches(12.3), Inches(0.5))
                    tf_note = note_box.text_frame
                    p_note = tf_note.paragraphs[0]
                    run_note = p_note.add_run()
                    run_note.text = note
                    run_note.font.size = Pt(11)
                    run_note.font.color.rgb = GRAY

            if stype != "title":
                num_box = slide.shapes.add_textbox(Inches(12.3), Inches(7.1), Inches(0.8), Inches(0.3))
                tf_num = num_box.text_frame
                p_num = tf_num.paragraphs[0]
                p_num.alignment = PP_ALIGN.RIGHT
                run_num = p_num.add_run()
                run_num.text = str(idx)
                run_num.font.size = Pt(9)
                run_num.font.color.rgb = GRAY

        ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
        out_path = abs_reports(output_filename)
        prs.save(out_path)
        return f"[OK] PPTX saved: {out_path}"

    except Exception as e:
        return f"[ERROR] PPTX export failed: {e}\n{traceback.format_exc()}"
