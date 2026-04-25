---
name: report-generation
description: >
  Generate business reports and presentation decks: HTML reports, PDF export,
  PowerPoint (PPTX) slide decks, and executive summaries. Use when asked to
  create a report, generate a PDF, build a slide deck, or produce a deliverable
  document from analysis results or charts.
---

# Report Generation Skill

## Required Packages
```
pip_install("reportlab weasyprint python-pptx jinja2")
```

## 1. HTML Report Template

```python
from jinja2 import Template
from pathlib import Path

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Helvetica Neue', sans-serif; margin: 40px; color: #333; }
    h1   { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; }
    h2   { color: #444; margin-top: 32px; }
    .metric { display: inline-block; background: #f0f4ff; border-radius: 8px;
              padding: 16px 24px; margin: 8px; text-align: center; }
    .metric .value { font-size: 28px; font-weight: bold; color: #1a73e8; }
    .metric .label { font-size: 12px; color: #666; margin-top: 4px; }
    img { max-width: 100%; border-radius: 4px; margin: 16px 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
    th { background: #f5f5f5; }
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  <p>{{ period }} | 產生時間：{{ generated_at }}</p>

  <h2>關鍵指標</h2>
  {% for m in metrics %}
  <div class="metric">
    <div class="value">{{ m.value }}</div>
    <div class="label">{{ m.label }}</div>
  </div>
  {% endfor %}

  <h2>分析摘要</h2>
  <p>{{ summary }}</p>

  {% for chart in charts %}
  <h2>{{ chart.title }}</h2>
  <img src="{{ chart.path }}" alt="{{ chart.title }}">
  {% endfor %}
</body>
</html>
"""

def render_html_report(title, period, metrics, summary, charts, output_path):
    """Render an HTML report from structured data."""
    from datetime import datetime
    html = Template(TEMPLATE).render(
        title=title,
        period=period,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        metrics=metrics,
        summary=summary,
        charts=charts,
    )
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"HTML report saved: {output_path}")
```

## 2. PDF from HTML

```python
# Option A: weasyprint (better CSS support)
from weasyprint import HTML
HTML(filename="report.html").write_pdf("report.pdf")

# Option B: reportlab (more control, no CSS)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=A4)
styles = getSampleStyleSheet()
story = [
    Paragraph("Report Title", styles["Title"]),
    Paragraph("Summary text here...", styles["Normal"]),
    Image("chart.png", width=400, height=280),
]
doc.build(story)
```

## 3. PowerPoint Slide Deck

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()
slide_layout = prs.slide_layouts[1]  # Title and Content

# Title slide
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "業務分析報告"
slide.placeholders[1].text = "2024 Q1"

# Content slide
slide = prs.slides.add_slide(slide_layout)
slide.shapes.title.text = "關鍵指標"
tf = slide.placeholders[1].text_frame
tf.text = f"總營收：$2.3M (+18.4%)"
tf.add_paragraph().text = "最大類別：電子產品（42%）"
tf.add_paragraph().text = "異常月份：3月（-22%）"

# Chart slide
slide = prs.slides.add_slide(slide_layout)
slide.shapes.title.text = "銷售趨勢"
slide.shapes.add_picture("chart.png", Inches(1), Inches(1.5), Inches(8), Inches(5))

prs.save("report.pptx")
print("PPTX saved: report.pptx")
```

## 4. Output Checklist

Before reporting as complete:
- [ ] Charts saved as `.png` files in `outputs/`
- [ ] `summary.json` with key metrics
- [ ] HTML report generated and opens correctly in browser
- [ ] PDF exported from HTML
- [ ] All files placed under `{COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS}/`
