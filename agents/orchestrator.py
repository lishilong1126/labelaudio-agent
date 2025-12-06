"""
Master Orchestrator Agent
=========================
The "Brain" of the Multi-Agent System.
Responsible for interpreting user requests and delegating to specialists.
"""

import logging
from typing import Annotated, TypedDict, Union, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.audio_specialist import create_audio_agent
from agents.annotation_specialist import create_annotation_agent
from config import Config  # Updated import

logger = logging.getLogger(__name__)

# ==========================================
# 1. Define Sub-Agent Tools
# ==========================================
# These tools wrap the sub-agents. The Master Agent will "call" these tools
# which in turn invoke the sub-agent's executor.

audio_agent_executor = None
annotation_agent_executor = None

@tool
async def delegate_to_audio_specialist(task: str) -> str:
    """
    Delegate a task to the Audio Analysis Specialist.
    Use this for: Transcription, Diarization, Speaker ID, Audio Event Detection.
    Args:
        task: A clear, self-contained instruction for the audio agent (e.g., "Transcribe https://...").
    Returns:
        The result of the analysis (usually a summary + file path).
    """
    logger.info(f"👉 Delegating to Audio Agent: {task}")
    if not audio_agent_executor:
        return "Error: Audio andent not initialized."
        
    response = await audio_agent_executor.ainvoke({"messages": [HumanMessage(content=task)]})
    return response["messages"][-1].content

@tool
async def delegate_to_annotation_specialist(task: str) -> str:
    """
    Delegate a task to the Label Studio Annotation Specialist.
    Use this for: Creating projects, Generating templates, Importing data.
    args:
        task: A detailed instruction including:
              1. The ACTION (Create/Import)
              2. The PROJECT NAME
              3. The AUDIO URL (Vital!)
              4. The DATA FILE PATH
              (e.g., "Create project X for audio https://... and import ./tmp/result.json")
    Returns:
        Confirmation of action.
    """
    logger.info(f"👉 Delegating to Annotation Agent: {task}")
    if not annotation_agent_executor:
        return "Error: Annotation agent not initialized."
        
    response = await annotation_agent_executor.ainvoke({"messages": [HumanMessage(content=task)]})
    return response["messages"][-1].content

# ==========================================
# 2. Master Agent Logic
# ==========================================

MASTER_SYSTEM_PROMPT = """You are the **Master Orchestrator** for an intelligent audio annotation system.
Your job is to coordinate a team of specialized agents to fulfill user requests.

## Your Team
1. **Audio Specialist**: Experts in listening, transcribing, and understanding audio. Pass them the audio URL.
2. **Annotation Specialist**: Experts in Label Studio. Pass them the analysis results (file paths) to create projects and imports.

## Workflow Example
**User**: "Transcribe this file and put it in Label Studio."
**You**:
1. Call `delegate_to_audio_specialist` with "Transcribe [URL]...".
2. Receive response: "Done. Result saved to ./tmp/result.json".
3. Call `delegate_to_annotation_specialist` with "Create proper project and import ./tmp/result.json".
4. Receive response: "Project created, data imported."
5. Reply to User: "Success! Transcribed and imported to Project X."

## Rules
1. **ALWAYS** delegate complex work.
2. **CRITICAL**: When delegating to Annotation Specialist, you MUST include the **original Audio URL** in the task description. The specialist needs it for the import.
3. Pass file paths explicitly.
4. **One-Shot Execution**: Do not stop to ask the user for confirmation after every step. If the user's intent is clear (e.g., "Transcribe and Import"), execute the full pipeline.
5. **No Hallucination**: Do not make up file paths. Only use paths returned by the Audio Agent.
6. **Efficiency**: Delegate immediately.
"""

async def create_master_agent():
    """Initialize the full multi-agent capability"""
    global audio_agent_executor, annotation_agent_executor
    
    # 1. Initialize Sub-Agents
    # Note: sharing the same LLM config for now
    audio_agent_executor, audio_client = await create_audio_agent(
        Config.LLM_MODEL, Config.LLM_API_KEY, Config.LLM_BASE_URL
    )
    
    annotation_agent_executor, annot_client = await create_annotation_agent(
        Config.LLM_MODEL, Config.LLM_API_KEY, Config.LLM_BASE_URL
    )
    
    # 2. Define Master Tools
    master_tools = [delegate_to_audio_specialist, delegate_to_annotation_specialist]
    
    # 3. Create Master LLM
    llm = ChatOpenAI(
        model=Config.LLM_MODEL,
        api_key=Config.LLM_API_KEY,
        base_url=Config.LLM_BASE_URL,
        temperature=0
    )
    
    # 4. Use simple Tool Calling Agent (Re-using deepagents helper for consistency)
    from deepagents import create_deep_agent
    master_agent = create_deep_agent(
        model=llm,
        tools=master_tools,
        system_prompt=MASTER_SYSTEM_PROMPT
    )
    
    return master_agent, [audio_client, annot_client]
