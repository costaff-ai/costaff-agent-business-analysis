---
name: knowledge-report
description: >
  Generate a PDF report on any topic or concept when no input data file is
  provided — e.g. "write a report on quantum mechanics", "introduction to
  machine learning", "explain blockchain". Compose the content from knowledge,
  then call create_report_from_markdown and export_pdf.
---

# Knowledge Report Skill

Use this skill for **Mode C** — when the user requests a report on a topic and
there is no file to read (no JSON, CSV, or workspace file referenced).

## Workflow

### Step 1. Do NOT call any data-reading tools
Skip `read_result()`, `read_csv()`, and `analyze_data()`. There is no input file.

### Step 2. Compose the Markdown content

Structure the report body as follows (adapt sections to the topic):

```markdown
## Introduction
What the topic is and why it matters. 2–3 sentences.

## Background / History
Key developments or context (if relevant).

## Core Concepts

### Concept 1
Explanation...

### Concept 2
Explanation...

## Applications
- Real-world use case 1
- Real-world use case 2
- Real-world use case 3

## Current State / Challenges
Where things stand today and open problems.

## Summary
- Key takeaway 1
- Key takeaway 2
- Key takeaway 3
```

Use fenced ` ``` ` blocks for formulas, equations, pseudocode, or any technical notation.

### Step 3. Call create_report_from_markdown

```
Tool: create_report_from_markdown
Args:
  title           — descriptive report title, e.g. "量子力學介紹"
  markdown_content — the full Markdown string from Step 2
  output_filename  — snake_case .html filename, e.g. "quantum_mechanics.html"
```

### Step 4. Call export_pdf

```
Tool: export_pdf
Args:
  html_filename   — same filename from Step 3, e.g. "quantum_mechanics.html"
  output_filename — same base name with .pdf, e.g. "quantum_mechanics.pdf"
```

### Step 5. Report back
Copy the **exact return value** of `export_pdf()` as the PDF path. Do not construct the path yourself.
