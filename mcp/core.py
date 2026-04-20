import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/data")
AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR = os.getenv("AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR", "/app/data/agent-business-analysis")

mcp = FastMCP("business-analysis-mcp", host="0.0.0.0", port=int(os.getenv("MCP_BA_PORT", "8083")))


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def abs_workspace(filename: str) -> str:
    return str(Path(WORKSPACE_DIR) / filename)


def abs_reports(filename: str) -> str:
    return str(Path(AGENT_BUSINESS_ANALYSIS_WORKSPACE_DIR) / filename)
