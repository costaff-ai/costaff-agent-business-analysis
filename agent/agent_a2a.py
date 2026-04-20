import os
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from a2a.types import AgentCard
from agent import viz_report_agent

PORT = int(os.getenv("PORT", "8081"))
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")

# Minimal agent card — no individual tool skills exposed to parent agent.
agent_card = AgentCard(
    name=viz_report_agent.name,
    url=f"http://{PUBLIC_HOST}:{PORT}",
    description=viz_report_agent.description,
    version="1.0.0",
    capabilities={},
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
)

app = to_a2a(viz_report_agent, host=PUBLIC_HOST, port=PORT, protocol="http", agent_card=agent_card)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
