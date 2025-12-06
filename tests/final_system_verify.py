
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from agents.orchestrator import create_master_agent
from config import Config
from mcp_client.agent_logger import AgentExecutionLogger

load_dotenv()

async def final_acceptance_test():
    print("🚀 Starting FINAL System Acceptance Test...")
    
    # 1. Initialize Master Agent
    agent, clients = await create_master_agent()
    
    # 2. Define User Task
    audio_url = "https://shilong-test.oss-cn-beijing.aliyuncs.com/DB_0528_0011_01_2_A_0003.wav?Expires=1765048679&OSSAccessKeyId=TMP.3KnFwd6kF79GN4hDxRzyWRrQNZd9VWYWy1Acd11vr1RCp246vwqmGaddiKc9VG2BmQfsoBVhCBL9KXaBpktUvBpANfSh9q&Signature=ujgxnhnYJtO0ogVSbdC%2Bc9EPxYU%3D"
    
    task_description = f"""
    Please analyze this audio: {audio_url}
    
    Requirements:
    1. Perform Speech-to-Text (Transcription).
    2. Detect Start/End timestamps.
    3. Identify Speakers.
    4. Detect Audio Events.
    5. FINALLY: Create a NEW Label Studio project named 'Final_Acceptance_Project' and IMPORT these results.
    """
    
    print(f"📝 Task: Use Master Agent to process audio and import to Label Studio.")
    print("-" * 50)
    
    try:
        # 3. Execute Master Agent
        response = await agent.ainvoke({"messages": [("user", task_description)]})
        print("\n✅ Execution Complete.")
        print("-" * 50)
        print(response["messages"][-1].content)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # 4. Cleanup
        for client in clients:
            try:
                await client.aclose()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(final_acceptance_test())
