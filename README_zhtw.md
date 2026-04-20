# Mateclaw Viz Report Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![mateclaw.agent.json](https://img.shields.io/badge/mateclaw-compatible-blue.svg)](https://github.com/MateClawAI/mateclaw)

**繁體中文** | [English](./README.md)

**Mateclaw Viz Report Agent** 是一個基於 **Google ADK** 和 **A2A 協議**構建的資料視覺化與報告生成 Agent。專門負責讀取分析結果（來自檔案路徑或結構化文字），生成圖表（PNG），並產出 HTML 或 PDF 報告，最後將報告路徑回傳給呼叫方 Agent。

作為 [Mateclaw](https://github.com/MateClawAI/mateclaw) 平台的第一方外部 Agent，也可獨立運行或整合至任何支援 A2A 的系統。

---

## 目錄

- [運作原理](#運作原理)
- [功能特色](#功能特色)
- [專案架構](#專案架構)
- [快速開始](#快速開始)
- [環境變數](#環境變數)
- [MCP 擴充](#mcp-擴充)
- [mateclaw.agent.json](#mateclawagentjson)
- [輸入與輸出](#輸入與輸出)
- [授權](#授權)

---

## 運作原理

```
Mateclaw Agent
     │
     │  A2A 協議 (/.well-known/agent.json)
     ▼
Viz Report Agent  ──►  MCP Viz Server  ──►  圖表與報告生成
                             │
                             └──►  /app/data/reports/
```

支援兩種輸入模式：

1. **檔案路徑模式** — 接收來自 `mateclaw-coding-agent` 的輸出檔案路徑（如 `/app/data/coding_workspace/result.json`）並讀取資料
2. **直接內容模式** — 直接接收來自呼叫方 Agent 的結構化文字內容

Agent 接著會：
- 透過 matplotlib / plotly 生成 PNG 圖表
- 組合包含圖表與摘要的 HTML 報告
- 將所有檔案儲存至 `/app/data/reports/`
- 將報告路徑回傳給呼叫方

---

## 功能特色

- **圖表生成** — 透過專用 MCP 工具生成 PNG 圖表（長條圖、折線圖、散點圖、圓餅圖、熱力圖）
- **HTML 報告生成** — 帶有嵌入式圖表的風格化、自包含 HTML 報告
- **PDF 匯出** — 依需求將報告轉換為 PDF
- **A2A 相容** — 提供 `/.well-known/agent.json` 健康檢查端點
- **動態 MCP 支援** — 可透過 Mateclaw Dashboard 在不重新部署的情況下動態新增 MCP Server
- **多模型支援** — 原生支援 Google Gemini，或任何 LiteLLM 相容的模型提供者
- **共享 Volume 整合** — 從 `coding_workspace` 讀取輸入，輸出至 `reports/`
- **mateclaw.agent.json 宣告** — 聲明功能供 Mateclaw 平台自動發現

---

## 專案架構

```
mateclaw-viz-report-agent/
├── agent/                    # ADK Agent 定義
│   ├── agent.py              # LlmAgent，含動態 MCP 載入邏輯
│   ├── utils/
│   │   └── instructions.py   # 系統提示詞
│   └── requirements.txt
├── mcp/                      # MCP Viz Server
│   ├── server.py             # FastMCP Server，提供圖表與報告工具
│   └── requirements.txt
├── docker-compose.yaml       # 獨立部署設定
└── mateclaw.agent.json       # Mateclaw 平台宣告文件
```

---

## 快速開始

### 前置需求

- Docker 與 Docker Compose
- Google Gemini API Key **或** LiteLLM 相容的模型提供者

### 獨立運行

```bash
# 克隆
git clone https://github.com/MateClawAI/mateclaw-viz-report-agent.git
cd mateclaw-viz-report-agent

# 設定環境變數
cp agent/.env.example agent/.env
# 編輯 agent/.env，填入 API Key

# 啟動
docker compose up -d --build
```

Agent 將在 `http://localhost:8081` 提供服務。

### 透過 Mateclaw 平台部署

直接從 Mateclaw CLI 部署：

```bash
mateclaw agent deploy --local /path/to/mateclaw-viz-report-agent
```

Mateclaw 會讀取 `mateclaw.agent.json`，自動建立容器、註冊 Agent，並接入整個生態系。

---

## 環境變數

| 變數名稱 | 必填 | 預設值 | 說明 |
|---------|------|--------|------|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API Key |
| `VIZ_REPORT_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Gemini 模型名稱 |
| `MATECLAW_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` 或 `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | LiteLLM 模型名稱 |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API Base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API Key |
| `MCP_VIZ_URL` | ❌ | `http://mcp-viz-report:8083/sse` | 內部 MCP Viz Server URL |
| `CODING_WORKSPACE_DIR` | ❌ | `/app/data/coding_workspace` | 輸入目錄（來自 coding agent） |
| `REPORTS_DIR` | ❌ | `/app/data/reports` | 報告輸出目錄 |
| `VIZ_REPORT_AGENT_MCP_URLS` | ❌ | — | 額外 MCP Server 的 JSON 設定（由 Mateclaw Dashboard 管理） |

---

## MCP 擴充

Viz Report Agent 預設連接自身的 **MCP Viz Server** 進行圖表與報告生成。

額外的 MCP 可從 **Mateclaw Dashboard** 動態指派：`Agents → viz-report-agent → MCP Extensions → Apply & Restart`，無需重新部署。

額外 MCP 透過 `VIZ_REPORT_AGENT_MCP_URLS` 環境變數以 JSON dict 格式傳入：

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
  "description": "讀取分析結果，生成圖表視覺化與 HTML 報告，回傳報告路徑。",
  "a2a_service": { "port": 8081, "health_path": "/.well-known/agent.json" },
  "env_required": ["GOOGLE_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "VIZ_REPORT_AGENT_MCP_URLS"
}
```

---

## 輸入與輸出

### 輸入

| 模式 | 說明 |
|------|------|
| 檔案路徑 | 由 `mateclaw-coding-agent` 產出的 `.json` / `.csv` 檔案路徑 |
| 直接內容 | 直接在任務訊息中傳入的結構化文字、表格或摘要 |

### 輸出

| 類型 | 位置 | 說明 |
|------|------|------|
| PNG 圖表 | `/app/data/reports/` | 各別圖表圖片 |
| HTML 報告 | `/app/data/reports/` | 嵌入圖表的自包含報告 |
| PDF 報告 | `/app/data/reports/` | PDF 版本（依需求生成） |

> 本 Agent **不負責**執行程式碼或進行計算。計算工作由 [`mateclaw-coding-agent`](https://github.com/MateClawAI/mateclaw-coding-agent) 負責。

---

## 授權

本專案採用 MIT 授權條款。詳見 `LICENSE`。
