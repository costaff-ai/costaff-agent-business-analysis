# CoStaff Business Analysis Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.0-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/costaff-ai/costaff)

[繁體中文](./README_zhtw.md) | **English**

**CoStaff Business Analysis Agent** is a BI reporting agent built on **Google ADK** and the **A2A protocol**. It accepts any data source — workspace files, raw numbers, or structured text — autonomously selects the right chart types, generates visualisations, writes analytical narrative, and delivers a polished PDF report or PowerPoint slide deck.

> *"I turn numbers into reports that anyone can understand."*

Designed as a first-party external agent for the [CoStaff](https://github.com/costaff-ai/costaff) platform, it can also run standalone or integrate with any A2A-compatible system.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)
- [MCP Extensions](#mcp-extensions)
- [costaff.agent.json](#costaffagentjson)
- [Input & Output](#input--output)
- [License](#license)

---

## How It Works

```
CoStaff Agent
     │
     │  A2A Protocol (/.well-known/agent-card.json)
     ▼
Business Analysis Agent  ──►  MCP Business Analysis Server  ──►  Charts & Reports
                                          │
                                          └──►  /app/data/reports/
```

The agent follows a four-step workflow for every task:

1. **Understand** — load data from workspace files (JSON/CSV) or accept inline content
2. **Analyse** — run statistical summary to identify trends, outliers, and key metrics
3. **Visualise** — autonomously choose and generate the most appropriate charts
4. **Report** — compose analytical narrative and export a PDF report or PPTX slide deck

---

## Features

- **Autonomous chart selection** — agent decides the best chart type based on data shape, no manual instructions needed
- **10+ chart types** — bar, line, area, pie, scatter, histogram, box, multi-bar, multi-line, heatmap, confusion matrix
- **Data analysis** — statistical summary (min, max, mean, median, std, trend, top/bottom values)
- **CSV support** — reads CSV files directly via pandas, not just JSON
- **Analytical narrative** — writes 1–2 sentence insights per chart and metric
- **PDF export** — styled, self-contained PDF reports with embedded charts
- **PowerPoint export** — dark-themed PPTX slide decks ready for presentations
- **Audience adaptation** — adjusts language and depth for technical vs. business audiences
- **A2A-compatible** — exposes `/.well-known/agent-card.json` health endpoint
- **Dynamic MCP support** — additional MCP servers can be assigned at runtime from the CoStaff dashboard
- **Multi-model support** — works with Google Gemini natively or any LiteLLM-compatible provider

---

## Architecture

```
costaff-agent-business-analysis/
├── agent/
│   ├── agent.py                           # LlmAgent with dynamic MCP loading
│   ├── agent_a2a.py                       # A2A server entry point
│   ├── utils/
│   │   ├── __init__.py
│   │   └── instructions/
│   │       └── agent_instruction.md       # Agent system prompt
│   └── requirements.txt
├── mcp/
│   ├── server.py                          # FastMCP server — all analysis & export tools
│   └── requirements.txt
├── docker-compose.yaml
└── costaff.agent.json
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Google Gemini API Key **or** LiteLLM-compatible provider

### Standalone

```bash
git clone https://github.com/costaff-ai/costaff-agent-business-analysis.git
cd costaff-agent-business-analysis
```
# Set your API key
echo "GOOGLE_API_KEY=your_key_here" > .env

docker compose up -d --build
```

The agent will be available at `http://localhost:8081`.

### Via CoStaff Platform (recommended)

```bash
costaff agent add business-analysis --github https://github.com/costaff-ai/costaff-agent-business-analysis
```

The CLI clones the repo, builds the agent + MCP containers, registers the agent in `config.json`, and wires it into the shared workspace network automatically. `GOOGLE_API_KEY` (and any required secret) is prompted during `add`.

**Wiring mode — do NOT pass `--enable-transfer` for this agent.** It is registered as an **AgentTool** (the default, stable contract): the Manager calls it like a function and receives a clean text result. `--enable-transfer` exists *only* for agents whose sub-agent must receive **multimodal image input** — it switches the *entire* Manager into ADK transfer mode and carries session history (see `costaff-agent-nutrition`). This is a text-task agent, so the default is correct and recommended.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API key |
| `BUSINESS_ANALYSIS_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Model name for Gemini provider |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` or `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | Model name for LiteLLM provider |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `MCP_BA_URL` | ❌ | `http://costaff-mcp-business-analysis:8083/mcp` | Internal MCP server URL |
| `WORKSPACE_DIR` | ❌ | `/app/data/coding_workspace` | Input directory |
| `AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR` | ❌ | `/app/data/reports` | Output directory for reports |
| `BUSINESS_ANALYSIS_AGENT_MCP_URLS` | ❌ | — | JSON dict of extra MCP servers |

---

## MCP Tools

The built-in MCP server exposes the following tools:

| Tool | Description |
|---|---|
| `list_workspace(subdir)` | List files in the data workspace |
| `read_result(filepath)` | Read a JSON or text file |
| `read_csv(filepath)` | Read a CSV file — returns columns, shape, stats summary, and sample records |
| `analyze_data(data_json)` | Statistical summary: min, max, mean, median, std, trend, top/bottom values |
| `generate_chart(...)` | Generate a PNG chart (10+ types) |
| `create_html_report(...)` | Assemble a styled HTML report with metrics, charts, and narrative |
| `export_pdf(...)` | Convert HTML report to PDF via WeasyPrint |
| `export_pptx(...)` | Generate a dark-themed PowerPoint slide deck |

### Supported chart types

`bar` · `line` · `area` · `pie` · `scatter` · `histogram` · `box` · `multi_bar` · `multi_line` · `heatmap` · `confusion_matrix`

---

## MCP Extensions

Additional MCPs can be assigned dynamically from the **CoStaff dashboard** under `Agents → costaff-agent-business-analysis → MCP Extensions → Apply & Restart` — no redeployment needed.

```json
{
  "my-data-mcp": {
    "url": "https://my-data-mcp.internal/mcp",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

---

## costaff.agent.json

```json
{
  "name": "costaff-agent-business-analysis",
  "version": "0.1.0",
  "description": "接收任意數據，自動選擇圖表類型、生成視覺化、撰寫分析敘事，產出 PDF 報告或投影片。",
  "a2a_service": { "port": 8081, "health_path": "/.well-known/agent-card.json" },
  "env_required": ["GOOGLE_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "BUSINESS_ANALYSIS_AGENT_MCP_URLS"
}
```

---

## Input & Output

### Input

| Mode | Description |
|---|---|
| Workspace file | `.json` or `.csv` file in the shared workspace (e.g. from `costaff-agent-coding`) |
| Inline data | Raw numbers, tables, or summaries passed directly in the task message |

### Output

| Type | Location | Description |
|---|---|---|
| PNG charts | `/app/data/reports/` | Individual chart images |
| HTML report | `/app/data/reports/` | Intermediate self-contained report |
| PDF report | `/app/data/reports/` | Primary deliverable — always generated |
| PPTX deck | `/app/data/reports/` | Slide deck — generated when presentation is requested |

> This agent does **not** execute code or perform computation. It focuses solely on presentation and insight.

---

## License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
