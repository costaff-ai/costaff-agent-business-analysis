"""Native function tools for the BA agent.

Only the 4 shared manager-core tools live here now — they reach the
costaff-core HTTP shim via httpx (no MCP client, keeps BA off a 2nd MCP
session, keeps DB/notifiers/tokens centralised). BA's OWN tools are
served by its MCP server and reached via McpToolset over SSE (see
agent/mcp_toolsets/), so they are no longer wrapped here.
"""
from .costaff_api import load_costaff_api_tools

__all__ = ["load_costaff_api_tools"]
