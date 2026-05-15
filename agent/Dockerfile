FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential patch && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Vendored fix for the anyio CancelScope cross-task race in MCP
# StreamableHTTP (upstream PR google/adk-python#5509, not yet merged).
# Adds McpToolset(use_isolated_event_loop=True). Remove this block and the
# adk_patches/ dir once the PR lands in a released google-adk version.
COPY adk_patches /app/adk_patches
# --batch: never prompt (a prompt would consume the patch stream from stdin
# and silently drop later hunks). After applying, VERIFY every required
# insertion landed — fail the build loudly rather than ship a half-patched
# ADK that silently falls back to the racy code path.
RUN SITE=$(python -c "import site; print(site.getsitepackages()[0])") && \
    cd "$SITE" && \
    patch -p2 --batch --fuzz 3 < /app/adk_patches/5509-isolated-event-loop.patch && \
    test -f google/adk/tools/mcp_tool/mcp_thread_utils.py && \
    grep -q "def list_tools_in_thread" google/adk/tools/mcp_tool/mcp_thread_utils.py && \
    grep -q "use_isolated_event_loop: bool = False" google/adk/tools/mcp_tool/mcp_toolset.py && \
    grep -q "self._use_isolated_event_loop = use_isolated_event_loop" google/adk/tools/mcp_tool/mcp_toolset.py && \
    grep -q "from .mcp_thread_utils import list_tools_in_thread" google/adk/tools/mcp_tool/mcp_toolset.py && \
    grep -q "use_isolated_event_loop" google/adk/tools/mcp_tool/mcp_tool.py && \
    echo "PR#5509 patch fully applied + verified"

COPY . .

EXPOSE 8081

CMD ["python", "agent_a2a.py"]
