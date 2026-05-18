import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents import LlmAgent

from instruction import build_instruction
from mcp_toolsets import load_all_mcp_toolsets
from models import selected_model
from skills import load_all_skills
from tools import load_costaff_api_tools
from progress import before_model_callback  # SPIKE: observability only

# Tools =
#   - BA's own MCP via McpToolset, transport SSE by default (race-free
#     under to_a2a; MCP_BA_TRANSPORT=streamable-http to switch back once
#     ADK fixes #4454). See mcp_toolsets/.
#   - the 4 shared manager-core tools via the costaff-core HTTP shim
#     (httpx, no MCP client, keeps BA off a 2nd MCP session). See
#     agent/tools/costaff_api.py.
#   - skills.
tools = list(load_all_mcp_toolsets())
tools.extend(load_costaff_api_tools())
tools.append(load_all_skills())

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
    # SPIKE (observability only, returns None): does the model's actual
    # LlmRequest contain PROGRESS_CONTEXT? If yes, a reliable automatic
    # panel is achievable (before_model parse → state → tool callbacks).
    before_model_callback=before_model_callback,
    tools=tools,
    sub_agents=[],
    # Leaf agent: A2A response auto-returns control to the manager.
    # Both flags + empty sub_agents → ADK uses SingleFlow and omits the
    # transfer-to-agent system prompt, preventing Gemini from hallucinating
    # `transfer_to_agent` calls that would crash the run.
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
