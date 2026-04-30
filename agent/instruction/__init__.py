"""Auto-load `system.md` and provide a build_instruction() helper.

Usage:
    from instruction import build_instruction
    instruction = build_instruction()

Substitutes runtime placeholders ({PREFERRED_LANGUAGE}, {SHARED_DIR},
{COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS}) with values from environment
variables. Falls back to a generic placeholder if `system.md` is missing.
"""
import os
from pathlib import Path

_SYSTEM_PATH = Path(__file__).parent / "system.md"

if _SYSTEM_PATH.exists():
    instruction_content = _SYSTEM_PATH.read_text(encoding="utf-8")
else:
    instruction_content = "You are a helpful AI assistant."


def build_instruction() -> str:
    """Substitute runtime placeholders in the instruction template."""
    preferred_lang = os.getenv("COSTAFF_PREFERRED_LANGUAGE", "English")
    shared_dir = os.getenv(
        "COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS",
        "/app/data/shared/costaff-agent-business-analysis",
    )
    return (
        instruction_content
        .replace("{PREFERRED_LANGUAGE}", preferred_lang)
        .replace("{COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS}", shared_dir)
        .replace("{SHARED_DIR}", "/app/data/shared/")
    )
