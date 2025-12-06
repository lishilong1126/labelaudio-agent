
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

async def verify_music_template():
    print("🚀 Starting Music Template Generation Verification...")
    
    agent, client = await create_annotation_agent(Config.LLM_MODEL, Config.LLM_API_KEY, Config.LLM_BASE_URL)
    
    # Task explicitly asks for a NEW project for MUSIC to trigger dynamic generation
    task = "Please create a new project named 'Verify_Music_Project' for Classical Music Annotation. I need to label segments as 'Adagio', 'Allegro', 'Andante' and also annotate the 'Instrument' (Violin, Piano, Flute) for each segment."
    
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
    asyncio.run(verify_music_template())
