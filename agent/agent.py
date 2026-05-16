import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents import LlmAgent

from instruction import build_instruction
from models import selected_model
from skills import load_all_skills
from tools import load_all_function_tools

# Tools = native httpx-backed function tools (BA's own + 4 shared
# manager-core) + Skill toolset. NO McpToolset: the BA agent process
# holds zero MCP streamable-http client, so the ADK/anyio CancelScope
# cross-task race (google/adk-python#4454) cannot occur. The MCP servers
# still run and hold all real logic — only the transport is httpx now.
tools = list(load_all_function_tools())
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
    tools=tools,
    sub_agents=[],
    # Leaf agent: A2A response auto-returns control to the manager.
    # Both flags + empty sub_agents → ADK uses SingleFlow and omits the
    # transfer-to-agent system prompt, preventing Gemini from hallucinating
    # `transfer_to_agent` calls that would crash the run.
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
