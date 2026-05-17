import os

from core import mcp
import tools  # noqa: F401 — registers all @mcp.tool() decorators

if __name__ == "__main__":
    # Transport is env-selectable. Default = SSE: empirically race-free
    # under to_a2a()+ADK1.33 (the streamable-http anyio CancelScope race
    # google/adk-python#4454 does NOT occur on SSE — verified 2026-05-16).
    # SSE is deprecated upstream (MCP spec 2025-03-26) but is the
    # transport Google's own multi-agent ADK examples use; keep
    # MCP_TRANSPORT=streamable-http as the switch-back path for when
    # ADK fixes #4454. FastMCP binds host/port from its constructor.
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)
