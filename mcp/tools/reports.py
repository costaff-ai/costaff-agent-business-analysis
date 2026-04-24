import json
import base64
import traceback
from datetime import datetime
from pathlib import Path
import markdown as md_parser
from core import mcp, COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS as AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR, SHARED_DIR as WORKSPACE_DIR, ensure_dir, abs_my_shared as abs_reports

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
    ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
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
            </div>''',
            )
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
    <p class="meta">Generated by CoStaff Business Analysis Agent &nbsp;·&nbsp; {generated_at}</p>
  </div>
  {body_html}
  <div class="report-footer">CoStaff AI Platform · Business Analysis Agent</div>
</div>
</body>
</html>"""

    out_path = abs_reports(output_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
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

    # Search for the HTML file: reports dir first, then anywhere in workspace
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
        patched_html = _inject_noto_font(raw_html)
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

        blank_layout = prs.slide_layouts[6]  # completely blank

        for slide_data in slides:
            slide = prs.slides.add_slide(blank_layout)

            # Dark background
            bg = slide.background
            fill = bg.fill
            fill.solid()
            fill.fore_color.rgb = DARK

            stype = slide_data.get("type", "content")
            slide_title = slide_data.get("title", "")

            if stype == "title":
                # Large centered title slide
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

                # Accent line
                line = slide.shapes.add_shape(1, Inches(4.67), Inches(4.0), Inches(4.0), Inches(0.04))
                line.fill.solid()
                line.fill.fore_color.rgb = BLUE
                line.line.fill.background()

            elif stype == "content":
                # Title bar at top
                title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(10), Inches(0.7))
                tf = title_box.text_frame
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = slide_title
                run.font.size = Pt(24)
                run.font.bold = True
                run.font.color.rgb = WHITE

                # Bullets
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
                # Title
                title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(10), Inches(0.7))
                tf = title_box.text_frame
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = slide_title
                run.font.size = Pt(24)
                run.font.bold = True
                run.font.color.rgb = WHITE

                # Image
                img_path = slide_data.get("image_path", "")
                if img_path and Path(img_path).exists():
                    slide.shapes.add_picture(img_path, Inches(1.5), Inches(1.3), Inches(10.3), Inches(5.2))

                # Note below image
                note = slide_data.get("note", "")
                if note:
                    note_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.8), Inches(12.3), Inches(0.5))
                    tf_note = note_box.text_frame
                    p_note = tf_note.paragraphs[0]
                    run_note = p_note.add_run()
                    run_note.text = note
                    run_note.font.size = Pt(11)
                    run_note.font.color.rgb = GRAY

            # Slide number (bottom right, all slides except title)
            if stype != "title":
                num_box = slide.shapes.add_textbox(Inches(12.3), Inches(7.1), Inches(0.8), Inches(0.3))
                tf_num = num_box.text_frame
                p_num = tf_num.paragraphs[0]
                p_num.alignment = PP_ALIGN.RIGHT
                run_num = p_num.add_run()
                run_num.text = str(slides.index(slide_data) + 1)
                run_num.font.size = Pt(9)
                run_num.font.color.rgb = GRAY

        ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
        out_path = abs_reports(output_filename)
        prs.save(out_path)
        return f"[OK] PPTX saved: {out_path}"

    except Exception as e:
        return f"[ERROR] PPTX export failed: {e}\n{traceback.format_exc()}"
