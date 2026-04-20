# CoStaff Business Analysis Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/costaff-ai/costaff)

**繁體中文** | [English](./README.md)

**CoStaff Business Analysis Agent** 是基於 **Google ADK** 與 **A2A 協議**構建的商業智慧報告 Agent。能接受任意來源的資料（workspace 檔案、原始數字或結構化文字），自主選擇最合適的圖表類型、生成視覺化、撰寫分析敘事，最終產出完整的 PDF 報告或 PowerPoint 投影片。

> *「我把數字變成報告，讓任何人都能理解數據在說什麼。」*

作為 [CoStaff](https://github.com/costaff-ai/costaff) 平台的第一方外部 Agent，也可獨立運行或整合至任何支援 A2A 的系統。

---

## 目錄

- [運作原理](#運作原理)
- [功能特色](#功能特色)
- [專案架構](#專案架構)
- [快速開始](#快速開始)
- [環境變數](#環境變數)
- [MCP 工具](#mcp-工具)
- [MCP 擴充](#mcp-擴充)
- [costaff.agent.json](#costaffagentjson)
- [輸入與輸出](#輸入與輸出)
- [授權](#授權)

---

## 運作原理

```
CoStaff Agent
     │
     │  A2A 協議 (/.well-known/agent.json)
     ▼
Business Analysis Agent  ──►  MCP Business Analysis Server  ──►  圖表與報告
                                          │
                                          └──►  /app/data/reports/
```

每次任務的四步驟工作流程：

1. **理解資料** — 從 workspace 檔案（JSON/CSV）載入資料，或直接接受行內輸入
2. **分析資料** — 執行統計摘要，識別趨勢、異常值與關鍵指標
3. **自主視覺化** — 自行判斷並生成最合適的圖表，不需要外部指令
4. **產出報告** — 撰寫分析敘事，匯出 PDF 報告或 PPTX 投影片

---

## 功能特色

- **自主選擇圖表** — Agent 根據資料型態自動決定最適合的圖表類型，無需手動指定
- **10+ 圖表類型** — 長條圖、折線圖、面積圖、圓餅圖、散點圖、直方圖、箱型圖、多系列長條/折線、熱力圖、混淆矩陣
- **資料分析** — 統計摘要（最小值、最大值、平均值、中位數、標準差、趨勢、前後排名）
- **CSV 支援** — 透過 pandas 直接讀取 CSV 檔案，不只限於 JSON
- **分析敘事** — 為每張圖表和指標撰寫 1–2 句洞察說明
- **PDF 匯出** — 附有嵌入式圖表的完整 PDF 報告
- **PowerPoint 匯出** — 深色主題 PPTX 投影片，可直接拿去開會
- **受眾語言適配** — 根據情境調整語言深度（技術 vs. 業務受眾）
- **A2A 相容** — 提供 `/.well-known/agent.json` 健康檢查端點
- **動態 MCP 支援** — 可透過 CoStaff Dashboard 在不重新部署的情況下動態新增 MCP Server
- **多模型支援** — 原生支援 Google Gemini，或任何 LiteLLM 相容的模型提供者

---

## 專案架構

```
costaff-agent-business-analysis/
├── agent/
│   ├── agent.py                           # LlmAgent，含動態 MCP 載入邏輯
│   ├── agent_a2a.py                       # A2A Server 入口
│   ├── utils/
│   │   ├── __init__.py
│   │   └── instructions/
│   │       └── agent_instruction.md       # Agent 系統提示詞
│   └── requirements.txt
├── mcp/
│   ├── server.py                          # FastMCP Server — 所有分析與匯出工具
│   └── requirements.txt
├── docker-compose.yaml
└── costaff.agent.json
```

---

## 快速開始

### 前置需求

- Docker 與 Docker Compose
- Google Gemini API Key **或** LiteLLM 相容的模型提供者

### 獨立運行

```bash
git clone https://github.com/costaff-ai/costaff-agent-business-analysis.git
cd costaff-agent-business-analysis
```
# 設定 API Key
echo "GOOGLE_API_KEY=your_key_here" > .env

docker compose up -d --build
```

Agent 將在 `http://localhost:8081` 提供服務。

### 透過 CoStaff 平台部署

```bash
cst agent deploy --local /path/to/costaff-agent-business-analysis
```

CoStaff 會讀取 `costaff.agent.json`，自動建立容器、註冊 Agent，並接入整個生態系。

---

## 環境變數

| 變數名稱 | 必填 | 預設值 | 說明 |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API Key |
| `BUSINESS_ANALYSIS_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Gemini 模型名稱 |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` 或 `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | LiteLLM 模型名稱 |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API Base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API Key |
| `MCP_BA_URL` | ❌ | `http://costaff-mcp-business-analysis:8083/mcp` | 內部 MCP Server URL |
| `WORKSPACE_DIR` | ❌ | `/app/data/coding_workspace` | 資料輸入目錄 |
| `REPORTS_DIR` | ❌ | `/app/data/reports` | 報告輸出目錄 |
| `BUSINESS_ANALYSIS_AGENT_MCP_URLS` | ❌ | — | 額外 MCP Server 的 JSON 設定 |

---

## MCP 工具

內建 MCP Server 提供以下工具：

| 工具 | 說明 |
|---|---|
| `list_workspace(subdir)` | 列出資料 workspace 中的檔案 |
| `read_result(filepath)` | 讀取 JSON 或文字檔案 |
| `read_csv(filepath)` | 讀取 CSV 檔案 — 回傳欄位名稱、資料形狀、統計摘要與樣本資料 |
| `analyze_data(data_json)` | 統計摘要：最小值、最大值、平均值、中位數、標準差、趨勢、前後排名 |
| `generate_chart(...)` | 生成 PNG 圖表（10+ 種類型） |
| `create_html_report(...)` | 組合含有指標、圖表與敘事的 HTML 報告 |
| `export_pdf(...)` | 透過 WeasyPrint 將 HTML 報告轉換為 PDF |
| `export_pptx(...)` | 生成深色主題 PowerPoint 投影片 |

### 支援的圖表類型

`bar` · `line` · `area` · `pie` · `scatter` · `histogram` · `box` · `multi_bar` · `multi_line` · `heatmap` · `confusion_matrix`

---

## MCP 擴充

額外的 MCP 可從 **CoStaff Dashboard** 動態指派：`Agents → business-analysis-agent → MCP Extensions → Apply & Restart`，無需重新部署。

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
  "name": "business-analysis-agent",
  "version": "0.1.0",
  "description": "接收任意數據，自動選擇圖表類型、生成視覺化、撰寫分析敘事，產出 PDF 報告或投影片。",
  "a2a_service": { "port": 8081, "health_path": "/.well-known/agent.json" },
  "env_required": ["GOOGLE_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "BUSINESS_ANALYSIS_AGENT_MCP_URLS"
}
```

---

## 輸入與輸出

### 輸入

| 模式 | 說明 |
|---|---|
| Workspace 檔案 | 共享 workspace 中的 `.json` 或 `.csv` 檔案（如 `costaff-agent-coding` 的輸出） |
| 行內資料 | 直接在任務訊息中傳入的原始數字、表格或摘要 |

### 輸出

| 類型 | 位置 | 說明 |
|---|---|---|
| PNG 圖表 | `/app/data/reports/` | 各別圖表圖片 |
| HTML 報告 | `/app/data/reports/` | 中間產物（自包含格式） |
| PDF 報告 | `/app/data/reports/` | 主要交付物 — 每次都會生成 |
| PPTX 投影片 | `/app/data/reports/` | 投影片 — 明確要求時生成 |

> 本 Agent **不負責**執行程式碼或進行計算，專注於資料呈現與洞察分析。

---

## 授權

本專案採用 MIT 授權條款。詳見 `LICENSE`。
