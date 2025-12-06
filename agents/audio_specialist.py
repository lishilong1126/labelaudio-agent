"""
Audio Analysis Specialist Agent
===============================
Responsible for:
1. Deep Audio Analysis (ASR, Diarization, Event Detection)
2. Normalizing results into standard formats
3. Handling large file processing via 'Pass-by-Reference'
"""

import logging
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from mcp_client.mcp_client import create_mcp_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the **Audio Analysis Specialist**.
Your role is to listen, transcribe, and understand audio data.

## Capabilities
- **Transcription**: Use `transcribe_audio` or `transcribe_simple` to convert speech to text.
- **Diarization**: Use `transcribe_with_speakers` to identify *who* is speaking.
- **Event Detection**: Use `detect_audio_events` or `comprehensive_audio_analysis` to find non-speech events (laughter, music, etc.).
- **Timestamping**: Use `get_word_timestamps` for precision alignment.

## Guidelines
1. **Pass-by-Reference**: TOOLS now return a `full_result_path` (e.g., `/tmp_results/x.json`). You MUST strictly output this path in your final answer so the Master Agent can use it.
2. **Context Safety**: Do NOT output the full JSON content or read the file. It is too large. Just confirm the summary and provide the **absolute file path**.
3. **Tool Selection**:
    - For Transcription -> `transcribe_audio` (best for file generation).
    - For Summary/Analysis -> `comprehensive_audio_analysis` (now also returns file path).
4. **Final Answer Format**: "Analysis complete. File saved at: [ABSOLUTE PATH]"
"""

async def create_audio_agent(model_name: str, api_key: str, base_url: str):
    """Factory to create the Audio Specialist Agent"""
    
    # 1. Connect to Audio + Paraformer Servers
    client = await create_mcp_client(servers=["audio_server", "paraformer_server"])
    tools = await client.get_tools()
    
    logger.info(f"🎙️  Audio Agent loaded tools: {[t.name for t in tools]}")
    
    # 2. Create Agent
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0
    )
    
    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )
    
    return agent, client
