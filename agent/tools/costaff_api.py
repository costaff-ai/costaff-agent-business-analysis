"""The 4 shared manager-core tools as native function tools.

httpx → the costaff-core plain-HTTP shim (POST /api/tool/{name} on
costaff-mcp-costaff, already deployed). No MCP client on this side →
no anyio cancel-scope race. DB/notifiers/bot-tokens stay centralised in
the costaff-mcp container; nothing duplicated here.
"""
import os

from ._http import call_shim

_BASE = os.getenv("COSTAFF_CORE_API_URL", "http://costaff-mcp-costaff:8081")


def send_message_now(
    channel: str,
    recipient: str,
    body: str = None,
    subject: str = None,
    app_name: str = "costaff_agent",
    user_id: str = None,
    session_id: str = None,
) -> str:
    """Immediately send a progress/status message to the user's channel.

    Use at meaningful checkpoints when the task carries a
    [PROGRESS_CONTEXT] block. Prefix body with [BA], plain text, no emoji.
    channel/recipient/user_id/session_id come from [PROGRESS_CONTEXT].
    """
    return call_shim(
        _BASE, "send_message_now",
        channel=channel, recipient=recipient, body=body, subject=subject,
        app_name=app_name, user_id=user_id, session_id=session_id,
    )


def add_task_comment(
    task_id: str, user_id: str, author: str, content: str,
    comment_type: str = "note",
) -> str:
    """Add a permanent comment to a ProjectTask (task history).

    author: 'user' or 'business_analysis_agent'.
    comment_type: result | decision | issue | note.
    """
    return call_shim(
        _BASE, "add_task_comment",
        task_id=task_id, user_id=user_id, author=author,
        content=content, comment_type=comment_type,
    )


def move_to_shared(src_path: str, overwrite: bool = False) -> str:
    """Copy a file/dir from a private workspace to the shared workspace.

    src_path: absolute path under /app/data. Mirrored under /app/data/shared/.
    """
    return call_shim(_BASE, "move_to_shared", src_path=src_path, overwrite=overwrite)


def list_data_files(path: str, pattern: str = None) -> str:
    """List files under a path inside /app/data — verify outputs exist.

    path: absolute path under /app/data. pattern: optional glob (e.g. '*.pdf').
    """
    return call_shim(_BASE, "list_data_files", path=path, pattern=pattern)


def report_step(
    session_id: str,
    step: str,
    status: str,
    agent: str = "business_analysis_agent",
    channel: str = "telegram",
    user_id: str = "",
) -> str:
    """Report ONE work step to the user's live progress panel (a single
    Telegram message that updates in place).

    Call this for every major step of the task:
      - when the step STARTS:  report_step(session_id=..., step="生成圖表", status="doing", ...)
      - when it FINISHES:      report_step(session_id=..., step="生成圖表", status="done", ...)
      - if it FAILED:          report_step(session_id=..., step="生成圖表", status="failed", ...)

    session_id / channel / user_id come from the task's [PROGRESS_CONTEXT]
    block. `step` is a short human label (same label for its doing→done
    pair). status: "doing" | "done" | "failed".
    """
    return call_shim(
        _BASE, "report_step",
        session_id=session_id, step=step, status=status,
        agent=agent, channel=channel, user_id=user_id,
    )


def load_costaff_api_tools() -> list:
    """Return the shared manager-core tools as native ADK function tools."""
    return [send_message_now, add_task_comment, move_to_shared,
            list_data_files, report_step]
