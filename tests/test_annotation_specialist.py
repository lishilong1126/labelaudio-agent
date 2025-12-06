import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())
logging.basicConfig(level=logging.INFO)
load_dotenv()

async def test_annotation_specialist():
    print("🚀 Testing Annotation Specialist...")
    from agents.annotation_specialist import create_annotation_agent
    from audio_agent import Config
    
    # 1. Create Agent
    agent, client = await create_annotation_agent(Config.LLM_MODEL, Config.LLM_API_KEY, Config.LLM_BASE_URL)
    
    # 2. Find a result file
    import glob
    files = glob.glob("tmp_results/*.json")
    if not files:
        print("❌ No result files found in tmp_results/")
        return
    
    target_file = os.path.abspath(files[0])
    print(f"📂 Using result file: {target_file}")
    
    # 3. Send Task
    task = f"Create a new Label Studio project named 'Test Specialist Project' and import the analysis result from: {target_file}"
    
    try:
        response = await agent.ainvoke({"messages": [("user", task)]})
        print("\n✅ Specialist Response:")
        print(response["messages"][-1].content)
    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_annotation_specialist())
