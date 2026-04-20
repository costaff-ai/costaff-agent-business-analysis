import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams, StreamableHTTPServerParams
from utils import AGENT_INSTRUCTION

def get_connection_params(entry):
    if isinstance(entry, str):
        url, headers, transport = entry, None, "sse" if "/sse" in entry else "streamable"
    else:
        url       = entry.get("url", "")
        headers   = entry.get("headers") or None
        transport = entry.get("transport", "streamable")
    if not url:
        raise ValueError("MCP entry has no URL")
    if transport == "sse" or "/sse" in url:
        return SseServerParams(url=url, headers=headers)
    return StreamableHTTPServerParams(url=url, headers=headers)

# Own MCP — always connected
MCP_VIZ_URL = os.getenv("MCP_VIZ_URL", "http://mcp-viz-report:8083/sse")
tools = [McpToolset(connection_params=SseServerParams(url=MCP_VIZ_URL))]
logger.info(f"Viz-Report MCP URL: {MCP_VIZ_URL}")

# Additional MCPs configured via mateclaw dashboard (VIZ_REPORT_AGENT_MCP_URLS)
raw_extra = os.getenv("VIZ_REPORT_AGENT_MCP_URLS", "")
if raw_extra:
    try:
        extra_config = json.loads(raw_extra)
        for mcp_name, entry in extra_config.items():
            if isinstance(entry, dict) and not entry.get("enabled", True):
                logger.info(f"Skipping disabled extra MCP: {mcp_name}")
                continue
            try:
                tools.append(McpToolset(connection_params=get_connection_params(entry)))
                logger.info(f"Added extra MCP: {mcp_name}")
            except Exception as e:
                logger.error(f"Failed to load extra MCP '{mcp_name}': {e}")
    except json.JSONDecodeError:
        logger.error("VIZ_REPORT_AGENT_MCP_URLS is not valid JSON, skipping extra MCPs")

model_provider = os.getenv("MATECLAW_AGENT_MODEL_PROVIDER", "gemini").lower()
model_name = os.getenv("VIZ_REPORT_AGENT_MODEL", "gemini-2.5-flash")

if model_provider == "litellm":
    from google.adk.models.lite_llm import LiteLlm
    selected_model = LiteLlm(
        model=os.getenv("LITELLM_MODEL_NAME"),
        api_base=os.getenv("LITELLM_API_BASE"),
        api_key=os.getenv("LITELLM_API_KEY"),
    )
    logger.info("Viz-Report Agent using LiteLLM model provider")
else:
    selected_model = model_name
    logger.info(f"Viz-Report Agent using model: {selected_model}")

viz_report_agent = LlmAgent(
    name="viz_report_agent",
    model=selected_model,
    description="讀取分析結果，生成圖表視覺化與 HTML 報告，回傳報告路徑。",
    instruction=AGENT_INSTRUCTION,
    tools=tools,
)
