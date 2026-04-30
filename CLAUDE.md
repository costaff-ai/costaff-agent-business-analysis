# CoStaff BA Agent 開發規範

適用於 `costaff-agent-business-analysis/` 的專屬準則。通用 Agent 規範見上層 `costaff-agent/CLAUDE.md`。

## 0. Skills 知識庫

| Skill 檔案 | 適用情境 |
|---|---|
| `skill/costaff-agent-business-analysis/BA_AGENT_DESIGN_SKILL.md` | 修改 instruction、診斷幻覺、設計 skill |

> 先讀通用 `skill/costaff-agent/` 下的三個 skill，再讀本 skill。

## 1. Port 對照

| 容器 | Port | 用途 |
|---|---|---|
| `costaff-agent-business-analysis` | `8081` | A2A endpoint |
| `costaff-mcp-business-analysis` | `8083` | BA MCP tools |

`agent.py` 的 `DEFAULT_MCP_URL` 必須指向 `8083`，不是 `8081`。

## 2. 幻覺診斷快速確認

```bash
# 判斷是路徑幻覺還是工具名稱幻覺
docker logs costaff-mcp-business-analysis --since 5m 2>&1 | grep -E "CallToolRequest|ListToolsRequest"
# 只有 ListToolsRequest → 路徑幻覺（工具從未被呼叫）
# 有 CallToolRequest 但出錯 → 工具名稱幻覺

docker logs costaff-agent-business-analysis --since 5m 2>&1 | grep "Tool.*not found"
```

## 3. 測試

```bash
cd costaff-agent/costaff-agent-business-analysis
python3 -m pytest tests/ --cov=mcp/tools --cov-report=term-missing
```

測試架構需在 `conftest.py` 注入假的 `core` module（因為 `mcp/tools/` 使用絕對 import `from core import ...`）。詳見 `BA_AGENT_DESIGN_SKILL.md` Section 6。
