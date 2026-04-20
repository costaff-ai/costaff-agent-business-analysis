import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from utils import AGENT_INSTRUCTION

def get_connection_params(entry):
    if isinstance(entry, str):
        url, headers = entry, None
    else:
        url     = entry.get("url", "")
        headers = entry.get("headers") or None
    if not url:
        raise ValueError("MCP entry has no URL")
    return StreamableHTTPServerParams(url=url, headers=headers)

# Own MCP — always connected
# Try to use the service name derived from costaff naming convention first
mcp_token = os.getenv("MCP_SECRET_KEY", "REDACTED")
DEFAULT_MCP_URL = "http://costaff-ba-agent-mcp-business-analysis:8081/mcp"
MCP_BA_URL = os.getenv("MCP_BA_URL", DEFAULT_MCP_URL)

mcp_params = StreamableHTTPServerParams(
    url=MCP_BA_URL, 
    headers={"Authorization": f"Bearer {mcp_token}"}
)

tools = [McpToolset(connection_params=mcp_params)]
logger.info(f"Business Analysis MCP URL: {MCP_BA_URL}")

# Additional MCPs configured via CoStaff dashboard (BUSINESS_ANALYSIS_AGENT_MCP_URLS)
raw_extra = os.getenv("BUSINESS_ANALYSIS_AGENT_MCP_URLS", "")
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
        logger.error("BUSINESS_ANALYSIS_AGENT_MCP_URLS is not valid JSON, skipping extra MCPs")

model_provider = (os.getenv("BUSINESS_ANALYSIS_AGENT_MODEL_PROVIDER") or os.getenv("COSTAFF_AGENT_MODEL_PROVIDER") or "gemini").lower()
model_name = os.getenv("BUSINESS_ANALYSIS_AGENT_MODEL", "gemini-2.5-flash")

preferred_lang = os.getenv("COSTAFF_PREFERRED_LANGUAGE", "Traditional Chinese (繁體中文)")
instruction = AGENT_INSTRUCTION.replace("{PREFERRED_LANGUAGE}", preferred_lang)

if model_provider == "litellm":
    from google.adk.models.lite_llm import LiteLlm
    selected_model = LiteLlm(
        model=os.getenv("LITELLM_MODEL_NAME"),
        api_base=os.getenv("LITELLM_API_BASE"),
        api_key=os.getenv("LITELLM_API_KEY"),
    )
    logger.info("Business Analysis Agent using LiteLLM model provider")
else:
    selected_model = model_name
    logger.info(f"Business Analysis Agent using model: {selected_model}")

business_analysis_agent = LlmAgent(
    name="business_analysis_agent",
    model=selected_model,
    description=(
        "A business intelligence reporting agent that accepts any data source — "
        "workspace files (JSON/CSV), raw numbers, or structured text — "
        "autonomously selects appropriate chart types, generates visualisations, "
        "writes analytical narrative, and produces a PDF report or PowerPoint (PPTX) slide deck. "
        "Does not perform computation or modelling; focuses solely on presentation and insight."
    ),
    instruction=instruction,
    tools=tools,
)
