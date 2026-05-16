"""Plain-HTTP shim for this MCP server's tools.

The BA agent used to reach these tools via ADK's McpToolset
(streamable-http MCP client). Under ADK 1.24+/anyio 4.x + to_a2a(), that
client's `async with anyio.create_task_group()` gets entered and exited
in different asyncio tasks → `unhandled errors in a TaskGroup` → the
agent silently loses all its tools (charts/reports/pdf) and tasks fail
intermittently (issue google/adk-python#4454, no upstream fix).

This exposes the SAME @mcp.tool() functions over an ordinary JSON HTTP
endpoint on the SAME Starlette app the MCP server already serves. The BA
agent calls them with a plain httpx.post — no MCP client, no anyio
cancel scope, no race. Tool logic stays here (no duplication into the
agent); only the agent→server transport changes.

Route: POST /api/tool/{name}
  body: JSON object of keyword arguments
  resp: {"result": "<tool return string>"} or {"error": "..."} 4xx/5xx
"""
import inspect
import logging

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from tools.data_io import list_workspace, ensure_directory, read_result, read_csv
from tools.analysis import analyze_data
from tools.charts import generate_chart, generate_distribution_plots
from tools.reports import (
    create_report_from_markdown,
    create_html_report,
    export_pdf,
    export_pptx,
)

logger = logging.getLogger("business-analysis-mcp")

# Allowlist — exactly the @mcp.tool() functions the BA agent uses.
_TOOLS = {
    "list_workspace": list_workspace,
    "ensure_directory": ensure_directory,
    "read_result": read_result,
    "read_csv": read_csv,
    "analyze_data": analyze_data,
    "generate_chart": generate_chart,
    "generate_distribution_plots": generate_distribution_plots,
    "create_report_from_markdown": create_report_from_markdown,
    "create_html_report": create_html_report,
    "export_pdf": export_pdf,
    "export_pptx": export_pptx,
}


async def _handle(request: Request) -> JSONResponse:
    name = request.path_params.get("name", "")
    fn = _TOOLS.get(name)
    if fn is None:
        return JSONResponse(
            {"error": f"Unknown tool '{name}'. Allowed: {sorted(_TOOLS)}"},
            status_code=404,
        )
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            {"error": "Body must be a JSON object of keyword arguments."},
            status_code=400,
        )
    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": f"Body must be a JSON object, got {type(payload).__name__}."},
            status_code=400,
        )
    try:
        if inspect.iscoroutinefunction(fn):
            result = await fn(**payload)
        else:
            result = fn(**payload)
    except TypeError as e:
        logger.warning(f"[http_api] {name} bad args: {e}")
        return JSONResponse({"error": f"Bad arguments for {name}: {e}"}, status_code=400)
    except Exception as e:
        logger.exception(f"[http_api] {name} raised")
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return JSONResponse({"result": result if result is not None else ""})


def register_http_api(app) -> None:
    """Attach POST /api/tool/{name} to the MCP server's Starlette app."""
    app.router.routes.append(
        Route("/api/tool/{name}", _handle, methods=["POST"])
    )
    logger.info(
        "HTTP tool shim mounted: POST /api/tool/{name} "
        f"({', '.join(sorted(_TOOLS))})"
    )
