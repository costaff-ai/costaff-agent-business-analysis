"""
Test configuration for BA MCP tools.

Injects a fake `core` module into sys.modules before any tool file is imported,
so the tools can run without a live MCP server or Docker environment.
"""
import sys
import types
import tempfile
import shutil
import atexit
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# mcp/ must be on sys.path so "from core import ..." and "from tools.X import ..." work
MCP_DIR = Path(__file__).parent.parent / "mcp"
sys.path.insert(0, str(MCP_DIR))

# Create temp dirs once for the whole test session (at collection time, before imports)
_TMP_BASE = Path(tempfile.mkdtemp(prefix="ba_mcp_test_"))
_SHARED_DIR = _TMP_BASE / "shared"
_AGENT_DIR = _TMP_BASE / "agent"
_SHARED_DIR.mkdir()
_AGENT_DIR.mkdir()

# Build fake core with no-op mcp.tool() decorator
_fake_core = types.ModuleType("core")
_fake_core.mcp = MagicMock()
_fake_core.mcp.tool.return_value = lambda f: f   # @mcp.tool() returns function unchanged
_fake_core.WORKSPACE_DIR = str(_AGENT_DIR)
_fake_core.SHARED_DIR = str(_SHARED_DIR)
_fake_core.COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS = str(_AGENT_DIR)
_fake_core.ensure_dir = lambda path: Path(path).mkdir(parents=True, exist_ok=True)
_fake_core.abs_workspace = lambda f: str(_AGENT_DIR / f)
_fake_core.abs_shared = lambda f: str(_SHARED_DIR / f)
_fake_core.abs_my_shared = lambda f: str(_AGENT_DIR / f)

sys.modules["core"] = _fake_core

atexit.register(shutil.rmtree, _TMP_BASE, True)


@pytest.fixture
def shared_dir():
    """Shared workspace directory (maps to SHARED_DIR inside container)."""
    return _SHARED_DIR


@pytest.fixture
def agent_dir():
    """BA agent output directory (maps to COSTAFF_SHARED_DIR_BUSINESS_ANALYSIS)."""
    return _AGENT_DIR
