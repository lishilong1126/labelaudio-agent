import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Setup path
sys.path.append(os.getcwd())

# Config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_mas")

# Load Env
load_dotenv()

async def test_mas_workflow():
    print("🚀 Starting Multi-Agent System Verification...")
    
    from agents.orchestrator import create_master_agent
    
    # 1. Create Master Agent
    print("🤖 Creating Master Agent...")
    try:
        agent, clients = await create_master_agent()
        print("✅ Master Agent Created")
    except Exception as e:
        print(f"❌ Failed to create Master Agent: {e}")
        return

    # 2. Define Test Task
    audio_url = "https://shilong-test.oss-cn-beijing.aliyuncs.com/DB_0528_0011_01_2_A_0003.wav?Expires=1765048679&OSSAccessKeyId=TMP.3KnFwd6kF79GN4hDxRzyWRrQNZd9VWYWy1Acd11vr1RCp246vwqmGaddiKc9VG2BmQfsoBVhCBL9KXaBpktUvBpANfSh9q&Signature=ujgxnhnYJtO0ogVSbdC%2Bc9EPxYU%3D"
    task = f"""
    Please process this audio URL: {audio_url}
    1. Transcribe it using the Audio Specialist.
    2. Import the result into a Label Studio project (Project ID 5) using the Annotation Specialist.
    """
    
    print(f"📝 Sending Task: {task.strip()[:100]}...")
    
    # 3. Invoke Agent
    try:
        response = await agent.ainvoke({"messages": [("user", task)]})
        print("\n✅ Agent Response:")
        print(response["messages"][-1].content)
    except Exception as e:
        print(f"\n❌ Agent Execution Failed: {e}")
        
    # 4. Cleanup
    for client in clients:
        if hasattr(client, "aclose"):
            await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_mas_workflow())
