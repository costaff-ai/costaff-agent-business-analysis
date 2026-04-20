# Mateclaw Viz Report Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![mateclaw.agent.json](https://img.shields.io/badge/mateclaw-compatible-blue.svg)](https://github.com/MateClawAI/mateclaw)

[繁體中文](./README_zhtw.md) | **English**

**Mateclaw Viz Report Agent** is a data visualisation and report generation agent built on **Google ADK** and the **A2A protocol**. It reads analysis results from file paths or structured text, generates charts (PNG), and produces HTML or PDF reports — returning the report path to the orchestrating agent.

Designed as a first-party external agent for the [Mateclaw](https://github.com/MateClawAI/mateclaw) platform, it can also run standalone or integrate with any A2A-compatible system.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [MCP Extensions](#mcp-extensions)
- [mateclaw.agent.json](#mateclawagentjson)
- [Input & Output](#input--output)
- [License](#license)

---

## How It Works

```
Mateclaw Agent
     │
     │  A2A Protocol (/.well-known/agent.json)
     ▼
Viz Report Agent  ──►  MCP Viz Server  ──►  Chart & Report Generation
                             │
                             └──►  /app/data/reports/
```

Two input modes are supported:

1. **File path mode** — Receives a file path from `mateclaw-coding-agent` output (e.g. `/app/data/coding_workspace/result.json`) and reads the data
2. **Direct content mode** — Receives structured text content directly from the orchestrating agent

The agent then:
- Generates PNG charts via matplotlib / plotly
- Composes an HTML report with embedded charts and summary
- Saves everything to `/app/data/reports/`
- Returns the report path to the caller

---

## Features

- **Chart generation** — PNG charts (bar, line, scatter, pie, heatmap) via dedicated MCP tooling
- **HTML report generation** — styled, self-contained HTML reports with embedded charts
- **PDF export** — convert reports to PDF on demand
- **A2A-compatible** — exposes `/.well-known/agent.json` health endpoint
- **Dynamic MCP support** — additional MCP servers can be assigned at runtime from the Mateclaw dashboard without redeployment
- **Multi-model support** — works with Google Gemini natively or any LiteLLM-compatible provider
- **Shared volume integration** — reads from `coding_workspace`, writes to `reports/` — both on the shared volume
- **mateclaw.agent.json manifest** — declares capabilities for Mateclaw platform discovery

---

## Architecture

```
mateclaw-viz-report-agent/
├── agent/                    # ADK agent definition
│   ├── agent.py              # LlmAgent with dynamic MCP loading
│   ├── utils/
│   │   └── instructions.py   # System prompt
│   └── requirements.txt
├── mcp/                      # MCP Viz Server
│   ├── server.py             # FastMCP server exposing chart & report tools
│   └── requirements.txt
├── docker-compose.yaml       # Standalone deployment
└── mateclaw.agent.json       # Mateclaw platform manifest
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Google Gemini API Key **or** LiteLLM-compatible provider

### Standalone

```bash
# Clone
git clone https://github.com/MateClawAI/mateclaw-viz-report-agent.git
cd mateclaw-viz-report-agent

# Configure
cp agent/.env.example agent/.env
# Edit agent/.env with your API key

# Start
docker compose up -d --build
```

The agent will be available at `http://localhost:8081`.

### Via Mateclaw Platform

Deploy directly from the Mateclaw CLI:

```bash
mateclaw agent deploy --local /path/to/mateclaw-viz-report-agent
```

Mateclaw will read `mateclaw.agent.json`, build and start the containers, register the agent, and wire it into the ecosystem automatically.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API key |
| `VIZ_REPORT_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Model name for Gemini provider |
| `MATECLAW_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` or `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | Model name for LiteLLM provider |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `MCP_VIZ_URL` | ❌ | `http://mcp-viz-report:8083/sse` | Internal MCP Viz Server URL |
| `CODING_WORKSPACE_DIR` | ❌ | `/app/data/coding_workspace` | Input directory (from coding agent) |
| `REPORTS_DIR` | ❌ | `/app/data/reports` | Output directory for reports |
| `VIZ_REPORT_AGENT_MCP_URLS` | ❌ | — | JSON dict of extra MCP servers (set via Mateclaw dashboard) |

---

## MCP Extensions

The Viz Report Agent always connects to its own **MCP Viz Server** for chart and report generation.

Additional MCPs can be assigned dynamically from the **Mateclaw dashboard** under `Agents → viz-report-agent → MCP Extensions → Apply & Restart` — no redeployment needed.

Extra MCPs are passed via `VIZ_REPORT_AGENT_MCP_URLS` as a JSON dict:

```json
{
  "my-data-mcp": {
    "url": "https://my-data-mcp.internal/mcp",
    "transport": "streamable",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

---

## mateclaw.agent.json

```json
{
  "name": "viz-report-agent",
  "version": "0.0.1",
  "description": "Reads analysis results, generates chart visualisations and HTML reports, returns the report path.",
  "a2a_service": { "port": 8081, "health_path": "/.well-known/agent.json" },
  "env_required": ["GOOGLE_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "VIZ_REPORT_AGENT_MCP_URLS"
}
```

---

## Input & Output

### Input

| Mode | Description |
|------|-------------|
| File path | Path to a `.json` / `.csv` file produced by `mateclaw-coding-agent` |
| Direct content | Structured text, tables, or summaries passed directly in the task message |

### Output

| Type | Location | Description |
|------|----------|-------------|
| PNG charts | `/app/data/reports/` | Individual chart images |
| HTML report | `/app/data/reports/` | Self-contained report with embedded charts |
| PDF report | `/app/data/reports/` | PDF version (on request) |

> This agent does **not** execute code or perform computation. Computation is handled by [`mateclaw-coding-agent`](https://github.com/MateClawAI/mateclaw-coding-agent).

---

## License

Distributed under the MIT License. See `LICENSE` for details.
