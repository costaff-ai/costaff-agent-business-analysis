"""Live progress panel hooks — ADK before/after tool callbacks.

Every tool the agent invokes is auto-reported to the costaff-core
`/api/progress_step` endpoint, which maintains a single self-updating
Telegram message ([ Business Analysis Agent ] Working / tool ... Doing).

CONTRACT (critical): these callbacks MUST return None and MUST NOT
raise. ADK 1.33 treats a truthy before_tool_callback return as "skip the
tool, use this response" and a truthy after_tool_callback return as
"replace the tool response". A panel failure can never affect tool
execution — everything is wrapped, returns None.
"""
import logging
import os
import re

logger = logging.getLogger(__name__)

_BASE = os.getenv("COSTAFF_CORE_API_URL", "http://costaff-mcp-costaff:8081")
_SECRET = os.getenv("MCP_SECRET_KEY", "").strip()
_AGENT = "business_analysis_agent"

# invocation_id -> {user_id, channel, session_id} | None  (parse PROGRESS_CONTEXT once)
_PCTX: dict = {}
_RE = {
    "user_id": re.compile(r"^\s*user_id\s*=\s*(.+?)\s*$", re.M),
    "channel": re.compile(r"^\s*channel\s*=\s*(.+?)\s*$", re.M),
    "session_id": re.compile(r"^\s*session_id\s*=\s*(.+?)\s*$", re.M),
}


def _content_text(uc) -> str:
    try:
        if uc is None:
            return ""
        parts = getattr(uc, "parts", None)
        if parts:
            return "\n".join((getattr(p, "text", "") or "") for p in parts)
        return str(uc)
    except Exception:
        return ""


def _progress_ctx(tool_context):
    try:
        inv = getattr(tool_context, "invocation_id", None) or ""
        if inv in _PCTX:
            return _PCTX[inv]
        text = _content_text(getattr(tool_context, "user_content", None))
        ctx = None
        if "[PROGRESS_CONTEXT]" in text:
            vals = {}
            for k, rx in _RE.items():
                m = rx.search(text)
                if m:
                    vals[k] = m.group(1).strip()
            if vals.get("session_id"):
                ctx = {
                    "user_id": vals.get("user_id", ""),
                    "channel": vals.get("channel", ""),
                    "session_id": vals["session_id"],
                }
        if len(_PCTX) > 256:
            _PCTX.clear()
        _PCTX[inv] = ctx
        return ctx
    except Exception:
        return None


async def _post(payload: dict):
    try:
        import httpx
        headers = {}
        if _SECRET:
            headers["Authorization"] = f"Bearer {_SECRET}"
        async with httpx.AsyncClient(timeout=4.0) as c:
            await c.post(f"{_BASE.rstrip('/')}/api/progress_step",
                         json=payload, headers=headers)
    except Exception:
        pass  # fail-safe: the panel must never affect the agent


def _tool_name(tool) -> str:
    return (getattr(tool, "name", None)
            or getattr(tool, "__name__", None) or "tool")


def _ok_from_response(resp) -> bool:
    try:
        s = (resp if isinstance(resp, str) else str(resp))[:300].lower()
        return not any(m in s for m in
                       ("[error]", "traceback", "not found", "exception"))
    except Exception:
        return True


async def before_tool_callback(tool, args, tool_context):
    try:
        ctx = _progress_ctx(tool_context)
        if ctx:
            await _post({
                "action": "step", "key": ctx["session_id"],
                "recipient": ctx["user_id"], "channel": ctx["channel"],
                "session_id": ctx["session_id"], "agent": _AGENT,
                "tool": _tool_name(tool), "phase": "start", "ok": True,
            })
    except Exception:
        logger.debug("[progress] before swallowed", exc_info=True)
    return None  # MUST be None — never skip/alter the tool


async def after_tool_callback(tool, args, tool_context, tool_response):
    try:
        ctx = _progress_ctx(tool_context)
        if ctx:
            await _post({
                "action": "step", "key": ctx["session_id"],
                "recipient": ctx["user_id"], "channel": ctx["channel"],
                "session_id": ctx["session_id"], "agent": _AGENT,
                "tool": _tool_name(tool), "phase": "end",
                "ok": _ok_from_response(tool_response),
            })
    except Exception:
        logger.debug("[progress] after swallowed", exc_info=True)
    return None  # MUST be None — never replace the tool response
