import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents import LlmAgent

from instruction import build_instruction
from mcp_toolsets import load_all_mcp_toolsets
from models import selected_model
from skills import load_all_skills

# Tools = MCP toolsets + Skill toolset
tools = list(load_all_mcp_toolsets())
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
)
