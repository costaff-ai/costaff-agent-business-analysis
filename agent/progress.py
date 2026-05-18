"""Code-driven live progress panel for the A2A-served BA agent.

The Manager-side before_tool_callback (costaff core) deterministically
appends a real [PROGRESS_CONTEXT] block (user_id / channel /
session_id=task_<id>) into BA's request, so it arrives in
llm_request.contents. This module turns that into the user's single
live Telegram panel WITHOUT any LLM involvement:

  before_model_callback : parse the block once → callback state
  before_tool_callback  : each real tool starts  → report_step "doing"
  after_tool_callback   : each real tool finishes → "done" / "failed"

Core panel_finalize (executor) flips the header to Done/Failed when the
task ends. Every callback is fail-safe: it never raises and always
returns None, so it can never skip a model/tool call.
"""
import asyncio
import logging
import re

from tools._http import call_shim
from tools.costaff_api import _BASE

logger = logging.getLogger("progress")

_RE = {
    "user_id": re.compile(r"^\s*user_id\s*=\s*(.+?)\s*$", re.M),
    "channel": re.compile(r"^\s*channel\s*=\s*(.+?)\s*$", re.M),
    "session_id": re.compile(r"^\s*session_id\s*=\s*(.+?)\s*$", re.M),
}

# Plumbing the user should not see as work lines (the 4 shared core
# tools + report_step itself). BA's real verbs (generate_chart,
# export_pdf, create_html_report, ...) are NOT in this set → each shows.
_PLUMBING = {
    "send_message_now",
    "add_task_comment",
    "move_to_shared",
    "list_data_files",
    "report_step",
}


def _txt(x) -> str:
    try:
        if x is None:
            return ""
        if isinstance(x, str):
            return x
        parts = getattr(x, "parts", None)
        if parts:
            return "\n".join((getattr(p, "text", "") or "") for p in parts)
        return str(x)
    except Exception:
        return ""


def _pc_from_state(tool_context):
    try:
        st = getattr(tool_context, "state", None)
        if st is None:
            return None
        return st.get("_pc")
    except Exception:
        return None


async def _report(pc, step, status):
    try:
        await asyncio.to_thread(
            call_shim,
            _BASE,
            "report_step",
            session_id=pc["session_id"],
            step=step,
            status=status,
            channel=pc["channel"],
            user_id=pc["user_id"],
        )
    except Exception:
        logger.info("[panel] report_step failed", exc_info=True)


async def before_model_callback(callback_context, llm_request):
    """Parse the real PROGRESS_CONTEXT once → callback state."""
    try:
        st = getattr(callback_context, "state", None)
        if st is None or st.get("_pc"):
            return None
        contents = getattr(llm_request, "contents", None) or []
        ctext = "\n".join(_txt(c) for c in contents)
        if "[PROGRESS_CONTEXT]" not in ctext:
            return None
        g = {k: (rx.search(ctext).group(1).strip()
                 if rx.search(ctext) else None)
             for k, rx in _RE.items()}
        sid = g["session_id"]
        if not (sid and sid.startswith("task_")):
            return None
        st["_pc"] = {
            "session_id": sid,
            "channel": g["channel"] or "telegram",
            "user_id": g["user_id"] or "",
        }
        logger.info(f"[panel] armed → {sid} ch={g['channel']}")
    except Exception:
        logger.info("[panel] before_model failed", exc_info=True)
    return None


async def before_tool_callback(tool, args, tool_context):
    """Each real tool call → a panel line in 'doing'."""
    try:
        name = getattr(tool, "name", "") or ""
        if name in _PLUMBING:
            return None
        pc = _pc_from_state(tool_context)
        if pc:
            await _report(pc, name, "doing")
    except Exception:
        logger.info("[panel] before_tool failed", exc_info=True)
    return None


async def after_tool_callback(tool, args, tool_context, tool_response):
    """Each real tool finish → flip its line to 'done' / 'failed'."""
    try:
        name = getattr(tool, "name", "") or ""
        if name in _PLUMBING:
            return None
        pc = _pc_from_state(tool_context)
        if not pc:
            return None
        txt = str(tool_response) if tool_response is not None else ""
        ok = "[ERROR]" not in txt and "Traceback" not in txt
        await _report(pc, name, "done" if ok else "failed")
    except Exception:
        logger.info("[panel] after_tool failed", exc_info=True)
    return None
