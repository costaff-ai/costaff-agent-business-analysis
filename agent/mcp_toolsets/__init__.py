"""MCP toolset loader for the business-analysis agent.

Loads:
    1. The agent's own MCP server (URL from MCP_BA_URL env var, defaults
       to costaff-mcp-business-analysis:8083). Authorization header is
       attached using MCP_SECRET_KEY.
    2. Any extra MCP servers configured via BUSINESS_ANALYSIS_AGENT_MCP_URLS
       (set by the CoStaff dashboard at deploy time).

Usage:
    from mcp_toolsets import load_all_mcp_toolsets
    toolsets = load_all_mcp_toolsets()  # list of McpToolset
"""
import json
import logging
import os
from typing import List

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams

logger = logging.getLogger(__name__)

DEFAULT_MCP_URL = "http://costaff-mcp-business-analysis:8083/mcp"


def _connection_params(entry):
    """Coerce an entry (string URL or dict) into StreamableHTTPServerParams."""
    if isinstance(entry, str):
        url, headers = entry, None
    else:
        url = entry.get("url", "")
        headers = entry.get("headers") or None
    if not url:
        raise ValueError("MCP entry has no URL")
    return StreamableHTTPServerParams(url=url, headers=headers)


def load_all_mcp_toolsets() -> List[McpToolset]:
    """Build the agent's MCP toolset list from env configuration."""
    toolsets: List[McpToolset] = []

    # Own MCP — always connected, with bearer auth
    own_url = os.getenv("MCP_BA_URL", DEFAULT_MCP_URL)
    mcp_token = os.getenv(
        "MCP_SECRET_KEY",
        "REDACTED",
    )
    own_params = StreamableHTTPServerParams(
        url=own_url,
        headers={"Authorization": f"Bearer {mcp_token}"},
    )
    toolsets.append(McpToolset(connection_params=own_params))
    logger.info(f"Business Analysis MCP URL: {own_url}")

    # Extra MCPs from CoStaff dashboard (e.g. costaff core MCP)
    raw_extra = os.getenv("BUSINESS_ANALYSIS_AGENT_MCP_URLS", "")
    if raw_extra:
        try:
            extra_config = json.loads(raw_extra)
        except json.JSONDecodeError:
            logger.error(
                "BUSINESS_ANALYSIS_AGENT_MCP_URLS is not valid JSON, skipping extra MCPs"
            )
            return toolsets

        for name, entry in extra_config.items():
            if isinstance(entry, dict) and not entry.get("enabled", True):
                logger.info(f"Skipping disabled extra MCP: {name}")
                continue
            tool_filter = entry.get("tool_filter") if isinstance(entry, dict) else None
            try:
                toolsets.append(McpToolset(
                    connection_params=_connection_params(entry),
                    tool_filter=tool_filter,
                ))
                if tool_filter:
                    logger.info(f"Added extra MCP: {name} (filtered to {len(tool_filter)} tools: {tool_filter})")
                else:
                    logger.info(f"Added extra MCP: {name} (no filter — all tools imported)")
            except Exception as e:
                logger.error(f"Failed to load extra MCP '{name}': {e}")

    return toolsets
