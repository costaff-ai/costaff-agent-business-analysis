"""Model selector: pick the LLM to use based on model provider env vars.

Resolution order:
    BUSINESS_ANALYSIS_AGENT_MODEL_PROVIDER → COSTAFF_AGENT_MODEL_PROVIDER → "gemini"

If provider == "litellm":
    use the LiteLlm instance from litellm_model.py (configured via
    LITELLM_MODEL_NAME / LITELLM_API_BASE / LITELLM_API_KEY)
otherwise:
    use the Gemini model name string from gemini_model.py
    (BUSINESS_ANALYSIS_AGENT_MODEL, default gemini-2.5-flash)
"""
import os

from .gemini_model import gemini_model

_provider = (
    os.getenv("BUSINESS_ANALYSIS_AGENT_MODEL_PROVIDER")
    or os.getenv("COSTAFF_AGENT_MODEL_PROVIDER")
    or "gemini"
).lower()

if _provider == "litellm":
    from .litellm_model import litellm_model
    selected_model = litellm_model
else:
    selected_model = gemini_model
