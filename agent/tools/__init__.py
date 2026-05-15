"""Native function tools for the BA agent.

Currently exposes httpx wrappers for the shared manager-core tools so the
agent does NOT open a 2nd MCP session (which triggers the anyio
CancelScope race). See costaff_api.py.
"""
from .costaff_api import load_costaff_api_tools

__all__ = ["load_costaff_api_tools"]
