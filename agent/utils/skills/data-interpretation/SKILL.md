---
name: data-interpretation
description: >
  Interpret structured data (JSON, CSV, numbers, tables) to extract business
  insights: identify trends, compare periods, spot anomalies, calculate growth
  rates, and write analytical narrative. Use when asked to analyse, summarise,
  explain, or draw conclusions from data — before generating charts or reports.
---

# Data Interpretation Skill

## 1. Reading the Data

```python
import json
import pandas as pd

# JSON result from coding agent
with open("results.json") as f:
    data = json.load(f)

# CSV
df = pd.read_csv("data.csv")
print(df.describe())
print(df.head(10))
```

## 2. Key Metrics to Extract

For any dataset, identify:
- **Total / sum** — overall scale
- **Average / median** — typical value
- **Min / max** — range and extremes
- **Period-over-period change** — growth rate `(new - old) / old * 100`
- **Top N** — ranked leaders
- **Outliers** — values > 2× standard deviation from mean

```python
# Growth rate
growth = (current - previous) / previous * 100
print(f"Growth: {growth:+.1f}%")

# Top 5
top5 = df.nlargest(5, "revenue")[["category", "revenue"]]

# Outliers (IQR method)
Q1, Q3 = df["value"].quantile([0.25, 0.75])
IQR = Q3 - Q1
outliers = df[(df["value"] < Q1 - 1.5*IQR) | (df["value"] > Q3 + 1.5*IQR)]
```

## 3. Narrative Writing Pattern

Structure analytical narrative as:

1. **Overview sentence** — what the data covers, time period, total records
2. **Headline finding** — the single most important insight
3. **Supporting details** — 2–3 key metrics with numbers
4. **Trend or comparison** — direction and magnitude
5. **Anomaly or highlight** — anything unexpected

Example:
> "2024 年第一季共記錄 12,450 筆銷售，總營收達 $2.3M，較去年同期成長 18.4%。
> 最大貢獻類別為「電子產品」（42% 佔比），環比增加 $120K。
> 值得注意的是，3 月單月營收出現異常下滑（-22%），可能需要進一步調查。"

## 4. Choosing Chart Types

| Data pattern | Recommended chart |
|-------------|------------------|
| Trend over time | Line chart |
| Category comparison | Bar / horizontal bar |
| Part-of-whole | Pie chart (≤ 6 categories) |
| Correlation | Scatter plot |
| Distribution | Histogram |
| Multiple metrics at once | Dashboard (2×2 grid) |

## 5. Output Format

Always produce:
1. A `summary.json` with key metrics (for programmatic consumption)
2. A written narrative (for the report)

```python
import json

summary = {
    "period": "2024-Q1",
    "total_records": int(len(df)),
    "total_revenue": float(df["revenue"].sum()),
    "growth_pct": float(growth),
    "top_category": str(top5.iloc[0]["category"]),
    "anomalies_found": int(len(outliers)),
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
```
