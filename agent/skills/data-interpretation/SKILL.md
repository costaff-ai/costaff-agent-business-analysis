---
name: data-interpretation
description: >
  Mode A — Data Analysis. Use when the input contains numbers, metrics, CSV,
  ML results, or time-series data. Read and analyse the data, choose charts,
  write narrative, then hand off to report-generation skill for the final report.
---

# Data Interpretation Skill (Mode A)

## Workflow

### Step 1. Read the Data

**CRITICAL — exact tool names (do NOT invent names):**

```
Tool: read_csv(filepath)        — for CSV files (.csv)
Tool: read_result(filepath)     — for JSON / text result files (.json, .txt, .md)
Tool: list_workspace(subdir)    — to discover available files first
```

`read_file` does **NOT** exist. Use `read_result` for any non-CSV file.

`filepath` is relative to `/app/data/shared/` and **must include the source agent's project subdirectory**, e.g. `costaff-agent-coding/wine-svm/results.json`. A path like `costaff-agent-coding/results.json` (no project subdir) is wrong — the coding agent never writes at its root. The inner layout (whether the file sits at the project root or under an inner directory like `outputs/`) is decided by the source agent or the caller's spec — use the exact path the Manager handed you, do not infer.

### Step 2. Analyse

```
Tool: analyze_data(data_json)
```

Pass the `records` array from `read_csv()` or the raw JSON from `read_result()`.
Returns: min, max, mean, median, std, trend, top3/bottom3 per column.

### Step 3. Choose 1–4 Charts

| Data pattern | Best chart |
|---|---|
| Comparison across categories | `bar` |
| Change over time / trend | `line` or `area` |
| Part-of-whole / composition | `pie` (≤ 6 categories) |
| Distribution / spread | `histogram` or `box` |
| Relationship between two variables | `scatter` |
| ML confusion matrix | `confusion_matrix` |
| Correlation matrix | `heatmap` |
| Multiple series comparison | `multi_bar` or `multi_line` |

```
Tool: generate_chart(data_json, chart_type, title, output_filename, xlabel, ylabel)
```

`output_filename` MUST be `<report-name>/<descriptive_name>.png`, e.g. `sales-q3-report/revenue_trend.png`. The directory part is the kebab-case `<report-name>/` from the caller's plan. **Never** use a bare filename like `revenue_trend.png` — it would land at the BA shared root, which is forbidden.

**Tip — distribution plots for many features**: when the task is "show distributions / histograms / boxplots for these N features from a CSV", call `generate_distribution_plots(csv_path, features, output_subdir)` once instead of looping `generate_chart()`. Saves several minutes by collapsing N round-trips into one.

### Step 4. Write Narrative

For each chart and key metric, write **1–2 sentences: fact + implication**.

Structure:
1. **Overview** — what the data covers, time period, total records
2. **Headline finding** — the single most important insight
3. **Supporting details** — 2–3 key metrics with numbers
4. **Trend or comparison** — direction and magnitude
5. **Anomaly or highlight** — anything unexpected

Example:
> "2024 Q1 recorded 12,450 sales totalling $2.3M, up 18.4% year-on-year.
> Electronics led at 42% share, adding $120K month-on-month.
> March showed an unexpected -22% dip worth investigating."

### Step 5. Build the Report

Hand off to the `report-generation` skill with the charts and narrative ready.

---

## Key Metrics to Extract

For any dataset, identify:
- **Total / sum** — overall scale
- **Average / median** — typical value
- **Min / max** — range and extremes
- **Period-over-period change** — `(new - old) / old * 100`
- **Top N** — ranked leaders
- **Outliers** — values > 2× standard deviation from mean

```python
# Growth rate
growth = (current - previous) / previous * 100

# Top 5
top5 = df.nlargest(5, "revenue")[["category", "revenue"]]

# Outliers (IQR method)
Q1, Q3 = df["value"].quantile([0.25, 0.75])
IQR = Q3 - Q1
outliers = df[(df["value"] < Q1 - 1.5*IQR) | (df["value"] > Q3 + 1.5*IQR)]
```

## Metric Cards for the Report

Pass the most important 2–5 numbers as `{"type": "metric"}` blocks to `create_html_report()`:

```json
[
  {"type": "metric", "label": "Total Revenue",  "value": "$2.3M"},
  {"type": "metric", "label": "Growth Rate",    "value": "+18.4%"},
  {"type": "metric", "label": "Top Category",   "value": "Electronics"},
  {"type": "metric", "label": "Anomalies",      "value": "1"}
]
```

All output files go under `/app/data/shared/costaff-agent-business-analysis/<report-name>/` — **inside a kebab-case `<report-name>/` subdirectory**, never at the BA shared root.
