import os

from core import mcp
import tools  # noqa: F401 — registers all @mcp.tool() decorators

if __name__ == "__main__":
    import uvicorn

    from http_api import register_http_api

    # Build the Starlette app explicitly (instead of mcp.run()) so we can
    # mount the plain-HTTP tool shim alongside the MCP /mcp endpoint. The
    # shim lets the BA agent call tools via httpx (no MCP client → no
    # anyio cancel-scope race) while the MCP /mcp endpoint stays available
    # for anything that still wants it.
    app = mcp.streamable_http_app()
    register_http_api(app)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("MCP_BA_PORT", "8083")),
        log_level="info",
    )
