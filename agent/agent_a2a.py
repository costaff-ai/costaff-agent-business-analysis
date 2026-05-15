import os
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from agent import business_analysis_agent

PORT = int(os.getenv("PORT", "8081"))
# Use the service name as defined in the generated compose fragment
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "costaff-agent-business-analysis")

app = to_a2a(business_analysis_agent, host=PUBLIC_HOST, port=PORT, protocol="http")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
