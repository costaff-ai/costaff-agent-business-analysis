import os
import uvicorn

# --- Experiment 2026-05-15: force A2A Agent Executor V2 ---------------------
# The legacy A2A executor structures the agent run such that the MCP
# ClientSession's anyio cancel scope is entered and exited in different
# tasks, which under anyio 4.x raises "unhandled errors in a TaskGroup
# (1 sub-exception)" and the sub-agent silently loses all its MCP tools.
# Executor V2 (ExecutorImpl) runs the agent inside a single structured
# `async with Aclosing(runner.run_async(...))` context, which may avoid
# the cross-task cancel-scope mismatch.
#
# `to_a2a()` does not expose force_new_version, so we patch the default
# before the executor is instantiated. This is a reversible one-file
# change — delete this block to revert to the legacy executor.
import google.adk.a2a.executor.a2a_agent_executor as _aexec

_orig_executor_init = _aexec.A2aAgentExecutor.__init__


def _force_v2_init(self, *args, **kwargs):
    kwargs.setdefault("force_new_version", True)
    _orig_executor_init(self, *args, **kwargs)


_aexec.A2aAgentExecutor.__init__ = _force_v2_init
# --- end experiment --------------------------------------------------------

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from agent import business_analysis_agent

PORT = int(os.getenv("PORT", "8081"))
# Use the service name as defined in the generated compose fragment
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "costaff-agent-business-analysis")

app = to_a2a(business_analysis_agent, host=PUBLIC_HOST, port=PORT, protocol="http")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
