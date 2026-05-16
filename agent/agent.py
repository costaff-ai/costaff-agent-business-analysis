import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

from instruction import build_instruction
from models import selected_model
from skills import load_all_skills
from tools import load_costaff_api_tools

# --- EXPERIMENT 2026-05-16: SSE transport race test ----------------------
# Isolate one variable: BA's OWN tools go back through an MCP client, but
# via the DEPRECATED SSE transport instead of streamable-http, to measure
# empirically whether the anyio cancel-scope race (#4454) is
# streamable-http-specific or transport-agnostic. The 4 shared
# manager-core tools stay on the verified race-free httpx path so they
# don't confound the result. `git revert` restores the all-httpx
# (race=0, verified) production setup.
_BA_SSE_URL = os.getenv(
    "MCP_BA_SSE_URL", "http://costaff-mcp-business-analysis:8083/sse"
)
tools = [
    McpToolset(connection_params=SseConnectionParams(url=_BA_SSE_URL)),
    *load_costaff_api_tools(),   # shared 4 — unchanged, httpx, race-free
]
tools.append(load_all_skills())
# --- end experiment ------------------------------------------------------

# Instruction (placeholders resolved here)
instruction = build_instruction()

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
    sub_agents=[],
    # Leaf agent: A2A response auto-returns control to the manager.
    # Both flags + empty sub_agents → ADK uses SingleFlow and omits the
    # transfer-to-agent system prompt, preventing Gemini from hallucinating
    # `transfer_to_agent` calls that would crash the run.
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
