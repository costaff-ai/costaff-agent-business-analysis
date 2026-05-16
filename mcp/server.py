import os

from core import mcp
import tools  # noqa: F401 — registers all @mcp.tool() decorators

if __name__ == "__main__":
    # --- EXPERIMENT 2026-05-16: SSE transport race test -------------------
    # Temporarily serve the deprecated SSE transport so we can empirically
    # measure whether the anyio cancel-scope race (#4454) is specific to
    # streamable-http or transport-agnostic. SSE is DEPRECATED upstream
    # (MCP spec 2025-03-26, removal mid-2026) — this is a measurement only,
    # NOT a production change. `git revert` restores the streamable-http +
    # /api/tool shim setup (the verified race-free production solution).
    #
    # FastMCP binds host/port from its constructor (core.py:
    # FastMCP("business-analysis-mcp", host="0.0.0.0", port=8083)).
    # transport="sse" serves the SSE stream at /sse + POST /messages/.
    mcp.run(transport="sse")
    # --- end experiment --------------------------------------------------
