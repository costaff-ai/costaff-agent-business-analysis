from pathlib import Path

AGENT_INSTRUCTION = (Path(__file__).parent / "instructions" / "agent_instruction.md").read_text()
