import os
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from a2a.types import AgentCard
from agent import business_analysis_agent

PORT = int(os.getenv("PORT", "8081"))
# Use the service name as defined in the generated compose fragment
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "costaff-ext-ba-agent")

# Minimal agent card — no individual tool skills exposed to parent agent.
agent_card = AgentCard(
    name=business_analysis_agent.name,
    url=f"http://{PUBLIC_HOST}:{PORT}",
    description=business_analysis_agent.description,
    version="1.0.0",
    capabilities={
        "display_name": "AI 數據分析與報告人員"
    },
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
)

app = to_a2a(business_analysis_agent, host=PUBLIC_HOST, port=PORT, protocol="http", agent_card=agent_card)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
