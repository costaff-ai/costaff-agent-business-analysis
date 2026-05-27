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
        ensure_dir(str(Path(html_path).parent))
        Path(html_path).write_text(html_content, encoding="utf-8")
        patched = inject_noto_font(html_content)
        # base_url is the BA shared root, NOT the HTML's parent dir.
        # data-interpretation / report-generation skills both instruct agents
        # to write image paths as `<report-name>/<file>.png` relative to the
        # BA shared root. If we used the HTML's parent dir (which IS the
        # `<report-name>/` subdir) the path would double up to
        # `<report-name>/<report-name>/<file>.png` and WeasyPrint silently
        # renders the PDF without the images.
        WeasyprintHTML(string=patched, base_url=AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR).write_pdf(pdf_path)
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

    IMPORTANT — image references: image src in markdown MUST be either
    (a) a bare filename like `chart.png`, (b) a path relative to the BA
    shared root like `<report-name>/chart.png`, or (c) an absolute path
    starting with `/app/data/`. Remote URLs (http://, https://) are
    rejected at validation — they would 404 at PDF render time.
    """
    # Hallucination guard: reject markdown with remote-URL image refs.
    # gemini-3-flash-preview has been observed inventing URLs like
    # `https://raw.githubusercontent.com/.../chart.png` that don't exist.
    # WeasyPrint silently fails on those and ships an image-less PDF.
    url_imgs = re.findall(r'!\[[^\]]*\]\((https?://[^)]+)\)', markdown_content)
    if url_imgs:
        return (
            "[ERROR] markdown_content contains remote image URLs which are "
            "always 404. Use the exact filenames returned by generate_chart "
            "(e.g. `<report-name>/chart.png`), not http(s) URLs. "
            f"Offenders: {url_imgs[:3]}"
        )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body_html = md_parser.markdown(
        markdown_content,
        extensions=["fenced_code", "tables", "nl2br", "toc"]
    )
    wrapped_body = f'<div class="report-body">\n{body_html}\n  </div>'
    html = render_html(title, wrapped_body, generated_at, MARKDOWN_CSS)

    stem = Path(output_filename).stem
    if output_filename.lower().endswith(".pdf"):
        html_path = abs_reports(f"{Path(output_filename).parent}/{stem}.html")
        pdf_path  = abs_reports(output_filename)
        return _html_to_pdf(html, html_path, pdf_path)

    out_path = abs_reports(output_filename)
    ensure_dir(str(Path(out_path).parent))
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
        html_path = abs_reports(f"{Path(output_filename).parent}/{stem}.html")
        pdf_path  = abs_reports(output_filename)
        return _html_to_pdf(html, html_path, pdf_path)

    out_path = abs_reports(output_filename)
    ensure_dir(str(Path(out_path).parent))
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
        ensure_dir(str(Path(pdf_path).parent))
        raw_html = Path(html_path).read_text(encoding="utf-8")
        patched_html = inject_noto_font(raw_html)
        # See _html_to_pdf for why base_url is the BA shared root, not html's parent.
        HTML(string=patched_html, base_url=AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR).write_pdf(pdf_path)
        return f"[OK] PDF saved: {pdf_path}"
    except Exception as e:
        return f"[ERROR] PDF export failed: {e}"


"""PowerPoint deck generation.

The visual identity (background colour, accents, body / heading fonts)
lives in real `.pptx` template files under `mcp/assets/templates/`.
Each template was produced by `build_templates.py` and carries:

- a custom Office colour scheme (`<a:clrScheme name="CoStaff …">`) so
  the client's PowerPoint shows our palette under `Design → Colors`
  and global re-theme just works.
- a custom font scheme (Space Grotesk / Manrope) — falls back to the
  system default when the named fonts aren't installed.
- a coloured master-slide background.

`export_pptx` loads the template, dispatches each requested slide to a
layout helper, and saves. The layout helpers still use explicit RGB
values because python-pptx doesn't expose theme-colour references for
ad-hoc textbox styling — the upshot is the template painted the bg /
chrome, and the layout code paints the on-slide content.

To restyle: open the template `.pptx` in PowerPoint → View → Slide
Master → adjust → save. Re-run `build_templates.py` only when the
palette / font choices themselves change.
"""

# Template files shipped alongside the code; resolved at import time so
# missing template surfaces as a clear FileNotFoundError instead of a
# runtime KeyError inside export_pptx.
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


def _template_path(theme: str) -> Path:
    """Map theme name -> template .pptx, fall back to dark."""
    candidate = _TEMPLATE_DIR / f"{theme}.pptx"
    if candidate.exists():
        return candidate
    return _TEMPLATE_DIR / "dark.pptx"


# RGB palette used by layout helpers for in-slide text/shapes. These
# *match* the template colour schemes built by build_templates.py — keep
# in sync if you tweak one of them.
_PPTX_THEMES = {
    "dark": {
        "bg": (0x1e, 0x29, 0x3b),     # slate-900
        "accent": (0x60, 0xA5, 0xFA),  # blue-400
        "accent2": (0xA7, 0x8B, 0xFA), # violet-400 (secondary)
        "text": (0xFF, 0xFF, 0xFF),
        "text_dim": (0xCB, 0xD5, 0xE1),# slate-300
        "text_muted": (0x94, 0xA3, 0xB8),
        "card": (0x33, 0x41, 0x5A),    # slate-700 (KPI card bg etc.)
    },
    "light": {
        "bg": (0xFF, 0xFF, 0xFF),
        "accent": (0x25, 0x63, 0xEB),
        "accent2": (0x7C, 0x3A, 0xED),
        "text": (0x0F, 0x17, 0x2A),
        "text_dim": (0x33, 0x44, 0x55),
        "text_muted": (0x6B, 0x72, 0x80),
        "card": (0xF1, 0xF5, 0xF9),
    },
    "corporate": {
        "bg": (0xF8, 0xFA, 0xFB),
        "accent": (0x0F, 0x4C, 0x75),
        "accent2": (0x3F, 0x72, 0xAF),
        "text": (0x1A, 0x1A, 0x1A),
        "text_dim": (0x40, 0x40, 0x40),
        "text_muted": (0x70, 0x70, 0x70),
        "card": (0xEC, 0xF3, 0xF9),
    },
}


def _pp_color(rgb_tuple):
    from pptx.dml.color import RGBColor
    return RGBColor(*rgb_tuple)


def _add_text(slide, x_in, y_in, w_in, h_in, text, *,
              size=18, bold=False, color=None, align=None, italic=False,
              wrap=True, font_name=None):
    """Helper: drop a text box with one paragraph. Returns the text frame."""
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN
    box = slide.shapes.add_textbox(Inches(x_in), Inches(y_in), Inches(w_in), Inches(h_in))
    tf = box.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    if align == "center": p.alignment = PP_ALIGN.CENTER
    elif align == "right": p.alignment = PP_ALIGN.RIGHT
    elif align == "left":  p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if font_name: run.font.name = font_name
    if color is not None:
        run.font.color.rgb = _pp_color(color)
    return tf


def _add_bullets(slide, x_in, y_in, w_in, h_in, bullets, *,
                 size=18, color=None, bullet_char="•"):
    """Helper: drop a bullet list. Each bullet becomes a paragraph; the
    `bullet_char` is prefixed manually because python-pptx doesn't expose
    the underlying <a:buChar> cleanly without XML diving."""
    from pptx.util import Inches, Pt
    box = slide.shapes.add_textbox(Inches(x_in), Inches(y_in), Inches(w_in), Inches(h_in))
    tf = box.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(8)
        r = p.add_run()
        r.text = f"  {bullet_char}  {bullet}"
        r.font.size = Pt(size)
        if color is not None:
            r.font.color.rgb = _pp_color(color)
    return tf


def _solid_fill_shape(slide, kind, x_in, y_in, w_in, h_in, color, *, no_line=True):
    """Add a filled shape (rectangle=1, etc.) and return it."""
    from pptx.util import Inches
    shp = slide.shapes.add_shape(kind, Inches(x_in), Inches(y_in), Inches(w_in), Inches(h_in))
    shp.fill.solid()
    shp.fill.fore_color.rgb = _pp_color(color)
    if no_line: shp.line.fill.background()
    return shp


def _set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _pp_color(color)


def _layout_title(slide, sd, theme):
    """Title cover slide: large centered title + subtitle + accent rule."""
    _add_text(slide, 1, 2.5, 11.33, 1.6,
              sd.get("title", ""), size=48, bold=True, color=theme["text"], align="center")
    subtitle = sd.get("subtitle", "")
    if subtitle:
        _add_text(slide, 1, 4.3, 11.33, 0.8,
                  subtitle, size=22, color=theme["text_muted"], align="center")
    _solid_fill_shape(slide, 1, 5.33, 4.05, 2.67, 0.06, theme["accent"])


def _layout_section(slide, sd, theme):
    """Section divider — large title, optional subtitle, accent block on the side."""
    _solid_fill_shape(slide, 1, 0.5, 2.8, 0.5, 2.2, theme["accent"])
    _add_text(slide, 1.3, 3.0, 11.5, 1.4,
              sd.get("title", ""), size=42, bold=True, color=theme["text"])
    subtitle = sd.get("subtitle", "")
    if subtitle:
        _add_text(slide, 1.3, 4.4, 11.5, 0.9,
                  subtitle, size=20, color=theme["text_dim"])


def _layout_content(slide, sd, theme):
    """Bullets slide with title bar and optional sub-heading."""
    _add_text(slide, 0.6, 0.45, 12, 0.8,
              sd.get("title", ""), size=26, bold=True, color=theme["text"])
    _solid_fill_shape(slide, 1, 0.6, 1.15, 1.2, 0.04, theme["accent"])
    sub = sd.get("subtitle", "")
    if sub:
        _add_text(slide, 0.6, 1.28, 12, 0.6,
                  sub, size=14, italic=True, color=theme["text_muted"])
    bullets = sd.get("bullets", [])
    if bullets:
        y = 1.95 if sub else 1.55
        _add_bullets(slide, 0.8, y, 11.7, 5.0, bullets, size=18, color=theme["text_dim"])


def _layout_image(slide, sd, theme):
    """Title + full-width image + caption note."""
    _add_text(slide, 0.6, 0.45, 12, 0.8,
              sd.get("title", ""), size=24, bold=True, color=theme["text"])
    from pptx.util import Inches
    img_path = sd.get("image_path", "")
    if img_path and Path(img_path).exists():
        slide.shapes.add_picture(img_path, Inches(1.5), Inches(1.3), Inches(10.3), Inches(5.2))
    note = sd.get("note", "")
    if note:
        _add_text(slide, 0.6, 6.7, 12.1, 0.55,
                  note, size=11, color=theme["text_muted"], italic=True)


def _layout_two_column(slide, sd, theme):
    """Two columns. Each side can be {heading, bullets} or {image_path}.
    Right column 50% width starting at x=6.9."""
    _add_text(slide, 0.6, 0.45, 12, 0.8,
              sd.get("title", ""), size=24, bold=True, color=theme["text"])
    _solid_fill_shape(slide, 1, 0.6, 1.15, 1.2, 0.04, theme["accent"])
    from pptx.util import Inches
    for col_key, x0 in (("left", 0.6), ("right", 6.9)):
        col = sd.get(col_key, {}) or {}
        heading = col.get("heading", "")
        if heading:
            _add_text(slide, x0, 1.55, 5.8, 0.6,
                      heading, size=18, bold=True, color=theme["accent"])
        bullets = col.get("bullets") or []
        if bullets:
            _add_bullets(slide, x0, 2.1, 5.8, 4.7, bullets, size=16, color=theme["text_dim"])
        img = col.get("image_path", "")
        if img and Path(img).exists():
            slide.shapes.add_picture(img, Inches(x0), Inches(2.1), Inches(5.8), Inches(4.7))
        body = col.get("body", "")
        if body and not bullets:
            _add_text(slide, x0, 2.1, 5.8, 4.7, body, size=16, color=theme["text_dim"])


def _layout_quote(slide, sd, theme):
    """Big italic quote, centered, with attribution below."""
    quote = sd.get("text", "")
    attribution = sd.get("attribution", "")
    _solid_fill_shape(slide, 1, 1.0, 2.0, 0.08, 3.5, theme["accent"])
    _add_text(slide, 1.5, 2.0, 10.8, 3.5,
              f'“{quote}”', size=32, italic=True, color=theme["text"], align="left")
    if attribution:
        _add_text(slide, 1.5, 5.6, 10.8, 0.6,
                  f"— {attribution}", size=16, color=theme["text_muted"], align="left")


def _layout_kpi(slide, sd, theme):
    """Row of 2–4 KPI cards: big number on top, label below, optional delta."""
    _add_text(slide, 0.6, 0.45, 12, 0.8,
              sd.get("title", ""), size=24, bold=True, color=theme["text"])
    _solid_fill_shape(slide, 1, 0.6, 1.15, 1.2, 0.04, theme["accent"])
    kpis = sd.get("kpis", []) or []
    n = max(1, min(4, len(kpis)))
    gap = 0.4
    total_w = 13.33 - 1.0 - (n - 1) * gap
    card_w = total_w / n
    x = 0.5
    y = 2.2
    h = 3.3
    for kpi in kpis[:n]:
        _solid_fill_shape(slide, 1, x, y, card_w, h, theme["card"])
        _add_text(slide, x, y + 0.4, card_w, 1.6,
                  kpi.get("value", ""), size=44, bold=True, color=theme["accent"], align="center")
        _add_text(slide, x, y + 2.0, card_w, 0.6,
                  kpi.get("label", ""), size=16, color=theme["text_dim"], align="center")
        change = kpi.get("change", "")
        if change:
            up = isinstance(change, str) and change.lstrip().startswith(("+", "↑", "▲"))
            color = (0x4A, 0xDE, 0x80) if up else theme["text_muted"]
            _add_text(slide, x, y + 2.55, card_w, 0.5,
                      change, size=14, bold=True, color=color, align="center")
        x += card_w + gap


def _layout_chart(slide, sd, theme):
    """Native PowerPoint chart from a category-series spec. Editable inside
    PowerPoint after generation (unlike a rasterised PNG)."""
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    from pptx.util import Inches
    _add_text(slide, 0.6, 0.45, 12, 0.8,
              sd.get("title", ""), size=24, bold=True, color=theme["text"])
    _solid_fill_shape(slide, 1, 0.6, 1.15, 1.2, 0.04, theme["accent"])

    kind = (sd.get("chart_type") or "column").lower()
    type_map = {
        "bar":       XL_CHART_TYPE.BAR_CLUSTERED,
        "column":    XL_CHART_TYPE.COLUMN_CLUSTERED,
        "line":      XL_CHART_TYPE.LINE,
        "pie":       XL_CHART_TYPE.PIE,
        "area":      XL_CHART_TYPE.AREA,
        "doughnut":  XL_CHART_TYPE.DOUGHNUT,
    }
    xl_type = type_map.get(kind, XL_CHART_TYPE.COLUMN_CLUSTERED)

    data = CategoryChartData()
    cats = sd.get("categories", [])
    data.categories = cats
    for series in (sd.get("series") or []):
        data.add_series(series.get("name", ""), series.get("values", []))

    chart_shape = slide.shapes.add_chart(
        xl_type, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2), data,
    )
    chart = chart_shape.chart
    chart.has_title = False
    if xl_type != XL_CHART_TYPE.PIE and xl_type != XL_CHART_TYPE.DOUGHNUT:
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False

    note = sd.get("note", "")
    if note:
        _add_text(slide, 0.6, 6.85, 12.1, 0.5,
                  note, size=11, color=theme["text_muted"], italic=True)


def _layout_closing(slide, sd, theme):
    """Closing slide — title + subtitle + optional contact line."""
    _solid_fill_shape(slide, 1, 5.33, 5.6, 2.67, 0.06, theme["accent"])
    _add_text(slide, 1, 2.6, 11.33, 1.4,
              sd.get("title", "Thank you"), size=52, bold=True, color=theme["text"], align="center")
    subtitle = sd.get("subtitle", "")
    if subtitle:
        _add_text(slide, 1, 4.2, 11.33, 0.9,
                  subtitle, size=22, color=theme["text_dim"], align="center")
    contact = sd.get("contact", "")
    if contact:
        _add_text(slide, 1, 6.4, 11.33, 0.5,
                  contact, size=14, color=theme["text_muted"], align="center")


_LAYOUTS = {
    "title":      _layout_title,
    "section":    _layout_section,
    "content":    _layout_content,
    "image":      _layout_image,
    "two_column": _layout_two_column,
    "quote":      _layout_quote,
    "kpi":        _layout_kpi,
    "chart":      _layout_chart,
    "closing":    _layout_closing,
}


@mcp.tool()
def export_pptx(
    title: str,
    slides_json: str,
    output_filename: str,
    theme: str = "dark",
) -> str:
    """
    Generate a polished PowerPoint slide deck (.pptx) using AI-driven
    layouts. Picks a layout per slide based on its `type` field and
    composes a coherent visual story across slides.

    Available `type` values (let the content drive the choice):
      • title       — cover slide. {title, subtitle?}
      • section     — divider between major parts of the deck. {title, subtitle?}
      • content     — bullets with a small lead-in. {title, subtitle?, bullets[]}
      • image       — full-width image with caption. {title, image_path, note?}
      • two_column  — side-by-side columns; each column = {heading?, bullets?[],
                      image_path?, body?}. Spec: {title, left:{…}, right:{…}}
      • quote       — large pull-quote with attribution. {text, attribution?}
      • kpi         — 2–4 standout numbers in cards.
                      {title, kpis:[{value, label, change?}, …]}
      • chart       — native PowerPoint chart (editable after generation).
                      {title, chart_type: bar|column|line|pie|area|doughnut,
                       categories:[…], series:[{name, values:[…]}, …], note?}
      • closing     — thank-you / next-steps. {title?, subtitle?, contact?}

    theme: "dark" (default), "light", or "corporate".

    output_filename: saved under /app/data/reports/ (e.g. 'q3_report.pptx')
    Returns: absolute path to saved PPTX.
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ImportError:
        return "[ERROR] python-pptx is not installed."

    palette = _PPTX_THEMES.get(theme, _PPTX_THEMES["dark"])
    template = _template_path(theme)

    try:
        slides = json.loads(slides_json)
        # Load the branded template so the deck inherits theme colours,
        # fonts and master-slide background. Falls back to dark when the
        # requested theme isn't shipped.
        prs = Presentation(str(template))
        prs.core_properties.title = title
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)
        # The template ships with a single blank layout at index 6 (the
        # default Office "Blank" layout).
        blank_layout = prs.slide_layouts[6]

        total = len(slides)
        for idx, slide_data in enumerate(slides, start=1):
            slide = prs.slides.add_slide(blank_layout)
            _set_bg(slide, palette["bg"])

            stype = (slide_data.get("type") or "content").lower()
            layout_fn = _LAYOUTS.get(stype, _layout_content)
            layout_fn(slide, slide_data, palette)

            # Slide number bottom-right, except on cover/section/closing
            # where chrome would feel out of place.
            if stype not in ("title", "section", "closing"):
                from pptx.enum.text import PP_ALIGN
                num_box = slide.shapes.add_textbox(Inches(12.3), Inches(7.1), Inches(0.8), Inches(0.3))
                tf_num = num_box.text_frame
                p_num = tf_num.paragraphs[0]
                p_num.alignment = PP_ALIGN.RIGHT
                run_num = p_num.add_run()
                run_num.text = f"{idx} / {total}"
                run_num.font.size = Pt(9)
                run_num.font.color.rgb = _pp_color(palette["text_muted"])

        ensure_dir(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR)
        out_path = abs_reports(output_filename)
        prs.save(out_path)
        return f"[OK] PPTX saved: {out_path}"

    except Exception as e:
        return f"[ERROR] PPTX export failed: {e}\n{traceback.format_exc()}"
