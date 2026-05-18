"""Live progress panel hooks — ADK callbacks (1.33).

Canonical ADK pattern (per official docs/samples): a tool callback's own
`user_content` is unreliable for an A2A/AgentTool-invoked sub-agent (it
is the latest model/tool turn, not the originating prompt). So we parse
the PROGRESS_CONTEXT block ONCE in `before_agent_callback` — which fires
at agent entry with the real input content — stash it in session
`state`, and the tool callbacks read it back from `tool_context.state`.

Every tool the agent invokes is then auto-reported to costaff-core
`/api/progress_step`, which edits one Telegram message in place.

CONTRACT (critical): all callbacks MUST return None and MUST NOT raise.
ADK 1.33 treats a truthy before_tool_callback return as "skip the tool"
and a truthy after_tool_callback return as "replace the response". A
panel failure can never affect tool execution — everything is wrapped.
"""
import logging
import os
import re

logger = logging.getLogger("progress")

_BASE = os.getenv("COSTAFF_CORE_API_URL", "http://costaff-mcp-costaff:8081")
_SECRET = os.getenv("MCP_SECRET_KEY", "").strip()
_AGENT = "business_analysis_agent"
_STATE_KEY = "_progress_ctx"

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


def _parse_pctx(text: str):
    if not text or "[PROGRESS_CONTEXT]" not in text:
        return None
    vals = {}
    for k, rx in _RE.items():
        m = rx.search(text)
        if m:
            vals[k] = m.group(1).strip()
    if not vals.get("session_id"):
        return None
    return {
        "user_id": vals.get("user_id", ""),
        "channel": vals.get("channel", ""),
        "session_id": vals["session_id"],
    }


async def before_agent_callback(callback_context):
    """Parse PROGRESS_CONTEXT from the agent's real input once and stash
    it in session state for the tool callbacks. One INFO line per task
    so the path is observable without per-tool log spam."""
    try:
        # SPIKE observability: dump the ids ADK gives this A2A sub-agent so
        # we can check whether core can map BA's session back to the task
        # (the principled design needs no PROGRESS_CONTEXT, just a
        # core-mappable session id). One line per task; fail-safe.
        try:
            sess = getattr(callback_context, "session", None)
            sid = getattr(sess, "id", None)
            inv = getattr(callback_context, "invocation_id", None)
            uid = getattr(callback_context, "user_id", None)
            logger.info(
                f"[progress-spike] session.id={sid!r} invocation_id={inv!r} "
                f"user_id={uid!r}"
            )
        except Exception:
            logger.info("[progress-spike] id dump failed", exc_info=True)

        ctx = _parse_pctx(_content_text(getattr(callback_context, "user_content", None)))
        if ctx:
            callback_context.state[_STATE_KEY] = ctx
            logger.info(
                f"[progress] ctx resolved: channel={ctx['channel']} "
                f"session={ctx['session_id']}"
            )
        else:
            logger.info("[progress] no PROGRESS_CONTEXT in agent input — panel off")
    except Exception:
        logger.debug("[progress] before_agent swallowed", exc_info=True)
    return None


def _ctx_from_state(tool_context):
    try:
        return tool_context.state.get(_STATE_KEY)
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
        ctx = _ctx_from_state(tool_context)
        if ctx:
            await _post({
                "action": "step", "key": ctx["session_id"],
                "recipient": ctx["user_id"], "channel": ctx["channel"],
                "session_id": ctx["session_id"], "agent": _AGENT,
                "tool": _tool_name(tool), "phase": "start", "ok": True,
            })
    except Exception:
        logger.debug("[progress] before_tool swallowed", exc_info=True)
    return None  # MUST be None — never skip/alter the tool


async def after_tool_callback(tool, args, tool_context, tool_response):
    try:
        ctx = _ctx_from_state(tool_context)
        if ctx:
            await _post({
                "action": "step", "key": ctx["session_id"],
                "recipient": ctx["user_id"], "channel": ctx["channel"],
                "session_id": ctx["session_id"], "agent": _AGENT,
                "tool": _tool_name(tool), "phase": "end",
                "ok": _ok_from_response(tool_response),
            })
    except Exception:
        logger.debug("[progress] after_tool swallowed", exc_info=True)
    return None  # MUST be None — never replace the tool response
