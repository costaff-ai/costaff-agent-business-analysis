"""before_model_callback SPIKE — observability ONLY, fail-safe.

Decides whether PROGRESS_CONTEXT is present in the ACTUAL LlmRequest the
model receives for the A2A-invoked BA agent — the surface that
tool_context.user_content / before_agent user_content could NOT see
(iter1/iter2 logged "no PROGRESS_CONTEXT"). If it IS here, the reliable
automatic panel is achievable (before_model parses once → state →
tool callbacks report each tool).

Logs ONE decisive line per invocation. Returns None and never raises —
ADK treats a truthy before_model_callback return as "skip the model
call", so this must NOT alter execution.
"""
import logging
import re

logger = logging.getLogger("progress")

_SEEN = set()  # invocation ids already logged (one decisive line each)
_RE = {
    "user_id": re.compile(r"^\s*user_id\s*=\s*(.+?)\s*$", re.M),
    "channel": re.compile(r"^\s*channel\s*=\s*(.+?)\s*$", re.M),
    "session_id": re.compile(r"^\s*session_id\s*=\s*(.+?)\s*$", re.M),
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


async def before_model_callback(callback_context, llm_request):
    try:
        inv = getattr(callback_context, "invocation_id", None) or id(llm_request)
        if inv in _SEEN:
            return None
        _SEEN.add(inv)
        if len(_SEEN) > 512:
            _SEEN.clear()

        contents = getattr(llm_request, "contents", None) or []
        ctext = "\n".join(_txt(c) for c in contents)
        cfg = getattr(llm_request, "config", None)
        sysi = _txt(getattr(cfg, "system_instruction", None)) if cfg is not None else ""

        where = []
        if "[PROGRESS_CONTEXT]" in ctext:
            where.append("contents")
        if "[PROGRESS_CONTEXT]" in sysi:
            where.append("system_instruction")

        if where:
            blob = ctext + "\n" + sysi
            g = {}
            for k, rx in _RE.items():
                m = rx.search(blob)
                g[k] = m.group(1).strip() if m else None
            logger.info(
                f"[pm-spike] PROGRESS_CONTEXT FOUND in {where} → "
                f"session_id={g['session_id']!r} channel={g['channel']!r} "
                f"user_id={g['user_id']!r}"
            )
        else:
            logger.info(
                f"[pm-spike] PROGRESS_CONTEXT NOT in llm_request "
                f"(contents_len={len(ctext)} sysi_len={len(sysi)})"
            )
    except Exception:
        logger.info("[pm-spike] failed", exc_info=True)
    return None  # MUST be None — never skip the model call
