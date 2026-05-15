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
RUN SITE=$(python -c "import site; print(site.getsitepackages()[0])") && \
    cd "$SITE" && patch -p2 < /app/adk_patches/5509-isolated-event-loop.patch

COPY . .

EXPOSE 8081

CMD ["python", "agent_a2a.py"]
