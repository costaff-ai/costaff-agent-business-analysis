"""Native function tools for the 4 shared manager-core tools.

Instead of opening a 2nd MCP ClientSession to the Costaff core MCP (which
triggers the anyio CancelScope cross-task race and silently strips this
agent of its tools), these call the Costaff core's plain-HTTP shim with
httpx — no MCP client, no anyio cancel scope, no race.

The shim runs inside the costaff-mcp-costaff container, so DB, notifiers
and bot tokens stay centralised there; nothing is duplicated here.

Endpoint base URL comes from COSTAFF_CORE_API_URL (default points at the
in-network MCP service). Bearer auth is sent only if MCP_SECRET_KEY is
set (the MCP server runs auth-less when the key is empty).
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_BASE = os.getenv("COSTAFF_CORE_API_URL", "http://costaff-mcp-costaff:8081").rstrip("/")
_SECRET = os.getenv("MCP_SECRET_KEY", "").strip()
_TIMEOUT = float(os.getenv("COSTAFF_CORE_API_TIMEOUT", "30"))


def _call(tool: str, **kwargs) -> str:
    """POST kwargs to the core HTTP shim and return the tool's string result."""
    headers = {}
    if _SECRET:
        headers["Authorization"] = f"Bearer {_SECRET}"
    url = f"{_BASE}/api/tool/{tool}"
    try:
        resp = httpx.post(url, json=kwargs, headers=headers, timeout=_TIMEOUT)
    except Exception as e:
        logger.error(f"[costaff_api] {tool} transport error: {e}")
        return f"[ERROR] could not reach costaff core API: {e}"
    if resp.status_code != 200:
        try:
            err = resp.json().get("error", resp.text)
        except Exception:
            err = resp.text
        logger.warning(f"[costaff_api] {tool} -> {resp.status_code}: {err}")
        return f"[ERROR] {tool} failed ({resp.status_code}): {err}"
    try:
        return resp.json().get("result", "")
    except Exception:
        return resp.text


def send_message_now(
    channel: str,
    recipient: str,
    body: str = None,
    subject: str = None,
    app_name: str = "costaff_agent",
    user_id: str = None,
    session_id: str = None,
) -> str:
    """Immediately send a progress / status message to the user via their channel.

    Use this at meaningful checkpoints when the dispatch payload contains a
    [PROGRESS_CONTEXT] block. Prefix the body with [BA], plain text, no emoji.

    Args:
      channel: the user's channel (telegram / discord / line / webchat),
        usually taken verbatim from [PROGRESS_CONTEXT].
      recipient: the user id from [PROGRESS_CONTEXT].
      body: the message text (required).
      subject: optional subject line (email-style channels only).
      app_name: ADK app name; leave as default.
      user_id: the user id from [PROGRESS_CONTEXT].
      session_id: the session id from [PROGRESS_CONTEXT].
    """
    return _call(
        "send_message_now",
        channel=channel,
        recipient=recipient,
        body=body,
        subject=subject,
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )


def add_task_comment(
    task_id: str,
    user_id: str,
    author: str,
    content: str,
    comment_type: str = "note",
) -> str:
    """Add a permanent comment to a ProjectTask (forms the task history).

    Args:
      task_id: the ProjectTask id this comment belongs to.
      user_id: the user id (16-char hex) the task belongs to.
      author: 'user' or this agent's name (e.g. 'business_analysis_agent').
      content: the comment body (Markdown allowed).
      comment_type: one of result / decision / issue / note (default note).
    """
    return _call(
        "add_task_comment",
        task_id=task_id,
        user_id=user_id,
        author=author,
        content=content,
        comment_type=comment_type,
    )


def move_to_shared(src_path: str, overwrite: bool = False) -> str:
    """Copy a file/dir from a private workspace to the shared workspace.

    Args:
      src_path: absolute path under /app/data (e.g.
        /app/data/costaff-agent-business-analysis/report.pdf). It is
        mirrored under /app/data/shared/ preserving the relative path.
      overwrite: replace an existing destination when True.
    """
    return _call("move_to_shared", src_path=src_path, overwrite=overwrite)


def list_data_files(path: str, pattern: str = None) -> str:
    """List files under a path inside /app/data — use to verify outputs exist.

    Args:
      path: absolute path under /app/data (e.g.
        /app/data/shared/costaff-agent-coding). A full file path returns
        [EXISTS]/[NOT FOUND].
      pattern: optional filename glob, e.g. "*.csv".
    """
    return _call("list_data_files", path=path, pattern=pattern)


def load_costaff_api_tools() -> list:
    """Return the 4 shared tools as native ADK function tools."""
    return [send_message_now, add_task_comment, move_to_shared, list_data_files]
