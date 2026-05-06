---
name: report-generation
description: >
  Mode B — Document Formatting, and the final report/export step for all modes.
  Use for Mode B when input is Q&A, articles, code examples, or structured text.
  Also handles create_report_from_markdown, create_html_report, export_pdf, and
  export_pptx for Mode A and Mode C after analysis is complete.
---

# Report Generation Skill

All reports are produced by calling MCP tools — do NOT write Python code or
import libraries directly.

---

## Mode B Workflow — Document Formatting

Use when the input is Q&A, articles, interview questions, code examples, or
any structured non-numerical text.

### Step 1. Read the Content

```
Tool: read_result(filepath)
```

`filepath` is relative to `/app/data/shared/` and **must include the source agent's project subdirectory**, e.g. `costaff-agent-coding/wine-svm/outputs/results.json` — never just `costaff-agent-coding/results.json`.

### Step 2. Format as Markdown

Compose the full report body as a Markdown string:
- Title heading at the top
- `##` section per item / question
- Fenced ` ``` ` code blocks for any code
- Answer and explanation clearly separated

### Step 3. Build the Report → see **Building the Report** below.

---

## Building the Report (all modes)

### Choose the right tool

| Report content | Tool |
|---|---|
| Contains **code snippets**, backslashes, or regex patterns | `create_report_from_markdown()` |
| Pure data/numbers with metric cards and chart images | `create_html_report()` |

When in doubt, use `create_report_from_markdown()` — it handles any content safely.

---

### create_report_from_markdown

```
Tool: create_report_from_markdown
Args:
  title           — report title
  markdown_content — full body as a Markdown string
  output_filename  — kebab-case `<report-name>/<file>.html`,
                     e.g. "python-interview/python_questions.html"
```

The directory part MUST be the kebab-case `<report-name>/` from the caller's plan (or derived from the task topic). Never use a bare filename without subdirectory.

### Image references in markdown (CRITICAL)

When embedding charts in `markdown_content`, the `src` MUST be either:
- A **bare filename** that lives next to the HTML (e.g. `![alt](chart.png)`), OR
- A **path relative to the BA shared root** (e.g. `![alt](sales-q3-report/chart.png)`), OR
- An **absolute path** starting with `/app/data/` (e.g. `![alt](/app/data/shared/costaff-agent-business-analysis/sales-q3-report/chart.png)`).

**NEVER use a remote URL** (`http://`, `https://`, `https://raw.githubusercontent.com/...`). The tool now rejects markdown containing remote image URLs because gemini has been observed hallucinating them — `WeasyPrint` would silently produce an image-less PDF. If you find yourself wanting to write a URL, you're doing it wrong: use the exact filename that `generate_chart` just returned to you.

Correct:
```markdown
![房價與 PM2.5 對比](taipei-q3-report/price_vs_pm25.png)
```

Wrong (will be rejected):
```markdown
![房價與 PM2.5 對比](https://raw.githubusercontent.com/.../price_vs_pm25.png)
```

Markdown structure example:
```markdown
## Introduction
...

## Section 1
### Sub-topic
Content with `inline code` and:
```python
def example():
    return 42
```

## Summary
- Point 1
- Point 2
```

---

### create_html_report (data-heavy reports only)

```
Tool: create_html_report
Args:
  title        — report title
  sections_json — JSON array:
    [
      {"type": "heading", "text": "Results Summary"},
      {"type": "metric",  "label": "Accuracy",  "value": "97.2%"},
      {"type": "metric",  "label": "F1 Score",  "value": "0.96"},
      {"type": "text",    "text": "The model achieved..."},
      {"type": "image",   "path": "/app/data/shared/costaff-agent-business-analysis/sales-q3-report/chart.png",
                          "caption": "Confusion Matrix"},
      {"type": "divider"}
    ]
  output_filename — e.g. "sales-q3-report/sales_report.html"
```

**WARNING**: Do NOT put code snippets in `sections_json`. Use `create_report_from_markdown()` instead.

---

### export_pdf (ALWAYS — every mode)

After `create_report_from_markdown()` or `create_html_report()` returns `[OK]`:

```
Tool: export_pdf
Args:
  html_filename   — same path from create_report_from_markdown / create_html_report,
                    e.g. "python-interview/python_questions.html"
  output_filename — same path with .pdf, e.g. "python-interview/python_questions.pdf"
```

Copy the **exact return string** into your response as the PDF path.

---

### export_pptx (only when explicitly requested)

```
Tool: export_pptx
Args:
  title       — deck title
  slides_json — JSON array:
    [
      {"type": "title",   "title": "Q3 Sales Report", "subtitle": "CoStaff BI"},
      {"type": "content", "title": "Key Metrics",
                          "bullets": ["Revenue: $2.3M", "Growth: +18.4%"]},
      {"type": "image",   "title": "Revenue Trend",
                          "image_path": "/app/data/shared/costaff-agent-business-analysis/sales-q3-report/trend.png",
                          "note": "Strong Q3 recovery."}
    ]
  output_filename — e.g. "sales-q3-report/q3_report.pptx"
```

---

## Output Checklist

Before reporting as complete:
- [ ] `create_report_from_markdown()` or `create_html_report()` returned `[OK]`
- [ ] `export_pdf()` called and returned `[OK] PDF saved: <path>`
- [ ] Report the **exact return string** from `export_pdf()` — never construct your own path
- [ ] All output files are under `/app/data/shared/costaff-agent-business-analysis/<report-name>/` — **never directly at the agent root**
