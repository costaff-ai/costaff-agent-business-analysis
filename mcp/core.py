import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/data/costaff-agent-business-analysis")
SHARED_DIR = os.getenv("SHARED_DIR", "/app/data/shared")
COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS = os.getenv("COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS", "/app/data/shared/costaff-agent-business-analysis")

mcp = FastMCP("business-analysis-mcp", host="0.0.0.0", port=int(os.getenv("MCP_BA_PORT", "8083")))


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def abs_workspace(filename: str) -> str:
    return str(Path(WORKSPACE_DIR) / filename)


def abs_shared(filename: str) -> str:
    return str(Path(SHARED_DIR) / filename)


def abs_my_shared(filename: str) -> str:
    return str(Path(COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS) / filename)
