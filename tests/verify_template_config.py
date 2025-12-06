
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from agents.annotation_specialist import create_annotation_agent
from config import Config
from mcp_client.agent_logger import AgentExecutionLogger

load_dotenv()

async def verify_template():
    print("🚀 Starting Dynamic Template Verification...")
    
    agent, client = await create_annotation_agent(Config.LLM_MODEL, Config.LLM_API_KEY, Config.LLM_BASE_URL)
    
    # Task explicitly asks for a NEW project to trigger create_project
    task = "Please create a new project named 'Verify_Template_Project' for generic speech analysis. Ensure you use the Super Audio Template."
    
    print(f"📝 Task: {task}")
    
    try:
        response = await agent.ainvoke({"messages": [("user", task)]})
        print("\n✅ Execution Complete.")
        print("-" * 50)
        print(response["messages"][-1].content)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(verify_template())
