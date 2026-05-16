"""Native function tools for the BA agent (httpx-backed, zero MCP client).

All BA tools — its own (charts/reports/pdf) and the 4 shared manager-core
tools — are reached via plain httpx.post to the respective HTTP shims.
The BA agent process therefore holds NO MCP streamable-http client, so
the ADK/anyio CancelScope cross-task race cannot occur.
"""
from .ba_tools import load_ba_tools
from .costaff_api import load_costaff_api_tools


def load_all_function_tools() -> list:
    return [*load_ba_tools(), *load_costaff_api_tools()]


__all__ = ["load_all_function_tools", "load_ba_tools", "load_costaff_api_tools"]
